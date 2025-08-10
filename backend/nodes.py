import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import BaseMessage, AIMessage
from backend.config_state import ChatState, llm, embedding_model, structured_llm
from dotenv import load_dotenv
load_dotenv()

# Caching Variables
_cached_docs = None
_cached_chunks = None
_cached_vector_store = None
_cached_retriever = None

def intent_classifier(state: ChatState):
    query = state['query']
    classifier_prompt = f"""
    You are an intent classification assistant.
    Your job is to read the user's query and classify it into EXACTLY one category:
    - "medical" -- if it is related to heart failure management, cardiology, or relevant guidelines.
    - "general" -- if it is casual talk, unrelated, or about other topics.

    Do NOT answer the question, only respond with one word: "medical" or "general".

    User query:
    {query}
    """
    result = structured_llm.invoke(classifier_prompt).intent
    return {"intent": result}

def general_query(state:ChatState):
    """Answer the general query"""
    query=state['query']
    result = "Hello! This Clinical Decision Support System is designed to answer questions strictly based on the 2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure. Your question does not appear to be related to this guideline, so I am unable to provide a response within the scope of this system."

    # Preserve existing state if needed
    state['messages'] = state.get('messages', []) + [AIMessage(content=result)]
    return state



def doc_loader(state: ChatState):
    global _cached_docs
    if _cached_docs is None:
        guideline_path = state['guideline_path']
        loader = PyMuPDFLoader(guideline_path)
        _cached_docs = loader.load()
    return {'docs': _cached_docs}


def router(state: ChatState):
    """Route based on sentiment analysis result"""
    if state["intent"] == 'medical':
        return "medical"
    else:
        return "general"



def text_splitter(state: ChatState):
    global _cached_chunks
    if _cached_chunks is not None:
        print("Using cached chunks")
        return {'chunks': _cached_chunks}

    docs = state['docs']
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)
    _cached_chunks = chunks
    print("Created and cached chunks")
    return {'chunks': chunks}




def vector_db(state: ChatState):
    """Create or load vector database from chunks with lazy loading and caching"""

    global _cached_vector_store
    if _cached_vector_store is not None:
        # Vector store already cached, reuse it
        print("Using cached vector store")
        state['vector_store'] = _cached_vector_store
        return state

    persist_directory = 'chroma_db'

    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        # Load existing vector store
        _cached_vector_store = Chroma(
            embedding_function=embedding_model,
            persist_directory=persist_directory,
            collection_name='sample'
        )
        print("Loaded existing vector store")
    else:
        # Create new vector store from chunks
        chunks = state['chunks']
        _cached_vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=persist_directory,
            collection_name='sample'
        )
        print("Created new vector store")

    state['vector_store'] = _cached_vector_store
    return state




def retrieve_documents(state: ChatState):
    """Retrieve relevant documents based on query, with lazy loading and caching of the retriever."""
    global _cached_retriever

    query = state['query']
    vector_store = state.get('vector_store')

    # Extract plain query string from messages
    if isinstance(query, list) and all(isinstance(msg, BaseMessage) for msg in query):
        query = " ".join([msg.content for msg in query if hasattr(msg, 'content')])
    else:
        raise ValueError("Expected 'query' to be a list of BaseMessage with 'content'.")

    # Load or reuse vector store
    if not vector_store:
        vector_store = Chroma(
            embedding_function=embedding_model,
            persist_directory='chroma_db',
            collection_name='sample'
        )
        # Save vector_store in state for reuse
        state['vector_store'] = vector_store

    # Lazy load and cache retriever
    if _cached_retriever is None:
        base_retriever = vector_store.as_retriever(search_kwargs={'k': 7})
        compressor = LLMChainExtractor.from_llm(llm)
        _cached_retriever = ContextualCompressionRetriever(
            base_retriever=base_retriever,
            base_compressor=compressor
        )
        print("Retriever created and cached")
    else:
        print("Using cached retriever")

    # Retrieve documents using cached retriever
    retrieved_docs = _cached_retriever.invoke(query)
    print(f"Retrieved {len(retrieved_docs)} relevant documents")

    return {"retrieved_docs": retrieved_docs, "vector_store": vector_store}




def generation(state: ChatState):
    """Generate response based on retrieved documents"""
    query = state['query']
    retrieved_docs = state['retrieved_docs']
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    system_message = (
        "You are a Clinical Decision Support Assistant trained on the 2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure.\n\n"
        "- Respond ONLY using the content retrieved from the guidelines.\n"
        "- If the information is not available in the excerpts, respond with: This information is out of scope of the 2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure.\n"
        "- Keep the response concise and clinically relevant."
    )

    human_message = (
        "=== Physician Query ===\n{query}\n\n"
        "=== Relevant Guideline Excerpts ===\n{context}\n\n"
        "=== Response ===\n"
        "Provide a short, evidence-based summary to help the physician."
    )

    # Use structured prompt with system and human messages
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_message),
        HumanMessagePromptTemplate.from_template(human_message)
    ])
    parser = StrOutputParser()
    chain = prompt | llm | parser

    # Invoke with proper inputs
    result = chain.invoke({'context': context, 'query': query})
    return {'messages': [AIMessage(content=result)]}



# state = {'guideline_path': 'data/HF_Guideline.pdf'}
# doc_state = doc_loader({'guideline_path': 'data/HF_Guideline.pdf'})
# split_state = text_splitter({'docs': doc_state['docs']})
# chunks = split_state['chunks']
# state = {'chunks': chunks}
# vector_state = vector_db(state)
# state.update({
#     'query': 'What are the stages of heart failure?',
# })
# retrieved_state = retrieve_documents(state)
# state.update(retrieved_state)
# generated = generation(state)

# print(doc_loader(state))
# print(f"Chunks: {len(split_state['chunks'])}")
# print(split_state['chunks'][0])
# print(vector_state['vector_store'])  # Should show vector DB object
# print(f"Retrieved: {len(retrieved_state['retrieved_docs'])}")
# print(retrieved_state['retrieved_docs'][0].page_content)
# print(generated['result'])


