# Setup, Execution & Configuration Guide: Factory Operator AI Assistant

**Author:** Manufacturing AI Systems Architecture Team  
**Date:** August 2026  
**Format:** Markdown (MD)  

## Table of Contents
- [1. Overview](#1-overview)
- [2. Environment Setup](#2-environment-setup)
  - [2.1 What You Need](#21-what-you-need)
  - [2.2 Installing `uv` (Package Manager)](#22-installing-uv-package-manager)
  - [2.3 Installing the Project](#23-installing-the-project)
  - [2.4 Adding Your API Key](#24-adding-your-api-key)
- [3. Running the App](#3-running-the-app)
  - [3.1 Starting the Shop Floor Screen (UI)](#31-starting-the-shop-floor-screen-ui)
  - [3.2 Running the Nightly Update Script](#32-running-the-nightly-update-script)
  - [3.3 Running Automated Tests](#33-running-automated-tests)
  - [3.4 Updating the Search Database](#34-updating-the-search-database)
- [4. JSON Files Guide](#4-json-files-guide)
  - [4.1 `data/factory_knowledge_base.json` - Official Manuals](#41-datafactory_knowledge_basejson---official-manuals)
  - [4.2 `data/procedural_fault_trees.json` - Fix Paths & Success Rates](#42-dataprocedural_fault_treesjson---fix-paths--success-rates)
  - [4.3 `data/quarantine_sops.json` - Unverified Shortcuts](#43-dataquarantine_sopsjson---unverified-shortcuts)
  - [4.4 `data/escrow_rewards.json` - 8-Hour Waiting Room](#44-dataescrow_rewardsjson---8-hour-waiting-room)
  - [4.5 `data/pending_debriefs.json` - Questions for Operators](#45-datapending_debriefsjson---questions-for-operators)
  - [4.6 `data/graph_state.json` - Knowledge Graph File](#46-datagraph_statejson---knowledge-graph-file)
  - [4.7 Event Logs](#47-event-logs)
- [5. FAQ & Troubleshooting](#5-faq--troubleshooting)

---

## 1. Overview

This guide shows you how to set up the app, how to run it, and explains the JSON files used for storage.
For the system design, see [solution_design.md](solution_design.md).
For code details, see [code_and_modules_guide.md](code_and_modules_guide.md).

---

## 2. Environment Setup

### 2.1 What You Need
* **Operating System**: Windows 10/11, macOS, or Linux.
* **Python**: Python **3.10** or higher.
* **API Key**: A valid **Google Gemini API Key**.

### 2.2 Installing `uv` (Package Manager)
We recommend using `uv` because it is very fast at managing Python packages.

**Windows (PowerShell)**:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS & Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Standard pip (if you don't want to use uv)**:
```bash
pip install uv
```

### 2.3 Installing the Project

Go to the project folder:
```bash
cd factory-agent-app
```

**Using `uv` (Recommended)**:
```bash
uv sync
```

**Using Standard Python (`venv` + `pip`)**:
```bash
python -m venv .venv
   
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -e .
```

### 2.4 Adding Your API Key
Create a file named `.env` in the main project folder and add your key:
```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```

*(Optional setting to change the model)*:
```env
GEMINI_MODEL_NAME=gemini-2.5-flash
```

---

## 3. Running the App

### 3.1 Starting the Shop Floor Screen (UI)
This is the Streamlit app that the operators will see on their tablets.

**Run Command**:
```bash
uv run streamlit run app.py
```

* **URL**: `http://localhost:8501`
* **What you can do in the UI**:
  1. Pick an operator (e.g., John Doe the Novice, or Sarah the Expert) and a machine.
  2. Change the shift hour slider to test the Fatigue rules.
  3. Type a problem into the chat (like `"Alarm 102"`).
  4. Test the "Change Format" and "Solved" buttons.

### 3.2 Running the Nightly Update Script
This script normally runs at 03:00 AM. It checks the 8-hour escrow wait times, updates the knowledge graph and fault trees, and approves new shortcuts.

**Run Command**:
```bash
uv run python sleep_cycle_evaluator.py
```

**What it will print**:
```text
======================================================================
STARTING ASYNCHRONOUS SLEEP CYCLE BATCH EVALUATION (03:00 AM CRON)
======================================================================
[1/5] Ingesting shift events from data/episodic_event_queue.json...
[2/5] Evaluating Provisional Reward Escrow & Durability Window (8h)...
[3/5] Mutating Knowledge Graph & Recalculating State Tiers...
[4/5] Updating Bayesian Procedural Fault Trees...
[5/5] Checking Quarantine SOP Consensus (3-Expert Threshold)...
[FLUSH] Shift event queue cleared and archived to data/episodic_logs.json.
======================================================================
SLEEP CYCLE BATCH EVALUATION COMPLETE.
======================================================================
```

### 3.3 Running Automated Tests
Run these tests to make sure all the core features work:

```bash
uv run python verify_omni_concepts.py
uv run python verify_refactor.py
uv run python verify_section2.py
uv run python verify_section3.py
```

### 3.4 Updating the Search Database
If you add a new manual to `data/factory_knowledge_base.json`, you must run this script to update the search index (ChromaDB):

```bash
uv run python data/ingest.py
```

---

## 4. JSON Files Guide

All data is saved in simple JSON files in the `data/` folder. Here is what they look like.

### 4.1 `data/factory_knowledge_base.json` - Official Manuals
* **Purpose**: The official factory rules that the AI is allowed to read.
* **Format**:
```json
[
  {
    "sop_id": "SOP-HAAS-001",
    "title": "Haas VF-2: Low Air Pressure & Alarm 102 Troubleshooting",
    "machine_type": "Haas CNC",
    "target_error_code": "Alarm 102",
    "hazard_level": "Medium",
    "required_ppe": ["Safety Glasses", "Steel-toe Boots"],
    "loto_required": false,
    "summary": "Step-by-step resolution for Haas VF-2 Alarm 102.",
    "resolution_steps": [
      "Verify main shop air supply valve is OPEN.",
      "Check rear regulator gauge; nominal reading must exceed 85 PSI.",
      "Inspect pneumatic bowl filter for condensation or particulate clogging.",
      "Press RESET on Haas control pendant to clear alarm."
    ],
    "prohibited_actions": [
      "Do NOT bypass pneumatic pressure interlock switches.",
      "Do NOT open rear electrical cabinet while power is ON without LOTO."
    ]
  }
]
```

* **How to add a new one**: Add a new block to the JSON file, then run `uv run python data/ingest.py`.

### 4.2 `data/procedural_fault_trees.json` - Fix Paths & Success Rates
* **Purpose**: The different ways to fix an alarm, and how often each way has worked.
* **Format**:
```json
[
  {
    "error_code": "Alarm 102",
    "machine_type": "Haas CNC",
    "description": "Haas VF-2 Servos Off (Low Air Pressure)",
    "diagnostic_paths": [
      {
        "path_id": "HAAS_102_REGULATOR",
        "description": "Adjust Main Air Regulator on Rear Panel",
        "target_subsystem": "Pneumatics",
        "estimated_time_mins": 2.5,
        "success_count": 28,
        "failure_count": 2,
        "avg_execution_time_mins": 2.8,
        "min_tier_required": "Novice"
      }
    ]
  }
]
```

### 4.3 `data/quarantine_sops.json` - Unverified Shortcuts
* **Purpose**: Stores new shortcuts until 3 Experts approve them.
* **Format**:
```json
[
  {
    "sop_id": "QUAR-HAAS-102-001",
    "title": "Air Line Quick-Tap Bleed Shortcut",
    "machine_type": "Haas CNC",
    "target_error_code": "Alarm 102",
    "discovered_by": "OP-001",
    "timestamp": "2026-08-20T14:30:00",
    "description": "Lightly tap pressure regulator valve to unstick pilot plunger.",
    "estimated_time_mins": 1.5,
    "validating_experts": ["OP-002", "OP-004"],
    "consensus_reached": false,
    "min_tier_required": "Expert"
  }
]
```

### 4.4 `data/escrow_rewards.json` - 8-Hour Waiting Room
* **Purpose**: Holds rewards for 8 hours to make sure the machine doesn't break again.
* **Format**:
```json
[
  {
    "escrow_id": "ESCROW-89A12F",
    "session_id": "SESS-10492",
    "operator_id": "OP-001",
    "machine_id": "Haas VF-2",
    "fault_code": "Alarm 102",
    "durability_window_hours": 8.0,
    "provisional_autonomy_delta": 5.0,
    "provisional_bandit_reward": 1.0,
    "status": "PENDING_AUDIT"
  }
]
```

### 4.5 `data/pending_debriefs.json` - Questions for Operators
* **Purpose**: Stores the Yes/No questions to ask operators who fixed an alarm very fast.
* **Format**:
```json
[
  {
    "debrief_id": "DEBRIEF-43B0D9ED",
    "operator_id": "OP-002",
    "machine_id": "Haas VF-2",
    "fault_code": "Alarm 102",
    "actual_duration_mins": 1.8,
    "suspected_shortcut": "Regulator Quick Bleed Valve",
    "status": "PENDING"
  }
]
```

### 4.6 `data/graph_state.json` - Knowledge Graph File
* **Purpose**: The saved file that tracks operator skill scores and format choices.

### 4.7 Event Logs
* **`episodic_event_queue.json`**: A fast, temporary place to save events during the shift (under 5ms).
* **`episodic_logs.json`**: The permanent history log of everything that happened.

---

## 5. FAQ & Troubleshooting

**Q: Why do I get a `ModuleNotFoundError: No module named 'dotenv'` error?**
  * **Fix**: Make sure you are using `uv run python <script>.py` or that your virtual environment is activated.

**Q: How do I reset all operator skills back to zero?**
  * **Fix**: Open the Streamlit UI, go to the **Memory Diagnostics** tab, and click **"Reset Knowledge Graph"**, or just delete the `data/graph_state.json` file and restart the app.

**Q: How can I force the AI to try a new format?**
  * **Fix**: Click one of the manual "Change Format" buttons in the UI. This forces a change and teaches the AI your preference.
