========================================================================================
Adaptive Learning Mechanism for Manufacturing Operators: Architectural Solution Design
========================================================================================

:Author: Manufacturing AI Systems Architecture Team
:Date: August 2026
:Format: reStructuredText (RST)

.. contents:: Table of Contents
   :depth: 3
   :local:
   :backlinks: entry

.. note::
   **Companion Documentation**:
   
   * Detailed Module & Code Guide: `code_and_modules_guide.rst <code_and_modules_guide.rst>`_
   * Run, Setup & Configuration Guide: `run_and_configuration_guide.rst <run_and_configuration_guide.rst>`_

----------------------------------------------------------------------------------------

1. Executive Summary & Problem Motivation
==========================================

1.1 The Shopfloor Challenge
---------------------------
Modern manufacturing environments (such as precision CNC machining cells and high-tonnage
injection molding facilities) operate under stringent safety constraints, high equipment
costs, and tight production schedules. When machine alarms or anomalies occur (e.g., Haas CNC
servo failures or Engel barrel overheating), the shopfloor operator is the first line of defense.

However, shopfloor operators possess widely divergent skill profiles, experience levels,
cognitive styles, and learning trajectories:

* **Novice Operators** require structured, step-by-step visual guidance, explicit hazard
  warnings, and low autonomy thresholds to prevent safety incidents and equipment damage.
* **Experienced Machinists & Technicians** require terse, high-density technical parameters
  (e.g., hydraulic setpoints, M/G-codes, threshold tolerances) without conversational filler.
* **Troubleshooting Habits Differ**: Some operators excel at mechanical alignment but struggle
  with electrical diagnostics; some escalate immediately, while others attempt independent
  triage.
* **The "Paradox of Expertise"**: A senior technician who is an expert on a Haas CNC milling
  center may be a complete novice when assigned to an Engel injection molding press. Expertise
  is machine-specific, not global.
* **Shift Fatigue & Physical Realities**: Cognitive sharpness declines across long 12-hour shifts,
  and supervisor availability fluctuates between peak day shifts and unattended night shifts.

1.2 The Core Problem with Static AI Assistants
----------------------------------------------
Traditional conversational assistants or static retrieval-augmented generation (RAG) systems fail
in industrial settings because:

1. **One-Size-Fits-All Failure**: They treat every operator identically, either overwhelming a novice
   with dense technical jargon or frustrating an expert with remedial step-by-step instructions.
2. **Static Knowledge Stagnation**: Static manuals cannot learn or incorporate crowdsourced shopfloor
   heuristics, diagnostic shortcuts, or probabilistic failure frequencies discovered over time.
3. **Synchronous Profile Drift & UI Latency**: Mutating complex knowledge graphs synchronously on
   every live query introduces unacceptable UI latency and erratic intra-shift behavior oscillation.
4. **The "Duct-Tape" Trap**: Rewarding the AI immediately when an alarm clears encourages unstable
   temporary workarounds (e.g., zip-tying a sensor) that fail again hours later.
5. **Lack of Grounded Feedback**: Static assistants operate in an open loop without validating SCADA
   telemetry or coordinating with enterprise Computerized Maintenance Management Systems (CMMS).

1.3 Solution Mission Statement
------------------------------
This repository implements a production-grade **Adaptive Cognitive AI Assistant** that:

1. **Decouples Machine Competence from Cognitive Preferences**: Separates machine-specific autonomy
   scores from cognitive presentation preferences, eliminating the paradox of expertise.
2. **Maintains a Dynamic Procedural Skill Library**: Models machine troubleshooting as Bayesian
   diagnostic fault trees with empirical probability updates based on real resolution outcomes.
3. **Optimizes Personalization via Contextual Bandits**: Formulates format personalization as an
   exploration-exploitation problem using the Upper Confidence Bound (UCB1) algorithm with environmental
   fatigue gating.
4. **Enforces Dual-Loop Architecture**: Operates a sub-100ms synchronous interaction loop for active
   shifts and an asynchronous overnight "Sleep Cycle" evaluator for batch learning and graph mutations.
5. **Implements Industrial Safety & FMEA Guardrails**: Incorporates provisional reward escrow with
   an 8-hour durability window, 3-Expert quarantine consensus for new procedures, historical failure
   warnings, and human-in-the-loop micro-debriefing.

1.4 Core Architectural Assumptions
----------------------------------
To ground this solution in physical reality, the architecture relies on the following prerequisites:
1. **Unique Operator Identity:** Operators use individual logins (RFID/SSO); shared "Workstation" logins invalidate cognitive profiling.
2. **IT/OT Convergence:** The factory SCADA network can securely transmit real-time telemetry to the AI's IT infrastructure.
3. **Read-Only Sandboxing:** The AI is strictly advisory and has zero write-access to execute PLC commands, enforcing human-in-the-loop physical actuation.
4. **Outcome as a Proxy for Preference:** A durable, fast machine recovery is the objective ground-truth reward signal for format preference optimization.

----------------------------------------------------------------------------------------

2. High-Level Solution Architecture & Conceptual Flow
=====================================================

The system operates across two interlinked operational loops:

1. **The Real-Time Operational Loop (Synchronous, Sub-100ms)**:
   Handles operator queries, gathers environmental context, selects the optimal presentation style
   via state-bound contextual bandits, synthesizes grounded guidance with safety directives, records
   low-latency event logs, and supports instant human format overrides.
2. **The Asynchronous Learning & Governance Loop (Sleep Cycle Evaluator)**:
   Runs during shift transitions or overnight maintenance (e.g., 03:00 AM cron). It evaluates reward
   escrow durability against SCADA recurrence history, executes knowledge graph state mutations,
   updates Bayesian fault tree branch probabilities, and promotes validated quarantine procedures.

2.1 End-to-End System Flowchart
-------------------------------

