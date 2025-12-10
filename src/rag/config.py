"""
Configuration classes for RAGAnything

Contains configuration dataclasses with environment variable support
"""

from dataclasses import dataclass, field
from typing import List

from src.config.loader import get_str_env,get_bool_env,get_int_env


@dataclass
class RAGConfig:
    """Configuration class for RAG with environment variable support"""

    # Directory Configuration
    # ---
    working_dir: str = field(default=get_str_env("WORKING_DIR", "./rag_storage"))
    """Directory where RAG storage and cache files are stored."""

    # Parser Configuration
    # ---
    parse_method: str = field(default=get_str_env("PARSE_METHOD", "auto"))
    """Default parsing method for document parsing: 'auto', 'ocr', or 'txt'."""

    parser_output_dir: str = field(default=get_str_env("OUTPUT_DIR", "./output"))
    """Default output directory for parsed content."""

    parser: str = field(default=get_str_env("PARSER", "mineru"))    
    """Parser selection: 'mineru' or 'docling'."""

    display_content_stats: bool = field(
        default=get_bool_env("DISPLAY_CONTENT_STATS")
    )
    """Whether to display content statistics during parsing."""

    # Multimodal Processing Configuration
    # ---
    enable_image_processing: bool = field(
        default=get_bool_env("ENABLE_IMAGE_PROCESSING")
    )
    """Enable image content processing."""

    enable_table_processing: bool = field(
        default=get_bool_env("ENABLE_TABLE_PROCESSING")
    )
    """Enable table content processing."""

    enable_equation_processing: bool = field(
        default=get_bool_env("ENABLE_EQUATION_PROCESSING")
    )
    """Enable equation content processing."""

    # Batch Processing Configuration
    # ---
    max_concurrent_files: int = field(
        default=get_int_env("MAX_CONCURRENT_FILES", 1)
    )
    """Maximum number of files to process concurrently."""

    supported_file_extensions: List[str] = field(
        default_factory=lambda: get_str_env(
            "SUPPORTED_FILE_EXTENSIONS",
            ".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif,.gif,.webp,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md",
        ).split(",")
    )
    """List of supported file extensions for batch processing."""

    recursive_folder_processing: bool = field(
        default=get_bool_env("RECURSIVE_FOLDER_PROCESSING")
    )
    """Whether to recursively process subfolders in batch mode."""

    # Context Extraction Configuration
    # ---
    context_window: int = field(default=get_int_env("CONTEXT_WINDOW", 1))
    """Number of pages/chunks to include before and after current item for context."""

    context_mode: str = field(default=get_str_env("CONTEXT_MODE", "page"))
    """Context extraction mode: 'page' for page-based, 'chunk' for chunk-based."""

    max_context_tokens: int = field(
        default=get_int_env("MAX_CONTEXT_TOKENS", 2000)
    )
    """Maximum number of tokens in extracted context."""

    chunk_size: int = field(default=get_int_env("CHUNK_SIZE", 1500))
    """Default chunk size for document splitting."""

    include_headers: bool = field(default=get_bool_env("INCLUDE_HEADERS"))
    """Whether to include document headers and titles in context."""

    include_captions: bool = field(
        default=get_bool_env("INCLUDE_CAPTIONS")
    )
    """Whether to include image/table captions in context."""

    context_filter_content_types: List[str] = field(
        default_factory=lambda: get_str_env(
            "CONTEXT_FILTER_CONTENT_TYPES", "text"
        ).split(",")
    )
    """Content types to include in context extraction (e.g., 'text', 'image', 'table')."""

    content_format: str = field(default=get_str_env("CONTENT_FORMAT", "minerU"))
    """Default content format for context extraction when processing documents."""

    def __post_init__(self):
        """Post-initialization setup for backward compatibility"""
        # Support legacy environment variable names for backward compatibility
        legacy_parse_method = get_str_env("MINERU_PARSE_METHOD", None)
        if legacy_parse_method and not get_str_env("PARSE_METHOD", None):
            self.parse_method = legacy_parse_method
            import warnings

            warnings.warn(
                "MINERU_PARSE_METHOD is deprecated. Use PARSE_METHOD instead.",
                DeprecationWarning,
                stacklevel=2,
            )

    @property
    def mineru_parse_method(self) -> str:
        """
        Backward compatibility property for old code.

        .. deprecated::
           Use `parse_method` instead. This property will be removed in a future version.
        """
        import warnings

        warnings.warn(
            "mineru_parse_method is deprecated. Use parse_method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.parse_method

    @mineru_parse_method.setter
    def mineru_parse_method(self, value: str):
        """Setter for backward compatibility"""
        import warnings

        warnings.warn(
            "mineru_parse_method is deprecated. Use parse_method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.parse_method = value
