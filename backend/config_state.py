from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, List, Literal
from langchain.schema import Document
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

class IntentChecker(BaseModel):
    intent: Literal["medical", "general"] = Field(description="sentiment of the query")

class ChatState(TypedDict):
    intent: Literal['medical', 'general']
    query: Annotated[list[BaseMessage], add_messages]
    guideline_path: str
    docs: Annotated[List[Document], 'It will be a list of document_object']
    chunks: Annotated[list[Document], 'It will be a list of document_object chunks']
    retrieved_docs: Annotated[List[Document], 'Retrieved relevant documents']
    messages: list[BaseMessage]

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings':True}
)

llm = ChatGroq(model='llama-3.1-8b-instant', temperature=0.3)
# llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.3)

structured_llm = llm.with_structured_output(IntentChecker)