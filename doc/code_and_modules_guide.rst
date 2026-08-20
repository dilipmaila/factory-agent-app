========================================================================================
Code and Modules Technical Reference Guide: Factory Operator AI Assistant
========================================================================================

:Author: Manufacturing AI Systems Architecture Team
:Date: August 2026
:Format: reStructuredText (RST)

.. contents:: Table of Contents
   :depth: 3
   :local:
   :backlinks: entry

----------------------------------------------------------------------------------------

1. Document Overview & System Blueprint
=======================================

This document provides a comprehensive, module-by-module technical breakdown of the **Factory
Operator Adaptive AI Assistant** codebase. It outlines the architectural role, internal mechanics,
key classes, functions, and inter-module dependencies across every file in the repository.

For high-level conceptual architecture and mathematical formulations, refer to the companion
document: `solution_design.rst <solution_design.rst>`_.
For step-by-step runtime execution and JSON schema configurations, refer to: `run_and_configuration_guide.rst <run_and_configuration_guide.rst>`_.

1.1 High-Level Module Dependency Diagram
----------------------------------------

.. code-block:: text

   +-----------------------------------------------------------------------------------+
   |                                 PRESENTATION LAYER                                |
   |                            app.py (Streamlit Web HMI)                             |
   +-----------------------------------------------------------------------------------+
             │                                   │                               │
             ▼                                   ▼                               ▼
   +--------------------+              +--------------------+          +--------------------+
   |   AGENTS LAYER     |              |    MEMORY LAYER    |          |   SERVICES LAYER   |
   | - bandit_router.py | ──utilizes──> | - semantic_graph.py| <─────── | - scada_service.py |
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
   |                      sleep_cycle_evaluator.py (03:00 AM Cron)                     |
   +-----------------------------------------------------------------------------------+
                                                 │
                                                 ▼
   +-----------------------------------------------------------------------------------+
   |                              DATA & PERSISTENCE LAYER                             |
   |   data/*.json  |  data/chroma_db/  |  data/bm25_retriever.pkl  |  data/ingest.py      |
   +-----------------------------------------------------------------------------------+

----------------------------------------------------------------------------------------

2. Top-Level Applications & Orchestration
=========================================

2.1 `app.py` - Interactive Shopfloor HMI Application
----------------------------------------------------
* **File Path**: ``app.py``
* **Role**: Primary user interface and shopfloor HMI built using Streamlit. Simulates the operator's
  tablet or machine-mounted terminal.
* **Core Responsibilities**:

  1. **Session & Profile State Management**: Maintains operator identity, selected machine, active
     telemetry, dialogue history, and active cognitive state in ``st.session_state``.
  2. **Environmental Context Control**: Integrates ``MockECM`` to simulate shift progression (Hour 1 to 12),
     ambient noise/temperature, and supervisor availability.
  3. **Interactive Dialogue & Grounded Chat Loop**: Captures operator queries, coordinates working memory
     synthesis, calls ``ChatAgent`` with state-bound formatting directives, and displays responses.
  4. **Human Agency Format Overrides**: Provides instant UI override buttons (Visual, Terse, Detailed),
     allowing operators to bypass algorithmic routing and trigger real-time LLM re-synthesis with mathematical
     knowledge graph penalties applied to rejected formats.
  5. **Human-in-the-Loop Micro-Debrief Intercepts**: Renders pending debrief prompts on fast fixes
     and routes deterministic Y/N feedback to the quarantine store.
  6. **Closed-Loop Resolution Actions**: Renders *"Solved Independently"* and *"Escalate to Supervisor"*
     action triggers, routing low-latency events to ``ShadowObserver``.
  7. **Diagnostics & Multi-Tier Memory Visualizer**: Renders interactive tabs displaying live Knowledge Graph
     topologies, Bayesian fault-tree branch rankings, episodic audit logs, and escrow queues.

2.2 `sleep_cycle_evaluator.py` - Asynchronous Sleep Cycle Batch Evaluator
------------------------------------------------------------------------
* **File Path**: ``sleep_cycle_evaluator.py``
* **Role**: Standalone background batch evaluator simulating overnight (03:00 AM) cron execution or
  end-of-shift maintenance.
* **Core Responsibilities**:
  1. **Shift Event Ingestion**: Reads and aggregates all raw operational events from ``data/episodic_event_queue.json``.
  2. **Escrow Durability Auditing**: Evaluates provisional rewards in ``data/escrow_rewards.json`` against
     SCADA recurrence logs over the 8-hour Durability Window:
     * *Durable Fix*: Releases **$+1.0$** bandit reward and **$+5.0$** machine autonomy points.
     * *Duct-Tape Workaround*: Inverts reward into a **$-5.0$** bandit penalty and **$-15.0$** autonomy penalty.
  3. **Knowledge Graph Mutation**: Applies aggregated mathematical updates to machine autonomy scores,
     recomputes operator derived tiers, and updates state-bound UCB format weights in ``data/graph_state.json``.
  4. **Bayesian Procedural Tree Updates**: Updates branch success/failure counts and recomputes Laplace-smoothed
     probabilities in ``data/procedural_fault_trees.json``.
  5. **Quarantine Consensus Auto-Promotion**: Inspects ``data/quarantine_sops.json``; promotes procedures
     validated by 3 distinct Expert operators to the active library with ``min_tier_required: 'Expert'``.
  6. **Atomic Queue Flushing**: Archives processed events into ``data/episodic_logs.json`` and flushes the
     event queue atomically.

----------------------------------------------------------------------------------------

3. Agents Subsystem (`agents/`)
===============================

3.1 `agents/bandit_router.py` - Contextual Bandit Personalization Engine
------------------------------------------------------------------------
* **Class**: ``BanditRouter``
* **Role**: Implements the state-bound Upper Confidence Bound (UCB1) multi-armed bandit algorithm for
  presentation format selection.
* **Key Methods**:
  * ``select_format(operator_id, derived_tier, fatigue_index=0.0) -> Tuple[str, str]``:
    Identifies the cognitive state ``(operator_id, derived_tier)``, checks the **ECM Fatigue Gate**
    (if $\text{fatigue\_index} \ge 0.80$, sets exploration parameter $c = 0.0$), computes UCB1 scores
    across available arms (``Visual_StepByStep``, ``Terse_Technical``, ``Detailed_Text``), and returns the
    winning format arm along with its structural prompt directive.
  * ``get_format_prompt_directive(format_arm) -> str``:
    Returns the strict formatting instructions injected into the LLM master prompt.
  * ``calculate_ucb_score(mean_reward, total_pulls, arm_pulls, c=1.2) -> float``:
    Computes mathematical UCB score with exploration bonus.

3.2 `agents/chat_agent.py` - Grounded LLM Reasoning Agent
---------------------------------------------------------
* **Class**: ``ChatAgent``
* **Role**: Interfaces with Google Gemini Flash Lite via LangChain to generate grounded, safety-compliant,
  and formatted troubleshooting instructions.
* **Key Methods**:
  * ``generate_response(working_context_prompt) -> str``:
    Submits the compiled working memory context to Gemini and enforces zero-hallucination constraints.
  * ``stream_response(working_context_prompt) -> Generator``:
    Provides token streaming for real-time UI rendering in Streamlit.

3.3 `agents/shadow_observer.py` - Low-Latency Event Logger & Escrow Enqueuer
----------------------------------------------------------------------------
* **Class**: ``ShadowObserver``
* **Role**: Sub-100ms background evaluator monitoring operational outcomes and buffering shift events.
* **Key Methods**:
  * ``log_turn_feedback(session_id, operator_id, machine_id, format_used, cognitive_tier, outcome_status, duration_mins=None, suspected_shortcut=None) -> Dict``:
    Executes in **<5ms**. Appends the event to ``episodic_event_queue.json`` with strict status tagging.
  * ``enqueue_reward_escrow(session_id, operator_id, machine_id, format_used, cognitive_tier, fault_code)``:
    Places provisional positive rewards into ``escrow_rewards.json`` with an 8-hour durability timestamp.
  * ``check_and_enqueue_debrief(operator_id, machine_id, fault_code, actual_duration_mins, expected_duration_mins, suspected_shortcut)``:
    Flags abnormal fix speeds and enqueues interactive debriefs into ``pending_debriefs.json``.

----------------------------------------------------------------------------------------

4. Memory Subsystem (`memory/`)
===============================

4.1 `memory/semantic_graph.py` - Decoupled Knowledge Graph
----------------------------------------------------------
* **Class**: ``SemanticKnowledgeGraph``
* **Role**: Manages the directed NetworkX graph model decoupling domain competence from cognitive preferences.
* **Key Methods**:
  * ``initialize_default_graph(hr_data)``:
    Initializes graph nodes (``OPERATOR``, ``MACHINE``, ``STATE``, ``FORMAT``) and establishes decoupled
    ``OPERATES``, ``STATE_CONFIDENCE``, and ``PREFERS`` edges.
  * ``get_operator_machine_tier(operator_id, machine_id) -> Tuple[float, str]``:
    Retrieves machine-specific autonomy score (0.0 to 100.0) and computes derived tier (``Novice``,
    ``Intermediate``, ``Expert``).
  * ``get_state_bandit_stats(operator_id, derived_tier, format_arm) -> Dict``:
    Retrieves state-bound pull counts, cumulative reward weights, and success/escalation counts.
  * ``apply_format_override_penalty(operator_id, derived_tier, rejected_format)``:
    Applies $-10.0$ penalty weight to rejected format arm in active cognitive state.
  * ``save_graph_state(file_path)`` / ``load_graph_state(file_path)``:
    Serializes and deserializes graph state to/from JSON.

4.2 `memory/procedural_memory.py` - Dynamic Bayesian Fault Trees & Quarantine
-----------------------------------------------------------------------------
* **Class**: ``ProceduralMemory``
* **Role**: Manages dynamic probabilistic diagnostic trees and the sandboxed quarantine database.
* **Key Functions & Methods**:
  * ``calculate_branch_probability(success_count, failure_count, alpha=1.0, beta=1.0) -> float``:
    Computes Laplace-smoothed Beta-Binomial success probability.
  * ``get_ranked_diagnostic_paths(error_code, operator_tier=None) -> List[Dict]``:
    Retrieves and ranks diagnostic branches descending by probability score, filtering out branches
    requiring higher clearance than the operator's current tier.
  * ``record_branch_outcome(error_code, path_id, success=True, execution_time=None)``:
    Updates live branch telemetry counts.
  * ``add_quarantine_sop(sop_payload)``:
    Stores unvetted shortcut in ``quarantine_sops.json``.
  * ``validate_quarantine_sop(sop_id, operator_id, operator_tier) -> bool``:
    Records Senior/Expert validation; auto-promotes to active fault trees upon reaching 3 Expert votes.

4.3 `memory/debrief_store.py` - Micro-Debrief Loop Manager
----------------------------------------------------------
* **Class**: ``DebriefStore``
* **Role**: Manages the pending micro-debrief queue and handles operator Y/N validation responses.
* **Key Methods**:
  * ``enqueue_debrief(operator_id, machine_id, fault_code, actual_time, expected_time, suspected_shortcut) -> str``:
    Creates a new pending debrief record with unique ID.
  * ``get_pending_debriefs_for_operator(operator_id) -> List[Dict]``:
    Retrieves uncompleted debrief prompts for the active operator.
  * ``process_debrief_response(debrief_id, operator_confirmed: bool) -> Dict``:
    If confirmed (Yes), routes shortcut to quarantine store; if rejected (No), safely discards record.

4.4 `memory/episodic_store.py` - Event Queue & Historical Failure Logger
------------------------------------------------------------------------
* **Class**: ``EpisodicStore``
* **Role**: Handles low-latency event buffering, permanent turn logging, and historical failure retrieval.
* **Key Methods**:
  * ``enqueue_shift_event(event_dict)``:
    Fast append (<5ms) to ``episodic_event_queue.json``.
  * ``log_turn(session_id, operator_id, machine_id, query, response, format_used, status, cmms_ticket_id)``:
    Appends full interaction turns to ``episodic_logs.json`` with strict status enums.
  * ``get_historical_failures_for_fault(operator_id, fault_code) -> List[Dict]``:
    Queries past escalation records to inject failure warnings into working memory.

4.5 `memory/working_memory.py` - Dynamic Prompt Assembler
---------------------------------------------------------
* **Class**: ``WorkingMemorySynthesizer``
* **Role**: Compiles multi-source contextual information into a structured, grounded prompt.
* **Key Methods**:
  * ``synthesize_prompt(operator_id, machine_id, query, scada_telemetry, ecm_context, retrieved_sops, ranked_fault_branches, bandit_directive, failure_warnings=None) -> str``:
    Assembles the 7-section grounded prompt incorporating system identity, telemetry, safety holds,
    procedural fault branches, grounding excerpts, failure warnings, and formatting constraints.

4.6 `memory/search.py` - Hybrid Dense + Sparse Retriever (RRF)
---------------------------------------------------------------
* **Class**: ``HybridRetriever``
* **Role**: Executes Reciprocal Rank Fusion over ChromaDB dense vector embeddings and BM25 sparse keyword indices.
* **Key Methods**:
  * ``search(query, machine_filter=None, top_k=3) -> List[Dict]``:
    Executes parallel dense and sparse queries, computes RRF scores with $k_{\text{rrf}}=60$, applies
    machine metadata filters, and returns top-ranked authoritative SOP excerpts.

----------------------------------------------------------------------------------------

5. Mock Services Subsystem (`mock_services/`)
=============================================

5.1 `mock_services/scada_service.py` - Machine Telemetry & Alarms
-----------------------------------------------------------------
* **Class**: ``MockSCADA``
* **Role**: Emulates industrial PLC/SCADA systems: generates live machine telemetry (PSI, RPM, temperatures °C,
  hydraulic bar), manages active alarm states (e.g., `Alarm 102`, `E-201`), and validates repairs via ``verify_repair()``.

5.2 `mock_services/ecm_service.py` - Environmental Context Matrix
-----------------------------------------------------------------
* **Class**: ``MockECM``
* **Role**: Emulates physical shopfloor environment: calculates shift elapsed hours, computes the Fatigue Index
  ($\text{hours} / \text{total}$), tracks supervisor on-site/off-site status, and streams ambient noise/temperature.

5.3 `mock_services/cmms_service.py` - Maintenance Work Orders
-------------------------------------------------------------
* **Class**: ``MockCMMS``
* **Role**: Emulates enterprise maintenance ticketing: dispatches formal work orders (e.g., `TICK-2026-A83B`),
  assigns maintenance tiers (Level 1, Level 2), and manages work-order lifecycle states.

5.4 `mock_services/hr_lms_service.py` - Operator Roster & Cold-Start
--------------------------------------------------------------------
* **Class**: ``MockHRLMS``
* **Role**: Emulates HR and Learning Management Systems: stores operator records, shifts, tenure, safety
  certifications, and baseline qualification tiers for cold-start seeding.

----------------------------------------------------------------------------------------

6. Data & Ingestion Subsystem (`data/`)
=======================================

6.1 `data/ingest.py` - Knowledge Base Ingestion Pipeline
--------------------------------------------------------
* **File Path**: ``data/ingest.py``
* **Role**: Offline build script that reads ``data/factory_knowledge_base.json``, computes dense vector
  embeddings via Google Gemini, populates the persistent ChromaDB collection in ``data/chroma_db/``, and
  serializes the BM25 keyword index into ``data/bm25_retriever.pkl``.

6.2 JSON Storage Files Reference
--------------------------------
* ``data/factory_knowledge_base.json``: Curated authoritative factory SOPs and hazard matrices.
* ``data/procedural_fault_trees.json``: Dynamic Bayesian diagnostic trees and branch telemetry.
* ``data/quarantine_sops.json``: Sandboxed unvetted shortcuts pending 3-Expert consensus.
* ``data/escrow_rewards.json``: Provisional rewards held during the 8-hour Durability Window.
* ``data/pending_debriefs.json``: Enqueued micro-debrief prompts for fast-fix validations.
* ``data/episodic_event_queue.json``: Synchronous shift event buffer (<100ms).
* ``data/episodic_logs.json``: Permanent turn interaction audit ledger.
* ``data/graph_state.json``: Serialized NetworkX decoupled knowledge graph state.

----------------------------------------------------------------------------------------

7. Verification & Automated Test Suites
=======================================

The codebase includes three automated verification suites:

1. **`verify_refactor.py`**:
   Validates Section A (Procedural Memory & Bayesian Fault Trees), Section B (State-Bound Knowledge Graph
   Decoupling), and Section C (Fast Shift Event Queue & Batch Sleep Cycle Evaluator).
2. **`verify_section2.py`**:
   Validates Section 2.A (Durability Window & Escrow Recurrence Penalties), Section 2.B (Quarantine DB &
   3-Expert Consensus), Section 2.C (Status Tagging & Historical Failure Warnings), and Section 2.D
   (Format Overrides & Mathematical Graph Penalties).
3. **`verify_section3.py`**:
   Validates Section 3.A (Environmental Context Matrix & Fatigue Gating) and Section 3.B (Micro-Debrief Loop
   & Deterministic Routing).

To execute all test suites, run:

.. code-block:: bash

   uv run python verify_refactor.py
   uv run python verify_section2.py
   uv run python verify_section3.py
