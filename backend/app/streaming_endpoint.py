from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from typing import AsyncGenerator, Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime

from .agents import hr_agent_system
from .memory_manager import MemoryManager

async def stream_hr_response(query: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Streams HR agent responses in real-time using LangGraph's astream_events for true streaming
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
        
        # Configure the agent system for streaming
        initial_state = {
            "messages": [HumanMessage(content=user_content)]
        }
        
        # Yield initial connection message
        yield f"data: {json.dumps({'type': 'start', 'message': 'Connected to HR Assistant'})}\n\n"
        
        # Variables to accumulate the final response for storage
        final_response_parts = []
        current_tool = None
        
        try:
            # Use astream_events for true streaming - this streams events as they happen
            async for event in hr_agent_system.astream_events(initial_state, version="v2"):
                event_type = event.get("event")
                
                # Handle different types of events from the agent system
                if event_type == "on_chat_model_start":
                    # LLM is starting to generate a response
                    model_name = event.get("name", "Unknown Model")
                    yield f"data: {json.dumps({'type': 'llm_start', 'model': model_name, 'message': f'🤖 {model_name} is thinking...'})}\n\n"
                
                elif event_type == "on_chat_model_stream":
                    # Stream individual tokens from the LLM
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, 'content') and chunk.content:
                        token = chunk.content
                        final_response_parts.append(token)
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
                elif event_type == "on_tool_start":
                    # A tool is being called
                    tool_data = event.get("data", {})
                    tool_name = event.get("name", "Unknown Tool")
                    current_tool = tool_name
                    tool_input = tool_data.get("input", {})
                    
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'input': str(tool_input)[:200]})}\n\n"
                
                elif event_type == "on_tool_end":
                    # A tool has finished execution
                    tool_data = event.get("data", {})
                    tool_output = tool_data.get("output", "")
                    
                    # Truncate long outputs for cleaner streaming
                    if len(str(tool_output)) > 300:
                        display_output = str(tool_output)[:300] + "... (truncated)"
                    else:
                        display_output = str(tool_output)
                    
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': current_tool, 'output': display_output})}\n\n"
                    current_tool = None
                
                elif event_type == "on_chain_start":
                    # Agent or chain is starting
                    chain_name = event.get("name", "")
                    if "agent" in chain_name.lower():
                        yield f"data: {json.dumps({'type': 'agent_start', 'agent': chain_name, 'message': f'🔄 Starting {chain_name}...'})}\n\n"
                
                elif event_type == "on_chain_end":
                    # Agent or chain has finished
                    chain_name = event.get("name", "")
                    if "agent" in chain_name.lower():
                        yield f"data: {json.dumps({'type': 'agent_end', 'agent': chain_name, 'message': f'✅ {chain_name} completed'})}\n\n"
            
            # Compile final response and store it
            final_response = "".join(final_response_parts)
            
            # If no tokens were collected (which might happen with some tool-only responses),
            # try to get the final message from a direct invocation result
            if not final_response.strip():
                try:
                    result = hr_agent_system.invoke(initial_state)
                    if result and "messages" in result and result["messages"]:
                        final_response = result["messages"][-1].content
                except Exception:
                    final_response = "Response completed successfully."
            
            # Store assistant response in memory
            if final_response.strip():
                memory.add_message(sid, "assistant", final_response, {"ts": datetime.now().isoformat()})
            
            # Send completion message
            yield f"data: {json.dumps({'type': 'complete', 'final_response': final_response})}\n\n"
            
        except Exception as e:
            error_message = f'Streaming error: {str(e)}'
            yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
            
    except Exception as e:
        error_message = f'Setup error: {str(e)}'
        yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"

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