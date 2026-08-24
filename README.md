# Adaptive Factory Operator AI Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.13-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![LLM Engine](https://img.shields.io/badge/LLM-Google%20Gemini%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Package Manager](https://img.shields.io/badge/package%20manager-uv-purple.svg)](https://astral.sh/uv)

A **smart AI Copilot** for factory floors (CNC Machining & Injection Molding). It gives real-time, step-by-step help tailored to each operator's skill level. It learns from real SCADA outcomes and enforces safety rules—without ever making things up (no hallucination).

---

## 📚 Documentation

| Document | Contents |
|---|---|
| 🏛️ [solution_design.md](doc/solution_design.md) | How it works, the two-loop system, safety rules, and mathematical foundations |
| 📊 [evaluation_framework_design.md](doc/evaluation_framework_design.md) | Offline testing metrics, online production telemetry, and operational business KPIs |
| 💡 [architecture_and_behavioral_qa.md](doc/architecture_and_behavioral_qa.md) | Deep-dive Q&A on behavioral pattern learning, data sources, agents & safety |
| 🧪 [demo_and_evaluation_guide.md](doc/demo_and_evaluation_guide.md) | Interactive test cases & demo walkthrough for evaluating all design claims |
| 📦 [code_and_modules_guide.md](doc/code_and_modules_guide.md) | List of all code files and what they do |
| ⚙️ [run_and_configuration_guide.md](doc/run_and_configuration_guide.md) | How to install, run commands, JSON file setups, and FAQ |

---

## ✨ Key Features

| Feature | How It Works |
|---|---|
| **Tracks skill per machine** | Decoupled Knowledge Graph — An expert on Machine A is not assumed to be an expert on Machine B. |
| **Changes how it talks** | State-Bound UCB1 Bandit — Uses Visual, Short, or Detailed formats depending on your skill level. |
| **Protects tired workers** | ECM Fatigue Gate — Switches to the simplest format if your shift is almost over. |
| **Stops duct-tape fixes** | 8-Hour Durability Window — Waits 8 hours to ensure a fix is permanent before giving credit. |
| **Safely shares shortcuts** | 3-Expert Vote — Keeps new shortcuts hidden until 3 Experts approve them. |
| **Keeps the screen fast** | Shadow Observer — Logs events in under 5ms so the UI never freezes. |

---

## 📁 Files & Folders

```text
factory-agent-app/
├── app.py                          # Streamlit UI — The Shop Floor Screen
├── sleep_cycle_evaluator.py        # Nightly update script (runs at 03:00 AM)
├── doc/                            # Documentation
├── agents/
│   ├── bandit_router.py            # Picks the best format based on skill & fatigue
│   ├── chat_agent.py               # Google Gemini LLM agent
│   └── shadow_observer.py          # Fast event logger
├── memory/
│   ├── semantic_graph.py           # Tracks who knows which machine
│   ├── procedural_memory.py        # Fix paths and success rates
│   ├── debrief_store.py            # Asks operators how they fixed things so fast
│   ├── episodic_store.py           # Logs all events
│   ├── working_memory.py           # Builds the prompt for the LLM
│   └── search.py                   # Finds the right manual (ChromaDB + BM25)
├── mock_services/                  # Simulators for SCADA, CMMS, HR, and ECM
├── data/                           # JSON storage and search databases
├── pyproject.toml
└── .env                            # Your GOOGLE_API_KEY goes here
```

---

## 🚀 Quickstart

### 1. Requirements
- Python `3.10+`
- Google Gemini API Key

### 2. Install `uv` (Recommended)

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
uv sync                           # Install all required packages

# Create .env file:
echo GOOGLE_API_KEY=your_key_here > .env
```

> **If using standard pip**: `python -m venv .venv && .venv\Scripts\activate && pip install -e .`

---

## 🖥️ Run the App

```bash
# Start the Shop Floor Screen (UI)
uv run streamlit run app.py        # Opens at http://localhost:8501

# Run the nightly updates (verifies repair durability, updates graphs)
uv run python sleep_cycle_evaluator.py

# Update the search database (run this if you edit factory_knowledge_base.json)
uv run python data/ingest.py
```

---