.. code-block:: text

   =======================================================================================
                                 REAL-TIME OPERATIONAL LOOP (<100ms)
   =======================================================================================

   +-----------------------------------------------------------------------------------+
   |                                 SHOPFLOOR OPERATOR                                |
   |               (Selects Operator Profile, Machine, Enters Query on HMI/Tablet)      |
   +-----------------------------------------------------------------------------------+
                                            |
                                            | 1. Query / Alarm Trigger (e.g., "Alarm 102")
                                            v
   +-----------------------------------------------------------------------------------+
   |                    ENVIRONMENTAL CONTEXT MATRIX (ECM SERVICE)                     |
   |  - Shift Time & Fatigue Index (Hours / Total Shift)                               |
   |  - Supervisor On-Site / Off-Site Availability Status                              |
   |  - Shopfloor Noise (dB), Ambient Temp (°C), Active SCADA Sensor Stream            |
   +-----------------------------------------------------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                                                     |
         v                                                                     v
   +---------------------------------------+                 +---------------------------------+
   |      HYBRID RETRIEVAL & FAULT TREES   |                 |    STATE-BOUND BANDIT ROUTER    |
   | - Dense Semantic Search (ChromaDB)    |                 | - Operator Machine Derived Tier |
   | - Sparse Keyword Search (BM25 + RRF)  |                 | - Cognitive State (Op, Tier)    |
   | - Dynamic Bayesian Fault Tree Branch  |                 | - UCB1 Policy (Visual / Terse / |
   |   Ranking (Success Probability Score) |                 |   Detailed)                     |
   | - Quarantine Store Filter (Isolated)  |                 | - Fatigue Gate (Exploit if >=0.8)|
   +---------------------------------------+                 +---------------------------------+
         |                                                                     |
         | Ranked SOPs & Diagnostic Branches                                   | Winning Format Directive
         +----------------------------------+----------------------------------+
                                            |
                                            v
   +-----------------------------------------------------------------------------------+
   |                             WORKING MEMORY SYNTHESIZER                            |
   |  - Injects Mandatory Safety Directives (LOTO, High-Voltage, PPE Protocols)        |
   |  - Injects Live SCADA Telemetry & Alarm Parameter Status                          |
   |  - Injects Environmental Context & Supervisor Offline Overrides                   |
   |  - Injects Historical Failure Warnings (if operator previously escalated fault)   |
   |  - Injects Primary Recommended Fix & Alternative Diagnostic Branches              |
   |  - Enforces Contextual Bandit Format Structure Directives                         |
   +-----------------------------------------------------------------------------------+
                                            |
                                            | Grounded Working Context Prompt
                                            v
   +-----------------------------------------------------------------------------------+
   |                        LLM REASONING AGENT (Google Gemini)                        |
   |         Synthesizes safety-compliant, formatted, grounded troubleshooting text    |
   +-----------------------------------------------------------------------------------+
                                            |
                                            | Formatted Response Delivered to Operator
                                            v
   +-----------------------------------------------------------------------------------+
   |                            OPERATOR INTERACTION & ACTIONS                         |
   |                                                                                   |
   |  [Action 1: Solved Independently]   [Action 2: Escalate CMMS]   [Action 3: Format Override]
   +-----------------------------------------------------------------------------------+
                                            |
                                            v
   +-----------------------------------------------------------------------------------+
   |                      SHADOW OBSERVER LOW-LATENCY EVENT LOGGER                     |
   |  - Emits lightweight event payload to data/episodic_event_queue.json in <5ms      |
   |  - Holds provisional rewards in data/escrow_rewards.json (8-hr Durability Window) |
   |  - If resolution abnormally fast, enqueues Micro-Debrief for next session         |
   |  - Dispatches CMMS Ticket if escalated; re-synthesizes if format overridden       |
   +-----------------------------------------------------------------------------------+

   =======================================================================================
                           ASYNCHRONOUS LEARNING LOOP (SLEEP CYCLE)
   =======================================================================================

   +-----------------------------------------------------------------------------------+
   |                       SLEEP CYCLE BATCH EVALUATOR (03:00 AM)                      |
   |                             (sleep_cycle_evaluator.py)                            |
   +-----------------------------------------------------------------------------------+
        |                          |                           |                      |
        | 1. Escrow Validation     | 2. Graph State Mutations  | 3. Bayesian Trees    | 4. Quarantine
        v                          v                           v                      v
   +--------------------+     +--------------------+     +--------------------+  +--------------------+
   | ESCROW EVALUATION  |     | KNOWLEDGE GRAPH    |     | PROCEDURAL MEMORY  |  | CONSENSUS ENGINE   |
   | - Check SCADA logs |     | - Machine Autonomy |     | - Update branch    |  | - Check validations|
   |   for recurrence   |     |   (+5 sol, -15 esc)|     |   success/failure  |  | - 3-Expert votes   |
   | - Durable (>8h):   |     | - Recompute Tiers  |     |   counts & time    |  |   promotes to main |
   |   Release +1.0/+5.0|     | - State Bandit UCB |     | - Recalculate Beta |  |   Active Library   |
   | - Duct-Tape (<8h): |     |   weights (+1/-1)  |     |   conjugate scores |  |   with Expert tag  |
   |   Penalty -5.0/-15 |     | - Atomic Save Disk |     | - Atomic Save Disk |  | - Atomic Save Disk |
   +--------------------+     +--------------------+     +--------------------+  +--------------------+

----------------------------------------------------------------------------------------

3. Core Subsystems & Technical Architecture
===========================================

3.1 Subsystem 1: Multi-Tier Cognitive Memory Architecture
----------------------------------------------------------
Human cognitive processing relies on distinct memory structures: temporary sensory/working buffers,
episodic narratives, procedural routines, and long-term semantic relationships. The assistant
operationalizes this through five specialized memory tiers:

.. list-table:: Multi-Tier Cognitive Memory Architecture
   :widths: 18 22 35 25
   :header-rows: 1

   * - Memory Tier
     - Underlying Technology
     - Functional Role & Contents
     - Lifecycle & Update Cadence
   * - **Working Memory**
     - Dynamic In-Memory Assembler (`working_memory.py`)
     - Short-term context assembly combining active telemetry, ECM fatigue/supervisor state, historical failure warnings, retrieved SOPs, dynamic fault-tree branches, and bandit formatting directives.
     - Ephemeral; generated per query turn.
   * - **Decoupled Semantic Knowledge Graph**
     - Directed NetworkX Graph (`semantic_graph.py` -> `graph_state.json`)
     - Long-term cognitive representation decoupling machine-specific operator autonomy (`OPERATES` edges) from state-bound format preferences (`STATE_CONFIDENCE` & `PREFERS` edges).
     - Persisted JSON; updated asynchronously during batch Sleep Cycle evaluation.
   * - **Dynamic Procedural Memory (Fault Trees)**
     - Probabilistic JSON Store (`procedural_memory.py` -> `procedural_fault_trees.json`)
     - Dynamic diagnostic fault trees containing branching troubleshooting paths per alarm code, with live telemetry tracking success counts, failure counts, and execution times.
     - Persisted JSON; branch probabilities updated via Bayesian updates during Sleep Cycle.
   * - **Quarantine SOP Store**
     - Sandboxed JSON Store (`quarantine_sops.json`)
     - Isolated holding repository for crowdsourced operator shortcuts and debrief discoveries; strictly excluded from standard RAG retrieval until 3-Expert consensus is achieved.
     - Persisted JSON; evaluated during Sleep Cycle.
   * - **Episodic Store & Event Queue**
     - Append-Only JSON Logs (`episodic_store.py` -> `episodic_event_queue.json`, `episodic_logs.json`)
     - Shift event logging for low-latency writes (<5ms) and permanent audit ledger tracking queries, responses, format arms, CMMS ticket IDs, and resolution status enums.
     - Queue written synchronously; main ledger archived during Sleep Cycle.
   * - **Authoritative Grounding Store**
     - ChromaDB (Dense) + BM25 (Sparse) (`search.py`)
     - Fact-grounding repository containing official factory SOPs, machine operating manuals, hazard levels, and error codes.
     - Read-only at runtime; updated during offline engineering ingestion.

