from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from config_state import ChatState
from nodes import intent_classifier, general_query, router, doc_loader, text_splitter, vector_db, retrieve_documents, generation


def build_rag_graph():
    """Build and compile the RAG Graph"""
    checkpointer = InMemorySaver()
    graph = StateGraph(ChatState)

    graph.add_node('intent_classifier', intent_classifier)
    graph.add_node('general_query', general_query)
    graph.add_node('doc_loader', doc_loader)
    graph.add_node('text_splitter',text_splitter)
    graph.add_node('vector_db',vector_db)
    graph.add_node('retrieve_documents',retrieve_documents)
    graph.add_node('generation',generation)

    graph.set_entry_point('intent_classifier')
    graph.add_conditional_edges(
        "intent_classifier",
        router,
        {
            "general": "general_query",
            "medical": "doc_loader"
        }
    )
    graph.add_edge("doc_loader", "text_splitter")
    graph.add_edge("text_splitter", "vector_db")
    graph.add_edge("vector_db", "retrieve_documents")
    graph.add_edge("retrieve_documents", "generation")
    graph.add_edge("generation", END)
    graph.add_edge("general_query", END)
    compiled_graph = graph.compile(checkpointer=checkpointer)
    return compiled_graph

# def run_rag_pipeline(query:str):
#     """Run the complete pipeline"""
#     # Build the graph
#     rag_graph = build_rag_graph()

#     config = {'configurable': {'thread_id': 'thread-1'}}
#     initial_state = {
#         'query': query,
#         'guideline_path': 'data/HF_Guideline.pdf'
#     }

#     result = rag_graph.invoke(input=initial_state, config=config)
#     return result['result']

# result = run_rag_pipeline("What are the clinical stages of heart failure?")
# print(result)