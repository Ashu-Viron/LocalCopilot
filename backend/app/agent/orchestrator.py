"""Main AI agent orchestrator."""

import uuid
import re
from typing import Optional, List, Dict, Any
import asyncio

from app.models.chat_models import ChatRequest, ChatResponse, Message, Plan
from app.agent.memory import ConversationMemory, memory_manager
from app.agent.planner import planner
from app.agent.executor import executor
from app.utils.logger import logger
from app.services.ai_service import get_ai_service, AIServiceError
from app.tools import file_tools


class AIAgent:
    """Main AI agent orchestrator."""
    
    def __init__(self, llm_client=None):
        """
        Initialize agent.
        
        Args:
            llm_client: LLM client for generating responses
        """
        self.llm_client = llm_client
        self.max_iterations = 10
    
    def _build_system_prompt(self, workspace_files: List[str] = None) -> str:
        """Build system prompt for the AI assistant."""
        files_info = ""
        if workspace_files:
            files_info = f"\n\nWorkspace files available:\n" + "\n".join(f"- {f}" for f in workspace_files[:20])
        
        return f"""You are LocalCopilot, an AI coding assistant integrated into an IDE with FULL access to the local workspace.

IMPORTANT: You can read, edit, create, or delete files based on the user's intent. You DO NOT need to output XML tool calls or API requests. The system automatically intercepts your intents before you reply. Just converse normally.

Your capabilities:
- READ files: When user says "read X", "show X", "open X"
- EDIT files: When user says "change X", "modify X", "update X"
- CREATE files: When user says "create X", "make X"
- DELETE files: When user says "delete X", "remove X"

When performing file operations, you will be given specific instructions on how to output the content.
Always provide code examples when relevant and format your responses with markdown for better readability.{files_info}"""
    
    async def _detect_file_intent(self, message: str, last_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect if user wants to perform file operations.
        
        Args:
            message: User message
            last_file: Last file mentioned in conversation (for context)
        
        Returns:
            Dict with 'action' and 'path' if detected, empty dict otherwise
        """
        message_lower = message.lower()
        
        # Regex for paths with extensions or slashes
        path_regex = r'([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+|[a-zA-Z0-9_\-.]+(?:/[a-zA-Z0-9_\-.]+)+)'
        
        # Extract potential file path
        path = None
        # Try to find explicit "file X"
        explicit_match = re.search(r'file\s+["\']?([a-zA-Z0-9_\-./]+)["\']?', message_lower)
        if explicit_match:
            path = explicit_match.group(1)
        else:
            # Try to find any path with extension or slash
            path_match = re.search(path_regex, message_lower)
            if path_match:
                path = path_match.group(1)
                
        # If no path found in message, check if contextual patterns match
        if not path:
            if last_file:
                # If message starts with an action verb, or explicitly refers to "it"/"the file"
                contextual_edit_patterns = [
                    r'^(?:edit|change|modify|update|replace|put|add|write|complete|fix|finish|continue)\b',
                    r'\b(?:edit|change|modify|update|replace|put|add|write|complete|fix|finish|continue)\b.*(?:it|the\s+file|this\s+file|the\s+code|this|the\s+story)\b'
                ]
                for pattern in contextual_edit_patterns:
                    if re.search(pattern, message_lower):
                        logger.debug(f"Using context file {last_file} for edit: {message}")
                        return {"action": "edit", "path": last_file}
                        
            contextual_read_patterns = [
                r'(?:now\s+)?(?:you\s+)?read\s+(?:it|the\s+file|this\s+file)',
                r'(?:have\s+)?you\s+read\s+(?:it|the\s+file)',
                r'please\s+read\s+(?:it|the\s+file)',
            ]
            for pattern in contextual_read_patterns:
                if re.search(pattern, message_lower):
                    if last_file:
                        logger.debug(f"Using context file {last_file} for read: {message}")
                        return {"action": "read", "path": last_file}
            return {}

        # We have a path, now detect the intended action
        # Check for edit/modify verbs (most destructive/active operations take precedence)
        edit_verbs = r'\b(edit|change|modify|update|replace|put|add|write|complete|fix|finish|continue)\b'
        if re.search(edit_verbs, message_lower):
            return {"action": "edit", "path": path}
            
        # Check for create verbs
        create_verbs = r'\b(create|make|new)\b'
        if re.search(create_verbs, message_lower):
            return {"action": "create", "path": path}
            
        # Check for delete verbs
        delete_verbs = r'\b(delete|remove|rm)\b'
        if re.search(delete_verbs, message_lower):
            return {"action": "delete", "path": path}
            
        # Check for read verbs
        read_verbs = r'\b(read|show|open|display|view|cat|get|what\'?s?\s+in|contents?)\b'
        if re.search(read_verbs, message_lower):
            return {"action": "read", "path": path}
            
        return {}
    
    async def _execute_file_action(self, action: str, path: str, message: str) -> str:
        """
        Execute a file action and return result.
        
        Args:
            action: read, edit, create, delete
            path: File path
            message: Original user message (for content extraction)
            
        Returns:
            Result string to include in response
        """
        try:
            if action == "read":
                result = await file_tools.read_file(path)
                if result:
                    content = result.content if hasattr(result, 'content') else result.get('content', '')
                    return f"📄 **Contents of `{path}`:**\n\n```\n{content}\n```"
                else:
                    return f"❌ Could not read file `{path}`. File may not exist."
            
            elif action == "create":
                # Mark for creation - content will be extracted from AI response
                return f"CREATE_FILE:{path}"
            
            elif action == "delete":
                result = await file_tools.delete_file(path)
                if result and result.get("success"):
                    return f"✅ Deleted file `{path}` successfully."
                else:
                    return f"❌ Failed to delete file `{path}`."
            
            elif action == "edit":
                # For edits, check if file exists first
                existing = await file_tools.read_file(path)
                if existing:
                    content = existing.content if hasattr(existing, 'content') else existing.get('content', '')
                    return f"EDIT_FILE:{path}:EXISTING:{content}"
                else:
                    # File doesn't exist, treat as create
                    return f"CREATE_FILE:{path}"
            
            return ""
            
        except Exception as e:
            logger.error(f"File action error: {e}")
            return f"❌ Error performing {action} on `{path}`: {str(e)}"
    
    def _extract_code_from_response(self, response: str, file_path: str) -> Optional[str]:
        """
        Extract code block from AI response based on file type.
        
        Args:
            response: AI response text
            file_path: Target file path (for language detection)
            
        Returns:
            Extracted code or None
        """
        import re
        
        # Determine expected language from file extension
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        lang_map = {
            'py': ['python', 'py'],
            'js': ['javascript', 'js'],
            'ts': ['typescript', 'ts'],
            'jsx': ['jsx', 'javascript', 'js'],
            'tsx': ['tsx', 'typescript', 'ts'],
            'c': ['c'],
            'cpp': ['cpp', 'c++'],
            'h': ['c', 'cpp'],
            'java': ['java'],
            'go': ['go', 'golang'],
            'rs': ['rust', 'rs'],
            'rb': ['ruby', 'rb'],
            'php': ['php'],
            'html': ['html'],
            'css': ['css'],
            'json': ['json'],
            'yaml': ['yaml', 'yml'],
            'sh': ['bash', 'sh', 'shell'],
            'sql': ['sql'],
        }
        
        expected_langs = lang_map.get(ext, [ext]) if ext else []
        
        # Try to find code block with matching language (case insensitive)
        for lang in expected_langs:
            # Pattern: ```lang ... ```
            pattern = rf'```\s*{re.escape(lang)}\s*\n(.*?)```'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                logger.info(f"Extracted code for {file_path} using language tag: {lang}")
                return extracted
        
        # Try to find any code block (with or without language tag)
        # Pattern: ```[lang] ... ```
        pattern = r'```(?:[a-zA-Z0-9_\-\+]+)?\s*\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            # Use the largest code block (usually the main one)
            largest = max(matches, key=len)
            extracted = largest.strip()
            logger.info(f"Extracted code for {file_path} from generic code block ({len(extracted)} chars)")
            return extracted
        
        # Last resort: try pattern without newline requirement
        pattern = r'```(?:[a-zA-Z0-9_\-\+]+)?(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            # Filter out small matches (likely not code)
            code_blocks = [m.strip() for m in matches if len(m.strip()) > 10]
            if code_blocks:
                largest = max(code_blocks, key=len)
                logger.info(f"Extracted code for {file_path} from fallback pattern ({len(largest)} chars)")
                return largest
        
        logger.warning(f"Could not extract code block from response for {file_path}")
        return None
    
    async def _write_file_with_content(self, path: str, content: str) -> str:
        """
        Write content to a file and return status message.
        
        Args:
            path: File path
            content: File content
            
        Returns:
            Status message
        """
        try:
            # Check if file exists
            existing = await file_tools.read_file(path)
            
            if existing:
                # Update existing file
                result = await file_tools.write_file(path, content, backup=True)
            else:
                # Create new file
                result = await file_tools.create_file(path, content)
            
            if result and result.get("success"):
                return f"✅ Successfully wrote to `{path}`"
            else:
                msg = result.get("message", "Unknown error") if result else "Unknown error"
                return f"❌ Failed to write `{path}`: {msg}"
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return f"❌ Error writing `{path}`: {str(e)}"
    
    async def _get_workspace_files(self) -> List[str]:
        """Get list of files in workspace for context."""
        try:
            result = await file_tools.list_directory(".")
            if result:
                files = result.files if hasattr(result, 'files') else result.get('files', [])
                return [f.get('name', '') if isinstance(f, dict) else f.name for f in files]
        except:
            pass
        return []
    
    async def process_message(
        self,
        request: ChatRequest,
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Process user message and generate response.
        
        Args:
            request: ChatRequest with user message
            conversation_id: Optional conversation ID
            
        Returns:
            ChatResponse with assistant response
        """
        try:
            # Use provided or create new conversation ID
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Get or create conversation memory
            memory = memory_manager.get_or_create_conversation(conversation_id)
            
            # Add user message to memory
            memory.add_user_message(request.message)
            
            logger.info(f"Processing message in conversation {conversation_id}")
            
            # Get last mentioned file from context
            last_file = memory.metadata.get('last_file')
            
            # Detect file operation intent
            file_intent = await self._detect_file_intent(request.message, last_file)
            tool_logs = []
            has_file_changes = False
            file_action_result = ""
            pending_file_path = None
            existing_content = ""
            
            # Execute file operation if detected
            if file_intent:
                action = file_intent.get("action")
                path = file_intent.get("path")
                logger.info(f"Detected file intent: {action} on {path}")
                tool_logs.append(f"Detected: {action} {path}")
                
                # Store this file in context for future requests
                memory.metadata['last_file'] = path
                
                file_action_result = await self._execute_file_action(action, path, request.message)
                
                # Handle edit with existing content
                if file_action_result.startswith("EDIT_FILE:"):
                    parts = file_action_result.split(":EXISTING:", 1)
                    edit_path = parts[0].replace("EDIT_FILE:", "")
                    existing_content = parts[1] if len(parts) > 1 else ""
                    file_action_result = f"PENDING_WRITE:{edit_path}"
                    # Add existing content to context for AI
                    tool_logs.append(f"Reading existing content of {edit_path}")
                
                if "✅" in file_action_result:
                    has_file_changes = True
                    tool_logs.append(f"Completed: {action} {path}")
            
            # Get workspace files for context
            workspace_files = await self._get_workspace_files()
            
            # Check if we need to write a file (create or edit)
            if file_action_result.startswith("CREATE_FILE:"):
                pending_file_path = file_action_result.replace("CREATE_FILE:", "")
            elif file_action_result.startswith("PENDING_WRITE:"):
                pending_file_path = file_action_result.replace("PENDING_WRITE:", "")
            
            # If we performed a successful file read, skip AI and return directly
            if file_action_result.startswith("📄"):
                logger.info(f"File read successful, skipping AI call")
                memory.add_assistant_message(file_action_result)
                response = ChatResponse(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    message=file_action_result,
                    plan=None,
                    tool_logs=tool_logs,
                    has_file_changes=has_file_changes
                )
                logger.info(f"Generated response for conversation {conversation_id}")
                return response
            
            # If a completed operation (delete success/failure, errors), return directly
            if ("✅" in file_action_result or "❌" in file_action_result) and not pending_file_path:
                logger.info(f"File operation completed, skipping AI call")
                memory.add_assistant_message(file_action_result)
                response = ChatResponse(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    message=file_action_result,
                    plan=None,
                    tool_logs=tool_logs,
                    has_file_changes=has_file_changes
                )
                return response
            
            # Generate AI response using A4F API
            try:
                ai_service = get_ai_service()
                
                # Build conversation context for AI
                system_prompt = self._build_system_prompt(workspace_files)
                
                # If creating/editing file, add specific instruction
                if pending_file_path:
                    ext = pending_file_path.split('.')[-1].lower() if '.' in pending_file_path else 'txt'
                    system_prompt += f"""

IMPORTANT: The user wants you to create or modify the file `{pending_file_path}`.
You MUST include the complete file content in a code block with the appropriate language tag.
Format: ```{ext}
<complete file content here>
```
Do not use placeholder comments like "// your code here" - provide the actual working code."""

                    if existing_content:
                        system_prompt += f"""

Here is the CURRENT content of the file you need to modify:
```{ext}
{existing_content}
```
Please provide the FULL updated file content in your response."""

                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                
                # Add conversation history
                history = memory.get_history()
                for msg in history[-10:]:  # Last 10 messages for context
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                
                # Get AI response
                response_text = await ai_service.async_chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048
                )

                # If we performed a file action (read/delete), prepend the result
                if file_action_result:
                    response_text = f"{file_action_result}\n\n{response_text}"
                
                # If we have a pending file to write, extract code and write it
                if pending_file_path:
                    extracted_code = self._extract_code_from_response(response_text, pending_file_path)
                    if extracted_code:
                        write_result = await self._write_file_with_content(pending_file_path, extracted_code)
                        tool_logs.append(write_result)
                        has_file_changes = "✅" in write_result
                        # Prepend the result to response
                        response_text = f"{write_result}\n\n{response_text}"
                    else:
                        # Could not extract code, warn user
                        response_text = f"⚠️ I generated code but couldn't automatically write it to `{pending_file_path}`. Please copy the code manually.\n\n{response_text}"
                
            except AIServiceError as e:
                logger.warning(f"AI service error, using fallback: {e}")
                if file_action_result:
                    response_text = file_action_result
                else:
                    response_text = f"I understand you're asking about: {request.message}\n\n"
                    response_text += "I'm currently having trouble connecting to the AI service. Please check your API configuration."
            except Exception as e:
                logger.warning(f"Unexpected error in AI call: {e}")
                if file_action_result:
                    response_text = file_action_result
                else:
                    response_text = f"I received your message: {request.message}\n\n"
                    response_text += "There was an issue processing your request. Please try again."
            
            # Add assistant message to memory
            memory.add_assistant_message(response_text)
            
            # Create response
            response = ChatResponse(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                message=response_text,
                plan=None,
                tool_logs=tool_logs,
                has_file_changes=has_file_changes
            )
            
            logger.info(f"Generated response for conversation {conversation_id}")
            return response
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            response_text = f"Error processing your request: {str(e)}"
            
            return ChatResponse(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id or str(uuid.uuid4()),
                message=response_text,
                tool_logs=[]
            )
    
    async def process_message_stream(
        self,
        request: ChatRequest,
        conversation_id: str = None
    ):
        """
        Process user message and generate streaming response.
        
        Args:
            request: ChatRequest with user message
            conversation_id: Optional conversation ID
            
        Yields:
            Dict chunks with 'type' and 'content'
        """
        from typing import AsyncGenerator, Dict, Any
        
        try:
            # Use provided or create new conversation ID
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Yield conversation ID first
            yield {"type": "conversation_id", "content": conversation_id}
            
            # Get or create conversation memory
            memory = memory_manager.get_or_create_conversation(conversation_id)
            
            # Add user message to memory
            memory.add_user_message(request.message)
            
            logger.info(f"Processing message (streaming) in conversation {conversation_id}")
            
            # Get last mentioned file from context
            last_file = memory.metadata.get('last_file')
            
            # Detect file operation intent
            file_intent = await self._detect_file_intent(request.message, last_file)
            has_file_changes = False
            pending_file_path = None
            file_action_result = ""
            existing_content = ""
            
            # Execute file operation if detected
            if file_intent:
                action = file_intent.get("action")
                path = file_intent.get("path")
                logger.info(f"Detected file intent: {action} on {path}")
                yield {"type": "tool_log", "content": f"Detected: {action} {path}"}
                
                # Store this file in context for future requests
                memory.metadata['last_file'] = path
                
                file_action_result = await self._execute_file_action(action, path, request.message)
                
                # Handle edit with existing content
                if file_action_result.startswith("EDIT_FILE:"):
                    parts = file_action_result.split(":EXISTING:", 1)
                    edit_path = parts[0].replace("EDIT_FILE:", "")
                    existing_content = parts[1] if len(parts) > 1 else ""
                    file_action_result = f"PENDING_WRITE:{edit_path}"
                    yield {"type": "tool_log", "content": f"Reading existing content of {edit_path}"}
                
                if "✅" in file_action_result:
                    has_file_changes = True
                    yield {"type": "file_change", "content": f"Completed: {action} {path}"}
                
                if file_action_result.startswith("CREATE_FILE:"):
                    pending_file_path = file_action_result.replace("CREATE_FILE:", "")
                elif file_action_result.startswith("PENDING_WRITE:"):
                    pending_file_path = file_action_result.replace("PENDING_WRITE:", "")
            
            # Get workspace files for context
            workspace_files = await self._get_workspace_files()
            
            # If we performed a successful file read, skip AI and return directly
            if file_action_result.startswith("📄"):
                logger.info(f"File read successful, skipping AI call")
                yield {"type": "chunk", "content": f"{file_action_result}"}
                memory.add_assistant_message(file_action_result)
                yield {"type": "done", "conversation_id": conversation_id, "has_file_changes": has_file_changes}
                return
            
            # If a completed operation (delete success/failure, errors), return directly
            if ("✅" in file_action_result or "❌" in file_action_result) and not pending_file_path:
                logger.info(f"File operation completed, skipping AI call")
                yield {"type": "chunk", "content": f"{file_action_result}"}
                memory.add_assistant_message(file_action_result)
                yield {"type": "done", "conversation_id": conversation_id, "has_file_changes": has_file_changes}
                return
            
            # Generate AI response using A4F API with streaming
            try:
                ai_service = get_ai_service()
                
                # Build conversation context for AI
                system_prompt = self._build_system_prompt(workspace_files)
                
                # If creating/editing file, add specific instruction
                if pending_file_path:
                    ext = pending_file_path.split('.')[-1].lower() if '.' in pending_file_path else 'txt'
                    system_prompt += f"""

IMPORTANT: The user wants you to create or modify the file `{pending_file_path}`.
You MUST include the complete file content in a code block with the appropriate language tag.
Format: ```{ext}
<complete file content here>
```
Do not use placeholder comments like "// your code here" - provide the actual working code."""

                    if existing_content:
                        system_prompt += f"""

Here is the CURRENT content of the file you need to modify:
```{ext}
{existing_content}
```
Please provide the FULL updated file content in your response."""

                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                
                # Add conversation history
                history = memory.get_history()
                for msg in history[-10:]:  # Last 10 messages for context
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                
                # Stream AI response
                full_response = ""

                # If we performed a file action (read/delete), stream it first
                if file_action_result:
                    yield {"type": "chunk", "content": f"{file_action_result}\n\n"}

                for chunk in ai_service.chat_completion_stream(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048
                ):
                    full_response += chunk
                    yield {"type": "chunk", "content": chunk}
                
                # If we have a pending file to write, extract code and write it
                if pending_file_path:
                    extracted_code = self._extract_code_from_response(full_response, pending_file_path)
                    if extracted_code:
                        write_result = await self._write_file_with_content(pending_file_path, extracted_code)
                        yield {"type": "tool_log", "content": write_result}
                        has_file_changes = "✅" in write_result
                        yield {"type": "file_change", "content": write_result}
                    else:
                        yield {"type": "chunk", "content": f"\n\n⚠️ Could not auto-extract code for `{pending_file_path}`. Please copy manually."}
                
                # Add assistant message to memory
                memory.add_assistant_message(full_response)
                
            except AIServiceError as e:
                logger.warning(f"AI service error: {e}")
                yield {"type": "chunk", "content": f"AI service error: {str(e)}"}
            except Exception as e:
                logger.warning(f"Unexpected error in AI call: {e}")
                yield {"type": "chunk", "content": f"Error: {str(e)}"}
            
            # Signal completion
            yield {"type": "done", "conversation_id": conversation_id, "has_file_changes": has_file_changes}
            
        except Exception as e:
            logger.error(f"Error processing message stream: {e}")
            yield {"type": "error", "content": str(e)}
    
    async def execute_plan(
        self,
        plan: Plan,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Execute a plan and track results.
        
        Args:
            plan: Plan to execute
            conversation_id: Conversation ID
            
        Returns:
            Execution results
        """
        try:
            results = {
                "conversation_id": conversation_id,
                "steps_executed": 0,
                "successes": 0,
                "failures": 0,
                "tool_logs": []
            }
            
            for step in plan.steps:
                logger.info(f"Executing step {step.step_number}: {step.action}")
                
                if step.tool:
                    # Execute tool would happen here
                    pass
                
                results["steps_executed"] += 1
            
            return results
        
        except Exception as e:
            logger.error(f"Error executing plan: {e}")
            return {"error": str(e)}
    
    async def get_conversation_context(
        self,
        conversation_id: str
    ) -> Optional[List[Message]]:
        """
        Get conversation context.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages or None
        """
        memory = memory_manager.get_conversation(conversation_id)
        if memory:
            return memory.get_history()
        return None
    
    async def list_conversations(self) -> List[str]:
        """Get list of active conversations."""
        return memory_manager.list_conversations()
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        return memory_manager.delete_conversation(conversation_id)


# Global agent instance
agent = AIAgent()