3.1.1 The Decoupled Semantic Knowledge Graph Topology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To prevent the "Paradox of Expertise" (where an expert on Machine A is incorrectly treated as an
expert on unfamiliar Machine B), the knowledge graph decouples domain competence from cognitive format
preferences:

.. code-block:: text

   [OPERATOR: Sarah] ──── (OPERATES: Haas VF-2, Autonomy=95.0, Tier=Expert) ───> [MACHINE: Haas VF-2]
          │
          ├────────────── (OPERATES: Engel 330, Autonomy=15.0, Tier=Novice) ───> [MACHINE: Engel 330]
          │
          ├────────────── (STATE_CONFIDENCE) ───> [STATE: OP-002:Expert]
          │                                              │
          │                                              ├── (PREFERS: weight=4.8) ──> [FORMAT: Terse_Technical]
          │                                              └── (PREFERS: weight=0.2) ──> [FORMAT: Visual_StepByStep]
          │
          └────────────── (STATE_CONFIDENCE) ───> [STATE: OP-002:Novice]
                                                         │
                                                         ├── (PREFERS: weight=3.9) ──> [FORMAT: Visual_StepByStep]
                                                         └── (PREFERS: weight=0.1) ──> [FORMAT: Terse_Technical]

* **Domain Confidence Edges (``OPERATES``)**: Connects ``Operator`` to ``Machine``, tracking
  machine-specific ``autonomy_score`` (0.0 to 100.0) and ``derived_tier`` (``Novice``, ``Intermediate``,
  ``Expert``).
* **Cognitive State Nodes (``STATE:<Operator_ID>:<Tier>``)**: Independent cognitive representation
  representing how the operator learns when in a given competence mindset.
* **Cognitive Preference Edges (``PREFERS``)**: Connects each ``STATE`` node to format arms, maintaining
  independent UCB statistics (cumulative reward weight $W_i$, pull count $N_i$, success count, and
  escalation count).

3.1.2 Dynamic Operator Skill Tier Thresholding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An operator's skill tier on any specific machine is dynamically derived from their machine-specific
autonomy score:

.. code-block:: text

   +-------------------------------------------------------------------+
   | Machine Autonomy Score (A) >= 75.0      --> Derived Tier = "Expert"       |
   | 40.0 <= Machine Autonomy Score (A) < 75 --> Derived Tier = "Intermediate" |
   | Machine Autonomy Score (A) < 40.0       --> Derived Tier = "Novice"       |
   +-------------------------------------------------------------------+
**Continuous LMS Certification Overrides**: During the overnight Sleep Cycle, the system queries the factory Learning Management System (LMS). If an operator receives a new offline certification for a machine, their Autonomy Score for that `OPERATES` edge is deterministically overridden to 85.0 (Expert), bypassing the need for slow, empirical telemetry learning.

3.1.3 Dynamic Procedural Memory & Bayesian Fault Trees
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Troubleshooting procedures are structured as dynamic probabilistic trees supporting multiple
diagnostic branches per alarm code. Each branch maintains live telemetry:

