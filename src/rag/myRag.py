import asyncio
from calendar import c
from dataclasses import dataclass
from functools import cache
import hashlib
import json
import logging
import os
from pathlib import Path
from pydoc import doc, text
from typing import Any, Dict, List, Optional,Tuple

from src.config.loader import get_str_env
from src.rag.rag import Rag, Resource
from src.rag.config import RAGConfig
from src.rag.parser import DoclingParser, MineruExecutionError, MineruParser
from src.rag.utils import compute_mdhash_id,generate_cache_key,split_content
from src.rag.modalprocessors import ImageModalProcessor, TableModalProcessor, EquationModalProcessor, GenericModalProcessor
from src.rag.rag import BaseKVStorage, Retriever
from src.myllms.factory import get_llm_by_type

@dataclass
class MyRag(Rag):
    model_processors: Dict[str, Any]
    def __init__(self,context_extractor, vectors_db: Retriever, kv_db: BaseKVStorage, llm_name: str|None = None):
        self.config = RAGConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.vectors_db = vectors_db
        self.kv_db = kv_db
        self.llm_name = get_str_env("RAG_LLM_MODEL","basic")
        self.llm = get_llm_by_type(self.llm_name)
        self.context_extractor = context_extractor
        self._initialize_processors()

    def _initialize_processors(self):
        # Create different multimodal processors based on configuration
        self.modal_processors = {}

        if self.config.enable_image_processing:
            self.modal_processors["image"] = ImageModalProcessor(
                vectors_db=self.vectors_db,
                llm=get_llm_by_type("vision"),
                context_extractor=self.context_extractor,
            )

        if self.config.enable_table_processing:
            self.modal_processors["table"] = TableModalProcessor(
                self.vectors_db,
                self.llm,
                context_extractor=self.context_extractor,   
            )

        if self.config.enable_equation_processing:
            self.modal_processors["equation"] = EquationModalProcessor(
                self.vectors_db,
                self.llm,
                context_extractor=self.context_extractor,   
            )

        # Always include generic processor as fallback
        self.modal_processors["generic"] = GenericModalProcessor(
            self.vectors_db,
            self.llm,
            context_extractor=self.context_extractor,   
        )

        self.logger.info("Multimodal processors initialized with context support")
        self.logger.info(f"Available processors: {list(self.modal_processors.keys())}")


    
    async def process_folder_complete(
        self,
        folder_path: str,
        output_dir: str|None = None,
        parse_method: str|None = None,
        display_stats: bool|None = None,
        file_extensions: Optional[List[str]] = None,
        recursive: bool|None = None,
        max_workers: int|None = None,
        **kwargs,
    ):
        """
        Process all supported files in a folder

        Args:
            folder_path: Path to the folder containing files to process
            output_dir: Directory for parsed outputs (optional)
            parse_method: Parsing method to use (optional)
            display_stats: Whether to display statistics (optional)
            split_by_character: Character to split by (optional)
            split_by_character_only: Whether to split only by character (optional)
            file_extensions: List of file extensions to process (optional)
            recursive: Whether to process folders recursively (optional)
            max_workers: Maximum number of workers for concurrent processing (optional)
        """
        if output_dir is None:
            output_dir = self.config.parser_output_dir
        if parse_method is None:
            parse_method = self.config.parse_method
        if display_stats is None:
            display_stats = True
        if file_extensions is None:
            file_extensions = self.config.supported_file_extensions
        if recursive is None:
            recursive = self.config.recursive_folder_processing
        if max_workers is None:
            max_workers = self.config.max_concurrent_files


        # Get all files in the folder
        folder_path_obj = Path(folder_path)
        if not folder_path_obj.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # Collect files based on supported extensions
        files_to_process = []
        for file_ext in file_extensions:
            if recursive:
                pattern = f"**/*{file_ext}"
            else:
                pattern = f"*{file_ext}"
            files_to_process.extend(folder_path_obj.glob(pattern))

        if not files_to_process:
            self.logger.warning(f"No supported files found in {folder_path}")
            return

        self.logger.info(
            f"Found {len(files_to_process)} files to process in {folder_path}"
        )

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Process files with controlled concurrency
        semaphore = asyncio.Semaphore(max_workers)
        tasks = []

        async def process_single_file(file_path: Path, cache_key: str):
            async with semaphore:
                is_in_subdir = (
                    lambda file_path, dir_path: len(
                        file_path.relative_to(dir_path).parents
                    )
                    > 1
                )(file_path, folder_path_obj)

                try:
                    await self.process_document_complete(
                        str(file_path),
                        output_dir=(
                            output_dir
                            if not is_in_subdir
                            else str(
                                output_path
                                / file_path.parent.relative_to(folder_path_obj)
                            )
                        ),
                        parse_method=parse_method,
                        file_name=(
                            None
                            if not is_in_subdir
                            else str(file_path.relative_to(folder_path_obj))
                        ),
                        cache_key=cache_key,
                        **kwargs
                    )
                    return True, str(file_path), None
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {str(e)}")
                    return False, str(file_path), str(e)

        # Create tasks for all files
        for file_path in files_to_process:
            cache_key = await generate_cache_key(file_path, parse_method, **kwargs)
            if await self.kv_db.has_id(cache_key):
                self.logger.info(f"Skipping already processed file: {file_path}")
                continue
            task = asyncio.create_task(process_single_file(file_path, cache_key))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_files = []
        failed_files = []
        for result in results:
            if isinstance(result, Exception):
                failed_files.append(("unknown", str(result)))
            else:
                success, file_path, error = result
                if success:
                    successful_files.append(file_path)
                else:
                    failed_files.append((file_path, error))

        # Display statistics if requested
        if display_stats:
            self.logger.info("Processing complete!")
            self.logger.info(f"  Successful: {len(successful_files)} files")
            self.logger.info(f"  Failed: {len(failed_files)} files")
            if failed_files:
                self.logger.warning("Failed files:")
                for file_path, error in failed_files:
                    self.logger.warning(f"  - {file_path}: {error}")

    async def process_document_complete(
        self,
        file_path: str,
        output_dir: str|None = None,
        parse_method: str|None = None,
        display_stats: bool|None = None,
        doc_id: str | None = None,
        file_name: str | None = None,
        cache_key: str|None = None,
        **kwargs,
    ):
        """
        Complete document processing workflow

        Args:
            file_path: Path to the file to process
            output_dir: output directory (defaults to config.parser_output_dir)
            parse_method: Parse method (defaults to config.parse_method)
            display_stats: Whether to display content statistics (defaults to config.display_content_stats)
            split_by_character: Optional character to split the text by
            split_by_character_only: If True, split only by the specified character
            doc_id: Optional document ID, if not provided will be generated from content
            **kwargs: Additional parameters for parser (e.g., lang, device, start_page, end_page, formula, table, backend, source)
        """

        # Use config defaults if not provided
        if output_dir is None:
            output_dir = self.config.parser_output_dir
        if parse_method is None:
            parse_method = self.config.parse_method
        if display_stats is None:
            display_stats = self.config.display_content_stats

        self.logger.info(f"Starting complete document processing: {file_path}")

        # Step 1: Parse document
        content_list, content_based_doc_id = await self.parse_document(
            file_path, output_dir, parse_method, display_stats,cache_key=cache_key, **kwargs
        )

        # Use provided doc_id or fall back to content-based doc_id
        if doc_id is None:
            doc_id = content_based_doc_id

        # Step 2: Separate text and multimodal content
        text_content, multimodal_items = self.separate_content(content_list)

        # Step 3: Insert pure text content with all parameters
        if text_content.strip():
            if file_name is None:
                file_name = os.path.basename(file_path)
            chunks = split_content(text_content)
            generic_processor = self.modal_processors["generic"]
            for chunk in chunks:
                await generic_processor.process_multimodal_content(
                    modal_content=chunk,
                    file_path=file_name,
                    doc_id=doc_id, 
                    content_type="text",
                )

        # Step 4: Process multimodal content (using specialized processors)
        if multimodal_items:
            await self._process_multimodal_content(multimodal_items, file_path, doc_id)

        self.logger.info(f"Document {file_path} processing complete!")

    async def parse_document(
        self,
        file_path: str,
        output_dir: str|None = None,
        parse_method: str|None = None,
        display_stats: bool|None = None,
        cache_key: str|None = None,
        **kwargs,
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Parse document with caching support

        Args:
            file_path: Path to the file to parse
            output_dir: Output directory (defaults to config.parser_output_dir)
            parse_method: Parse method (defaults to config.parse_method)
            display_stats: Whether to display content statistics (defaults to config.display_content_stats)
            **kwargs: Additional parameters for parser (e.g., lang, device, start_page, end_page, formula, table, backend, source)

        Returns:
            tuple[List[Dict[str, Any]], str]: (content_list, doc_id)
        """
        # Use config defaults if not provided
        if output_dir is None:
            output_dir = self.config.parser_output_dir
        if parse_method is None:
            parse_method = self.config.parse_method
        if display_stats is None:
            display_stats = self.config.display_content_stats

        self.logger.info(f"Starting document parsing: {file_path}")



        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Choose appropriate parsing method based on file extension
        ext = file_path.suffix.lower()

        try:
            doc_parser = (
                DoclingParser() if self.config.parser == "docling" else MineruParser()
            )

            # Log parser and method information
            self.logger.info(
                f"Using {self.config.parser} parser with method: {parse_method}"
            )

            if ext in [".pdf"]:
                self.logger.info("Detected PDF file, using parser for PDF...")
                content_list = await asyncio.to_thread(
                    doc_parser.parse_pdf,
                    pdf_path=file_path,
                    output_dir=output_dir,
                    method=parse_method,
                    **kwargs,
                )
            elif ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".bmp",
                ".tiff",
                ".tif",
                ".gif",
                ".webp",
            ]:
                self.logger.info("Detected image file, using parser for images...")
                # Use the selected parser's image parsing capability
                if hasattr(doc_parser, "parse_image"):
                    content_list = await asyncio.to_thread(
                        doc_parser.parse_image,
                        image_path=file_path,
                        output_dir=output_dir,
                        **kwargs,
                    )
                else:
                    # Fallback to MinerU for image parsing if current parser doesn't support it
                    self.logger.warning(
                        f"{self.config.parser} parser doesn't support image parsing, falling back to MinerU"
                    )
                    content_list = MineruParser().parse_image(
                        image_path=file_path, output_dir=output_dir, **kwargs
                    )
            elif ext in [
                ".doc",
                ".docx",
                ".ppt",
                ".pptx",
                ".xls",
                ".xlsx",
                ".html",
                ".htm",
                ".xhtml",
            ]:
                self.logger.info(
                    "Detected Office or HTML document, using parser for Office/HTML..."
                )
                content_list = await asyncio.to_thread(
                    doc_parser.parse_office_doc,
                    doc_path=file_path,
                    output_dir=output_dir,
                    **kwargs,
                )
            else:
                # For other or unknown formats, use generic parser
                self.logger.info(
                    f"Using generic parser for {ext} file (method={parse_method})..."
                )
                content_list = await asyncio.to_thread(
                    doc_parser.parse_document,
                    file_path=file_path,
                    method=parse_method,
                    output_dir=output_dir,
                    **kwargs,
                )

        except MineruExecutionError as e:
            self.logger.error(f"Mineru command failed: {e}")
            raise
        except Exception as e:
            self.logger.error(
                f"Error during parsing with {self.config.parser} parser: {str(e)}"
            )
            raise e

        msg = f"Parsing {file_path} complete! Extracted {len(content_list)} content blocks"
        self.logger.info(msg)

        if len(content_list) == 0:
            raise ValueError("Parsing failed: No content was extracted")

        # Generate doc_id based on content
        doc_id = self._generate_content_based_doc_id(content_list)
        content,multiModal_items = self.separate_content(content_list)
        data = {
            cache_key:{
                "content": content,
                "doc_id": doc_id,
                "multiModal_items": multiModal_items,
            }
        }
        await self.kv_db.upsert(data)

        # Display content statistics if requested
        if display_stats:
            self.logger.info("\nContent Information:")
            self.logger.info(f"* Total blocks in content_list: {len(content_list)}")

            # Count elements by type
            block_types: Dict[str, int] = {}
            for block in content_list:
                if isinstance(block, dict):
                    block_type = block.get("type", "unknown")
                    if isinstance(block_type, str):
                        block_types[block_type] = block_types.get(block_type, 0) + 1

            self.logger.info("* Content block types:")
            for block_type, count in block_types.items():
                self.logger.info(f"  - {block_type}: {count}")

        return content_list, doc_id
    
    
    def _generate_content_based_doc_id(self, content_list: List[Dict[str, Any]]) -> str:
        """
        Generate doc_id based on document content

        Args:
            content_list: Parsed content list

        Returns:
            str: Content-based document ID with doc- prefix
        """

        # Extract key content for ID generation
        content_hash_data = []

        for item in content_list:
            if isinstance(item, dict):
                # For text content, use the text
                if item.get("type") == "text" and item.get("text"):
                    content_hash_data.append(item["text"].strip())
                # For other content types, use key identifiers
                elif item.get("type") == "image" and item.get("img_path"):
                    content_hash_data.append(f"image:{item['img_path']}")
                elif item.get("type") == "table" and item.get("table_body"):
                    content_hash_data.append(f"table:{item['table_body']}")
                elif item.get("type") == "equation" and item.get("text"):
                    content_hash_data.append(f"equation:{item['text']}")
                else:
                    # For other types, use string representation
                    content_hash_data.append(str(item))

        # Create a content signature
        content_signature = "\n".join(content_hash_data)

        # Generate doc_id from content
        doc_id = compute_mdhash_id(content_signature, prefix="doc-")

        return doc_id

    def separate_content(
        self,content_list: List[Dict[str, Any]],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Separate text content and multimodal content

        Args:
            content_list: Content list from MinerU parsing

        Returns:
            (text_content, multimodal_items): Pure text content and multimodal items list
        """
        text_parts = []
        multimodal_items = []

        for item in content_list:
            content_type = item.get("type", "text")

            if content_type == "text":
                # Text content
                text = item.get("text", "")
                if text.strip():
                    text_parts.append(text)
            else:
                # Multimodal content (image, table, equation, etc.)
                multimodal_items.append(item)

        # Merge all text content
        text_content = "\n\n".join(text_parts)

        self.logger.info("Content separation complete:")
        self.logger.info(f"  - Text content length: {len(text_content)} characters")
        self.logger.info(f"  - Multimodal items count: {len(multimodal_items)}")

        # Count multimodal types
        modal_types = {}
        for item in multimodal_items:
            modal_type = item.get("type", "unknown")
            modal_types[modal_type] = modal_types.get(modal_type, 0) + 1

        if modal_types:
            self.logger.info(f"  - Multimodal type distribution: {modal_types}")

        return text_content, multimodal_items
    async def _process_multimodal_content(
        self,
        multimodal_items: List[Dict[str, Any]],
        file_path: str,
        doc_id: str,
    ):
        """
        Process multimodal content (using specialized processors)

        Args:
            multimodal_items: List of multimodal items
            file_path: File path (for reference)
            doc_id: Document ID for proper chunk association
            pipeline_status: Pipeline status object
            pipeline_status_lock: Pipeline status lock
        """

        if not multimodal_items:
            self.logger.debug("No multimodal content to process")
            return
        for item in multimodal_items:
            modal_type = item.get("type", "unknown")
            self.logger.info(f"Processing {modal_type} content")
            if modal_type == "discarded":
                self.logger.info(f"Discarding {modal_type} content as per configuration")
                continue
            elif modal_type in self.modal_processors:
                processor = self.modal_processors.get(modal_type)
            else:
                processor = self.modal_processors.get("generic")

            await processor.process_multimodal_content(
                modal_content=item,
                content_type = modal_type,
                file_path=file_path,
                item_info=item,
                doc_id=doc_id, )
    

    async def insert(self,
        folder_path: str,
        output_dir: str|None = None,
        parse_method: str|None = None,
        display_stats: bool|None = None,
        file_extensions: Optional[List[str]] = None,
        recursive: bool|None = None,
        max_workers: int|None = None,
        **kwargs,):
            await self.process_folder_complete(
                folder_path,
                output_dir,
                parse_method,
                display_stats,
                file_extensions,
                recursive,
                max_workers,
                **kwargs,
            )
            
    async def aquery(self, query: str, resources: list[Resource] = []) -> list[str]:
        return self.vectors_db.query_relevant_documents(query, resources)