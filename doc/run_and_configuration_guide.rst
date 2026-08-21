========================================================================================
Operations, Execution & Configuration Guide: Factory Operator AI Assistant
========================================================================================

:Author: Manufacturing AI Systems Architecture Team
:Date: August 2026
:Format: reStructuredText (RST)

.. contents:: Table of Contents
   :depth: 3
   :local:
   :backlinks: entry

----------------------------------------------------------------------------------------

1. Overview & Setup Prerequisites
=================================

This guide covers environment setup, run commands, and JSON data store schemas.
For architecture and math, see `solution_design.rst <solution_design.rst>`_.
For module-level code reference, see `code_and_modules_guide.rst <code_and_modules_guide.rst>`_.

----------------------------------------------------------------------------------------

2. Environment Setup & Workspace Configuration
==============================================

2.1 System Prerequisites
------------------------
* **Operating System**: Windows 10/11, macOS (Apple Silicon or Intel), or Linux (Ubuntu 20.04+).
* **Python Runtime**: Python **3.10** or higher (Python 3.13 recommended).
* **API Access**: A valid **Google Gemini API Key** with access to Gemini Flash models.

2.2 Installing the `uv` Package Manager
---------------------------------------
`uv` is an extremely fast Python package and project manager. It is recommended for managing dependencies
and virtual environments.

**Windows (PowerShell)**:

.. code-block:: powershell

   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

**macOS & Linux (Bash / Zsh)**:

.. code-block:: bash

   curl -LsSf https://astral.sh/uv/install.sh | sh

**Alternative (Standard pip)**:

.. code-block:: bash

   pip install uv

2.3 Setting Up Virtual Environment & Dependencies
-------------------------------------------------

Navigate to the project root directory:

.. code-block:: bash

   cd factory-agent-app

**Option A: Using `uv` (Recommended)**:

.. code-block:: bash

   # Synchronize project dependencies from pyproject.toml and uv.lock
   uv sync

**Option B: Using Standard Python Virtual Environment (`venv` + `pip`)**:

.. code-block:: bash

   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment
   # On Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # On Linux / macOS:
   source .venv/bin/activate

   # Install dependencies
   pip install -e .

2.4 Configuring Environment Variables (`.env`)
----------------------------------------------
Create or edit the ``.env`` file in the project root directory:

.. code-block:: env

   GOOGLE_API_KEY=your_actual_gemini_api_key_here

*(Optional settings)*:

.. code-block:: env

   # Model Selection Override (Default: gemini-2.5-flash)
   GEMINI_MODEL_NAME=gemini-2.5-flash

----------------------------------------------------------------------------------------

3. Running the Applications
===========================

3.1 Starting the Streamlit Interactive Shopfloor HMI
----------------------------------------------------
The Streamlit application provides the real-time tablet interface for operators and administrators.

**Run Command**:

.. code-block:: bash

   # Using uv:
   uv run streamlit run app.py

   # Or using activated virtual environment:
   streamlit run app.py

* **Default Local URL**: ``http://localhost:8501``
* **Key Interactions**:

  1. **Operator & Machine selectors** (sidebar) — switch between John Doe (Novice), Sarah Jenkins (Expert/Novice on Engel), Mike Chang (Intermediate).
  2. **ECM sliders** — adjust shift hour and supervisor toggle to test fatigue gating.
  3. **Chat input / quick-prompt buttons** — type queries like ``"Alarm 102"`` or ``"Barrel overheat"``.
  4. **Format Override buttons & Feedback buttons** — trigger instant LLM re-synthesis or log resolution outcomes.

3.2 Running the Offline Sleep Cycle Batch Evaluator
---------------------------------------------------
The offline evaluator simulates the 03:00 AM overnight maintenance process. It evaluates provisional
rewards in escrow against SCADA recurrence history, executes graph state mutations, updates Bayesian
fault trees, and promotes consensus-approved quarantine SOPs.

**Run Command**:

.. code-block:: bash

   # Using uv:
   uv run python sleep_cycle_evaluator.py

   # Or using activated virtual environment:
   python sleep_cycle_evaluator.py

**Expected Console Output**:

