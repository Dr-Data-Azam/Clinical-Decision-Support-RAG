# --- 1. Imports ---
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import List, Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from graph import build_rag_graph


# --- 2. Pydantic Models ---
# For the /bot endpoint
class AskBot(BaseModel):
    message: str

# For the CDS Hooks service
class Prefetch(BaseModel):
    patient: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    medications: Optional[Dict[str, Any]] = None

class CDSHookRequest(BaseModel):
    hook: str
    hookInstance: str
    context: Dict[str, Any]
    prefetch: Prefetch = Field(default_factory=Prefetch)


# --- 3. Global RAG App and Lifespan Manager ---
# This global variable will hold our compiled RAG graph
rag_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function runs once at application startup.
    We build the RAG graph here to ensure it's a single, shared instance.
    """
    global rag_app
    print("Application startup: Building shared RAG graph...")
    rag_app = build_rag_graph()
    print("Shared RAG graph built successfully.")
    yield
    # Code below yield runs on shutdown
    print("Application shutdown.")


# manager is defined, and the lifespan manager is correctly passed to it.
app = FastAPI(lifespan=lifespan)

# This allows the CDS Hooks Sandbox (and other websites) to call our API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


# --- 4. Helper Function  ---
def format_query_from_fhir(prefetch_data: Prefetch) -> str:
    
    patient = prefetch_data.patient or {}
    conditions_bundle = prefetch_data.conditions or {}
    meds_bundle = prefetch_data.medications or {}
    try:
        birth_date_str = patient.get("birthDate", "2000-01-01")
        birth_date = date.fromisoformat(birth_date_str)
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except (ValueError, TypeError):
        age = "an unknown age"
    gender = patient.get("gender", "unknown gender")
    patient_summary = f"A {age}-year-old {gender} patient"
    conditions_list = [entry.get("resource", {}).get("code", {}).get("text", "unspecified condition") for entry in conditions_bundle.get("entry", [])]
    # has_hf = any("Vascular dementia, uncomplicated" in c.lower() for c in conditions_list)
    # if not has_hf:
    #     return "Patient does not have a recorded diagnosis of heart failure."
    conditions_summary = f"with diagnoses including: {', '.join(conditions_list) if conditions_list else 'none listed'}"
    meds_list = [entry.get("resource", {}).get("medicationCodeableConcept", {}).get("text", "unspecified medication") for entry in meds_bundle.get("entry", [])]
    meds_summary = f"and is currently prescribed: {', '.join(meds_list) if meds_list else 'no active medications'}"
    final_query = (
        f"Based on the 2022 AHA/ACC/HFSA guidelines, what are the key recommendations "
        f"for managing heart failure in the following clinical scenario? \n\n"
        f"**Patient Profile:** {patient_summary} {conditions_summary} {meds_summary}. \n\n"
        f"Please provide a concise, evidence-based summary."
    )
    return final_query


# --- 5. API Endpoints ---

@app.post("/bot")
async def bot(input: AskBot):
    """
    Endpoint for the Streamlit App.
    """
    
    if rag_app is None:
        return {"error": "RAG application is not initialized."}, 503

    config = {'configurable': {'thread_id': 'streamlit-thread-1'}} 
    initial_state = {
        'query': [HumanMessage(content=input.message)],
        'guideline_path': 'data/HF_Guideline.pdf'
    }
    response = rag_app.invoke(input=initial_state, config=config)

    output = response['messages'][-1].content
    return {'output': output}


# In your main.py file, replace the existing discovery function with this one.

@app.get("/cds-services")
def discovery():
    """
    The CDS Hooks Discovery endpoint.
    CORRECTED: The prefetch queries have been simplified to be more
    compatible with public FHIR sandboxes.
    """
    return {
        "services": [
            {
                "id": "heart-failure-guideline",
                "hook": "patient-view",
                "title": "Heart Failure Guideline Support",
                "description": "Provides clinical guidance for Heart Failure management based on the 2022 AHA/ACC/HFSA guidelines.",
                "prefetch": {
                    "patient": "Patient/{{context.patientId}}",
                    # This is simpler and more likely to be supported
                    "conditions": "Condition?patient={{context.patientId}}",
                    # This is also simpler and more likely to work
                    "medications": "MedicationRequest?patient={{context.patientId}}"
                },
                "access": {
                    "type": "patient",
                    "level": "read"
                }
            }
        ]
    }


@app.post("/cds-services/heart-failure-guideline")
async def handle_hook(request: CDSHookRequest):
    """
    The main CDS Service endpoint for the `patient-view` hook.
    """

    if rag_app is None:
        return {"error": "CDS service is not initialized."}, 503


    query_input = format_query_from_fhir(request.prefetch)
    # if "does not have" in query_input:
    #     return {"cards": []}


    initial_state = {
        'query': [HumanMessage(content=query_input)],
        'guideline_path': 'data/HF_Guideline.pdf'
    }
    config = {'configurable': {'thread_id': request.hookInstance}} # Use hookInstance for a unique thread per request
    rag_response = rag_app.invoke(input=initial_state, config=config)
    rag_result_text = rag_response['messages'][-1].content
    card = {
        "summary": "Heart Failure Guideline Recommendation",
        "indicator": "info",
        "detail": rag_result_text,
        "source": {
            "label": "2022 AHA/ACC/HFSA Guideline for HF Management",
            "url": "https://hfsa.org/hfguidelines2022"
        },
              "links": [
        {
          "label": "Open Full CDSS Chatbot",
          "url": "https://cds-frontend-app.ambitiouscliff-0211bfd7.eastus.azurecontainerapps.io",
          "type": "absolute"
        }
      ]
    }
    return {"cards": [card]}


# --- 6. Main execution block ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


# Having some problem with ngrok so i directly used localhost url!