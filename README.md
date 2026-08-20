# Adaptive Factory Operator AI Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.13-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![LLM Engine](https://img.shields.io/badge/LLM-Google%20Gemini%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Package Manager](https://img.shields.io/badge/package%20manager-uv-purple.svg)](https://astral.sh/uv)

A production-grade, closed-loop **Adaptive Cognitive AI Assistant** designed for precision manufacturing shopfloors (CNC Machining & Injection Molding). The system personalizes troubleshooting guidance in real-time, learns from operational feedback without hallucinations, and enforces strict industrial safety guardrails.

---

## 📚 Architectural & Technical Documentation

Comprehensive documentation is available in the [`doc/`](doc/) directory:

* 🏛️ **[Architectural Solution Design (`doc/solution_design.rst`)](doc/solution_design.rst)**:
  Full end-to-end system design, dual-loop lifecycle (<100ms sync vs. overnight async), decoupled knowledge graph topology, Bayesian fault trees, UCB1 bandit formulation, FMEA safety guardrails, and pilot validation plans.
* 📦 **[Code & Modules Technical Reference (`doc/code_and_modules_guide.rst`)](doc/code_and_modules_guide.rst)**:
  In-depth class-by-class and method-by-method breakdown of all modules (`app.py`, `agents/`, `memory/`, `mock_services/`, `sleep_cycle_evaluator.py`, test suites).
* ⚙️ **[Operations, Execution & Configuration Guide (`doc/run_and_configuration_guide.rst`)](doc/run_and_configuration_guide.rst)**:
  Step-by-step runtime manual, JSON schema definitions, instructions for modifying databases (`quarantine_sops.json`, `procedural_fault_trees.json`, `escrow_rewards.json`), and troubleshooting FAQ.

---

## 🌟 Key Architectural Innovations

1. **Decoupled Cognitive State Graph (`memory/semantic_graph.py`)**:
   Decouples machine-specific operator competence (`OPERATES` edges with autonomy scores 0–100%) from cognitive presentation preferences (`PREFERS` edges per cognitive state). Eliminates the *Paradox of Expertise* where a CNC expert is treated as an expert on an unfamiliar injection molding press.
2. **Dynamic Bayesian Fault Trees (`memory/procedural_memory.py`)**:
   Models machine alarms as dynamic diagnostic trees with branching paths. Branch probabilities update via Beta-Binomial conjugate updating (Laplace smoothing) based on real-world resolution telemetry.
3. **Contextual Bandit with Fatigue Gating (`agents/bandit_router.py`)**:
   UCB1 multi-armed bandit dynamically routes between `Visual_StepByStep`, `Terse_Technical`, and `Detailed_Text`. The **Environmental Context Matrix (ECM)** triggers a **Fatigue Gate** ($\text{Fatigue Index} \ge 0.80$) to force 100% exploitation of concise formats during late shift hours.
4. **Provisional Reward Escrow & The 8-Hour Durability Window (`data/escrow_rewards.json`)**:
   Resolves the *"Duct-Tape Problem"*. Resolution rewards are held in escrow for 8 hours. If SCADA detects a recurring fault within 8 hours, the provisional reward is inverted into a $-5.0$ bandit penalty and $-15.0$ autonomy penalty.
5. **3-Expert Quarantine Consensus (`data/quarantine_sops.json`)**:
   Crowdsourced shortcuts captured via micro-debriefs are sandboxed in quarantine until 3 distinct Senior/Expert operators validate them, preventing unverified shortcuts from leaking to novices.
6. **Sub-100ms Synchronous Event Logging (`agents/shadow_observer.py`)**:
   Emits shift event payloads to `data/episodic_event_queue.json` in **<5ms**, eliminating intra-shift UI latency and semantic profile drift.
7. **Human Agency Hard Overrides**:
   Operators can override bandit format selections instantly from the UI, triggering real-time LLM re-synthesis and applying learning penalties to the rejected format.

---

## 📁 Repository Structure