.. code-block:: text

   ======================================================================
   STARTING ASYNCHRONOUS SLEEP CYCLE BATCH EVALUATION (03:00 AM CRON)
   ======================================================================
   [1/5] Ingesting shift events from data/episodic_event_queue.json...
         -> Loaded X shift events.
   [2/5] Evaluating Provisional Reward Escrow & Durability Window (8h)...
         -> Escrow Audit: X durable releases (+1.0 / +5.0), Y duct-tape penalties (-5.0 / -15.0).
   [3/5] Mutating Knowledge Graph & Recalculating State Tiers...
         -> Operator OP-001 Haas Autonomy: 35.0 -> 40.0 (Derived Tier: Intermediate).
         -> Graph state atomically persisted to data/graph_state.json.
   [4/5] Updating Bayesian Procedural Fault Trees...
         -> Updated X diagnostic branch probabilities via Laplace conjugate updating.
   [5/5] Checking Quarantine SOP Consensus (3-Expert Threshold)...
         -> Quarantine SOP promoted to Active Library with clearance tag.
   [FLUSH] Shift event queue cleared and archived to data/episodic_logs.json.
   ======================================================================
   SLEEP CYCLE BATCH EVALUATION COMPLETE.
   ======================================================================

3.3 Running Automated Test & Verification Suites
------------------------------------------------
Execute all four verification test suites to validate architectural integrity:

.. code-block:: bash

   # Suite 0: Omni-Cognitive Features (Anti-Patterns, SOS Mode, Domain Fencing, Forced Epsilon)
   uv run python verify_omni_concepts.py

   # Suite 1: Procedural Bayesian Trees, Decoupled Graph & Shift Queue
   uv run python verify_refactor.py

   # Suite 2: Escrow Durability, Quarantine Consensus & Format Overrides
   uv run python verify_section2.py

   # Suite 3: Environmental Context Matrix, Fatigue Gating & Micro-Debriefs
   uv run python verify_section3.py

3.4 Re-building the Vector & Keyword Search Indices
---------------------------------------------------
If you add new standard SOPs to ``data/factory_knowledge_base.json``, run the offline ingestion pipeline
to refresh ChromaDB embeddings and BM25 index:

.. code-block:: bash

   uv run python data/ingest.py

----------------------------------------------------------------------------------------

4. JSON Configuration & Data Store Guide
========================================

All system state and configurations are persisted in human-readable JSON files inside the ``data/``
directory. Below are the exact schemas, required fields, and instructions for customizing them.

4.1 `data/factory_knowledge_base.json` - Grounding SOPs
-------------------------------------------------------
* **Purpose**: Authoritative factory operating procedures used by the Hybrid Retrieval engine (ChromaDB + BM25).
* **Schema Definition**:

.. code-block:: json

   [
     {
       "sop_id": "SOP-HAAS-001",
       "title": "Haas VF-2: Low Air Pressure & Alarm 102 Troubleshooting",
       "machine_type": "Haas CNC",
       "target_error_code": "Alarm 102",
       "hazard_level": "Medium",
       "required_ppe": ["Safety Glasses", "Steel-toe Boots"],
       "loto_required": false,
       "summary": "Step-by-step resolution for Haas VF-2 Alarm 102 (SERVOS OFF) caused by low pneumatic pressure.",
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

* **How to Add a New SOP**:
  1. Append a new JSON object to the array with a unique ``sop_id``.
  2. Specify ``machine_type`` (e.g., ``"Haas CNC"``, ``"Engel Injection Molder"``) and ``target_error_code``.
  3. Detail ``resolution_steps`` and ``prohibited_actions``.
  4. Run ``uv run python data/ingest.py`` to regenerate vector embeddings.

4.2 `data/procedural_fault_trees.json` - Dynamic Bayesian Fault Trees
---------------------------------------------------------------------
* **Purpose**: Dynamic diagnostic trees with multiple branching paths and live telemetry counts per error code.
* **Schema Definition**:

.. code-block:: json

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
         },
         {
           "path_id": "HAAS_102_SOLENOID",
           "description": "Inspect Pre-Charge Solenoid Valve Wiring",
           "target_subsystem": "Electrical",
           "estimated_time_mins": 12.0,
           "success_count": 4,
           "failure_count": 6,
           "avg_execution_time_mins": 14.2,
           "min_tier_required": "Intermediate"
         }
       ]
     }
   ]

* **How to Modify or Add Diagnostic Paths**:
  * Set ``min_tier_required`` to ``"Novice"``, ``"Intermediate"``, or ``"Expert"`` to restrict advanced paths from novices.
  * Adjust ``success_count`` and ``failure_count`` to preset baseline prior probabilities.

4.3 `data/quarantine_sops.json` - Sandboxed Crowdsourced Procedures
-------------------------------------------------------------------
* **Purpose**: Holds unverified operator shortcuts until 3-Expert consensus is achieved.
* **Schema Definition**:

.. code-block:: json

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

