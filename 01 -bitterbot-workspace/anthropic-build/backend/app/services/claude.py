"""
Claude Opus 4 Integration Service
"""
import os
from typing import List, Dict, Any, Optional
import anthropic
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message, ContentBlock, ToolUseBlock
import json
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
        # Initialize both sync and async clients for flexibility
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-opus-4-20250514"
        self.available_tools = self._initialize_tools()
    
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize available MCP tools"""
        return [
            {
                "name": "web_search",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "code_interpreter",
                "description": "Execute Python code for calculations or data processing",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "file_reader",
                "description": "Read and analyze file contents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "operation": {"type": "string", "enum": ["read", "analyze", "summarize"]}
                    },
                    "required": ["path", "operation"]
                }
            }
        ]
    
    async def create_task_breakdown(self, user_message: str) -> Dict[str, Any]:
        """Analyze user message and create task breakdown"""
        # This is a simplified version - in real implementation,
        # Claude would analyze the request and create appropriate tasks
        
        tasks = []
        
        # Analyze complexity
        if any(keyword in user_message.lower() for keyword in ["research", "analyze", "compare", "create"]):
            tasks.extend([
                {"title": "Research and Gather Information", "tools": ["web_search"]},
                {"title": "Analyze and Process Data", "tools": ["code_interpreter"]},
                {"title": "Synthesize Results", "tools": []},
                {"title": "Generate Comprehensive Response", "tools": []}
            ])
        elif any(keyword in user_message.lower() for keyword in ["file", "document", "read"]):
            tasks.extend([
                {"title": "Access File System", "tools": ["file_reader"]},
                {"title": "Process File Content", "tools": ["code_interpreter"]},
                {"title": "Generate Summary", "tools": []}
            ])
        else:
            tasks.extend([
                {"title": "Understand Request", "tools": []},
                {"title": "Process Information", "tools": []},
                {"title": "Generate Response", "tools": []}
            ])
        
        return {
            "main_task": f"Handle: {user_message[:50]}...",
            "subtasks": tasks,
            "estimated_time": len(tasks) * 2  # seconds
        }
    
    async def process_message(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        on_tool_use: Optional[callable] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a message with Claude Opus 4 using tools"""
        logger.debug(f"Starting process_message with:\nMessage: {message}\nConversation history: {conversation_history}")
        
        # Default system prompt for BitterBot
        if not system_prompt:
            system_prompt = """You are BitterBot, an advanced AI assistant with a purple-themed interface. 
            You help users with any task they need, from coding to research to creative work.
            You're friendly, helpful, and occasionally make references to your purple aesthetic.
            When given tasks, break them down into clear steps that can be tracked."""
            
        # Format messages for API call
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current message
        messages.append({"role": "user", "content": message})
            
        try:
            # Initial response with tool use
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                system=system_prompt,
                tools=self.available_tools,
                tool_choice={"type": "auto"}
            )
            
            # Process tool uses if any
            tool_results = []
            for content_block in response.content:
                if isinstance(content_block, ToolUseBlock):
                    # Notify about tool use
                    if on_tool_use:
                        await on_tool_use({
                            "tool": content_block.name,
                            "input": content_block.input,
                            "status": "executing"
                        })
                    
                    # Execute tool (mocked for MVP)
                    tool_result = await self._execute_tool(
                        content_block.name,
                        content_block.input
                    )
                    
                    tool_results.append({
                        "tool_use_id": content_block.id,
                        "output": tool_result
                    })
                    
                    if on_tool_use:
                        await on_tool_use({
                            "tool": content_block.name,
                            "status": "completed",
                            "result": tool_result
                        })
            
            # If tools were used, get final response
            if tool_results:
                # Format assistant message with tool uses
                assistant_content = []
                for block in response.content:
                    if isinstance(block, ToolUseBlock):
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })
                    elif hasattr(block, 'text'):
                        assistant_content.append({"type": "text", "text": block.text})
                
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                
                # Format tool results properly
                tool_result_messages = []
                for result in tool_results:
                    tool_result_messages.append({
                        "type": "tool_result", 
                        "tool_use_id": result["tool_use_id"], 
                        "content": result["output"]
                    })
                
                messages.append({
                    "role": "user",
                    "content": tool_result_messages
                })
                
                final_response = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=4096
                )
                
                # Extract text content from the response more safely
                content_text = ""
                for block in final_response.content:
                    if hasattr(block, 'text'):
                        content_text += block.text
                
                # Create a mapping of tool_use_ids to tool names for better frontend display
                tool_mapping = {}
                for block in response.content:
                    if isinstance(block, ToolUseBlock):
                        tool_mapping[block.id] = block.name
                
                # Extract tasks from the response content
                tasks = self._extract_tasks(content_text)
                        
                return {
                    "content": content_text,
                    "tasks": tasks,
                    "tools_used": [{
                        "id": result["tool_use_id"],
                        "name": tool_mapping.get(result["tool_use_id"], "unknown")
                    } for result in tool_results],
                    "metadata": {
                        "model": self.model,
                        "timestamp": datetime.utcnow().isoformat(),
                        "usage": {
                            "input_tokens": final_response.usage.input_tokens,
                            "output_tokens": final_response.usage.output_tokens
                        }
                    }
                }
            else:
                # No tools were used
                content = response.content[0].text
                tasks = self._extract_tasks(content)
                
                return {
                    "content": content,
                    "tasks": tasks,
                    "tools_used": [],
                    "metadata": {
                        "model": self.model,
                        "timestamp": datetime.utcnow().isoformat(),
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Claude API Error: {str(e)}")
            return {
                "content": f"I encountered an error: {str(e)}",
                "tasks": [],
                "tools_used": [],
                "metadata": {
                    "error": True,
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool (mocked for MVP)"""
        # In real implementation, this would connect to actual MCP servers
        
        if tool_name == "web_search":
            await asyncio.sleep(1)  # Simulate network delay
            return json.dumps({
                "results": [
                    {
                        "title": "Example Result 1",
                        "snippet": "This is a simulated search result for: " + tool_input.get("query", ""),
                        "url": "https://example.com/1"
                    },
                    {
                        "title": "Example Result 2",
                        "snippet": "Another simulated result with relevant information",
                        "url": "https://example.com/2"
                    }
                ]
            })
        
        elif tool_name == "code_interpreter":
            await asyncio.sleep(0.5)  # Simulate execution
            code = tool_input.get("code", "")
            return json.dumps({
                "output": f"Executed code successfully:\n{code}\n\nResult: 42",
                "execution_time": "0.5s"
            })
        
        elif tool_name == "file_reader":
            await asyncio.sleep(0.5)
            return json.dumps({
                "status": "success",
                "content": "File content would appear here",
                "metadata": {
                    "size": "1.2MB",
                    "type": "text/plain"
                }
            })
        
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
    def _extract_tasks(self, content: str) -> List[Dict]:
        """Extract task breakdown from response"""
        # Simple task extraction - looks for numbered lists or bullet points
        tasks = []
        lines = content.split('\n')
        
        task_patterns = ['1.', '2.', '3.', '•', '-', '*']
        current_task_num = 1
        
        for line in lines:
            line = line.strip()
            for pattern in task_patterns:
                if line.startswith(pattern):
                    task_text = line[len(pattern):].strip()
                    if task_text:
                        tasks.append({
                            "id": f"task_{current_task_num}",
                            "title": f"Step {current_task_num}",
                            "description": task_text,
                            "status": "pending",
                            "progress": 0.0
                        })
                        current_task_num += 1
                        break
        
        # If no tasks found, create a single task
        if not tasks and content:
            tasks.append({
                "id": "task_1",
                "title": "Process Request",
                "description": "Working on your request...",
                "status": "in_progress",
                "progress": 0.5
            })
        
        return tasks
        
    async def get_response(
        self, 
        message: str, 
        context: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """Get response from Claude with optional context (simplified version)"""
        
        # This is a simpler version of process_message that doesn't use tools
        # Useful for basic chat functionality
        
        messages = []
        
        # Add context/history if provided
        if context:
            messages.extend(context)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Default system prompt for BitterBot
        if not system_prompt:
            system_prompt = """You are BitterBot, an advanced AI assistant with a purple-themed interface. 
            You help users with any task they need, from coding to research to creative work.
            You're friendly, helpful, and occasionally make references to your purple aesthetic.
            When given tasks, break them down into clear steps that can be tracked."""
        
        try:
            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )
            
            # Extract task breakdown if present
            content = response.content[0].text
            tasks = self._extract_tasks(content)
            
            return {
                "content": content,
                "tasks": tasks,
                "model": self.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Claude API Error: {str(e)}")
            raise