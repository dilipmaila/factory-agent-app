# Code and Modules Technical Guide: Factory Operator AI Assistant

## Table of Contents

- [1. Document Overview](#1-document-overview)
  - [1.1 High-Level Module Architecture Diagram](#11-high-level-module-architecture-diagram)
- [2. Top-Level Applications](#2-top-level-applications)
  - [2.1 `app.py` - Shopfloor Streamlit Web Interface](#21-apppy---shopfloor-streamlit-web-interface)
  - [2.2 `sleep_cycle_evaluator.py` - Asynchronous Nightly Batch Evaluator](#22-sleep_cycle_evaluatorpy---asynchronous-nightly-batch-evaluator)
- [3. Agents Subsystem (`agents/`)](#3-agents-subsystem-agents)
  - [3.1 `agents/bandit_router.py` - Contextual Format Router (`ContextualBandit`)](#31-agentsbandit_routerpy---contextual-format-router-contextualbandit)
  - [3.2 `agents/chat_agent.py` - Manufacturing LLM Chat Agent (`ManufacturingChatAgent`)](#32-agentschat_agentpy---manufacturing-llm-chat-agent-manufacturingchatagent)
  - [3.3 `agents/shadow_observer.py` - Synchronous Event Logger & Escrow Sentinel (`ShadowObserver`)](#33-agentsshadow_observerpy---synchronous-event-logger--escrow-sentinel-shadowobserver)
- [4. Memory Subsystem (`memory/`)](#4-memory-subsystem-memory)
  - [4.1 `memory/semantic_graph.py` - Decoupled Cognitive Knowledge Graph (`OperatorKnowledgeGraph`)](#41-memorysemantic_graphpy---decoupled-cognitive-knowledge-graph-operatorknowledgegraph)
  - [4.2 `memory/procedural_memory.py` - Bayesian Fault Trees & Quarantine (`ProceduralMemory`)](#42-memoryprocedural_memorypy---bayesian-fault-trees--quarantine-proceduralmemory)
  - [4.3 `memory/debrief_store.py` - Micro-Debrief Verification Store (`DebriefManager`)](#43-memorydebrief_storepy---micro-debrief-verification-store-debriefmanager)
  - [4.4 `memory/episodic_store.py` - Fast Event Queue & Audit History (`EpisodicMemory`)](#44-memoryepisodic_storepy---fast-event-queue--audit-history-episodicmemory)
  - [4.5 `memory/working_memory.py` - Multi-Source Context Synthesizer (`build_prompt`)](#45-memoryworking_memorypy---multi-source-context-synthesizer-build_prompt)
  - [4.6 `memory/search.py` - Dense/Sparse Hybrid Retriever (`HybridRetriever`)](#46-memorysearchpy---densesparse-hybrid-retriever-hybridretriever)
- [5. Mock Services Subsystem (`mock_services/`)](#5-mock-services-subsystem-mock_services)
  - [5.1 `mock_services/scada_service.py` - SCADA Telemetry & Alarm Service (`MockSCADA`)](#51-mock_servicesscada_servicepy---scada-telemetry--alarm-service-mockscada)
  - [5.2 `mock_services/ecm_service.py` - Environmental Context Matrix Service (`ECMService`)](#52-mock_servicesecm_servicepy---environmental-context-matrix-service-ecmservice)
  - [5.3 `mock_services/cmms_service.py` - Maintenance Work Order Service (`MockCMMS`)](#53-mock_servicescmms_servicepy---maintenance-work-order-service-mockcmms)
  - [5.4 `mock_services/hr_lms_service.py` - HR & Operator LMS Service (`MockHRLMS`)](#54-mock_serviceshr_lms_servicepy---hr--operator-lms-service-mockhrlms)
- [6. Data & Indexing Subsystem (`data/`)](#6-data--indexing-subsystem-data)
  - [6.1 `data/ingest.py` - Vector & Keyword Store Ingestion Pipeline](#61-dataingestpy---vector--keyword-store-ingestion-pipeline)
  - [6.2 State & Storage Files](#62-state--storage-files)

---

## 1. Document Overview

This technical guide documents every source file, class, method signature, and data structure in the **Factory Operator AI Assistant** codebase.

For architectural design rationales and mathematical formulations, refer to [solution_design.md](solution_design.md).  
For offline, online, and operational evaluation metrics, refer to [evaluation_framework_design.md](evaluation_framework_design.md).  
For interactive demo test scenarios, refer to [demo_and_evaluation_guide.md](demo_and_evaluation_guide.md).  
For installation, environment variables, and execution steps, refer to [run_and_configuration_guide.md](run_and_configuration_guide.md).

### 1.1 High-Level Module Architecture Diagram

```text
   +-----------------------------------------------------------------------------------+
   |                                 PRESENTATION LAYER                                |
   |                            app.py (Streamlit Web HMI)                             |
   +-----------------------------------------------------------------------------------+
             │                                   │                               │
             ▼                                   ▼                               ▼
   +--------------------+              +--------------------+          +--------------------+
   |   AGENTS LAYER     |              |    MEMORY LAYER    |          |   SERVICES LAYER   |
   | - ContextualBandit | ──uses────>  | - OperatorKnowledge| <─────── | - MockSCADA        |
   | - Manufacturing    |              |   Graph            |          | - ECMService       |
   |   ChatAgent        |              | - ProceduralMemory |          | - MockCMMS         |
   | - ShadowObserver   |              | - WorkingMemory    |          | - MockHRLMS        |
   +--------------------+              |   (build_prompt)   |          +--------------------+
                                       | - EpisodicMemory   |
                                       | - DebriefManager   |
                                       | - HybridRetriever  |
                                       +--------------------+
                                                 │
                                                 ▼
   +-----------------------------------------------------------------------------------+
   |                             BATCH GOVERNANCE LAYER                                |
   |              sleep_cycle_evaluator.py (SleepCycleEvaluator Batch Script)          |
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

### 2.1 `app.py` - Shopfloor Streamlit Web Interface
* **File**: [`app.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/app.py)
* **Description**: The primary operator-facing touch interface built with Streamlit. It connects the live chat interface, real-time telemetry simulator, and diagnostic inspection panels into a single dashboard.
* **Key Responsibilities**:
  1. **Session & Resource Management**: Instantiates and caches singleton services via `get_shared_resources()` (`MockSCADA`, `MockCMMS`, `MockHRLMS`, `ECMService`, `OperatorKnowledgeGraph`, `ProceduralMemory`, `EpisodicMemory`, `DebriefManager`, `HybridRetriever`, `ContextualBandit`, `ManufacturingChatAgent`, `ShadowObserver`, `SleepCycleEvaluator`).
  2. **Environmental & Context Sidebar**: Allows selecting active operators, target machines, shift duration, supervisor presence, ambient noise, and simulated SCADA alarms.
  3. **Adaptive Chat Loop**: Coordinates context synthesis (`build_prompt`), contextual bandit format selection (`ContextualBandit.select_format`), grounded LLM generation (`ManufacturingChatAgent.generate_response`), and synchronous resolution capture via `ShadowObserver.evaluate_session`.
  4. **Human-in-the-Loop Controls**: Includes manual format overrides (-10.0 penalty), Micro-Debrief Yes/No verification dialogs, and escalation dispatch triggers.
  5. **Diagnostic Inspection Panels (Tabs)**:
     - **Knowledge Graph & Skill Inspector**: Visualizes decoupled machine autonomy scores, derived cognitive tiers, and state-bound format UCB score breakdowns.
     - **Dynamic Procedural Memory & Quarantine**: Displays Bayesian ranked fault trees, anti-patterns, and consensus validation widgets for senior operators.
     - **Shift Event Log & Escrow Ledger**: Shows pending feedback events, escrow records awaiting 8-hour durability verification, and recent session transcripts.
     - **ECM & SCADA Telemetry**: Real-time sensor monitors and alarm injection controls.

---

### 2.2 `sleep_cycle_evaluator.py` - Asynchronous Nightly Batch Evaluator
* **File**: [`sleep_cycle_evaluator.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/sleep_cycle_evaluator.py)
* **Class**: `SleepCycleEvaluator`
* **Description**: Simulates an overnight batch maintenance cron job (e.g., scheduled at 03:00 AM) that verifies repair durability, applies mathematical profile updates, and clears the shift event queues.
* **Key Attributes**:
  * `DURABILITY_THRESHOLD_HOURS: float = 8.0`: Duration of the durability window required to confirm permanent resolution and guard against "duct-tape" fixes.
* **Key Methods**:
  * `__init__(knowledge_graph=None, procedural_memory=None, episodic_memory=None, scada_service=None)`:
    Initializes evaluator with the graph, procedural store, episodic store, and SCADA service.
  * `evaluate_durability(machine_id: str, fault_code: str, resolved_time_str: str, current_time: Optional[datetime.datetime] = None, threshold_hours: float = 8.0) -> Tuple[str, Optional[Dict[str, Any]]]`:
    Checks SCADA historical alarm logs against the resolution timestamp. Returns:
    - `"RECURRENCE_DETECTED"` + alarm record: If a duplicate alarm occurred within 8 hours.
    - `"MATURED_DURABLE"` + `None`: If >= 8 hours have passed without recurrent alarms.
    - `"PENDING"` + `None`: If the 8-hour durability window is still in progress.
  * `run_sleep_cycle(current_time: Optional[datetime.datetime] = None, force_mature_escrow: bool = False) -> Dict[str, Any]`:
    Executes the batch pipeline:
    1. Ingests immediate escalation events (`ESCALATED_CMMS`): applies **-15.0** machine autonomy penalty and **-1.0** bandit reward.
    2. Evaluates escrow records:
       - **Duct-Tape Fix (Recurrence)**: Inverts provisional reward to **-5.0** bandit penalty, **-15.0** autonomy penalty, and increments fault path failure counts.
       - **Matured Durable Fix**: Releases **+1.0** bandit reward, **+5.0** autonomy gain, and increments fault path success counts.
    3. Mutates and persists `graph_state.json` and `procedural_fault_trees.json`.
    4. Archives processed events to `episodic_logs.json`, flushes `episodic_event_queue.json`, and updates `escrow_rewards.json`.
  * `main()`: CLI entry point supporting `--verbose` and `--force-mature` flags.

---

## 3. Agents Subsystem (`agents/`)

### 3.1 `agents/bandit_router.py` - Contextual Format Router (`ContextualBandit`)
* **File**: [`agents/bandit_router.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/agents/bandit_router.py)
* **Class**: `ContextualBandit`
* **Description**: Multi-Armed Bandit router implementing the Upper Confidence Bound (UCB1) algorithm. Decouples presentation format preferences across cognitive proficiency states (`Novice`, `Intermediate`, `Expert`) and handles Environmental Context Matrix (ECM) overrides.
* **Class Constants**:
  * `ARMS = ["Visual_StepByStep", "Terse_Technical", "Detailed_Text"]`
  * `ARM_INSTRUCTIONS`: Dictionary mapping format arms (and `SOS_SHUTDOWN`) to precise LLM formatting prompts.
* **Key Methods**:
  * `__init__(knowledge_graph: OperatorKnowledgeGraph, exploration_c: float = 1.2)`:
    Binds the bandit router to the operator knowledge graph.
  * `calculate_ucb_scores(operator_id: str, cognitive_tier: str, exploration_override_c: Optional[float] = None) -> Dict[str, Dict[str, Any]]`:
    Computes UCB metrics for each format arm in the given cognitive state using:
    $$\text{Score} = \bar{\mu}_{\text{arm}} + c \cdot \sqrt{\frac{\ln(N + 1)}{n_{\text{arm}}}}$$
    When `exploration_override_c <= 0.0` (e.g., during Fatigue Gate), exploration is set to 0.0 (100% exploitation).
  * `select_format(operator_id: str, machine_id: str, ecm_payload: Optional[Dict[str, Any]] = None, forced_format: Optional[str] = None, is_severity_1: bool = False, forced_epsilon_challenge: bool = False) -> Tuple[str, str, Dict[str, Any], str]`:
    Selects the winning format arm. Returns `(best_arm, arm_instruction, ucb_scores, derived_tier)`.
    - **Emergency Override (Severity-1)**: Forces `SOS_SHUTDOWN` directives.
    - **Fatigue Gate**: If `fatigue_index >= 0.80`, sets `c = 0.0` and exploits the highest empirical mean reward format.
    - **Forced Epsilon Challenge**: Selects the least-pulled arm to test latent preferences.
  * `update_reward(operator_id: str, cognitive_tier: str, format_used: str, reward_value: float) -> Dict[str, Any]`:
    Updates the weight and pull count of the format edge connected to the operator's cognitive state node.
  * `trigger_format_override(operator_id: str, machine_id: str, rejected_format: str, requested_format: str) -> Tuple[str, str, Dict[str, Any]]`:
    Applies a hard **-10.0** mathematical penalty to the rejected format and **+2.0** reward to the requested format.

---

### 3.2 `agents/chat_agent.py` - Manufacturing LLM Chat Agent (`ManufacturingChatAgent`)
* **File**: [`agents/chat_agent.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/agents/chat_agent.py)
* **Class**: `ManufacturingChatAgent`
* **Description**: LLM wrapper interfacing with Google Gemini Flash Lite via LangChain to generate grounded, safety-compliant troubleshooting instructions.
* **Key Methods**:
  * `__init__(model_name: Optional[str] = None, temperature: float = 0.2, api_key: Optional[str] = None)`:
    Loads API credentials and initializes the Gemini chat model (default: `gemini-3.5-flash-lite`, temperature `0.2`).
  * `_init_llm() -> None`:
    Instantiates `ChatGoogleGenerativeAI` with automated fallback cascading across candidate models (`gemini-3.5-flash-lite` $\rightarrow$ `gemini-3.1-flash-lite` $\rightarrow$ `gemini-2.5-flash-lite` $\rightarrow$ `gemini-2.5-flash`).
  * `_extract_text(content: Any) -> str` *(static)*:
    Safely unpacks LLM response objects across strings, message content lists, dictionaries, or multimodal chunks.
  * `generate_response(working_memory_text: str, user_query: Optional[str] = None, chat_history: Optional[List[Any]] = None) -> str`:
    Invokes the LLM using the structured working memory prompt and returns clean markdown.

---

### 3.3 `agents/shadow_observer.py` - Synchronous Event Logger & Escrow Sentinel (`ShadowObserver`)
* **File**: [`agents/shadow_observer.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/agents/shadow_observer.py)
* **Class**: `ShadowObserver`
* **Description**: Synchronous, low-latency event observer (<100ms) that monitors operator resolution actions during live shifts without blocking UI rendering.
* **Key Methods**:
  * `__init__(episodic_memory: EpisodicMemory, cmms_service: Optional[MockCMMS] = None, scada_service: Optional[MockSCADA] = None, debrief_manager: Optional[DebriefManager] = None)`:
    Binds memory stores and mock services.
  * `evaluate_session(operator_id: str, machine_id: str, format_used: str, escalated: bool, cognitive_tier: str = "Novice", error_code: Optional[str] = None, path_id: Optional[str] = None, execution_time_mins: Optional[float] = None, sop_avg_time_mins: float = 10.0, suspected_shortcut_title: Optional[str] = None, suspected_shortcut_payload: Optional[Dict[str, Any]] = None, issue_desc: str = "...", query: str = "", response: str = "", session_id: Optional[str] = None) -> Dict[str, Any]`:
    Synchronously executes:
    1. If **escalated**: Creates CMMS work order (`MockCMMS.create_escalation_ticket`) and tags status `ESCALATED_CMMS`.
    2. If **solved independently**: Verifies SCADA telemetry (`MockSCADA.verify_repair`), tags status `SUCCESS`, and deposits a provisional positive reward (+1.0) into `escrow_rewards.json`.
    3. **Micro-Debrief Detection**: If resolution time is $\le 50\%$ of SOP average, enqueues an unverified record into `pending_debriefs.json`.
    4. Appends the event to `episodic_event_queue.json` and updates the active turn in `episodic_logs.json`.
    5. Returns operational telemetry, IDs, and execution latency.

---

## 4. Memory Subsystem (`memory/`)

### 4.1 `memory/semantic_graph.py` - Decoupled Cognitive Knowledge Graph (`OperatorKnowledgeGraph`)
* **File**: [`memory/semantic_graph.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/memory/semantic_graph.py)
* **Class**: `OperatorKnowledgeGraph`
* **Description**: NetworkX-powered directed graph maintaining strict decoupling between **machine-specific domain competence** (autonomy score $0\dots100$) and **state-bound cognitive format preferences**. Serializes to `data/graph_state.json`.
* **Topology**:
  - `OPERATOR:{id}` $\xrightarrow{\text{OPERATES}}$ `MACHINE:{id}` (stores `autonomy_score`, `derived_tier`, `success_count`, `escalation_count`).
  - `OPERATOR:{id}` $\xrightarrow{\text{STATE_CONFIDENCE}}$ `STATE:{id}:{tier}` (links operator to cognitive tiers: Novice, Intermediate, Expert).
  - `STATE:{id}:{tier}` $\xrightarrow{\text{PREFERS}}$ `FORMAT:{arm}` (stores `weight`, `pull_count`, `success_count`, `escalation_count`).
* **Key Methods**:
  * `calculate_tier_from_score(score: float) -> str` *(static)*:
    Maps score to tier: $\ge 75.0 \implies \text{Expert}$, $40.0\dots74.9 \implies \text{Intermediate}$, $< 40.0 \implies \text{Novice}$.
  * `get_or_create_operator(operator_id: str, name: str = "", default_tier: str = "Novice") -> str`:
    Ensures complete node and edge topology exists for an operator.
  * `get_machine_competence(operator_id: str, machine_id: str) -> Dict[str, Any]`:
    Returns `autonomy_score`, `derived_tier`, `success_count`, and `escalation_count`.
  * `get_autonomy_score(operator_id: str, machine_id: str) -> float`
  * `get_machine_tier(operator_id: str, machine_id: str) -> str`
  * `get_operator_tier(operator_id: str, machine_id: Optional[str] = None) -> str`
  * `update_autonomy_score(operator_id: str, machine_id: str, delta: float) -> Tuple[float, str]`:
    Updates score (clamped between $0.0$ and $100.0$), recalculates `derived_tier`, updates success/escalation counters, and persists graph.
  * `get_state_format_weights(operator_id: str, cognitive_tier: str) -> Dict[str, Dict[str, Any]]`:
    Retrieves arm statistics for a specific cognitive state node.
  * `update_state_format_weight(operator_id: str, cognitive_tier: str, format_name: str, reward: float) -> Dict[str, Any]`:
    Increments `pull_count`, updates `weight`, and updates success/escalation counts on the `PREFERS` edge.
  * `get_machine_similarity(machine_a: str, machine_b: str) -> float`:
    Returns domain similarity score ($0.85$ for intra-discipline CNC/Molding, $0.15$ cross-discipline).
  * `infer_confidence_from_similar_machines(operator_id: str, target_machine: str) -> Tuple[float, str]`:
    Uses graph traversal to infer confidence on unfamiliar machines.
  * `check_domain_fencing(operator_id: str, machine_id: str, target_subsystem: str) -> Dict[str, Any]`:
    Enforces safety boundaries on high-risk subsystems (high voltage, PCBs, radiation, relief valves).
  * `to_summary_dict(operator_id: str, machine_id: str) -> Dict[str, Any]`:
    Builds data payload for the UI Cognitive Inspector.
  * `save_to_file(filepath: Optional[str] = None) -> None` / `load_from_file(filepath: Optional[str] = None) -> None`

---

### 4.2 `memory/procedural_memory.py` - Bayesian Fault Trees & Quarantine (`ProceduralMemory`)
* **File**: [`memory/procedural_memory.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/memory/procedural_memory.py)
* **Function**: `calculate_branch_probability(successes: int, failures: int, alpha: float = 1.0, beta: float = 1.0) -> float`
  - Computes Bayesian Beta-Binomial success probability with Laplace smoothing:
    $$P(\text{Success}) = \frac{\text{successes} + \alpha}{\text{successes} + \text{failures} + \alpha + \beta}$$
* **Class**: `ProceduralMemory`
* **Description**: Manages active dynamic probabilistic fault trees (`data/procedural_fault_trees.json`) and quarantined shortcut candidate SOPs (`data/quarantine_sops.json`).
* **Key Methods**:
  * `__init__(data_file: Optional[str] = None, quarantine_file: Optional[str] = None)`:
    Initializes storage paths and loads records.
  * `get_all_trees(operator_tier: str = "Expert") -> List[Dict[str, Any]]`:
    Returns all active fault trees enriched with Bayesian probabilities and filtered by operator tier clearance.
  * `get_fault_tree(error_code: str, machine: Optional[str] = None, operator_tier: str = "Expert") -> Optional[Dict[str, Any]]`:
    Retrieves and ranks diagnostic paths descending by probability score.
  * `search(query: str, machine: Optional[str] = None, operator_tier: str = "Novice") -> List[Dict[str, Any]]`:
    Searches active fault trees; strictly excludes quarantined procedures and filters out Expert-only paths for Novice/Intermediate operators.
  * `update_path_telemetry(error_code: str, path_id: str, success: bool) -> Optional[Dict[str, Any]]`:
    Increments path success/failure counts and recalculates `probability_score`.
  * `get_quarantined_trees() -> List[Dict[str, Any]]`:
    Returns all candidate shortcuts pending consensus.
  * `add_to_quarantine(error_code: str, machine: str, title: str, path_payload: Dict[str, Any], operator_id: Optional[str] = None) -> Dict[str, Any]`:
    Stores an unverified shortcut in `quarantine_sops.json`.
  * `validate_quarantine_sop(error_code: str, path_id: str, operator_id: str, operator_tier: str) -> Dict[str, Any]`:
    Records an Expert validation signature. If $\ge 3$ unique Expert operators validate the shortcut, automatically promotes it to the active library with `min_tier_required: 'Expert'`.
  * `format_procedural_context(fault_trees: List[Dict[str, Any]]) -> str`:
    Formats ranked diagnostic paths and unified anti-patterns ("What Not To Do") into structured text for prompt assembly.

---

### 4.3 `memory/debrief_store.py` - Micro-Debrief Verification Store (`DebriefManager`)
* **File**: [`memory/debrief_store.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/memory/debrief_store.py)
* **Class**: `DebriefManager`
* **Description**: Manages the micro-debrief verification lifecycle (`data/pending_debriefs.json`), replacing telemetry guesswork with deterministic human sign-off.
* **Key Methods**:
  * `__init__(debrief_file: Optional[str] = None)`
  * `enqueue_debrief(operator_id: str, machine_id: str, fault_code: str, suspected_shortcut_title: str, suspected_path_payload: Dict[str, Any], actual_time_mins: float = 2.0, sop_avg_time_mins: float = 10.0) -> Dict[str, Any]`:
    Creates a pending debrief inquiry with unique ID `DEBRIEF-XXXXXXXX`.
  * `get_pending_debriefs(operator_id: Optional[str] = None) -> List[Dict[str, Any]]`:
    Returns active `PENDING` debriefs.
  * `dismiss_debrief(debrief_id: str) -> None`:
    Marks debrief as `DISMISSED` without action.
  * `clear_all_pending(operator_id: Optional[str] = None) -> int`:
    Dismisses all pending inquiries for an operator.
  * `process_debrief_response(debrief_id: str, confirmed: bool, procedural_memory: ProceduralMemory) -> Dict[str, Any]`:
    - If **confirmed (Yes)**: Routes shortcut to `quarantine_sops.json` via `ProceduralMemory.add_to_quarantine`.
    - If **rejected (No)**: Marks debrief `DISCARDED` with zero procedural memory mutations.

---

### 4.4 `memory/episodic_store.py` - Fast Event Queue & Audit History (`EpisodicMemory`)
* **File**: [`memory/episodic_store.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/memory/episodic_store.py)
* **Class**: `EpisodicMemory`
* **Description**: Manages three event streams:
  1. `episodic_event_queue.json`: Fast synchronous shift event queue (<100ms).
  2. `escrow_rewards.json`: Provisional reward escrow ledger for the 8-hour durability window.
  3. `episodic_logs.json`: Long-term immutable audit log.
* **Class Constants**:
  * `VALID_STATUSES = ["SUCCESS", "ESCALATED_CMMS", "ABANDONED_TIMEOUT", "IN_PROGRESS"]`
* **Key Methods**:
  * `__init__(log_file=None, queue_file=None, escrow_file=None)`
  * `enqueue_feedback_event(operator_id: str, machine_id: str, format_used: str, outcome_status: str, cognitive_tier: Optional[str] = None, error_code: Optional[str] = None, path_id: Optional[str] = None, ticket_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]`:
    Appends an event payload to `episodic_event_queue.json`.
  * `get_pending_events() -> List[Dict[str, Any]]` / `clear_event_queue() -> None`
  * `enqueue_escrow_reward(operator_id: str, machine_id: str, fault_code: str, format_used: str, cognitive_tier: str, path_id: Optional[str] = None, timestamp: Optional[str] = None, provisional_reward: float = 1.0) -> Dict[str, Any]`:
    Places a provisional reward record into `escrow_rewards.json`.
  * `get_escrow_records() -> List[Dict[str, Any]]` / `clear_escrow_records() -> None`
  * `log_turn(operator_id: str, machine_id: str, query: str, response: str, format_used: str, resolution_status: str = "IN_PROGRESS", ticket_id: Optional[str] = None, error_code: Optional[str] = None, retrieved_sop_ids: Optional[List[str]] = None) -> Dict[str, Any]`:
    Appends interaction turn to `episodic_logs.json`.
  * `update_resolution(operator_id: str, resolution_status: str, ticket_id: Optional[str] = None) -> Optional[Dict[str, Any]]`:
    Updates the status of the operator's most recent turn.
  * `get_operator_fault_history(operator_id: str, error_code: str) -> List[Dict[str, Any]]`:
    Queries historical failure episodes (`ESCALATED_CMMS`, `ABANDONED_TIMEOUT`) for recurring fault patterns.
  * `archive_batch_events(events: List[Dict[str, Any]]) -> None`
  * `get_recent_history(operator_id: Optional[str] = None, machine_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]`

---

### 4.5 `memory/working_memory.py` - Multi-Source Context Synthesizer (`build_prompt`)
* **File**: [`memory/working_memory.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/memory/working_memory.py)
* **Function**: `build_prompt(...) -> str`
* **Description**: Assembles the master prompt for LLM generation with strict hierarchical structuring:
  1. **Emergency SOS Header**: Triggers deterministic halt and isolation if Severity-1 active.
  2. **Operator & Decoupled State Context**: Injects operator name, machine, derived tier, and autonomy score.
  3. **Mandatory Safety Protocols (Priority 1)**: Injects critical PPE, LOTO, and hazard warnings.
  4. **Environmental Context Matrix Directives (ECM)**: Supervisor Gate (offline directives) and Fatigue Gate instructions.
  5. **Historical Escalation Warning Protocol**: Triggers proactive Level 2 maintenance dispatch offers if prior failures are recorded.
  6. **Bandit Formatting Directives (Priority 2)**: Visual, Terse, or Detailed formatting rules.
  7. **Dynamic Procedural Memory**: Bayesian ranked primary and backup fix paths, plus anti-patterns.
  8. **Grounded SOPs & Manuals (Priority 3)**: Authoritative documentation retrieved via hybrid search.
* **Signature**:
  ```python
  def build_prompt(
      safety_warnings: Union[List[str], str],
      bandit_format_instruction: str,
      retrieved_sops: List[Union[Document, Dict[str, Any], str]],
      user_query: str,
      operator_context: Optional[Dict[str, Any]] = None,
      procedural_fault_trees: Optional[List[Dict[str, Any]]] = None,
      procedural_context_text: Optional[str] = None,
      escalation_history: Optional[List[Dict[str, Any]]] = None,
      ecm_payload: Optional[Dict[str, Any]] = None,
  ) -> str
  ```

---

### 4.6 `memory/search.py` - Dense/Sparse Hybrid Retriever (`HybridRetriever`)
* **File**: [`memory/search.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/memory/search.py)
* **Class**: `HybridRetriever`
* **Description**: Combines dense semantic search (ChromaDB + `gemini-embedding-2`) and sparse lexical search (BM25) fused with Reciprocal Rank Fusion (RRF, constant $k=60$).
* **Key Methods**:
  * `__init__(chroma_persist_dir: str, bm25_path: str)`:
    Loads embedding model, vector store, and BM25 retriever from disk.
  * `search(query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]`:
    Executes dense and sparse retrievals, applies metadata filtering (e.g., machine name, doc type), merges document rankings via RRF formula:
    $$\text{RRF Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{\text{rank}_m(d) + 1 + 60}$$
    and returns top $k$ `Document` objects annotated with `rrf_score`.

---

## 5. Mock Services Subsystem (`mock_services/`)

### 5.1 `mock_services/scada_service.py` - SCADA Telemetry & Alarm Service (`MockSCADA`)
* **File**: [`mock_services/scada_service.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/mock_services/scada_service.py)
* **Class**: `MockSCADA`
* **Description**: Simulates shopfloor telemetry, live machine alarms, sensor thresholds (air pressure, barrel temperature), repair verification, and historical alarm logs for durability evaluation.
* **Key Methods**:
  * `get_active_alarm(machine_id: str) -> str`: Returns active alarm summary string.
  * `get_alarm_details(machine_id: str) -> Optional[Dict[str, Any]]`: Returns full telemetry and metadata.
  * `set_active_alarm(machine_id: str, alarm_code: str, name: str, description: str, telemetry: Optional[Dict[str, Any]] = None, timestamp: Optional[str] = None) -> None`:
    Sets active alarm and logs trigger to history.
  * `log_alarm_trigger(machine_id: str, alarm_code: str, timestamp: Optional[str] = None) -> Dict[str, Any]`
  * `get_alarm_history(machine_id: Optional[str] = None, alarm_code: Optional[str] = None) -> List[Dict[str, Any]]`
  * `clear_alarm(machine_id: str) -> None`
  * `verify_repair(machine_id: str) -> bool`: Simulates telemetry validation post-troubleshooting.

---

### 5.2 `mock_services/ecm_service.py` - Environmental Context Matrix Service (`ECMService`)
* **File**: [`mock_services/ecm_service.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/mock_services/ecm_service.py)
* **Function**: `generate_ecm_payload(operator_id: str, machine_id: str, hours_since_clock_in: float = 2.5, total_shift_hours: float = 8.0, supervisor_available: bool = True, ambient_noise_db: float = 78.0, ambient_temp_c: float = 22.5) -> Dict[str, Any]`
  - Calculates `fatigue_index = hours_since_clock_in / total_shift_hours`.
  - Determines `fatigue_gate_active` ($\text{index} \ge 0.80$), `supervisor_gate_active` ($\neg \text{supervisor_available}$), and `shift_phase`.
* **Class**: `ECMService`
* **Description**: Stateful service tracking shift progression and environmental conditions per operator.
* **Key Methods**:
  * `get_ecm_payload(operator_id: str, machine_id: str, override_hours: Optional[float] = None, override_supervisor: Optional[bool] = None) -> Dict[str, Any]`
  * `update_operator_shift(operator_id: str, hours_since_clock_in: float, supervisor_available: bool) -> None`

---

### 5.3 `mock_services/cmms_service.py` - Maintenance Work Order Service (`MockCMMS`)
* **File**: [`mock_services/cmms_service.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/mock_services/cmms_service.py)
* **Class**: `MockCMMS`
* **Description**: Simulates the Computerized Maintenance Management System for dispatching maintenance tickets upon escalation.
* **Key Methods**:
  * `create_escalation_ticket(operator_id: str, machine_id: str, issue_desc: str, priority: str = "HIGH") -> str`:
    Generates and records ticket `TICK-2026-XXXXXX` assigned to `L2_ELECTROMECHANICAL_MAINTENANCE`.
  * `get_ticket_details(ticket_id: str) -> Dict[str, Any]`
  * `get_tickets_for_operator(operator_id: str) -> List[Dict[str, Any]]`
  * `get_all_tickets() -> List[Dict[str, Any]]`

---

### 5.4 `mock_services/hr_lms_service.py` - HR & Operator LMS Service (`MockHRLMS`)
* **File**: [`mock_services/hr_lms_service.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/mock_services/hr_lms_service.py)
* **Class**: `MockHRLMS`
* **Description**: Simulates the HR/LMS database providing baseline operator profiles, default tier classifications, and certifications to initialize cold-start states.
* **Key Methods**:
  * `get_operator_tier(operator_id: str) -> str`: Returns cold-start default tier (`Novice`, `Intermediate`, `Expert`).
  * `get_operator_profile(operator_id: str) -> Optional[Dict[str, Any]]`: Returns profile with role, shift, experience, and certifications.
  * `get_all_operators() -> List[Dict[str, Any]]`

---

## 6. Data & Indexing Subsystem (`data/`)

### 6.1 `data/ingest.py` - Vector & Keyword Store Ingestion Pipeline
* **File**: [`data/ingest.py`](file:///c:/Users/dilip/Documents/ASTAR_ASSIGNEMNT/factory_agent/factory-agent-app/data/ingest.py)
* **Function**: `ingest_data(json_file_path: str, chroma_persist_dir: str, bm25_path: str)`
* **Description**: Standalone batch ingestion script that:
  1. Parses `data/factory_knowledge_base.json` into LangChain `Document` objects with structured metadata (`doc_type`, `machine`, `error_code`, `hazard_level`, `required_role`).
  2. Embeds documents with `GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")`.
  3. Builds and persists the Chroma vector store in `data/chroma_db/`.
  4. Builds and serializes the BM25 keyword retriever in `data/bm25_retriever.pkl`.

---

### 6.2 State & Storage Files

| File Path | Description | Access Pattern |
|:---|:---|:---|
| `data/factory_knowledge_base.json` | Official factory reference manuals and SOP documents. | Read-only at ingestion |
| `data/procedural_fault_trees.json` | Active probabilistic fault trees with Bayesian branch weights. | Real-time Read / Nightly Write |
| `data/quarantine_sops.json` | Quarantined shortcut procedures undergoing consensus review. | Real-time Read / Real-time Write |
| `data/escrow_rewards.json` | Provisional positive rewards awaiting 8-hour durability verification. | Real-time Append / Nightly Evaluate |
| `data/pending_debriefs.json` | Pending Micro-Debrief inquiries for rapid resolution events. | Real-time Read / Real-time Write |
| `data/episodic_event_queue.json` | Synchronous shift event buffer (<100ms) for live session telemetry. | Real-time Append / Nightly Flush |
| `data/episodic_logs.json` | Long-term immutable interaction audit history. | Real-time Append / Nightly Archive |
| `data/graph_state.json` | Decoupled NetworkX knowledge graph serialization. | Real-time Read / Real-time & Nightly Write |
| `data/chroma_db/` | ChromaDB vector database embeddings. | Real-time RAG Search |
| `data/bm25_retriever.pkl` | Pickled BM25 sparse keyword retriever. | Real-time RAG Search |
