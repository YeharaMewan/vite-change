from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import AsyncCallbackHandler
from typing import AsyncGenerator, Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime

from .agents import hr_agent_system
from .memory_manager import MemoryManager

class StreamingCallbackHandler(AsyncCallbackHandler):
    def __init__(self):
        self.tokens = []
        self.current_agent = ""
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM generates a new token"""
        self.tokens.append({
            "type": "token",
            "content": token,
            "agent": self.current_agent,
            "timestamp": datetime.now().isoformat()
        })
    
    async def on_agent_action(self, action, **kwargs) -> None:
        """Called when an agent takes an action"""
        self.tokens.append({
            "type": "agent_action", 
            "agent": action.tool,
            "action": str(action),
            "timestamp": datetime.now().isoformat()
        })
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when a tool starts"""
        self.tokens.append({
            "type": "tool_start",
            "tool": serialized.get("name", "unknown"),
            "input": input_str,
            "timestamp": datetime.now().isoformat()
        })
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when a tool ends"""
        self.tokens.append({
            "type": "tool_end",
            "output": output[:200] + "..." if len(output) > 200 else output,
            "timestamp": datetime.now().isoformat()
        })

async def stream_hr_response(query: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Streams HR agent responses in real-time using Server-Sent Events format
    """
    memory = MemoryManager()
    sid = session_id or "default"
    
    try:
        # Store user message
        memory.add_message(sid, "user", query, {"ts": datetime.now().isoformat()})
        
        # Prepare context
        ctx = memory.get_context(sid)
        context_snippet = ""
        if ctx:
            context_snippet = "Recent conversation context:\n" + "\n".join(
                [f"- {m.get('role')}: {m.get('content')[:120]}..." for m in ctx[-3:]]
            )
        
        user_content = query
        if context_snippet:
            user_content = f"{context_snippet}\n\nCurrent question: {query}"
        
        # Set up streaming callback
        streaming_handler = StreamingCallbackHandler()
        
        # Configure the agent system for streaming
        initial_state = {
            "messages": [HumanMessage(content=user_content)]
        }
        
        # Yield initial connection message
        yield f"data: {json.dumps({'type': 'start', 'message': 'Processing your HR request...'})}\n\n"
        
        # For real streaming, we need to use astream instead of invoke
        # Note: This requires LangGraph to support async streaming
        try:
            # Simulate streaming for now - replace with actual streaming when available
            yield f"data: {json.dumps({'type': 'agent_thinking', 'message': '🤖 HR Supervisor analyzing your request...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Execute the agent system
            response = hr_agent_system.invoke(initial_state)
            final_message = response["messages"][-1]
            response_text = final_message.content
            
            # Simulate streaming the response word by word
            words = response_text.split(' ')
            current_text = ""
            
            for i, word in enumerate(words):
                current_text += word + " "
                yield f"data: {json.dumps({'type': 'token', 'content': word + ' ', 'partial_response': current_text})}\n\n"
                await asyncio.sleep(0.05)  # Simulate typing delay
            
            # Store assistant response
            memory.add_message(sid, "assistant", response_text, {"ts": datetime.now().isoformat()})
            
            # Yield completion message
            yield f"data: {json.dumps({'type': 'complete', 'final_response': response_text})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Agent error: {str(e)}'})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'Streaming error: {str(e)}'})}\n\n"

# Add this to your FastAPI app
async def chat_stream_endpoint(query: str, session_id: Optional[str] = None):
    """
    Streaming endpoint for real-time HR chat responses
    """
    return StreamingResponse(
        stream_hr_response(query, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )