# app/api/endpoints.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.rag_search import RagSearch
from services.rag_question import RagQuestion
from services.qdrant_update import QdrantUpdater
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from config import settings

router = APIRouter()

class UpdateRequest(BaseModel):
    node_id: str
    answer: str

class QueryRequest(BaseModel):
    query: str
    product: str = "all"

def get_rag_search_service():
    return RagSearch()

def get_rag_question_service():
    llm = OpenAI(model=settings.OPENAI_LLM_MODEL, temperature=settings.TEMPERATURE, api_key=settings.OPENAI_API_KEY)
    return RagQuestion(llm=llm, embed_model=OpenAIEmbedding(model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY))

def get_qdrant_updater_service():
    return QdrantUpdater()

@router.post("/query")
async def query_rag(request: QueryRequest, rag_search_service: RagSearch = Depends(get_rag_search_service)):
    result = rag_search_service.query_rag(request.query, request.product)
    return result

@router.post("/ask")
async def ask_question(request: QueryRequest, rag_question_service: RagQuestion = Depends(get_rag_question_service)):
    try:
        result = rag_question_service.query(request.query)
        return result
    except Exception as e:
        # Log the error for debugging
        print(f"Error in ask_question endpoint: {str(e)}")
        # Return a more user-friendly error
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. The service might be temporarily unavailable."
        )

@router.post("/update")
async def update_document(update_data: UpdateRequest, qdrant_updater_service: QdrantUpdater = Depends(get_qdrant_updater_service)):
    print(f"Endpoint -> update_document -> node_id: {update_data.node_id}")
    try:
        result = qdrant_updater_service.update_document(
            update_data.node_id,
            update_data.answer
        )
        return {"message": "Document updated successfully", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))