.. code-block:: json

   {
     "error_code": "Alarm 102",
     "machine_type": "Haas CNC",
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

Each branch's empirical success probability is calculated using Beta-Binomial conjugate updating
with Laplace smoothing ($\alpha=1.0, \beta=1.0$):

.. math::

   P(\text{Success}) = \frac{\text{success\_count} + \alpha}{\text{success\_count} + \text{failure\_count} + \alpha + \beta}

When a query is processed, branches are sorted descending by $P(\text{Success})$. The Working Memory
Synthesizer directs the LLM to present the highest-probability path as the **Primary Recommended Fix**
while detailing fallback paths.

---

3.2 Subsystem 2: Contextual Multi-Armed Bandit Personalization Engine
---------------------------------------------------------------------

3.2.1 State-Bound Upper Confidence Bound (UCB1) Routing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Contextual Bandit router eliminates static rule-based assumptions by modeling format selection
as an exploration-exploitation policy. For each operator $u$, active cognitive tier $T$, and
presentation format arm $i \in \{\text{Visual\_StepByStep}, \text{Terse\_Technical}, \text{Detailed\_Text}\}$:

.. math::

   \text{UCB}_i(u, T) = \bar{X}_i(u, T) + c \cdot \sqrt{\frac{\ln(N(u, T) + 1)}{N_i(u, T) + \epsilon}}

Where:

* $\bar{X}_i(u, T) = \frac{W_i(u, T)}{N_i(u, T)}$ is the **Empirical Mean Reward** for arm $i$ in state $(u, T)$.
* $N(u, T) = \sum_{j} N_j(u, T)$ is the **Total Interaction Pulls** across all arms in state $(u, T)$.
* $c = 1.2$ is the **Exploration Hyperparameter** governing the uncertainty bonus.
* $\epsilon = 10^{-4}$ prevents division by zero for unpulled arms.

**Forced Epsilon Injection (Time-Decay Rule)**: To prevent permanent algorithmic pigeonholing, if an operator has not been presented with an alternative (e.g., higher-tier) format in the last 90 days, the router forcefully overrides UCB exploitation and injects an exploration turn. This continuously tests for human upskilling and shifts in cognitive preference.

3.2.2 Bandit Presentation Arms & Cognitive Objectives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Bandit Presentation Arms & Structural Directives
   :widths: 22 33 45
   :header-rows: 1

   * - Bandit Arm
     - Target Cognitive Mindset
     - Structural Directive Injected into Prompt
   * - **Visual_StepByStep**
     - Novices, visual learners, high-stress complex procedures.
     - Sequential numbered steps, bold visual tags (`[INSPECT]`, `[ACTION]`, `[VERIFY]`, `[SAFETY]`), markdown checklists `[ ]`, and ASCII flow arrows.
   * - **Terse_Technical**
     - Seasoned machinists, expert triage, time-critical production.
     - Maximum 2-3 bullet points or under 45 words. Zero pleasantries or conversational filler. Raw technical setpoints, M/G-codes, sensor bits, and direct corrective actions only.
   * - **Detailed_Text**
     - In-depth training, root-cause analysis, conceptual learners.
     - Comprehensive explanation detailing underlying physical/electrical principles, sensor operational thresholds, multi-stage triage, and preventive maintenance.

3.2.3 Environmental Context Matrix (ECM) & Fatigue Gating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Real-world shopfloors subject operators to cumulative physical and cognitive fatigue. The ECM service
evaluates shift metrics on every turn:

* **Fatigue Index**: $\text{Fatigue Index} = \frac{\text{Hours Since Clock-In}}{\text{Total Scheduled Shift Hours}}$.
* **The Fatigue Gate**: If $\text{Fatigue Index} \ge 0.80$ (e.g., hour 10 of a 12-hour shift), the Bandit
  Router sets exploration parameter $c = 0.0$ (**100% Exploitation**). This immediately suppresses
  experimental formats and locks into the most concise, proven format (``Terse_Technical`` or highest
  empirical mean) to protect tired operators from cognitive overload.
* **The Supervisor Gate**: If $\text{supervisor\_available} == \text{False}$, the Working Memory
  Synthesizer injects an emergency safety override instructing the operator to follow strict safety
  holds and avoid attempting unverified high-voltage actions without Level 2 supervision.

3.2.4 Instant Human Format Overrides (Human Agency Safeguard)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To prevent algorithmic lock-in and respect operator autonomy, the UI provides explicit format override
buttons. If an operator manually requests a different format:

1. **Immediate Execution**: The system bypasses bandit selection for the current turn and instantly
   re-synthesizes the LLM response using the requested format.
2. **Mathematical Penalty**: A heavy penalty ($-10.0$ reward weight, $+1$ pull count, $+1$ escalation)
   is applied to the rejected format arm in the operator's active cognitive state, rapidly teaching the
   bandit that the rejected format was unacceptable in that context.

---

3.3 Subsystem 3: Hybrid SOP Retrieval Engine (ChromaDB + BM25 + RRF)
--------------------------------------------------------------------
Shopfloor queries combine colloquial natural language symptoms (e.g., *"spindle vibrates during cutting"*)
with exact technical alphanumeric codes (e.g., *"Haas Alarm 102"*, *"Engel E-201"*, *"M06"*).

* **Dense Vector Search (ChromaDB + Gemini Embeddings)**: Captures high-level semantic similarity and
  synonym phrasing.
* **Sparse Keyword Search (BM25)**: Ensures 100% exact matching on critical alphanumeric fault codes and M/G-codes.

3.3.1 Reciprocal Rank Fusion (RRF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The retriever fuses both streams using Reciprocal Rank Fusion:

.. math::

   \text{RRF\_Score}(d) = \sum_{m \in \{\text{Dense}, \text{Sparse}\}} \frac{1}{k_{\text{rrf}} + \text{rank}_m(d)}

Where $k_{\text{rrf}} = 60$ is the standard smoothing constant, and $\text{rank}_m(d)$ is the 1-based rank
of document $d$ in retrieval stream $m$. Machine metadata filters ensure that queries initiated on a Haas
CNC machine strictly retrieve Haas-compatible procedures.

---

3.4 Subsystem 4: Working Memory Synthesizer & LLM Reasoning Agent
-----------------------------------------------------------------
The LLM (Google Gemini) is strictly constrained by the **Working Memory Synthesizer**, which dynamically
builds a grounded, multi-section prompt:

.. code-block:: text

   ========================= MASTER WORKING MEMORY PROMPT =========================
   1. SYSTEM IDENTITY & ROLE:
      Expert Shopfloor AI Copilot for CNC Milling & Injection Molding Equipment.

   2. CURRENT OPERATOR & OPERATIONAL CONTEXT:
      - Operator: Sarah Jenkins (Domain Tier: Expert | Autonomy: 95.0%)
      - Target Machine: Haas VF-2
      - Active SCADA Alarm: Alarm 102: SERVOS OFF (Air Pressure: 64.2 PSI | Nominal: >85 PSI)
      - Environmental Context: Shift Hour 3/8 | Fatigue Index: 0.38 | Supervisor: Online

   3. HISTORICAL FAILURE WARNINGS (Episodic Memory Injection):
      - System Note: Operator has 2 prior escalations for Alarm 102. Proactively acknowledge
        past difficulties and offer early CMMS dispatch if initial checks fail.

   4. MANDATORY SAFETY PROTOCOLS:
      - Lock-Out / Tag-Out (LOTO) mandatory before opening rear electrical enclosure.
      - Eye protection and pneumatic pressure discharge required.

   5. AUTHORITATIVE GROUNDING SOURCES (Retrieved SOPs & Procedural Fault Trees):
      - [Primary Recommended Path (P=0.93)]: Adjust Main Air Regulator on Rear Panel.
      - [Secondary Backup Path (P=0.40)]: Inspect Pre-Charge Solenoid Valve Wiring.
      - Official SOP Excerpts (SOP-HAAS-001).

   6. REQUIRED OUTPUT FORMATTING DIRECTIVE (State-Bound Bandit Winner):
      - Strictly Terse & Technical (Max 2-3 bullets, <=45 words, raw setpoints only).

   7. STRICT GROUNDING CONSTRAINTS:
      - Zero Hallucination: Ground guidance strictly in retrieved sources.
   ================================================================================

---

3.5 Subsystem 5: Shadow Observer, Closed-Loop Feedback & Durability Escrow
--------------------------------------------------------------------------

3.5.1 Sub-100ms Synchronous Event Logger
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When an operator completes an interaction turn, the ``ShadowObserver`` executes in **<5ms** (guaranteed
<100ms):

1. Constructs an event payload: ``session_id``, ``operator_id``, ``machine_id``, ``format_used``,
   ``cognitive_tier``, ``outcome_status`` (``SUCCESS``, ``ESCALATED_CMMS``, ``ABANDONED_TIMEOUT``,
   ``FORMAT_OVERRIDE``), and timestamp.
2. Appends the event to ``data/episodic_event_queue.json``.
3. Zero synchronous graph mutations occur during the active shift, ensuring instantaneous UI responsiveness
   and zero intra-shift semantic drift.

3.5.2 Provisional Reward Escrow & The 8-Hour Durability Window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To eliminate the "Duct-Tape Problem" (where temporary, unsafe fixes clear an alarm momentarily only to
fail again hours later):

* **Escrow Holding**: When an operator marks an issue resolved, the positive reward is placed in
  ``data/escrow_rewards.json`` with an **8-hour Durability Window** timestamp.
* **Overnight Durability Audit (Sleep Cycle)**:
  * The evaluator queries SCADA telemetry for recurring alarms on that machine and error code within 8 hours.
  * **Durable Fix (>8 hours clean)**: Releases standard positive rewards: **$+1.0$** to Bandit weight and
    **$+5.0$** to machine autonomy.
  * **Duct-Tape Failure (<8 hours recurrent alarm)**: Inverts the provisional reward into a severe penalty:
    **$-5.0$** to Bandit format weight and **$-15.0$** to machine autonomy.

3.5.3 Summary of Feedback Pathways
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Feedback Event Pathways & Lifecycle Actions
   :widths: 20 25 30 25
   :header-rows: 1

   * - Event Type
     - Operator / System Trigger
     - Synchronous Shift Action (<5ms)
     - Asynchronous Sleep Cycle Action
   * - **Independent Success**
     - Operator clicks *"Solved Independently"*.
     - Appends `SUCCESS` event to queue; places reward in escrow; triggers SCADA telemetry check.
     - Checks 8-hr recurrence; releases $+1.0$ bandit reward and $+5.0$ autonomy points; updates fault tree branch count.
   * - **Supervisor Escalation**
     - Operator clicks *"Escalate to Supervisor"*.
     - Appends `ESCALATED_CMMS` event to queue; auto-dispatches CMMS work order.
     - Deducts $-1.0$ bandit penalty and $-15.0$ autonomy points; updates fault tree failure count; recomputes operator tier.
   * - **Format Hard Override**
     - Operator clicks format override button.
     - Bypasses bandit; re-synthesizes LLM prompt instantly in requested format.
     - Applies $-10.0$ penalty to rejected format arm in active cognitive state in knowledge graph.
   * - **Session Abandonment**
     - Session times out without resolution.
     - Appends `ABANDONED_TIMEOUT` event to queue.
     - Logs failure event; increments fault tree failure count; preserves audit history.

---

3.6 Subsystem 6: Human-in-the-Loop Micro-Debrief Loop & Quarantine Store
------------------------------------------------------------------------

3.6.1 The Micro-Debrief Intercept
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When an operator resolves a complex machine alarm significantly faster than standard OEM duration
(e.g., clearing a 15-minute alarm in 2 minutes), the system avoids guessing:

1. **Detection**: Shadow Observer identifies the abnormal delta and creates a pending debrief in
   ``data/pending_debriefs.json``.
2. **Next-Session Prompt**: Upon the operator's next chat session, the assistant intercepts:
   *"Earlier you resolved Alarm 102 in ~2.0 min. Did you use the 'Regulator Pre-Charge Shortcut'? (Yes/No)"*
3. **Deterministic Routing**:
   * If **Yes**: Stores the new procedure in ``data/quarantine_sops.json`` with that operator's validation.
   * If **No**: Safely discards the telemetry hypothesis without corrupting procedural memory.

3.6.2 3-Expert Consensus Auto-Promotion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Newly discovered procedures remain quarantined and cannot be retrieved by general operators.
* When **3 distinct Expert operators** (``derived_tier == 'Expert'``) validate the quarantined procedure
  during micro-debriefs, the Sleep Cycle evaluator automatically promotes the procedure into the active
  ``data/procedural_fault_trees.json`` database.
* Promoted procedures receive an immutable metadata tag ``min_tier_required: 'Expert'``, guaranteeing
  that novices are never served unvetted shortcuts.

---

3.7 Subsystem 7: Shopfloor Integration & Mock Services
------------------------------------------------------
To enable end-to-end testing and demonstration without physical factory machinery, the system provides
four modular service emulators:

1. **SCADA Mock Service (`MockSCADA`)**:
   Simulates real-time sensor streams (air pressure PSI, spindle RPM, temperatures °C, hydraulic bar,
   clamping force kN, E-stop states), generates live machine alarms, and provides `verify_repair()` methods.
2. **CMMS Mock Service (`MockCMMS`)**:
   Simulates enterprise work-order management: generates tracking ticket IDs (e.g., `TICK-2026-A83B`),
   assigns maintenance tiers, and logs resolution histories.
3. **HR / LMS Mock Service (`MockHRLMS`)**:
   Maintains employee rosters, tenure, shift assignments, and cold-start qualification baselines.
4. **Environmental Context Service (`MockECM`)**:
   Computes real-time shift elapsed hours, fatigue indices, supervisor presence, ambient noise, and temperatures.

----------------------------------------------------------------------------------------

4. Comprehensive Answers to Core Architectural Questions
=========================================================

4.1 Question 1: What Behavioural Patterns Are Captured?
-------------------------------------------------------
The system captures five distinct behavioral dimensions over time:

1. **Cognitive Presentation Preferences per Competence State**:
   Tracks whether an operator responds best to visual checklists, terse parameters, or detailed
   tutorials when in Novice vs. Expert mindsets. Captured via state-bound UCB bandit weights and pull histories.
2. **Machine-Specific Domain Competence**:
   Tracks proficiency on each specific machine type (e.g., Haas CNC vs. Engel Injection Molder).
   Captured via machine-specific autonomy scores (0–100%) and independent success/escalation ratios.
3. **Troubleshooting Habits & Shortcut Discoveries**:
   Captures which specific diagnostic branches operators execute and tracks abnormal resolution speeds
   via micro-debrief validation.
4. **Escalation Propensity vs. Independent Triage**:
   Tracks whether an operator attempts self-directed triage or escalates immediately upon alarm onset.
5. **Fatigue Resilience & Shift Patterns**:
   Captures performance and escalation frequency across different shift hours (Hour 1 vs. Hour 11).

4.2 Question 2: What Data Sources Are Utilized?
-----------------------------------------------
The architecture unifies six heterogeneous industrial data sources:

1. **Live SCADA Telemetry & PLC Alarms**: Real-time sensor readings, error codes, and equipment states.
2. **Authoritative Engineering Knowledge Base**: Official SOPs, OEM manuals, LOTO rules, and hazard matrices.
3. **Dynamic Procedural Skill Library**: Probabilistic Bayesian fault trees with live branch success/failure counts.
4. **HR & LMS Systems**: Shift rosters, formal job classifications, tenure, and safety certifications.
5. **CMMS Escalation Ledger**: Historical work orders, repair logs, and maintenance dispatch tickets.
6. **Environmental Context Matrix (ECM)**: Shift elapsed hours, fatigue index, supervisor status, and ambient telemetry.

4.3 Question 3: What Agents and Components Are Needed?
------------------------------------------------------
The system utilizes a coordinated multi-component architecture:

* **Chat / Reasoning Agent (Google Gemini)**: Synthesizes grounded natural language guidance strictly adhering to prompt directives.
* **Contextual Bandit Router (Policy Engine)**: Evaluates state-bound UCB1 scores and enforces ECM fatigue gates.
* **Shadow Observer (Shift Event Logger & Micro-Debrief Generator)**: Executes sub-100ms event logging, manages provisional reward escrow, and enqueues debriefs.
* **Working Memory Synthesizer**: Constructs multi-section grounded prompts with safety, telemetry, failure warnings, and bandit directives.
* **Hybrid Search Retriever**: Fuses dense ChromaDB vector search and sparse BM25 keyword matching via RRF.
* **Decoupled Semantic Knowledge Graph**: Manages domain competence edges and state-bound format preferences.
* **Dynamic Procedural Memory Store**: Manages branching Bayesian fault trees and quarantine stores.
* **Sleep Cycle Batch Evaluator**: Executes overnight escrow durability checks, graph mutations, Bayesian updates, and consensus promotions.

4.4 Question 4: How Does the System Learn Over Time?
----------------------------------------------------
Learning occurs across three coupled mathematical mechanisms:

1. **State-Bound UCB Bandit Optimization**:
   Durable independent resolutions reinforce the active format arm ($+1.0$), while escalations and
   duct-tape failures apply penalties. As pulls $N$ accumulate, exploration bonuses decay, converging
   to the operator's optimal format for each competence state.
2. **Knowledge Graph Autonomy Evolution**:
   Machine autonomy scores update dynamically ($+5.0$ on durable success, $-15.0$ on escalation/duct-tape),
   driving smooth tier transitions across Novice, Intermediate, and Expert thresholds.
3. **Bayesian Procedural Fault Tree Updating**:
   Diagnostic branch success probabilities update via Beta-Binomial conjugate updating, ensuring that
   the most effective real-world troubleshooting paths rise to the top of the recommended hierarchy.

4.5 Question 5: How Is Memory Stored, Updated, and Corrected?
-------------------------------------------------------------

.. list-table:: Memory Management & Governance Lifecycle
   :widths: 20 35 45
   :header-rows: 1

   * - Memory Aspect
     - Storage Mechanism
     - Update & Correction Protocol
   * - **Shift Event Buffering**
     - `data/episodic_event_queue.json`
     - Synchronous, append-only JSON writes in <5ms. Flushed and archived during Sleep Cycle.
   * - **Reward Escrow**
     - `data/escrow_rewards.json`
     - Provisional rewards held during 8-hr Durability Window; validated against SCADA recurrence logs during Sleep Cycle.
   * - **Knowledge Graph**
     - `data/graph_state.json` (NetworkX)
     - Mutated during Sleep Cycle batch evaluation; atomic disk serialization prevents corruption. Admin reset button restores HR baseline if needed.
   * - **Procedural Memory**
     - `data/procedural_fault_trees.json`
     - Updated via Bayesian math during Sleep Cycle; new shortcuts isolated in `quarantine_sops.json` until 3-Expert consensus auto-promotes.
   * - **Episodic Audit Ledger**
     - `data/episodic_logs.json`
     - Permanent append-only JSON ledger with strict status tagging for compliance and traceability.

4.6 Question 6: How Does the Assistant Avoid Wrong Assumptions?
---------------------------------------------------------------
The architecture enforces seven complementary safeguards:

1. **Decoupled Competence & Preference**: Expert status on Machine A never leaks into unfamiliar Machine B.
2. **Cold-Start Bootstrapping**: New operators are initialized with verified HR/LMS qualification tiers.
3. **UCB Exploration Bonus ($c=1.2$)**: Prevents format lock-in by continually testing alternative formats.
4. **Asymmetric Penalty Function**: Escalations penalize autonomy by $-15.0$, while successes award $+5.0$,
   requiring sustained competence before tier advancement.
5. **Provisional Escrow & Duct-Tape Detection**: Penalizes temporary fixes that recur within 8 hours.
6. **Closed-Loop SCADA Verification**: Verifies physical sensor recovery before granting resolution rewards.
7. **Human-in-the-Loop Micro-Debriefs**: Validates suspected shortcuts with the operator before updating procedural databases.

4.7 Question 7: How Is the Profile Used to Personalize Future Support?
----------------------------------------------------------------------
When an operator initiates a query, personalization occurs across five distinct layers:

1. **Presentation Structure**: The state-bound Bandit Router determines whether the LLM responds in visual checklists, terse parameters, or detailed tutorials.
2. **Diagnostic Hierarchy**: Dynamic Bayesian fault trees rank troubleshooting paths so the operator sees the highest-probability fix first.
3. **Safety & Autonomy Framing**: Machine-specific tier and autonomy scores calibrate the depth of precautionary checks.
4. **Historical Failure Proactivity**: Prior escalations for that specific fault trigger proactive conversational warnings and early CMMS dispatch offers.
5. **Environmental & Fatigue Adaptation**: High fatigue indices suppress exploration; offline supervisor status injects strict safety holds.

----------------------------------------------------------------------------------------

5. Safety & FMEA Guardrails: Consensus, Durability & Human Agency
=================================================================

.. list-table:: Industrial Failure Modes & Mitigation Matrix (FMEA)
   :widths: 22 38 40
   :header-rows: 1

   * - Failure Mode
     - Operational Risk
     - Engineering Mitigation & Guardrail
   * - **1. The Duct-Tape Problem**
     - Operator applies temporary patch (e.g., wire tie); AI prematurely rewards fix; machine fails 2 hours later.
     - **Provisional Reward Escrow**: Rewards held for 8 hours. If SCADA detects recurrence, inverts to $-5.0$ bandit penalty and $-15.0$ autonomy penalty.
   * - **2. Unvetted Shopfloor Shortcut**
     - Operator discovers unsafe shortcut; AI suggests it to novices, risking injury or warranty void.
     - **Quarantine Store & 3-Expert Consensus**: New shortcuts isolated in `quarantine_sops.json`; requires 3 distinct Expert validations before auto-promoting with `min_tier_required: 'Expert'`.
   * - **3. Algorithmic Disempowerment**
     - Bandit explores visual steps during emergency triage when expert demands raw setpoints.
     - **Instant Format Override**: Operator clicks override; LLM re-synthesizes instantly; applies $-10.0$ penalty to rejected format in knowledge graph.
   * - **4. Premature Autonomy Promotion**
     - Novice gets lucky on 2 easy fixes; AI promotes to Intermediate and omits critical safety checks.
     - **Asymmetric Penalties & Tenure Floors**: $+5.0$ reward vs. $-15.0$ penalty ratio; minimum interaction counts required before tier transitions.
   * - **5. Conversational Amnesia on Hard Faults**
     - Operator struggles repeatedly with complex alarm; AI repeats same failed steps.
     - **Episodic Failure Injection**: Historical escalations injected into working memory; prompts LLM to offer early CMMS dispatch and acknowledge difficulty.
   * - **6. End-of-Shift Cognitive Fatigue**
     - Exhausted operator overwhelmed by complex formatting during shift final hours.
     - **ECM Fatigue Gate**: $\text{Fatigue Index} \ge 0.80$ forces exploration parameter $c = 0.0$ (100% exploitation of concise formats).
   * - **7. Critical Safety Hallucination**
     - LLM invents ungrounded high-voltage troubleshooting steps or omits LOTO.
     - **Hardcoded Safety Injection & Hybrid RRF**: Mandatory safety headers pre-injected regardless of LLM generation; grounding strictly restricted to verified SOPs.

----------------------------------------------------------------------------------------

6. Design of Experiment (Pilot Validation Plan)
===============================================

6.1 Core Hypotheses
-------------------
* **Primary Hypothesis ($H_1$)**: Operators supported by the adaptive AI assistant will achieve a
  $\ge 25\%$ reduction in **Mean Time to Repair (MTTR)** and machine downtime compared to static manuals.
* **Secondary Hypothesis ($H_2$)**: The state-bound Contextual Bandit router will converge to operator-preferred
  instruction formats within 5–8 interaction turns per cognitive state.
* **Tertiary Hypothesis ($H_3$)**: The dynamic Bayesian fault tree and consensus engine will achieve
  $\ge 95\%$ accuracy in prioritizing root-cause fixes while maintaining $0.0\%$ unvetted shortcut leaks to novices.

6.2 Pilot Evaluation Metrics
----------------------------

.. list-table:: Pilot Evaluation Metrics
   :widths: 22 38 40
   :header-rows: 1

   * - Metric Category
     - Key Indicator
     - Measurement Method & Target
   * - **Operational Efficiency**
     - Mean Time to Repair (MTTR)
     - Timestamp delta between alarm trigger and SCADA telemetry normalization. Target: $\ge 25\%$ reduction.
   * - **Autonomy & Triage**
     - Independent Resolution Ratio
     - Ratio of durable `SUCCESS` sessions to total sessions. Target: $\ge 70\%$ for standard alarms.
   * - **Policy Convergence**
     - Bandit Arm Convergence Speed
     - Turns required for winning arm UCB score to stabilize $\ge 0.5$ above competing arms. Target: $\le 8$ turns.
   * - **Safety & Grounding**
     - SOP Hallucination Rate
     - Blind engineering audit of LLM responses against grounding SOPs. Target: $0.0\%$ ungrounded procedures.
   * - **Durability & Quality**
     - 8-Hour Recurrence Rate
     - Percentage of resolved alarms recurring within 8 hours. Target: $<5.0\%$.
   * - **Operator Usability**
     - Cognitive Load & Usability
     - Post-shift NASA-TLX cognitive load index and System Usability Scale (SUS). Target: SUS $\ge 80$.

6.3 Verification of Behavioral Profile Accuracy
-----------------------------------------------
1. **Correlation Analysis**: Correlate learned machine autonomy scores with quarterly supervisor reviews
   to verify that AI-inferred tiers match ground-truth shopfloor performance.
2. **Blind A/B Testing**: Periodically serve alternative formats and measure whether task completion
   time increases when non-preferred formats are used.
3. **Drift Detection**: Monitor moving averages of autonomy scores to detect skill degradation or identify
   when newly introduced machine models require refresher training.

----------------------------------------------------------------------------------------

7. End-to-End Execution Scenarios
=================================

7.1 Scenario 1: Novice Operator on Haas CNC (Alarm 102 - Servos Off)
--------------------------------------------------------------------
1. **Operator Context**: John Doe (`OP-001`), Novice Tier (Autonomy: 35.0%), Shift Hour 2/8.
2. **Alarm Event**: Haas VF-2 triggers `Alarm 102: SERVOS OFF`. SCADA indicates air pressure at 64.2 PSI (nominal $>85\text{ PSI}$).
3. **Retrieval & Fault Tree**: Hybrid RRF matches `SOP-HAAS-001`. Dynamic fault tree ranks `HAAS_102_REGULATOR` (P=0.93) as Primary Recommended Fix.
4. **Bandit Policy**: Bandit evaluates state `(OP-001, Novice)` and selects `Visual_StepByStep` (highest UCB).
5. **Generation**: Gemini outputs a structured guide with `[SAFETY]`, `[INSPECT]`, and `[ACTION]` tags, instructing John to adjust the rear panel regulator.
6. **Action & Resolution**: John adjusts the regulator to 90 PSI and clicks *"Solved Independently"*.
7. **Observer Outcome**:
   * Appends `SUCCESS` event to `episodic_event_queue.json` in <5ms.
   * Places $+1.0$ reward and $+5.0$ autonomy points into `escrow_rewards.json` (8-hour window).
   * SCADA verifies pressure normalized to 92 PSI.

7.2 Scenario 2: Expert on Haas Operating as Novice on Engel (Decoupled States)
------------------------------------------------------------------------------
1. **Operator Context**: Sarah Jenkins (`OP-002`), Expert on Haas VF-2 (Autonomy: 95.0%), but newly assigned to Engel Injection Molder (Autonomy: 15.0%, Derived Tier: Novice).
2. **Alarm Event**: Engel Victory 330 triggers `E-201: BARREL OVERHEAT`.
3. **State-Bound Routing**:
   * System detects machine is Engel Victory 330.
   * Retrieves Sarah's machine-specific tier: `Novice`.
   * Queries state `(OP-002, Novice)` in knowledge graph.
   * Bandit selects `Visual_StepByStep` (rather than Terse Technical), providing Sarah with detailed visual thermocouple inspection steps appropriate for her novice status on this equipment.

7.3 Scenario 3: High-Fatigue Night Shift with Supervisor Offline
----------------------------------------------------------------
1. **Operator Context**: Mike Chang (`OP-003`), Intermediate Tier, Shift Hour 11/12 (Fatigue Index: 0.92), Supervisor Offline.
2. **Alarm Event**: Spindle vibration alarm on Haas VF-2.
3. **ECM Gating**:
   * Fatigue Index $\ge 0.80$ triggers Fatigue Gate: exploration parameter set to $c=0.0$ (100% exploitation). Bandit selects concise `Terse_Technical` to avoid cognitive overload.
   * Supervisor Offline triggers Supervisor Gate: Working Memory Synthesizer injects mandatory safety hold directive prohibiting unassisted enclosure opening.
4. **Generation**: LLM provides concise external checks and explicitly advises halting the spindle if vibration persists.

7.4 Scenario 4: Fast Fix & Micro-Debrief Loop
---------------------------------------------
1. **Event**: Sarah resolves a complex hydraulic alarm in 1.8 minutes (standard OEM time: 12 minutes).
2. **Debrief Enqueue**: Shadow Observer detects abnormal speed and enqueues a record in `data/pending_debriefs.json`.
3. **Next Session Intercept**: When Sarah opens the chat copilot on her next shift, the assistant asks:
   *"Earlier you resolved Alarm 304 in 1.8 min. Did you use the 'Manifold Bypass Bleed' shortcut? (Yes/No)"*
4. **Outcome**: Sarah clicks *"Yes"*. The procedure is stored in `data/quarantine_sops.json` with Sarah's Expert validation attached.

7.5 Scenario 5: Overnight Sleep Cycle Execution
-----------------------------------------------
1. **Trigger**: At 03:00 AM, `sleep_cycle_evaluator.py` runs batch evaluation.
2. **Escrow Durability Audit**:
   * Evaluates John Doe's Alarm 102 fix from Scenario 1: SCADA confirms 0 recurring alarms over 8 hours. Releases $+1.0$ bandit reward and $+5.0$ autonomy points to John's profile.
   * Evaluates another operator's quick fix: SCADA reveals alarm recurred 2 hours later. Inverts provisional reward into a $-5.0$ bandit penalty and $-15.0$ autonomy deduction (duct-tape penalty).
3. **Knowledge Graph Mutation**: Updates all operator-machine autonomy scores, recomputes derived tiers, and updates state-bound UCB weights in `data/graph_state.json`.
4. **Bayesian Tree Updates**: Updates branch success/failure counts in `data/procedural_fault_trees.json`.
5. **Consensus Auto-Promotion**: Finds a quarantined SOP that reached 3 Expert validations; promotes it to the active procedural library with `min_tier_required: 'Expert'`.
6. **Queue Flush**: Archives processed events and clears `data/episodic_event_queue.json`.

----------------------------------------------------------------------------------------

8. Repository Codebase Structure & File Mapping
===============================================

For a comprehensive line-by-line and class-by-class technical breakdown of all modules, refer to the
`code_and_modules_guide.rst <code_and_modules_guide.rst>`_. For environment setup, execution commands, and
JSON configuration schemas, refer to the `run_and_configuration_guide.rst <run_and_configuration_guide.rst>`_.

The repository is organized into clean, modular layers implementing the architecture described above:

.. code-block:: text

   factory-agent-app/
   ├── app.py                          # Streamlit UI & Interactive Multi-Tier Shopfloor Dashboard
   ├── sleep_cycle_evaluator.py        # Asynchronous Batch Sleep Cycle Evaluator & Escrow Engine
   ├── verify_refactor.py              # Verification Test Suite for Cognitive Decoupling & Queues
   ├── verify_section2.py              # Verification Test Suite for Escrow, Quarantine & Overrides
   ├── verify_section3.py              # Verification Test Suite for ECM, Fatigue & Micro-Debriefs
   ├── agents/
   │   ├── bandit_router.py            # UCB1 Multi-Armed Bandit Router with ECM Fatigue Gating
   │   ├── chat_agent.py               # Google Gemini Reasoning Agent with Grounded Generation
   │   └── shadow_observer.py          # Low-Latency Shift Event Logger & Escrow Enqueuer
   ├── memory/
   │   ├── semantic_graph.py           # Decoupled NetworkX Operator Competency Knowledge Graph
   │   ├── procedural_memory.py        # Dynamic Bayesian Fault Trees & Quarantine Consensus Store
   │   ├── debrief_store.py            # Micro-Debrief Store & Human-in-the-Loop Intercept Queue
   │   ├── episodic_store.py           # Low-Latency Event Queue & Permanent Audit Ledger
   │   ├── working_memory.py           # Dynamic Prompt Assembler with Safety & Context Injection
   │   └── search.py                   # Hybrid Dense Vector (ChromaDB) + Sparse BM25 Retriever (RRF)
   ├── mock_services/
   │   ├── scada_service.py            # Mock SCADA Telemetry Stream, Alarms & Repair Verification
   │   ├── ecm_service.py              # Environmental Context Matrix (Fatigue, Supervisor, Noise)
   │   ├── cmms_service.py             # Mock CMMS Work Order Dispatch & Ticket Lifecycle
   │   └── hr_lms_service.py           # Mock HR Roster, Operator Roles & Cold-Start Seeding
   └── data/
       ├── factory_knowledge_base.json # Authoritative Grounding SOPs
       ├── procedural_fault_trees.json # Active Dynamic Bayesian Fault Trees
       ├── quarantine_sops.json        # Sandboxed Crowdsourced Procedures
       ├── escrow_rewards.json         # Provisional Reward Escrow Ledger (8-hr Window)
       ├── pending_debriefs.json       # Enqueued Micro-Debrief Prompts
       ├── episodic_event_queue.json   # Synchronous Shift Event Queue (<100ms)
       ├── episodic_logs.json          # Permanent Append-Only Turn Audit Logs
       └── graph_state.json            # Knowledge Graph Serialization State

----------------------------------------------------------------------------------------

9. Conclusion & Summary
=======================

The Adaptive Cognitive AI Assistant transforms static, one-size-fits-all factory manuals into a
living, intelligent, closed-loop operational intelligence platform. By unifying **Decoupled
Competence Knowledge Graphs**, **State-Bound Contextual Bandits**, **Dynamic Bayesian Fault Trees**,
**Provisional Reward Escrow Durability Windows**, **Quarantine Consensus Auto-Promotion**, **Environmental
Context Fatigue Gating**, and **Sub-100ms Synchronous Event Logging**, the system delivers personalized,
safety-compliant, and self-improving operational intelligence tailored for high-stakes smart manufacturing.
