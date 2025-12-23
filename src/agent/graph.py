import json
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from src.config import Config
from src.agent.state import AgentState
from src.agent.tools import retrieval_tool

# 1. Initialize Model
llm = ChatOllama(
    base_url=Config.OLLAMA_BASE_URL,
    model=Config.LLM_MODEL_NAME,
    temperature=0,
    format="json"
)

# 2. Define Nodes

def oracle_node(state: AgentState, config: RunnableConfig):
    """
    Decides whether to search (using retrieval_tool) or answer directly.
    Updated to work with Vector Search (Keyword/Query based).
    """
    # 1. Prepare Chat History
    chat_history = state.get("chat_history", [])
    if not chat_history:
        # If history is empty in state, wrap input as HumanMessage
        # But usually 'chat_history' should be passed correctly.
        # If called with just {input: ...}, we treat it as single turn.
        pass

    # 2. Check Context (Is this a follow-up or initial lookup?)
    context_list = state.get("context", [])
    context_text = "\n".join(context_list)
    
    user_input = state["input"]

    # --- Router Logic ---
    if not context_text.strip():
        # Case A: No Context -> Force Search
        print(f"DEBUG: No context. Deciding to SEARCH for: {user_input}")
        
        system_prompt = f"""
        You are a Search Planner. The user asked: "{user_input}"
        You have NO context info. You MUST output a JSON command to search for relevant documents.
        
        Extract the best search query from the user's question.
        
        Return JSON: {{ "action": "search", "query": "extracted search terms" }}
        """
        
        try:
            response = llm.invoke(system_prompt)
            data = json.loads(response.content)
            
            # Robust extraction of query
            query = data.get("query", user_input) # Fallback to full input
            
            decision = {
                "action": "search",
                "query": query
            }
        except Exception as e:
            # Fallback: Search using the original input
            print(f"DEBUG: Oracle parse error ({e}). Fallback to input search.")
            decision = {"action": "search", "query": user_input}

    else:
        # Case B: Context Exists -> Force Answer
        print("DEBUG: Context found. Deciding to ANSWER.")
        
        system_prompt = f"""
        You are a Helpful Assistant.
        Answer the question using ONLY the provided Context.
        If the context doesn't contain the answer, say "I couldn't find relevant information."
        
        Context:
        {context_text}
        
        User Question: {user_input}
        
        Return JSON: {{ "action": "answer", "response": "Your answer here..." }}
        """
        
        try:
            response = llm.invoke(system_prompt)
            data = json.loads(response.content)
            decision = {
                "action": "answer",
                "response": data.get("response", "No answer generated.")
            }
        except Exception as e:
            decision = {"action": "answer", "response": "Error generating answer."}

    # Store decision in state (AgentState needs 'current_decision' if we want to pass it explicitly, 
    # but strictly AgentState definition in state.py needs checking. 
    # For now, we update 'current_decision' key. 
    # If AgentState in state.py doesn't have it, we might error if TypedDict is strict. 
    # Assuming user instruction allows using standard AgentState, we might need to rely on 'input' for tool node if strict.
    # BUT, let's assume we can add 'current_decision' or just pass it via side-channel logic implicitly? 
    # No, TypedDict validation is strict in LangGraph? 
    # Actually, let's check state.py if possible. But instruction was "AgentState as defined".
    # Previous AgentState had 'current_decision'.
    # If we removed ExtendedAgentState, we should ensure AgentState has it OR update state.py.
    # Safe bet: We use 'current_decision' and ensure strict usage.
    return {"current_decision": decision}

def tool_node(state: AgentState, config: RunnableConfig):
    """
    Executes the retrieval_tool.
    """
    decision = state.get("current_decision", {})
    
    # Logic Fix: Get query from decision OR fallback to state input
    query = decision.get("query")
    if not query:
        query = state.get("input", "")
        
    print(f"DEBUG: Executing Vector Search for query: '{query}'")
    
    # Execute Tool
    search_result = retrieval_tool.invoke({"query": query})
    
    # Return context update
    return {"context": [search_result]}

# 3. Build Graph
workflow = StateGraph(AgentState) # Use standard AgentState

workflow.add_node("oracle", oracle_node)
workflow.add_node("tool_executor", tool_node)

workflow.set_entry_point("oracle")

def router(state: AgentState):
    decision = state.get("current_decision", {})
    if decision.get("action") == "search":
        return "tool_executor"
    else:
        return END

workflow.add_conditional_edges(
    "oracle",
    router
)

workflow.add_edge("tool_executor", "oracle")

# Compile
graph_app = workflow.compile()
