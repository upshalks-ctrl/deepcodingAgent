"""
Approval tools for user interaction
"""

import os
import json
from typing import Any, Dict, Optional
from datetime import datetime


class ApprovalConfig:
    """Configuration for approval behavior"""

    def __init__(self):
        self.config_file = "approval_config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load approval configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except:
            pass

        # Default configuration
        return {
            "auto_approve": False,
            "auto_approve_write": False,
            "auto_approve_bash": False,
            "auto_approve_plan": False,
            "approved_operations": [],
            "denied_operations": []
        }

    def save_config(self):
        """Save approval configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def set_auto_approve(self, value: bool):
        """Set auto approve for all operations"""
        self.config["auto_approve"] = value
        self.save_config()

    def set_auto_approve_type(self, operation_type: str, value: bool):
        """Set auto approve for specific operation type"""
        self.config[f"auto_approve_{operation_type}"] = value
        self.save_config()

    def is_auto_approved(self, operation_type: str) -> bool:
        """Check if operation type is auto approved"""
        if self.config.get("auto_approve", False):
            return True
        return self.config.get(f"auto_approve_{operation_type}", False)


class ApprovalTool:
    """Tool for getting user approval"""

    name = "request_approval"
    description = "Request user approval for an operation"

    def __init__(self):
        self.config = ApprovalConfig()

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": ApprovalTool.name,
                "description": ApprovalTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "Type of operation (write, bash, plan)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of what needs approval"
                        },
                        "details": {
                            "type": "object",
                            "description": "Additional details about the operation"
                        }
                    },
                    "required": ["operation", "description"]
                }
            }
        }

    async def execute(self, operation: str, description: str, details: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute the approval request"""
        try:
            # Check if auto-approved
            if self.config.is_auto_approved(operation):
                return {
                    "success": True,
                    "approved": True,
                    "auto_approved": True,
                    "message": f"Auto-approved {operation} operation"
                }

            # Create approval request
            request = {
                "id": f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                "operation": operation,
                "description": description,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }

            # Display approval request
            print("\n" + "="*80)
            print("APPROVAL REQUIRED")
            print("="*80)
            print(f"Operation: {operation}")
            print(f"Description: {description}")

            if details:
                print("\nDetails:")
                for key, value in details.items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, indent=2)
                    print(f"  {key}: {value}")

            print("\n" + "-"*80)

            # Get user input
            while True:
                response = input("Approve? (y/n/a/s): ").lower().strip()

                if response == 'y' or response == 'yes':
                    # Remember approval for this session
                    self.config.config["approved_operations"].append(request["id"])
                    self.config.save_config()

                    return {
                        "success": True,
                        "approved": True,
                        "request_id": request["id"],
                        "message": "Operation approved by user"
                    }

                elif response == 'a' or response == 'always':
                    # Set auto-approve for this type
                    self.config.set_auto_approve_type(operation, True)

                    return {
                        "success": True,
                        "approved": True,
                        "auto_approved": True,
                        "message": f"Auto-approved all {operation} operations"
                    }

                elif response == 's' or response == 'skip':
                    return {
                        "success": True,
                        "approved": False,
                        "skipped": True,
                        "message": "Operation skipped"
                    }

                elif response == 'n' or response == 'no':
                    # Remember denial
                    self.config.config["denied_operations"].append(request["id"])
                    self.config.save_config()

                    return {
                        "success": True,
                        "approved": False,
                        "message": "Operation denied by user"
                    }

                else:
                    print("Invalid response. Please enter:")
                    print("  y/yes - Approve this operation")
                    print("  a/always - Auto-approve all operations of this type")
                    print("  s/skip - Skip this operation")
                    print("  n/no - Deny this operation")

        except KeyboardInterrupt:
            return {
                "success": False,
                "approved": False,
                "error": "Approval interrupted"
            }
        except Exception as e:
            return {
                "success": False,
                "approved": False,
                "error": str(e)
            }


class ConfigApprovalTool:
    """Tool for configuring approval settings"""

    name = "configure_approval"
    description = "Configure approval settings"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": ConfigApprovalTool.name,
                "description": ConfigApprovalTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "auto_approve": {
                            "type": "boolean",
                            "description": "Auto-approve all operations"
                        },
                        "auto_approve_write": {
                            "type": "boolean",
                            "description": "Auto-approve file write operations"
                        },
                        "auto_approve_bash": {
                            "type": "boolean",
                            "description": "Auto-approve bash command operations"
                        },
                        "auto_approve_plan": {
                            "type": "boolean",
                            "description": "Auto-approve planning operations"
                        }
                    },
                    "required": []
                }
            }
        }

    async def execute(
        self,
        auto_approve: Optional[bool] = None,
        auto_approve_write: Optional[bool] = None,
        auto_approve_bash: Optional[bool] = None,
        auto_approve_plan: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Execute the configuration"""
        try:
            config = ApprovalConfig()

            if auto_approve is not None:
                config.set_auto_approve(auto_approve)
                message = f"Auto-approve set to: {auto_approve}"
            else:
                updates = []
                if auto_approve_write is not None:
                    config.set_auto_approve_type("write", auto_approve_write)
                    updates.append(f"write: {auto_approve_write}")
                if auto_approve_bash is not None:
                    config.set_auto_approve_type("bash", auto_approve_bash)
                    updates.append(f"bash: {auto_approve_bash}")
                if auto_approve_plan is not None:
                    config.set_auto_approve_type("plan", auto_approve_plan)
                    updates.append(f"plan: {auto_approve_plan}")

                if updates:
                    message = f"Updated auto-approve for: {', '.join(updates)}"
                else:
                    message = "No changes made"

            return {
                "success": True,
                "message": message,
                "config": config.config
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }