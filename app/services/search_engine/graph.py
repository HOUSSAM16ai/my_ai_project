from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
import logging
import asyncio
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.services.search_engine.retriever import get_retriever

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    query: str
    filters: Optional[dict]
    documents: List[str]
    answer: str

async def retrieve_node(state: AgentState):
    query = state["query"]
    filters = state.get("filters", {})

    logger.info(f"LangGraph: Retrieving for query='{query}' filters={filters}")
    retriever = get_retriever()

    # Retrieve is async now in our wrapper
    results = await retriever.retrieve(query, filters)

    # Format documents
    docs = []
    for node in results:
        # node is a NodeWithScore
        content = node.node.text
        meta = node.node.metadata

        # Format explicitly
        docs.append(f"Source ({meta.get('year')} {meta.get('subject')}): {content}")

    return {"documents": docs}

async def generate_node(state: AgentState):
    documents = state["documents"]
    query = state["query"]

    if not documents:
        return {"answer": "لم يتم العثور على مستندات مطابقة."}

    # Combine documents
    context = "\n\n".join(documents)

    # Use Devstral via OpenRouter
    # We use the key from environment or fallback (passed in this session)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
         logger.warning("OPENROUTER_API_KEY not found, returning raw documents.")
         return {"answer": context}

    try:
        llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model="mistralai/devstral-2512:free",
            temperature=0.7
        )

        messages = [
            SystemMessage(content="أنت مساعد ذكي متخصص في شرح الدروس والتمارين التعليمية. استخدم السياق المقدم للإجابة على سؤال الطالب بدقة. اشرح المنهجية بوضوح."),
            HumanMessage(content=f"السياق:\n{context}\n\nالسؤال: {query}")
        ]

        response = await llm.ainvoke(messages)
        return {"answer": response.content}
    except Exception as e:
        logger.error(f"LLM Generation Failed: {e}")
        return {"answer": context} # Fallback to raw content

# Graph Definition
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

search_graph = workflow.compile()
