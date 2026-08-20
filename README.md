# Factory Operator AI Assistant

Smart AI Assistant for factory operators featuring real-time cognitive state tracking, UCB Contextual Bandit format personalization, NetworkX Knowledge Graph autonomy learning, and SCADA/CMMS closed-loop feedback.

## Project Structure

```text
factory-agent-app/
├── app.py                  # Main Streamlit Application
├── agents/                 # AI Agents & Policy Routing
│   ├── bandit_router.py    # UCB Multi-Armed Bandit algorithm
│   ├── chat_agent.py       # Google Gemini LLM Chat Agent
│   └── shadow_observer.py  # Autonomy & Feedback Learning Evaluator
├── memory/                 # Multi-Tier Memory Systems
│   ├── semantic_graph.py   # Operator Competency Knowledge Graph (NetworkX)
│   ├── episodic_store.py   # Historical Turn & Action Logger
│   ├── search.py           # Hybrid BM25 + Vector Search (RRF)
│   └── working_memory.py   # Dynamic Prompt Assembler
├── mock_services/          # Shopfloor System Emulators
│   ├── cmms_service.py     # Work Orders & Escalations
│   ├── hr_lms_service.py   # Operator Roles & Shift Records
│   └── scada_service.py    # Machine Telemetry & Alarms
├── data/                   # Data, Ingestion & Persistence
│   ├── ingest.py           # Ingestion script
│   ├── factory_knowledge_base.json
│   ├── chroma_db/          # Persistent Vector Store
│   ├── bm25_retriever.pkl  # Sparse Keyword Index
│   ├── graph_state.json    # Knowledge Graph Persistence
│   └── episodic_logs.json  # Interaction Audit Logs
├── pyproject.toml
├── .env
└── README.md
```

## Getting Started

### 1. Install Dependencies
```bash
uv sync
# or
pip install -r requirements.txt # or pip install -e .
```

### 2. Configure Environment
Ensure `.env` contains your Google Gemini API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Launch the Application
```bash
streamlit run app.py
```

