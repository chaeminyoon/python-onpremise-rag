
# Execution Command: python -m chainlit run app_chainlit.py -w --port 8501

import sys
import os
import chainlit as cl
from langchain_core.messages import HumanMessage, AIMessage

# Ensure src is importable
sys.path.append(os.getcwd())

from src.agent.graph import graph_app

@cl.on_chat_start
async def start():
    """
    Initializes the chat session.
    """
    cl.user_session.set("chat_history", [])
    await cl.Message(
        content="**Project Antigravity Agent**\n\n안녕하세요! 무엇을 도와드릴까요? (Ollama & Neo4j Connected)"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """
    Main chat handler. 
    Receives user message, invokes LangGraph agent, and sends response.
    """
    # 1. Retrieve Chat History
    history = cl.user_session.get("chat_history")
    
    # 2. UI Feedback: "Thinking..."
    feedback_msg = cl.Message(content="🤔 생각 중... (지식 그래프 탐색 및 추론)")
    await feedback_msg.send()
    
    # 3. Methodical Async Execution
    # LangGraph's .invoke is often synchronous (unless compiled with async nodes).
    # We use cl.make_async to run it in a thread/executor to avoid blocking the UI main loop.
    inputs = {
        "input": message.content,
        "chat_history": history
    }
    
    # Define a helper to run the graph
    def run_graph(inp):
        return graph_app.invoke(inp)

    # Convert to async
    run_graph_async = cl.make_async(run_graph)
    
    try:
        # Execute Agent
        result_state = await run_graph_async(inputs)
        
        # 4. Extract Answer and Context
        final_answer = result_state.get("answer", "죄송합니다. 답변을 생성하지 못했습니다.")
        contexts = result_state.get("context", [])
        
        # Update History in Session (Append new turn)
        # Note: LangGraph state might return full history, or we append manually.
        # Let's append manually to be safe if specific logic isn't in graph to persist across calls cleanly purely by state return.
        # Actually graph logic adds messages to state["chat_history"] usually? 
        # Checking src/agent/graph.py logic is prudent, but appending here is safe fallback.
        history.append(HumanMessage(content=message.content))
        history.append(AIMessage(content=final_answer))
        cl.user_session.set("chat_history", history)
        
        # 5. Send Final Response
        # We replace the "Thinking..." message with the final answer
        feedback_msg.content = final_answer
        
        # Add Sources if available
        if contexts:
            source_text = "\n\n**참고 문헌 (Sources):**\n"
            # Deduplicate
            unique_contexts = list(set(contexts))
            for i, ctx in enumerate(unique_contexts, 1):
                source_text += f"{i}. {ctx[:200]}...\n" # Truncate for display
            
            feedback_msg.content += source_text
            
        await feedback_msg.update()
        
    except Exception as e:
        feedback_msg.content = f"❌ 오류가 발생했습니다: {str(e)}"
        await feedback_msg.update()