```text
factory-agent-app/
├── app.py                          # Streamlit UI & Interactive Multi-Tier Shopfloor HMI
├── sleep_cycle_evaluator.py        # Asynchronous Batch Sleep Cycle Evaluator & Escrow Engine
├── verify_refactor.py              # Verification Suite: Procedural, Decoupled Graph & Queue
├── verify_section2.py              # Verification Suite: Escrow, Quarantine & Format Overrides
├── verify_section3.py              # Verification Suite: ECM, Fatigue Gating & Micro-Debriefs
├── doc/                            # Comprehensive System Documentation
│   ├── solution_design.rst         # Architectural Solution Design
│   ├── code_and_modules_guide.rst  # Code & Modules Technical Reference Guide
│   └── run_and_configuration_guide.rst # Operations, Run & JSON Configuration Guide
├── agents/                         # AI Agents & Policy Routing
│   ├── bandit_router.py            # UCB1 Multi-Armed Bandit with ECM Fatigue Gating
│   ├── chat_agent.py               # Google Gemini LLM Reasoning Agent (LangChain)
│   └── shadow_observer.py          # Low-Latency Shift Event Logger & Escrow Enqueuer
├── memory/                         # Multi-Tier Cognitive Memory Subsystems
│   ├── semantic_graph.py           # Decoupled NetworkX Knowledge Graph (Operator Autonomy)
│   ├── procedural_memory.py        # Dynamic Bayesian Fault Trees & Quarantine Consensus
│   ├── debrief_store.py            # Micro-Debrief Store & Fast-Fix Intercept Queue
│   ├── episodic_store.py           # Low-Latency Shift Event Queue & Turn Audit Ledger
│   ├── working_memory.py           # Dynamic Prompt Assembler with Safety & Alarm Injections
│   └── search.py                   # Hybrid Dense (ChromaDB) + Sparse (BM25) Retriever (RRF)
├── mock_services/                  # Shopfloor Integration Emulators
│   ├── scada_service.py            # SCADA Telemetry Stream, Alarms & verify_repair()
│   ├── ecm_service.py              # Environmental Context Matrix (Shift, Fatigue, Noise)
│   ├── cmms_service.py             # CMMS Work Order Dispatch & Maintenance Tickets
│   └── hr_lms_service.py           # Operator Rosters & Cold-Start Qualification Seeding
├── data/                           # Data Persistence, Indices & Ingestion
│   ├── ingest.py                   # Offline Knowledge Base Embedding Pipeline
│   ├── factory_knowledge_base.json # Authoritative Grounding SOPs
│   ├── procedural_fault_trees.json # Active Dynamic Bayesian Fault Trees
│   ├── quarantine_sops.json        # Sandboxed Crowdsourced Procedures
│   ├── escrow_rewards.json         # Provisional Reward Escrow Ledger (8-hr Window)
│   ├── pending_debriefs.json       # Enqueued Micro-Debrief Prompts
│   ├── episodic_event_queue.json   # Synchronous Shift Event Queue (<100ms)
│   ├── episodic_logs.json          # Permanent Append-Only Turn Audit Logs
│   └── graph_state.json            # Knowledge Graph Serialization State
├── pyproject.toml                  # Project Metadata & Python Dependencies
├── .env                            # Environment Variables & API Keys
└── README.md                       # Project Overview & Quickstart Guide
```

---

## 🚀 Workspace Setup & Installation

### 1. System Prerequisites
* **Python**: `3.10` or higher (Python `3.13` recommended).
* **Google Gemini API Key**: Required for vector embeddings and LLM reasoning.

### 2. Install Package Manager (`uv`)
[`uv`](https://github.com/astral-sh/uv) is recommended for fast dependency resolution and isolated virtual environments:

* **Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
* **macOS / Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Pip Fallback**:
  ```bash
  pip install uv
  ```

### 3. Install Project Dependencies

Navigate to the project root and synchronize dependencies:

```bash
# Using uv (Recommended):
uv sync

# Or using standard pip:
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -e .
```

### 4. Configure Environment Variables (`.env`)

Create or update `.env` in the repository root:

```env
GOOGLE_API_KEY=your_actual_google_gemini_api_key_here
```

---

## 🖥️ Running the Application & Tools

### 1. Launch the Interactive Streamlit Shopfloor HMI
```bash
uv run streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 2. Run the Offline Sleep Cycle Batch Evaluator
Simulates the overnight 03:00 AM batch audit, durability window evaluation, knowledge graph mutation, Bayesian tree update, and quarantine promotion:
```bash
uv run python sleep_cycle_evaluator.py
```

### 3. Execute Automated Verification Suites
Validate system behavior across all components:
```bash
# Suite 1: Bayesian Fault Trees, Decoupled Graph & Event Queue
uv run python verify_refactor.py

# Suite 2: Escrow Durability, Quarantine Consensus & Format Overrides
uv run python verify_section2.py

# Suite 3: Environmental Context Matrix, Fatigue Gating & Micro-Debriefs
uv run python verify_section3.py
```

### 4. Re-Index Grounding Knowledge Base
Rebuild ChromaDB dense vector store and BM25 index after editing `data/factory_knowledge_base.json`:
```bash
uv run python data/ingest.py
```

---

## 📄 License & Attribution

Designed and engineered for Advanced Manufacturing AI Systems. Grounded in ISO/OSHA industrial safety principles.