* **How Consensus Works**:
  * When an Expert operator validates this debrief, their ``operator_id`` is appended to ``validating_experts``.
  * When ``len(validating_experts) >= 3``, ``sleep_cycle_evaluator.py`` auto-promotes it into ``procedural_fault_trees.json`` and marks ``consensus_reached: true``.

4.4 `data/escrow_rewards.json` - Provisional Reward Escrow
----------------------------------------------------------
* **Purpose**: Holds provisional positive rewards during the 8-hour Durability Window.
* **Schema Definition**:

.. code-block:: json

   [
     {
       "escrow_id": "ESCROW-89A12F",
       "session_id": "SESS-10492",
       "operator_id": "OP-001",
       "machine_id": "Haas VF-2",
       "fault_code": "Alarm 102",
       "format_used": "Visual_StepByStep",
       "cognitive_tier": "Novice",
       "timestamp": "2026-08-20T10:15:00",
       "durability_window_hours": 8.0,
       "provisional_autonomy_delta": 5.0,
       "provisional_bandit_reward": 1.0,
       "status": "PENDING_AUDIT"
     }
   ]

4.5 `data/pending_debriefs.json` - Enqueued Micro-Debrief Prompts
-----------------------------------------------------------------
* **Purpose**: Stores pending Y/N debrief prompts triggered when an operator resolves an alarm unusually fast.
* **Schema Definition**:

.. code-block:: json

   [
     {
       "debrief_id": "DEBRIEF-43B0D9ED",
       "operator_id": "OP-002",
       "machine_id": "Haas VF-2",
       "fault_code": "Alarm 102",
       "actual_duration_mins": 1.8,
       "expected_duration_mins": 10.0,
       "suspected_shortcut": "Regulator Quick Bleed Valve",
       "timestamp": "2026-08-20T16:00:00",
       "status": "PENDING"
     }
   ]

4.6 `data/graph_state.json` - Decoupled Knowledge Graph State
-------------------------------------------------------------
* **Purpose**: Serialized NetworkX node-link structure storing operator competence, machine autonomy, and format preferences.
* **Node Types**:
  * ``{"id": "OPERATOR:OP-002", "type": "OPERATOR", "name": "Sarah Jenkins"}``
  * ``{"id": "MACHINE:Haas VF-2", "type": "MACHINE"}``
  * ``{"id": "STATE:OP-002:Expert", "type": "COGNITIVE_STATE", "operator_id": "OP-002", "tier": "Expert"}``
  * ``{"id": "FORMAT:Terse_Technical", "type": "FORMAT_ARM", "arm_name": "Terse_Technical"}``
* **Edge Types**:
  * ``OPERATES`` (Operator -> Machine): ``{"autonomy_score": 95.0, "derived_tier": "Expert", "success_count": 14}``
  * ``STATE_CONFIDENCE`` (Operator -> State): Links operator to their cognitive state nodes.
  * ``PREFERS`` (State -> Format): ``{"weight": 5.2, "pull_count": 8, "success_count": 7, "escalation_count": 1}``

4.7 `data/episodic_event_queue.json` & `data/episodic_logs.json`
----------------------------------------------------------------
* **`episodic_event_queue.json`**: Temporary buffer holding low-latency shift event payloads written in <5ms.
* **`episodic_logs.json`**: Permanent append-only audit ledger recording complete query-response turns with strict status enums:
  * ``"SUCCESS"``: Solved independently.
  * ``"ESCALATED_CMMS"``: Escalated to supervisor (linked with ``ticket_id``).
  * ``"FORMAT_OVERRIDE"``: Operator triggered a manual format override.
  * ``"ABANDONED_TIMEOUT"``: Operator left session without resolution.
  * ``"IN_PROGRESS"``: Turn currently active.

----------------------------------------------------------------------------------------

5. Troubleshooting & FAQ
========================

**Q: Why do I get a `ModuleNotFoundError: No module named 'dotenv'` error when running Python directly?**
  * **Cause**: You are invoking system Python rather than the project virtual environment.
  * **Fix**: Use ``uv run python <script>.py`` or activate ``.venv`` before running.

**Q: How do I reset all operator autonomy scores and knowledge graph weights back to factory defaults?**
  * **Fix**: In the Streamlit UI, expand the **Memory Diagnostics** tab and click **"Reset Knowledge Graph to HR Defaults"**, or delete ``data/graph_state.json`` and restart the app.

**Q: How do I force the system to test an untried presentation format?**
  * **Fix**: Click the manual format override buttons in the Streamlit UI (e.g. *"Force Visual"*), which forces an instant re-synthesis and trains the bandit policy.
