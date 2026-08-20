import json
import pickle
import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from pathlib import Path

load_dotenv()

def ingest_data(json_file_path: str, chroma_persist_dir: str, bm25_path: str):
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    documents = []
    for item in data:
        # Base metadata shared by all documents
        metadata = {
            "id": item.get("id"),
            "machine": item.get("machine"),
            "doc_type": item.get("doc_type") 
        }
        
        page_content = ""
        
        # Parse dynamically based on document type
        if item.get("doc_type") == "Manual":
            # Stitch text for the embedding model to understand the context
            page_content = f"Topic: {item.get('topic')}\nDetails: {item.get('content')}"
            
            # Add Manual-specific metadata
            metadata["topic"] = item.get("topic")
            
        elif item.get("doc_type") == "SOP":
            # Stitch SOP text into a readable guide for the embedding model
            page_content = (
                f"Error Code: {item.get('error_code')}\n"
                f"Description: {item.get('description')}\n"
                f"Resolution Steps: {item.get('resolution_steps')}\n"
                f"Prohibited Actions: {item.get('prohibited_actions')}"
            )
            
            # Add SOP-specific metadata for advanced filtering later
            metadata["error_code"] = item.get("error_code")
            metadata["hazard_level"] = item.get("hazard_level")
            metadata["required_role"] = item.get("required_role")
            
        else:
            print(f"Warning: Unknown doc_type for id {item.get('id')}")
            continue

        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
    
    print("Creating Chroma Vector Store...")
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=chroma_persist_dir
    )
    
    print("Creating BM25 Keyword Store...")
    bm25_retriever = BM25Retriever.from_documents(documents)
    with open(bm25_path, 'wb') as f:
        pickle.dump(bm25_retriever, f)
        
    print("Ingestion Complete!")

if __name__ == "__main__":
    # Ensure GOOGLE_API_KEY is available
    if "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable.")
    print("Starting the ingestion")
    # Get the data directory
    DATA_DIR = Path(__file__).resolve().parent

    # Resolve paths directly in the data directory
    DATA_FILE = DATA_DIR / "factory_knowledge_base.json"
    CHROMA_DIR = DATA_DIR / "chroma_db"
    BM25_FILE = DATA_DIR / "bm25_retriever.pkl"
    
    ingest_data(
        json_file_path=str(DATA_FILE),
        chroma_persist_dir=str(CHROMA_DIR),
        bm25_path=str(BM25_FILE),
    )