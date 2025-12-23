import phoenix as px
from openinference.instrumentation.langchain import LangChainInstrumentor

def setup_tracing():
    """
    Initializes Arize Phoenix for observability.
    - Launches local Phoenix server.
    - Auto-instruments LangChain/LangGraph to capture traces.
    """
    try:
        # Launch Phoenix (Idempotent: if running, it reconnects or users existing)
        session = px.launch_app()
        print(f"🚀 Phoenix Tracing UI launched at: {session.url}")
        
        # Instrument LangChain to send traces to the local Phoenix collector
        LangChainInstrumentor().instrument()
        print("✅ LangChain/LangGraph instrumentation enabled.")
        
        return session
    except Exception as e:
        print(f"⚠️ Failed to setup tracing: {e}")
        return None
