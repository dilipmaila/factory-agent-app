"""
Hybrid Search Retriever Module.
Combines ChromaDB Dense Vector Search with BM25 Sparse Keyword Search using Reciprocal Rank Fusion (RRF).
"""

import pickle
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()


class HybridRetriever:
    """
    Combines dense embeddings (Google Gemini) and sparse keyword matching (BM25)
    fused via Reciprocal Rank Fusion (RRF) for high-accuracy factory SOP and manual retrieval.
    """

    def __init__(self, chroma_persist_dir: str, bm25_path: str):
        # Initialize Google Embedding Model
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")

        # Load Local Chroma Vector Store
        self.vector_store = Chroma(
            persist_directory=str(chroma_persist_dir),
            embedding_function=self.embeddings,
        )

        # Load Local BM25 Keyword Store
        with open(bm25_path, "rb") as f:
            self.bm25_retriever = pickle.load(f)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Perform hybrid search using Reciprocal Rank Fusion (RRF).
        
        Args:
            query: User's search text / alarm query
            top_k: Number of combined documents to return
            filter_dict: Dictionary for metadata filtering (e.g., {"machine": "Haas VF-2", "doc_type": "SOP"})
        
        Returns:
            List of LangChain Document objects scored by RRF.
        """
        retrieve_k = max(top_k * 2, 10)

        # --- 1. Dense Search (Vector) ---
        vector_docs: List[Document] = []
        try:
            vector_docs = self.vector_store.similarity_search(
                query,
                k=retrieve_k,
                filter=filter_dict,
            )
        except Exception as e:
            # Fallback if filter syntax differs or empty
            print(f"[HybridRetriever] Dense search warning: {e}")
            vector_docs = self.vector_store.similarity_search(query, k=retrieve_k)
            if filter_dict:
                vector_docs = [
                    d for d in vector_docs
                    if all(d.metadata.get(k) == v for k, v in filter_dict.items())
                ]

        # --- 2. Sparse Search (Keyword/BM25) ---
        self.bm25_retriever.k = retrieve_k * 5
        sparse_docs_unfiltered = self.bm25_retriever.invoke(query)

        sparse_docs: List[Document] = []
        for doc in sparse_docs_unfiltered:
            if filter_dict:
                if all(doc.metadata.get(k) == v for k, v in filter_dict.items()):
                    sparse_docs.append(doc)
            else:
                sparse_docs.append(doc)

            if len(sparse_docs) == retrieve_k:
                break

        # --- 3. Reciprocal Rank Fusion (RRF) ---
        rrf_constant = 60
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        def add_scores(docs: List[Document]):
            for rank, doc in enumerate(docs):
                doc_id = doc.metadata.get("id")
                if not doc_id:
                    doc_id = str(hash(doc.page_content))

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = 0.0
                    doc_map[doc_id] = doc

                # RRF Formula: 1 / (rank + 1 + rrf_constant)
                doc_scores[doc_id] += 1.0 / (rank + 1 + rrf_constant)

        add_scores(vector_docs)
        add_scores(sparse_docs)

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        result_docs: List[Document] = []
        for doc_id, score in sorted_docs[:top_k]:
            doc = doc_map[doc_id]
            doc.metadata["rrf_score"] = score
            result_docs.append(doc)

        return result_docs
