"""Tool executor for running agent actions."""

from typing import Optional, Dict, Any, List
import uuid
from enum import Enum

from app.models.tool_models import ToolType, ToolRequest, ToolResult, ToolLog
from app.utils.logger import logger

# Import tool modules
from app.tools import file_tools, shell_tools, git_tools, search_tools


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class ToolExecutor:
    """Executes tools and manages results."""
    
    def __init__(self):
        """Initialize executor."""
        self.execution_logs: List[ToolLog] = []
    
    async def execute_tool(
        self,
        tool: ToolType,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Optional[ToolResult]:
        """
        Execute a tool.
        
        Args:
            tool: Tool type to execute
            parameters: Tool parameters
            timeout: Execution timeout in seconds
            
        Returns:
            ToolResult or None if failed
        """
        try:
            execution_id = str(uuid.uuid4())
            
            logger.info(f"Executing tool {tool.value} with parameters {parameters}")
            self._log(ToolLog(
                level="INFO",
                tool=tool,
                message=f"Starting execution of {tool.value}"
            ))
            
            # Execute based on tool type
            result = await self._execute_by_type(tool, parameters, execution_id, timeout)
            
            if result.success:
                self._log(ToolLog(
                    level="INFO",
                    tool=tool,
                    message=f"Successfully executed {tool.value}",
                    details={"execution_id": execution_id}
                ))
            else:
                self._log(ToolLog(
                    level="ERROR",
                    tool=tool,
                    message=f"Failed to execute {tool.value}",
                    details={"error": result.error}
                ))
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing tool: {e}")
            self._log(ToolLog(
                level="ERROR",
                message=f"Exception executing tool {tool.value}: {str(e)}"
            ))
            return None
    
    async def _execute_by_type(
        self,
        tool: ToolType,
        parameters: Dict[str, Any],
        execution_id: str,
        timeout: Optional[int]
    ) -> ToolResult:
        """
        Execute tool based on type.
        
        Args:
            tool: Tool type
            parameters: Parameters
            execution_id: Unique execution ID
            timeout: Timeout in seconds
            
        Returns:
            ToolResult
        """
        try:
            if tool == ToolType.FILE_READ:
                result = await file_tools.read_file(parameters["path"])
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result is not None,
                    output=result.dict() if result else None,
                    execution_time=0.1
                )
            
            elif tool == ToolType.FILE_WRITE:
                result = await file_tools.write_file(
                    parameters["path"],
                    parameters["content"],
                    parameters.get("backup", True)
                )
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result["success"],
                    output=result,
                    execution_time=0.1
                )
            
            elif tool == ToolType.FILE_CREATE:
                result = await file_tools.create_file(
                    parameters["path"],
                    parameters.get("content", "")
                )
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result["success"],
                    output=result,
                    execution_time=0.1
                )
            
            elif tool == ToolType.FILE_DELETE:
                result = await file_tools.delete_file(
                    parameters["path"],
                    parameters.get("backup", True)
                )
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result["success"],
                    output=result,
                    execution_time=0.1
                )
            
            elif tool == ToolType.FILE_LIST:
                result = await file_tools.list_directory(
                    parameters.get("path", ".")
                )
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result is not None,
                    output=result.dict() if result else None,
                    execution_time=0.1
                )
            
            elif tool == ToolType.SEARCH:
                result = await search_tools.search_files(
                    parameters["pattern"],
                    parameters.get("path"),
                    parameters.get("is_regex", False),
                    parameters.get("case_sensitive", False)
                )
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result is not None,
                    output=result.dict() if result else None,
                    execution_time=0.1
                )
            
            elif tool == ToolType.RUN_COMMAND:
                result = await shell_tools.run_command(
                    parameters["command"],
                    parameters.get("cwd"),
                    parameters.get("timeout", 30)
                )
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result is not None and result.return_code == 0,
                    output=result.dict() if result else None,
                    error=result.stderr if result and result.stderr else None,
                    execution_time=result.duration if result else 0
                )
            
            elif tool == ToolType.GIT_STATUS:
                result = await git_tools.git_status()
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result is not None,
                    output=result.dict() if result else None,
                    execution_time=0.1
                )
            
            elif tool == ToolType.GIT_COMMIT:
                result = await git_tools.git_commit(parameters["message"])
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result is not None and result.return_code == 0,
                    output=result.dict() if result else None,
                    execution_time=result.duration if result else 0
                )
            
            elif tool == ToolType.GIT_DIFF:
                result = await git_tools.git_diff(parameters.get("file_path"))
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=result is not None,
                    output=result.dict() if result else None,
                    execution_time=result.duration if result else 0
                )
            
            else:
                return ToolResult(
                    id=execution_id,
                    tool=tool,
                    success=False,
                    output=None,
                    error=f"Unknown tool: {tool}",
                    execution_time=0
                )
        
        except Exception as e:
            logger.error(f"Error in tool execution: {e}")
            return ToolResult(
                id=execution_id,
                tool=tool,
                success=False,
                output=None,
                error=str(e),
                execution_time=0
            )
    
    def _log(self, log: ToolLog):
        """Add log entry."""
        self.execution_logs.append(log)
    
    def get_logs(self, limit: Optional[int] = None) -> List[ToolLog]:
        """
        Get execution logs.
        
        Args:
            limit: Optional limit
            
        Returns:
            List of logs
        """
        if limit:
            return self.execution_logs[-limit:]
        return self.execution_logs
    
    def clear_logs(self):
        """Clear all logs."""
        self.execution_logs.clear()


# Global executor instance
executor = ToolExecutor()
