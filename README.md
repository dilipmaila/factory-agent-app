# Adaptive Factory Operator AI Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.13-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![LLM Engine](https://img.shields.io/badge/LLM-Google%20Gemini%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Package Manager](https://img.shields.io/badge/package%20manager-uv-purple.svg)](https://astral.sh/uv)

A **closed-loop Adaptive Cognitive AI Copilot** for precision manufacturing shopfloors (CNC Machining & Injection Molding). It personalizes troubleshooting guidance in real-time per operator skill level, learns from SCADA-verified outcomes, and enforces industrial safety guardrails — without hallucination.

---

## 📚 Documentation

| Document | Contents |
|---|---|
| 🏛️ [solution_design.rst](doc/solution_design.rst) | Architecture, dual-loop lifecycle, math formulations, FMEA guardrails, pilot plan |
| 📦 [code_and_modules_guide.rst](doc/code_and_modules_guide.rst) | Class & method reference for all modules |
| ⚙️ [run_and_configuration_guide.rst](doc/run_and_configuration_guide.rst) | Setup, run commands, JSON schema definitions, FAQ |

---

## ✨ Key Capabilities

| Capability | Mechanism |
|---|---|
| **Machine-specific skill profiling** | Decoupled NetworkX graph — Expert on Haas ≠ Expert on Engel |
| **Adaptive response formatting** | State-bound UCB1 bandit: Visual / Terse / Detailed per competence tier |
| **Cognitive fatigue adaptation** | ECM Fatigue Gate forces 100% exploitation at ≥80% shift completion |
| **Duct-tape fix prevention** | Rewards held in 8-hr escrow; SCADA recurrence inverts reward to penalty |
| **Crowdsourced SOP safety** | Discovered shortcuts quarantined until 3 distinct Expert sign-offs |
| **Sub-100ms event logging** | Shadow Observer writes to event queue in <5ms, zero intra-shift drift |

---

## 📁 Repository Structure

```text
factory-agent-app/
├── app.py                          # Streamlit UI — Shopfloor HMI
├── sleep_cycle_evaluator.py        # Async batch evaluator (03:00 AM cron)
├── verify_refactor.py / section2/3 # Automated verification suites
├── doc/                            # Architecture & operations documentation
├── agents/
│   ├── bandit_router.py            # UCB1 bandit with ECM fatigue gating
│   ├── chat_agent.py               # Gemini LLM agent (LangChain)
│   └── shadow_observer.py          # <5ms event logger & escrow enqueuer
├── memory/
│   ├── semantic_graph.py           # Decoupled knowledge graph (NetworkX)
│   ├── procedural_memory.py        # Bayesian fault trees & quarantine
│   ├── debrief_store.py            # Micro-debrief queue
│   ├── episodic_store.py           # Shift event queue & audit ledger
│   ├── working_memory.py           # Prompt assembler
│   └── search.py                   # Hybrid ChromaDB + BM25 retriever (RRF)
├── mock_services/                  # SCADA, CMMS, HR/LMS, ECM emulators
├── data/                           # JSON state stores & vector indices
├── pyproject.toml
└── .env                            # GOOGLE_API_KEY
```

---

## 🚀 Quickstart

### 1. Prerequisites
- Python `3.10+`
- Google Gemini API Key

### 2. Install `uv` (recommended)

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install & Configure

```bash
uv sync                           # Install dependencies

# Create .env in project root:
echo GOOGLE_API_KEY=your_key_here > .env
```

> **pip fallback**: `python -m venv .venv && .venv\Scripts\activate && pip install -e .`

---

## 🖥️ Run

```bash
# Shopfloor HMI (main UI)
uv run streamlit run app.py        # → http://localhost:8501

# Overnight batch learning (escrow audit, graph mutations, Bayesian updates)
uv run python sleep_cycle_evaluator.py

# Rebuild knowledge base index (after editing factory_knowledge_base.json)
uv run python data/ingest.py
```

### Verification Suites

```bash
uv run python verify_omni_concepts.py   # Anti-patterns, SOS, domain fencing
uv run python verify_refactor.py        # Bayesian trees, decoupled graph, queue
uv run python verify_section2.py        # Escrow, quarantine, format overrides
uv run python verify_section3.py        # ECM, fatigue gating, micro-debriefs
```

---

## 📄 License

Designed for Advanced Manufacturing AI Systems. Grounded in ISO/OSHA industrial safety principles.
