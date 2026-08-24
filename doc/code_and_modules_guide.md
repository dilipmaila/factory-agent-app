# Code and Modules Technical Guide: Factory Operator AI Assistant


## Table of Contents

- [1. Document Overview](#1-document-overview)
  - [1.1 High-Level Module Diagram](#11-high-level-module-diagram)
- [2. Top-Level Applications](#2-top-level-applications)
  - [2.1 `app.py` - The Shop Floor Screen (UI)](#21-apppy---the-shop-floor-screen-ui)
  - [2.2 `sleep_cycle_evaluator.py` - The Nightly Update Script](#22-sleep_cycle_evaluatorpy---the-nightly-update-script)
- [3. Agents Subsystem (`agents/`)](#3-agents-subsystem-agents)
  - [3.1 `agents/bandit_router.py` - Format Personalization Engine](#31-agentsbandit_routerpy---format-personalization-engine)
  - [3.2 `agents/chat_agent.py` - The AI Brain](#32-agentschat_agentpy---the-ai-brain)
  - [3.3 `agents/shadow_observer.py` - Fast Event Logger](#33-agentsshadow_observerpy---fast-event-logger)
- [4. Memory Subsystem (`memory/`)](#4-memory-subsystem-memory)
  - [4.1 `memory/semantic_graph.py` - Knowledge Graph](#41-memorysemantic_graphpy---knowledge-graph)
  - [4.2 `memory/procedural_memory.py` - Fault Trees & Quarantine](#42-memoryprocedural_memorypy---fault-trees--quarantine)
  - [4.3 `memory/debrief_store.py` - Micro-Debrief Loop](#43-memorydebrief_storepy---micro-debrief-loop)
  - [4.4 `memory/episodic_store.py` - Event Queue & History](#44-memoryepisodic_storepy---event-queue--history)
  - [4.5 `memory/working_memory.py` - Prompt Builder](#45-memoryworking_memorypy---prompt-builder)
  - [4.6 `memory/search.py` - Hybrid Search Engine](#46-memorysearchpy---hybrid-search-engine)
- [5. Mock Services Subsystem (`mock_services/`)](#5-mock-services-subsystem-mock_services)
  - [5.1 `mock_services/scada_service.py` - Machine Sensors](#51-mock_servicesscada_servicepy---machine-sensors)
  - [5.2 `mock_services/ecm_service.py` - Environment Context](#52-mock_servicesecm_servicepy---environment-context)
  - [5.3 `mock_services/cmms_service.py` - Maintenance Tickets](#53-mock_servicescmms_servicepy---maintenance-tickets)
  - [5.4 `mock_services/hr_lms_service.py` - HR & Training](#54-mock_serviceshr_lms_servicepy---hr--training)
- [6. Data & Indexing (`data/`)](#6-data--indexing-data)
  - [6.1 `data/ingest.py` - Search Index Builder](#61-dataingestpy---search-index-builder)
  - [6.2 JSON Files](#62-json-files)

---

## 1. Document Overview

This guide lists every code file in the project and explains what it does.
For the overall design and math, see [solution_design.md](solution_design.md).
For setup instructions and JSON files, see [run_and_configuration_guide.md](run_and_configuration_guide.md).

### 1.1 High-Level Module Diagram

```text
   +-----------------------------------------------------------------------------------+
   |                                 PRESENTATION LAYER                                |
   |                            app.py (Streamlit Web HMI)                             |
   +-----------------------------------------------------------------------------------+
             │                                   │                               │
             ▼                                   ▼                               ▼
   +--------------------+              +--------------------+          +--------------------+
   |   AGENTS LAYER     |              |    MEMORY LAYER    |          |   SERVICES LAYER   |
   | - bandit_router.py | ──uses────>  | - semantic_graph.py| <─────── | - scada_service.py |
   | - chat_agent.py    |              | - procedural_mem.py|          | - ecm_service.py   |
   | - shadow_obs.py    |              | - working_memory.py|          | - cmms_service.py  |
   +--------------------+              | - episodic_store.py|          | - hr_lms_service.py|
                                       | - debrief_store.py |          +--------------------+
                                       | - search.py (RAG)  |
                                       +--------------------+
                                                 │
                                                 ▼
   +-----------------------------------------------------------------------------------+
   |                             BATCH GOVERNANCE LAYER                                |
   |                      sleep_cycle_evaluator.py (03:00 AM Script)                   |
   +-----------------------------------------------------------------------------------+
                                                 │
                                                 ▼
   +-----------------------------------------------------------------------------------+
   |                              DATA & PERSISTENCE LAYER                             |
   |   data/*.json  |  data/chroma_db/  |  data/bm25_retriever.pkl  |  data/ingest.py      |
   +-----------------------------------------------------------------------------------+
```

---

## 2. Top-Level Applications

### 2.1 `app.py` - The Shop Floor Screen (UI)
* **File**: `app.py`
* **What it does**: The main screen operators use, built with Streamlit. It acts like a tablet on the shop floor.
* **Key Jobs**:
  1. **Manage Session State**: Remembers the current operator, machine, chat history, and skill state.
  2. **ECM Integration**: Controls shift hours, fatigue levels, and whether a supervisor is around.
  3. **Chat Loop**: Connects the working memory, the bandit (which picks the format), and the LLM (which writes the answer).
  4. **Human Controls**: Buttons to change the format, answer debriefs (Yes/No), and report if a fix worked.
  5. **Diagnostics**: Shows the knowledge graph, fault trees, and event logs in separate tabs.

### 2.2 `sleep_cycle_evaluator.py` - The Nightly Update Script
* **File**: `sleep_cycle_evaluator.py`
* **What it does**: A background script that runs overnight (e.g., at 03:00 AM) to process the day's data.
* **Key Jobs**:
  1. **Read Events**: Reads all events from `data/episodic_event_queue.json`.
  2. **Verify Repair Durability**: Checks if fixes lasted 8 hours. If yes: **+1.0** bandit reward & **+5.0** machine skill. If no (duct-tape fix): **-5.0** bandit penalty & **-15.0** machine skill.
  3. **Update Graph**: Updates operator skill scores, skill tiers, and UCB format weights in `data/graph_state.json`.
  4. **Update Fault Trees**: Recalculates branch probabilities (Laplace-smoothed) in `data/procedural_fault_trees.json`.
  5. **Promote Shortcuts**: Moves a shortcut to the active library if 3 Experts have approved it.
  6. **Clear Queue**: Saves the processed events to the permanent log (`data/episodic_logs.json`) and empties the queue.

---

## 3. Agents Subsystem (`agents/`)

### 3.1 `agents/bandit_router.py` - Format Personalization Engine
* **Class**: `BanditRouter`
* **What it does**: Uses the UCB1 algorithm to pick the best format for each operator.
* **Key Methods**:
  * `select_format(operator_id, derived_tier, fatigue_index=0.0) -> Tuple[str, str]`:
    Checks the skill state. If the Fatigue Index is >= 0.80, it sets exploration (c) to 0.0 (uses the most proven format). Otherwise, it calculates UCB1 scores for all formats (Visual, Terse, Detailed) and returns the winner.
  * `get_format_prompt_directive(format_arm) -> str`:
    Returns the exact instructions given to the LLM on how to format the text.
  * `calculate_ucb_score(mean_reward, total_pulls, arm_pulls, c=1.2) -> float`:
    The math function that calculates the UCB score with an exploration bonus.

### 3.2 `agents/chat_agent.py` - The AI Brain
* **Class**: `ChatAgent`
* **What it does**: Talks to Google Gemini Flash Lite using LangChain to write safe, formatted instructions.
* **Key Methods**:
  * `generate_response(working_context_prompt) -> str`:
    Sends the fully built prompt to Gemini and forces it to only use the provided manuals (zero hallucination).
  * `stream_response(working_context_prompt) -> Generator`:
    Streams the text back word-by-word so the UI feels fast.

### 3.3 `agents/shadow_observer.py` - Fast Event Logger
* **Class**: `ShadowObserver`
* **What it does**: A very fast script that saves events in the background so the UI doesn't freeze.
* **Key Methods**:
  * `log_turn_feedback(session_id, operator_id, machine_id, format_used, cognitive_tier, outcome_status, duration_mins=None, suspected_shortcut=None) -> Dict`:
    Runs in **<5ms**. Saves the event to the queue file.
  * `enqueue_reward_escrow(...)`:
    Puts positive rewards on provisional hold (8-hour durability window) in `escrow_rewards.json`.
  * `check_and_enqueue_debrief(...)`:
    Notices if a fix was unusually fast and schedules a debrief question for the operator's next session.

---

## 4. Memory Subsystem (`memory/`)

### 4.1 `memory/semantic_graph.py` - Knowledge Graph
* **Class**: `SemanticKnowledgeGraph`
* **What it does**: Tracks operator skill per machine, completely separate from their format preferences.
* **Key Methods**:
  * `initialize_default_graph(hr_data)`:
    Creates nodes for operators, machines, states, and formats, and connects them.
  * `get_operator_machine_tier(operator_id, machine_id) -> Tuple[float, str]`:
    Looks up the operator's score (0 to 100) on a specific machine and returns their tier (Novice, Intermediate, Expert).
  * `get_state_bandit_stats(operator_id, derived_tier, format_arm) -> Dict`:
    Gets the reward history for a specific format in a specific state.
  * `apply_format_override_penalty(operator_id, derived_tier, rejected_format)`:
    Subtracts 10.0 points from a format if the operator manually rejected it.
  * `save_graph_state(file_path)` / `load_graph_state(file_path)`:
    Saves and loads the graph to/from a JSON file.

### 4.2 `memory/procedural_memory.py` - Fault Trees & Quarantine
* **Class**: `ProceduralMemory`
* **What it does**: Manages the step-by-step fix paths and the quarantine area for new shortcuts.
* **Key Methods**:
  * `calculate_branch_probability(success_count, failure_count, alpha=1.0, beta=1.0) -> float`:
    Calculates the true success probability of a fix path using Beta-Binomial math.
  * `get_ranked_diagnostic_paths(error_code, operator_tier=None) -> List[Dict]`:
    Returns all possible fixes for an alarm, sorted from best to worst. Hides advanced fixes from novices.
  * `record_branch_outcome(error_code, path_id, success=True, execution_time=None)`:
    Updates the success or failure count for a fix.
  * `add_quarantine_sop(sop_payload)`:
    Saves a new, unverified shortcut to `quarantine_sops.json`.
  * `validate_quarantine_sop(sop_id, operator_id, operator_tier) -> bool`:
    Adds an Expert's vote to a shortcut. Moves it to the active library if it reaches 3 votes.

### 4.3 `memory/debrief_store.py` - Micro-Debrief Loop
* **Class**: `DebriefStore`
* **What it does**: Manages the questions asked to operators when they fix something surprisingly fast.
* **Key Methods**:
  * `enqueue_debrief(...) -> str`:
    Creates a new debrief question.
  * `get_pending_debriefs_for_operator(operator_id) -> List[Dict]`:
    Finds any waiting questions for the current operator.
  * `process_debrief_response(debrief_id, operator_confirmed: bool) -> Dict`:
    If the operator says "Yes", it sends the shortcut to quarantine. If "No", it deletes the record.

### 4.4 `memory/episodic_store.py` - Event Queue & History
* **Class**: `EpisodicStore`
* **What it does**: Handles fast saving of events and looks up past failures.
* **Key Methods**:
  * `enqueue_shift_event(event_dict)`:
    Fast save (<5ms) to the event queue.
  * `log_turn(...)`:
    Saves the full chat interaction to the permanent log.
  * `get_historical_failures_for_fault(operator_id, fault_code) -> List[Dict]`:
    Finds out if the operator has failed to fix this exact alarm in the past.

### 4.5 `memory/working_memory.py` - Prompt Builder
* **Class**: `WorkingMemorySynthesizer`
* **What it does**: Gathers all the data (telemetry, safety, manuals) and builds the final prompt for the LLM.
* **Key Methods**:
  * `synthesize_prompt(...) -> str`:
    Combines the machine state, safety rules, fix paths, manual excerpts, past failures, and format rules into one clean text prompt.

### 4.6 `memory/search.py` - Hybrid Search Engine
* **Class**: `HybridRetriever`
* **What it does**: Searches the factory manuals using both meaning (ChromaDB vectors) and exact keywords (BM25). Merges the results using Reciprocal Rank Fusion (RRF).
* **Key Methods**:
  * `search(query, machine_filter=None, top_k=3) -> List[Dict]`:
    Runs both searches, combines the scores, ensures it only returns manuals for the correct machine, and returns the top results.

---

## 5. Mock Services Subsystem (`mock_services/`)

### 5.1 `mock_services/scada_service.py` - Machine Sensors
* **Class**: `MockSCADA`
* **What it does**: Simulates machine sensors (pressure, temperature) and alarms. Has a `verify_repair()` function to check if a fix worked.

### 5.2 `mock_services/ecm_service.py` - Environment Context
* **Class**: `MockECM`
* **What it does**: Calculates how many hours the operator has worked (Fatigue Index), checks if a supervisor is around, and simulates noise/temperature.

### 5.3 `mock_services/cmms_service.py` - Maintenance Tickets
* **Class**: `MockCMMS`
* **What it does**: Simulates the ticketing system. Creates work orders (like `TICK-2026-A83B`) when a problem is escalated.

### 5.4 `mock_services/hr_lms_service.py` - HR & Training
* **Class**: `MockHRLMS`
* **What it does**: Simulates the HR system. Stores operator names, shifts, safety certs, and starting skill levels.

---

## 6. Data & Indexing (`data/`)

### 6.1 `data/ingest.py` - Search Index Builder
* **File**: `data/ingest.py`
* **What it does**: A script you run manually. It reads the official SOPs, uses Gemini to turn them into vector embeddings, and saves them into the ChromaDB and BM25 databases.

### 6.2 JSON Files
* `data/factory_knowledge_base.json`: The official factory manuals and safety rules.
* `data/procedural_fault_trees.json`: The active fix paths and their success/failure counts.
* `data/quarantine_sops.json`: New shortcuts waiting for 3 Experts to approve them.
* `data/escrow_rewards.json`: Provisional rewards ledger waiting for the 8-hour durability verification.
* `data/pending_debriefs.json`: Questions waiting to be asked to operators.
* `data/episodic_event_queue.json`: The fast, temporary event buffer.
* `data/episodic_logs.json`: The permanent history log.
* `data/graph_state.json`: The saved state of operator skills and format preferences.
