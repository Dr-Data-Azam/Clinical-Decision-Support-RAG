Enterprise-Ready Clinical Decision Support System (CDSS) for Heart Failure
This project demonstrates a production-ready, AI-powered Clinical Decision Support System designed to bridge the gap between complex medical guidelines and point-of-care decision-making. By leveraging a Retrieval-Augmented Generation (RAG) pipeline, the system provides clinicians with instant, evidence-based answers from the 2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure.

The architecture is designed for enterprise use, featuring a decoupled frontend and backend, containerized for portability, and deployed on a scalable cloud platform (Microsoft Azure).

🚀 Live Cloud Deployment
The full application is deployed on Microsoft Azure Container Apps.

Live Chatbot Frontend: https://cds-frontend-app.ambitiouscliff-0211bfd7.eastus.azurecontainerapps.io

Live Backend API Docs: https://cds-backend-app.ambitiouscliff-0211bfd7.eastus.azurecontainerapps.io/docs

✨ Core Features & Business Value
This system is more than a technical demo; it's a blueprint for a real-world clinical tool.

Reduces Clinical Workload: Automates the time-consuming process of searching through dense medical documents, allowing physicians to get answers in seconds.

Improves Quality of Care: Promotes adherence to the latest evidence-based guidelines, ensuring consistent and high-quality patient care.

Seamless EHR Integration: Utilizes the CDS Hooks industry standard to push context-aware recommendations directly into the physician's workflow, requiring no extra clicks or context switching.

Understands Patient Context: Consumes and processes patient data in the FHIR format to provide relevant, patient-specific guidance.

Application Interfaces
1. EHR-Integrated CDS Card: A recommendation card appears directly in the EHR when a relevant patient's chart is opened.

2. Interactive Chatbot: A full-featured chatbot, built with Streamlit, allows for deep-dive questions and follow-up conversations.

🏗️ Enterprise Architecture & Deployment
The system is built using a modern, scalable, multi-service architecture.

graph TD
    subgraph User Interfaces
        A[EHR System]
        B[Streamlit Web App]
    end

    subgraph Cloud Platform (Microsoft Azure)
        C[Azure Container App: Frontend]
        D[Azure Container App: Backend]
    end

    subgraph Container Registry
        E[Docker Hub Repositories]
    end

    A -- CDS Hooks Request --> D
    B -- REST API Call --> D

    C -- Pulls Image --> E
    D -- Pulls Image --> E

    D -- AI Processing --> F[LLM API (Groq)]
    D -- Vector Search --> G[Vector DB (ChromaDB)]

    style A fill:#D6EAF8,stroke:#2E86C1
    style B fill:#D6EAF8,stroke:#2E86C1
    style C fill:#D5F5E3,stroke:#28B463
    style D fill:#D5F5E3,stroke:#28B463

Containerization: Both the FastAPI backend and Streamlit frontend are containerized with Docker, ensuring consistency across development and production environments.

Cloud Deployment: The application is deployed on Microsoft Azure Container Apps, a serverless platform that provides automatic scaling, HTTPS, and managed infrastructure.

CI/CD Ready: Images are versioned and stored on Docker Hub, enabling automated build and deployment pipelines.

🛠️ Technology Stack
Backend: Python, FastAPI, Uvicorn

AI Engine: LangChain, LangGraph, Retrieval-Augmented Generation (RAG)

LLM Provider: Groq (for Llama 3.1)

Data & Storage: ChromaDB (Vector Store), PyMuPDF

Frontend: Streamlit

Health IT Standards: CDS Hooks, FHIR

Deployment: Docker, Docker Compose, Microsoft Azure (Container Apps, CLI), Docker Hub

🐳 Docker Hub Repositories
The container images for this project are publicly available on Docker Hub:

Backend Image: https://hub.docker.com/r/uddinazam9/cds-backend

Frontend Image: https://hub.docker.com/r/uddinazam9/cds-frontend


⚙️ Running Locally with Docker Compose
To run the entire multi-container application on your local machine:

Prerequisites
Docker & Docker Compose

A .env file in the root directory with your GROQ_API_KEY.

1. Run the Application
From the project root, execute the following command:

docker-compose up --build

2. Access the Services
Streamlit Frontend: http://localhost:8501

FastAPI Backend Docs: http://localhost:8000/docs

"Note: This is a personal portfolio project. The service may be slow or temporarily unavailable."