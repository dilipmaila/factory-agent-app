========================================================================================
Adaptive AI Assistant for Factory Operators: Solution Design
========================================================================================

:Author: Manufacturing AI Systems Architecture Team
:Date: August 2026
:Format: reStructuredText (RST)

.. contents:: Table of Contents
   :depth: 3
   :local:
   :backlinks: entry

.. note::
   **Companion Documents**:

   * Module & Code Guide: `code_and_modules_guide.rst <code_and_modules_guide.rst>`_
   * Setup & Run Guide: `run_and_configuration_guide.rst <run_and_configuration_guide.rst>`_

----------------------------------------------------------------------------------------

1. Summary
==========

What is the problem? What does this system do to fix it?

.. list-table:: Problems & Solutions at a Glance
   :widths: 35 65
   :header-rows: 1

   * - Problem
     - How the System Fixes It
   * - **Same instructions for everyone** -- too easy for experts, too hard for novices.
     - A **State-Bound UCB1 Bandit** picks the best format (Visual / Short / Detailed) for each operator on each machine.
   * - **Wrong skill level assumed** -- a CNC expert is treated as an expert on a machine they have never used.
     - The **Knowledge Graph** tracks skill per machine separately. Expertise on one machine does not carry over to another.
   * - **Outdated procedures** -- faster shortcuts found on the shop floor are never saved.
     - **Dynamic Bayesian Fault Trees** + a **3-Expert vote** auto-add new shortcuts after they are verified.
   * - **Slow UI** -- saving data during a shift makes the screen lag.
     - **Dual-Loop Design**: fast events are saved in under 5ms; heavy updates happen later during the Sleep Cycle.
   * - **Duct-tape fixes** -- the AI rewards a fix that breaks again hours later.
     - **8-Hour Wait Rule (Escrow)**: the AI waits 8 hours to confirm the fix is permanent before giving credit.
   * - **Tired operators** -- complex instructions overwhelm workers near the end of a long shift.
     - **ECM Fatigue Gate**: when the Fatigue Index reaches 0.80 or more, the system switches to the shortest, simplest format only.

**Design Assumptions**:

1. Every operator has a unique RFID or SSO login.
2. The factory IT and OT networks are connected (IT/OT convergence), so SCADA data is accessible.
3. The AI gives advice only. It **cannot** write to any PLC or control any machine directly.
4. A fast and durable machine recovery is the proof that a fix worked (the reward signal).

----------------------------------------------------------------------------------------

2. How the System Works: Two Loops
====================================

The system runs two loops at the same time.

**Loop 1 -- Real-Time Loop (under 100ms)**:
Runs every time an operator asks a question. It reads context, picks the best format,
writes the answer, and logs the event. No heavy data saves happen here.

**Loop 2 -- Async Learning Loop (Sleep Cycle)**:
Runs at night (e.g., 03:00 AM). It checks rewards, updates the knowledge graph,
updates fault trees, and promotes new shortcuts that passed the expert vote.

2.1 Full System Flowchart
--------------------------

.. code-block:: text

   ============================================================
                   REAL-TIME LOOP (under 100ms)
   ============================================================

   +-------------------------------------------------------+
   |                   SHOPFLOOR OPERATOR                  |
   |   (Picks profile, picks machine, types query on HMI)  |
   +-------------------------------------------------------+
                              |
                              | 1. Query or Alarm (e.g., "Alarm 102")
                              v
   +-------------------------------------------------------+
   |          ENVIRONMENTAL CONTEXT MATRIX (ECM)           |
   |  - Fatigue Index = Hours Worked / Total Shift Hours   |
   |  - Supervisor on-site or off-site?                    |
   |  - Noise (dB), temperature (C), live SCADA data       |
   +-------------------------------------------------------+
                              |
           +-----------------+------------------+
           |                                    |
           v                                    v
   +----------------------+      +----------------------------+
   | HYBRID RETRIEVAL &   |      |  STATE-BOUND BANDIT ROUTER |
   | FAULT TREES          |      |  - Operator skill tier for |
   | - ChromaDB (dense)   |      |    this specific machine   |
   | - BM25 + RRF (sparse)|      |  - UCB1 picks best format: |
   | - Bayesian Fault Tree|      |    Visual/Terse/Detailed   |
   | - Quarantine: BLOCKED|      |  - Fatigue Gate: if >= 0.8,|
   |   until 3 experts OK |      |    force shortest format   |
   +----------------------+      +----------------------------+
           |                                    |
           | Ranked SOPs & Fix Paths      Winning Format
           +-----------------+------------------+
                              |
                              v
   +-------------------------------------------------------+
   |              WORKING MEMORY SYNTHESIZER               |
   |  - Adds LOTO / High-Voltage / PPE safety rules        |
   |  - Adds live SCADA readings and alarm status          |
   |  - Adds ECM context and supervisor-offline warnings   |
   |  - Warns if operator has failed this alarm before     |
   |  - Adds top fix path and backup fix paths             |
   |  - Enforces the format chosen by the Bandit           |
   +-------------------------------------------------------+
                              |
                              v
   +-------------------------------------------------------+
   |           LLM REASONING AGENT (Google Gemini)         |
   |  Writes a safe, formatted, grounded response          |
   +-------------------------------------------------------+
                              |
                              v
   +-------------------------------------------------------+
   |                   OPERATOR ACTIONS                    |
   |  [Fixed It Myself] [Escalate CMMS] [Change Format]   |
   +-------------------------------------------------------+
                              |
                              v
   +-------------------------------------------------------+
   |        SHADOW OBSERVER -- EVENT LOGGER                |
   |  - Saves event in under 5ms                           |
   |  - Holds reward in escrow for 8 hours                 |
   |  - Queues Micro-Debrief if fix was unusually fast     |
   |  - Sends CMMS ticket if escalated                     |
   +-------------------------------------------------------+

   ============================================================
        ASYNC LOOP (SLEEP CYCLE -- runs at 03:00 AM)
   ============================================================

   +-------------------------------------------------------+
   |     SLEEP CYCLE EVALUATOR (sleep_cycle_evaluator.py)  |
   +-------------------------------------------------------+
    |               |               |               |
    | Escrow Check  | Graph Update  | Fault Trees   | Quarantine
    v               v               v               v
   +----------+ +----------+ +----------+ +----------+
   |Check SCAD| |Update    | |Update    | |3 Expert  |
   |logs for  | |autonomy  | |success / | |votes OK? |
   |recurring | |(+5/-15)  | |fail count| |Promote   |
   |alarms    | |Recalc    | |Recalc    | |with      |
   |>8h: +1/+5| |tier & UCB| |Beta prob | |Expert tag|
   |<8h: -5/-15 |Save disk | |Save disk | |Save disk |
   +----------+ +----------+ +----------+ +----------+


----------------------------------------------------------------------------------------

3. Core Subsystems
==================

3.1 Subsystem 1: Memory -- Five Layers
---------------------------------------

The system uses five types of memory, inspired by how the human brain stores information.

.. list-table:: Memory Layers
   :widths: 18 22 35 25
   :header-rows: 1

   * - Memory Type
     - Technology Used
     - What It Stores
     - When It Is Updated
   * - **Working Memory**
     - In-memory assembler (``working_memory.py``)
     - Short-term context for one query: SCADA data, fatigue state, retrieved SOPs, format directive.
     - Built fresh for every query. Thrown away after.
   * - **Knowledge Graph** (Decoupled)
     - NetworkX directed graph (``semantic_graph.py`` -> ``graph_state.json``)
     - Operator skill per machine (``OPERATES`` edges) and format preferences per skill state (``PREFERS`` edges). These two are kept separate on purpose.
     - Saved as JSON. Updated during the Sleep Cycle.
   * - **Procedural Memory** (Fault Trees)
     - JSON store (``procedural_memory.py`` -> ``procedural_fault_trees.json``)
     - Step-by-step fix paths for each alarm code. Each path tracks how often it succeeded or failed.
     - Saved as JSON. Branch probabilities updated during Sleep Cycle.
   * - **Quarantine SOP Store**
     - JSON store (``quarantine_sops.json``)
     - New shortcuts found by operators. Locked away. Cannot be used until 3 Expert operators approve.
     - Saved as JSON. Checked during Sleep Cycle.
   * - **Episodic Store & Event Queue**
     - Append-only JSON logs (``episodic_store.py`` -> ``episodic_event_queue.json``, ``episodic_logs.json``)
     - Every turn: query, response, format used, CMMS ticket ID, outcome.
     - Queue written in under 5ms. Full log archived during Sleep Cycle.
   * - **Authoritative Grounding Store**
     - ChromaDB (dense) + BM25 (sparse) (``search.py``)
     - Official factory SOPs, machine manuals, hazard levels, error codes.
     - Read-only during operation. Updated offline by engineers.

3.1.1 The Knowledge Graph -- Why It Is Decoupled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The key design rule: **skill on one machine does not equal skill on another machine.**

A CNC expert who has never used an injection molder must be treated as a novice on that
molder. To do this, the graph stores machine skill and format preference as separate,
independent pieces of information.

.. code-block:: text

   [OPERATOR: Sarah] ---- (OPERATES: Haas VF-2, Autonomy=95.0, Tier=Expert) --> [MACHINE: Haas VF-2]
          |
          +-- (OPERATES: Engel 330, Autonomy=15.0, Tier=Novice) --> [MACHINE: Engel 330]
          |
          +-- (STATE_CONFIDENCE) --> [STATE: OP-002:Expert]
          |                                |
          |                                +-- (PREFERS: weight=4.8) --> [FORMAT: Terse_Technical]
          |                                +-- (PREFERS: weight=0.2) --> [FORMAT: Visual_StepByStep]
          |
          +-- (STATE_CONFIDENCE) --> [STATE: OP-002:Novice]
                                           |
                                           +-- (PREFERS: weight=3.9) --> [FORMAT: Visual_StepByStep]
                                           +-- (PREFERS: weight=0.1) --> [FORMAT: Terse_Technical]

* **``OPERATES`` edges** -- connect an operator to a machine. Store the ``autonomy_score``
  (0.0 to 100.0) and the ``derived_tier`` (Novice, Intermediate, or Expert) for that
  specific machine.
* **``STATE`` nodes** -- one node per operator-tier combination (e.g., ``OP-002:Expert``).
  Tracks how that person learns when they are in that skill state.
* **``PREFERS`` edges** -- connect each STATE node to a format. Store UCB statistics:
  total reward weight (W), pull count (N), success count, and escalation count.

3.1.2 Skill Tier Thresholds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The system calculates the operator's tier from their autonomy score for that machine:

.. code-block:: text

   +-----------------------------------------------------------+
   | Autonomy Score >= 75.0        -->  Tier = "Expert"        |
   | 40.0 <= Autonomy Score < 75   -->  Tier = "Intermediate"  |
   | Autonomy Score < 40.0         -->  Tier = "Novice"        |
   +-----------------------------------------------------------+

**LMS Certification Override**: During the overnight Sleep Cycle, the system checks the
factory Learning Management System (LMS). If an operator earns a new offline certification
for a machine, their autonomy score for that machine is immediately set to 85.0 (Expert).
This skips the slow process of learning from telemetry.

3.1.3 Procedural Memory -- Bayesian Fault Trees
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each alarm code has a tree of fix paths. Each path records how many times it worked and
how many times it failed.

Example (Alarm 102 on Haas CNC):

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

**How the probability is calculated** (Beta-Binomial conjugate with Laplace smoothing,
alpha = 1.0, beta = 1.0):

.. code-block:: latex

   P(\text{Success}) = \frac{\text{success\_count} + \alpha}{\text{success\_count} + \text{failure\_count} + \alpha + \beta}

The path with the highest P(Success) is shown as the **Primary Recommended Fix**.
Lower-ranked paths are shown as backups.

----------------------------------------------------------------------------------------

3.2 Subsystem 2: Format Personalization -- Contextual Bandit
--------------------------------------------------------------

3.2.1 State-Bound UCB1 Algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The system does not use fixed rules to pick the response format. Instead, it uses a
**Contextual Bandit** that learns what format each operator prefers in each skill state.
This is an explore-vs-exploit algorithm.

For each operator (u), skill tier (T), and format arm
(i = Visual_StepByStep, Terse_Technical, or Detailed_Text):

.. code-block:: latex

   \text{UCB}_i(u, T) = \bar{X}_i(u, T) + c \cdot \sqrt{\frac{\ln(N(u, T) + 1)}{N_i(u, T) + \epsilon}}

What each symbol means:

* ``\bar{X}_i(u, T) = \frac{W_i(u, T)}{N_i(u, T)}`` -- **Average reward** for format i in state (u, T).
* ``N(u, T)`` -- **Total queries** made in state (u, T) across all formats.
* ``c = 1.2`` -- **Exploration bonus** weight. Higher value = tries new formats more often.
* ``\epsilon = 10^{-4}`` -- Tiny number to prevent dividing by zero for untried formats.

**90-Day Forced Exploration (Time-Decay Rule)**: If an operator has not seen an alternative
format in the last 90 days, the system forces one exploration turn. This checks whether
the operator has improved their skills and might prefer a different format now.

3.2.2 The Three Format Arms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Format Arms
   :widths: 22 33 45
   :header-rows: 1

   * - Format Arm
     - Best For
     - What the LLM Is Told to Produce
   * - **Visual_StepByStep**
     - Novices, visual learners, stressful or complex procedures.
     - Numbered steps. Bold action tags: ``[INSPECT]``, ``[ACTION]``, ``[VERIFY]``, ``[SAFETY]``. Markdown checkboxes ``[ ]``. ASCII flow arrows.
   * - **Terse_Technical**
     - Experienced machinists, urgent situations, experts who want raw data.
     - Maximum 2-3 bullet points or 45 words. No filler text. Raw setpoints, M/G-codes, sensor bits, and direct fixes only.
   * - **Detailed_Text**
     - Training, root-cause analysis, or operators who want to understand the "why."
     - Full explanation of the physical or electrical cause. Sensor thresholds. Multi-stage triage. Preventive maintenance notes.

3.2.3 Environmental Context Matrix (ECM) & Fatigue Gate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ECM service checks the operator's environment on every turn.

* **Fatigue Index formula**:
  ``Fatigue Index = Hours Worked Since Clock-In / Total Scheduled Shift Hours``
* **Fatigue Gate**: If ``Fatigue Index >= 0.80`` (e.g., hour 10 of a 12-hour shift),
  the exploration parameter is forced to ``c = 0.0`` (**100% exploit**). The system stops
  trying new formats and locks to the shortest, most proven format (usually
  ``Terse_Technical``). This protects tired operators from being overwhelmed.
* **Supervisor Gate**: If ``supervisor_available == False``, the Working Memory Synthesizer
  adds a mandatory safety message. It tells the operator to follow strict safety holds and
  not attempt any high-voltage work alone.

3.2.4 Human Format Override (Operator Always Wins)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Operators can override the format at any time. If they do:

1. **Instant re-synthesis**: The system ignores the Bandit for this turn and immediately
   rewrites the response in the chosen format.
2. **Heavy penalty applied**: A penalty of **-10.0** reward weight, +1 pull count, and
   +1 escalation count is applied to the rejected format in the operator's active state.
   The Bandit quickly learns not to use that format again for that operator in that context.

----------------------------------------------------------------------------------------

3.3 Subsystem 3: Finding the Right SOP -- Hybrid Retrieval (ChromaDB + BM25 + RRF)
-------------------------------------------------------------------------------------

Shop floor queries mix everyday language (e.g., *"spindle vibrates during cutting"*) with
exact codes (e.g., *"Haas Alarm 102"*, *"Engel E-201"*, *"M06"*). No single search method
handles both well.

* **Dense Vector Search (ChromaDB + Gemini Embeddings)**: Finds documents with the same
  *meaning*, even if worded differently.
* **Sparse Keyword Search (BM25)**: Guarantees exact matches on alarm codes and M/G-codes.

3.3.1 Reciprocal Rank Fusion (RRF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The two search results are merged using **Reciprocal Rank Fusion (RRF)**. This gives a
combined score to each document:

.. code-block:: latex

   \text{RRF\_Score}(d) = \sum_{m \in \{\text{Dense}, \text{Sparse}\}} \frac{1}{k_{\text{rrf}} + \text{rank}_m(d)}

* ``k_{\text{rrf}} = 60`` -- a smoothing constant (standard value).
* ``\text{rank}_m(d)`` -- where document d ranked in search stream m (1-based).

Machine filters are always active. A query on a Haas CNC machine only returns Haas
procedures. It never mixes in Engel molder procedures.

----------------------------------------------------------------------------------------

3.4 Subsystem 4: Working Memory Synthesizer & LLM (Google Gemini)
------------------------------------------------------------------

The Working Memory Synthesizer builds the full prompt before sending it to the LLM.
The LLM (Google Gemini) only sees this prompt. This keeps it grounded and safe.

**Example prompt structure**:

.. code-block:: text

   ================ MASTER WORKING MEMORY PROMPT ================
   1. ROLE:
      Expert Shopfloor AI Copilot for CNC Milling & Injection Molding.

   2. OPERATOR & MACHINE CONTEXT:
      - Operator: Sarah Jenkins (Tier: Expert | Autonomy: 95.0%)
      - Machine: Haas VF-2
      - Active Alarm: Alarm 102: SERVOS OFF
        (Air Pressure: 64.2 PSI | Nominal: >85 PSI)
      - Environment: Shift Hour 3/8 | Fatigue Index: 0.38 | Supervisor: Online

   3. HISTORY WARNINGS (from Episodic Memory):
      - Operator has 2 prior escalations for Alarm 102.
        Acknowledge past difficulty.
        Offer early CMMS dispatch if first checks fail.

   4. MANDATORY SAFETY RULES:
      - Lock-Out / Tag-Out (LOTO) before opening the rear electrical enclosure.
      - Eye protection and pneumatic pressure discharge required.

   5. RETRIEVED SOPs & FAULT TREE PATHS:
      - [Primary Fix (P=0.93)]: Adjust Main Air Regulator on Rear Panel.
      - [Backup Fix (P=0.40)]: Inspect Pre-Charge Solenoid Valve Wiring.
      - Official SOP source: SOP-HAAS-001.

   6. FORMAT DIRECTIVE (Bandit Winner):
      - Terse & Technical only. Max 2-3 bullets, <= 45 words, raw setpoints.

   7. GROUNDING RULE:
      - Only use the retrieved SOPs above. Do not invent any steps.
   ==============================================================

----------------------------------------------------------------------------------------

3.5 Subsystem 5: Shadow Observer, Feedback Loop & 8-Hour Escrow
----------------------------------------------------------------

3.5.1 Sub-100ms Event Logger
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After each operator interaction, the ``ShadowObserver`` runs in **under 5ms** (always
under 100ms). It does three things:

1. Builds an event record: ``session_id``, ``operator_id``, ``machine_id``,
   ``format_used``, ``cognitive_tier``, ``outcome_status`` (``SUCCESS``,
   ``ESCALATED_CMMS``, ``ABANDONED_TIMEOUT``, or ``FORMAT_OVERRIDE``), and a timestamp.
2. Appends the record to ``data/episodic_event_queue.json``.
3. Does **no** graph updates during the shift. This keeps the UI fast and prevents
   mid-shift data drift.

3.5.2 8-Hour Wait Rule (Provisional Reward Escrow)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This rule stops the AI from rewarding bad fixes that break again hours later
(the "Duct-Tape Problem").

* **Hold the reward**: When an operator marks an issue as resolved, the reward goes into
  ``data/escrow_rewards.json`` and waits for 8 hours.
* **Overnight check (Sleep Cycle)**:

  * The system reads SCADA logs to see if the same alarm came back within 8 hours.
  * **Durable fix (no recurrence after 8 hours)**: Release the reward: **+1.0** to
    bandit weight, **+5.0** to machine autonomy.
  * **Duct-tape fix (alarm came back within 8 hours)**: Flip the reward to a penalty:
    **-5.0** to bandit weight and **-15.0** to machine autonomy.

3.5.3 All Feedback Pathways
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Feedback Events & What Happens
   :widths: 20 25 30 25
   :header-rows: 1

   * - What Happened
     - Who or What Triggered It
     - Immediate Action (under 5ms)
     - Sleep Cycle Action
   * - **Fixed Independently**
     - Operator clicks *"Solved Independently"*.
     - Saves ``SUCCESS`` event; puts reward in escrow; starts SCADA check.
     - If clean after 8h: give **+1.0** bandit reward and **+5.0** autonomy. Update fault tree.
   * - **Escalated to Supervisor**
     - Operator clicks *"Escalate to Supervisor"*.
     - Saves ``ESCALATED_CMMS`` event; sends CMMS work order automatically.
     - Deduct **-1.0** bandit penalty and **-15.0** autonomy. Update fault tree failure count. Recalculate tier.
   * - **Format Override**
     - Operator clicks a format override button.
     - Bypass bandit; rewrite response instantly in the chosen format.
     - Apply **-10.0** penalty to the rejected format arm in the knowledge graph.
   * - **Session Abandoned**
     - Session times out with no resolution.
     - Saves ``ABANDONED_TIMEOUT`` event.
     - Log as failure. Increment fault tree failure count. Keep for audit history.

----------------------------------------------------------------------------------------

3.6 Subsystem 6: Micro-Debrief & Quarantine Store
--------------------------------------------------

3.6.1 The Micro-Debrief -- Asking the Operator What They Did
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an operator solves a complex alarm much faster than normal (e.g., a 15-minute job
done in 2 minutes), the system does not guess. It asks.

1. **Detection**: The Shadow Observer notices the unusual speed and saves a pending
   debrief in ``data/pending_debriefs.json``.
2. **Next-session prompt**: At the start of the operator's next session, the assistant asks:
   *"Earlier you resolved Alarm 102 in ~2.0 min. Did you use the 'Regulator Pre-Charge Shortcut'? (Yes/No)"*
3. **Two outcomes**:

   * **Yes** -- The new procedure is saved in ``data/quarantine_sops.json`` with this
     operator's validation attached.
   * **No** -- The record is discarded. Nothing is changed in the knowledge base.

3.6.2 3-Expert Consensus Auto-Promotion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* New shortcuts stay in the Quarantine Store. General operators cannot see them.
* When **3 different Expert operators** (those with ``derived_tier == 'Expert'``) each
  confirm the same shortcut during their own micro-debriefs, the Sleep Cycle evaluator
  moves it to the active ``data/procedural_fault_trees.json`` database.
* The promoted procedure gets a permanent tag: ``min_tier_required: 'Expert'``. This
  guarantees that novice operators are never shown an unvetted shortcut.

----------------------------------------------------------------------------------------

3.7 Subsystem 7: Mock Services for Testing
-------------------------------------------

These four services simulate real factory systems so the whole system can be tested
without real machines.

1. **SCADA Mock (``MockSCADA``)**: Simulates live sensor readings (air pressure PSI,
   spindle RPM, temperature C, hydraulic bar, clamping force kN, E-stop states).
   Generates machine alarms. Provides a ``verify_repair()`` method.
2. **CMMS Mock (``MockCMMS``)**: Simulates work-order management. Generates ticket IDs
   (e.g., ``TICK-2026-A83B``). Assigns maintenance tiers. Logs resolution history.
3. **HR / LMS Mock (``MockHRLMS``)**: Stores employee records, tenure, shift assignments,
   and cold-start qualification baselines.
4. **Environmental Context Mock (``MockECM``)**: Calculates shift hours elapsed, fatigue
   index, supervisor presence, noise level, and ambient temperature.


----------------------------------------------------------------------------------------

4. Architecture Q&A Reference
==============================

Quick answers to common design questions. See Section 3 for full details.

.. list-table:: Design Questions & Answers
   :widths: 30 35 35
   :header-rows: 1

   * - Question
     - Short Answer
     - See Section
   * - **What behaviors does the system learn?**
     - Format preference per skill state, machine-specific skill, escalation habits, fast-fix shortcuts, fatigue patterns.
     - 3.1 (Graph), 3.2 (Bandit), 3.6 (Debrief)
   * - **What data sources does it use?**
     - SCADA telemetry, Engineering SOPs, Bayesian fault trees, HR/LMS records, CMMS ledger, ECM context.
     - 3.3 (Retrieval), 3.4 (Working Memory), 3.7 (Mock Services)
   * - **What components are needed?**
     - Chat agent, Bandit Router, Shadow Observer, Working Memory Synthesizer, Hybrid Retriever, Knowledge Graph, Procedural Memory, Sleep Cycle Evaluator.
     - Section 3 (all subsections)
   * - **How does it learn over time?**
     - UCB bandit accumulates rewards. Autonomy scores change (+5 / -15). Beta-Binomial updates branch probabilities.
     - 3.2.1, 3.5.2, 3.1.3
   * - **How is memory stored and corrected?**
     - JSON files (graph, fault trees, escrow, debriefs, episodic queue). All heavy updates happen in the Sleep Cycle.
     - 3.5 (Escrow), 3.1 (Graph)
   * - **How does it avoid wrong assumptions?**
     - 7 safeguards: decoupled skill graph, cold-start seeding, UCB exploration, asymmetric penalties, escrow durability, SCADA verification, micro-debriefs.
     - 3.2.4, 3.5.2, 3.6, Section 5 (FMEA)
   * - **How is the operator profile used?**
     - 5 layers: response format, fix-path ranking, safety detail depth, historical failure warnings, fatigue and supervisor adaptation.
     - 3.2, 3.1.3, 3.5.3, 3.4

----------------------------------------------------------------------------------------

5. Safety Rules & Failure Mode Table (FMEA)
============================================

.. list-table:: Failure Modes & How the System Prevents Them
   :widths: 22 38 40
   :header-rows: 1

   * - Failure Mode
     - Risk
     - How the System Prevents It
   * - **1. Duct-Tape Fix**
     - Operator uses a temporary patch. Alarm clears. Machine fails again 2 hours later. AI already gave credit.
     - **8-Hour Escrow**: Reward is held. If SCADA shows the alarm came back, the reward flips to a **-5.0** bandit penalty and **-15.0** autonomy deduction.
   * - **2. Unvetted Shortcut Spread**
     - Operator finds an unsafe shortcut. AI suggests it to novices. Someone gets hurt or warranty is voided.
     - **Quarantine Store + 3-Expert Vote**: New shortcuts are locked in ``quarantine_sops.json``. They need 3 Expert confirmations before going live, and are permanently tagged ``min_tier_required: 'Expert'``.
   * - **3. Wrong Format in Emergency**
     - The Bandit shows visual steps during a crisis. The expert just needs raw setpoints now.
     - **Instant Format Override**: Operator switches format. Response is rewritten immediately. The rejected format gets a **-10.0** penalty in the knowledge graph.
   * - **4. Novice Promoted Too Fast**
     - Novice gets lucky on 2 easy fixes. AI promotes to Intermediate and removes safety checks.
     - **Asymmetric Penalties + Tenure Floors**: Gaining skill gives only +5.0 autonomy; a failure costs -15.0. A minimum number of interactions is required before any tier change.
   * - **5. AI Repeats Failed Steps**
     - Operator has struggled with the same alarm many times. AI keeps suggesting the same fix.
     - **Episodic Memory Injection**: Past escalations are injected into working memory. The LLM is told to offer early CMMS dispatch and acknowledge the difficulty.
   * - **6. End-of-Shift Cognitive Overload**
     - Tired operator gets a complex, multi-step response near the end of a 12-hour shift.
     - **ECM Fatigue Gate**: When ``Fatigue Index >= 0.80``, the exploration parameter is forced to ``c = 0.0``. Only the shortest, most proven format is used.
   * - **7. AI Invents Steps (Hallucination)**
     - LLM makes up troubleshooting steps or skips LOTO safety rules.
     - **Hardcoded Safety Injection + Hybrid RRF Grounding**: Safety headers (LOTO, PPE) are always added before the LLM generates anything. The LLM is restricted to the retrieved SOPs only.

----------------------------------------------------------------------------------------

6. Pilot Validation Plan
=========================

6.1 What We Are Testing
------------------------

* **Hypothesis H1**: Operators using the AI will achieve at least a **25% reduction in
  Mean Time to Repair (MTTR)** compared to static paper manuals.
* **Hypothesis H2**: The State-Bound Contextual Bandit will learn each operator's preferred
  format within **5-8 interactions** per skill state.
* **Hypothesis H3**: The Bayesian Fault Trees and 3-Expert Consensus Engine will pick the
  correct root-cause fix at least **95% of the time**, with **0% leakage** of unvetted
  shortcuts to novice operators.

6.2 Key Metrics
---------------

.. list-table:: Pilot Metrics
   :widths: 22 38 40
   :header-rows: 1

   * - Category
     - What We Measure
     - How & Target
   * - **Efficiency**
     - Mean Time to Repair (MTTR)
     - Time from alarm trigger to SCADA normalization. Target: **>= 25% reduction**.
   * - **Autonomy**
     - Independent Resolution Rate
     - Ratio of durable ``SUCCESS`` sessions to total sessions. Target: **>= 70%** for standard alarms.
   * - **Learning Speed**
     - Bandit Convergence Speed
     - Turns needed for the winning format UCB score to stay **>= 0.5** above competitors. Target: **<= 8 turns**.
   * - **Safety**
     - Hallucination Rate
     - Engineering audit of LLM responses vs. source SOPs. Target: **0.0%** ungrounded steps.
   * - **Fix Quality**
     - 8-Hour Recurrence Rate
     - Percentage of resolved alarms that come back within 8 hours. Target: **< 5.0%**.
   * - **Usability**
     - Cognitive Load
     - NASA-TLX score and System Usability Scale (SUS) after shift. Target: **SUS >= 80**.

6.3 How We Verify the Behavioral Profile
-----------------------------------------

1. **Correlation Check**: Compare the AI's learned autonomy scores to quarterly supervisor
   performance reviews. Do they agree?
2. **Blind A/B Test**: Occasionally serve a non-preferred format. Measure whether task
   completion time goes up.
3. **Drift Detection**: Watch autonomy score moving averages. Flag operators whose skills
   drop, or machines that need new training data.

----------------------------------------------------------------------------------------

7. Example Scenarios
=====================

7.1 Scenario 1: Novice Operator -- Haas CNC, Alarm 102 (Servos Off)
--------------------------------------------------------------------

1. **Operator**: John Doe (``OP-001``), Novice Tier (Autonomy: 35.0%), Shift Hour 2 of 8.
2. **Alarm**: Haas VF-2 fires ``Alarm 102: SERVOS OFF``. SCADA shows air pressure at
   64.2 PSI (nominal is > 85 PSI).
3. **Retrieval**: Hybrid RRF finds ``SOP-HAAS-001``. Fault tree ranks
   ``HAAS_102_REGULATOR`` (P=0.93) as the Primary Fix.
4. **Bandit**: Evaluates state ``(OP-001, Novice)``. Selects ``Visual_StepByStep``
   (highest UCB score).
5. **LLM Response**: Gemini outputs numbered steps with ``[SAFETY]``, ``[INSPECT]``, and
   ``[ACTION]`` tags. Tells John to adjust the rear panel regulator.
6. **Outcome**: John adjusts the regulator to 90 PSI. Clicks *"Solved Independently"*.
7. **Shadow Observer**:

   * Saves ``SUCCESS`` event to ``episodic_event_queue.json`` in under 5ms.
   * Puts +1.0 bandit reward and +5.0 autonomy into ``escrow_rewards.json`` (8-hour hold).
   * SCADA confirms pressure normalized to 92 PSI.

7.2 Scenario 2: Expert on Haas, Treated as Novice on Engel (Decoupled States)
-------------------------------------------------------------------------------

1. **Operator**: Sarah Jenkins (``OP-002``). Expert on Haas VF-2 (Autonomy: 95.0%).
   Newly assigned to Engel Injection Molder (Autonomy: 15.0%, Tier: Novice).
2. **Alarm**: Engel Victory 330 fires ``E-201: BARREL OVERHEAT``.
3. **State-Bound Routing**:

   * System detects the machine is an Engel Victory 330.
   * Reads Sarah's Engel-specific tier: **Novice**.
   * Queries state ``(OP-002, Novice)`` in the knowledge graph.
   * Bandit selects ``Visual_StepByStep`` -- not Terse_Technical. Sarah gets full visual
     steps for thermocouple inspection, matching her novice status on this specific machine.

7.3 Scenario 3: High Fatigue, Night Shift, Supervisor Offline
--------------------------------------------------------------

1. **Operator**: Mike Chang (``OP-003``), Intermediate Tier, Shift Hour 11 of 12
   (Fatigue Index: 0.92). Supervisor is offline.
2. **Alarm**: Spindle vibration alarm on Haas VF-2.
3. **ECM Gating**:

   * Fatigue Index = 0.92 >= 0.80 -- **Fatigue Gate fires**. Exploration set to
     ``c = 0.0`` (100% exploit). Bandit selects ``Terse_Technical``.
   * Supervisor is offline -- **Supervisor Gate fires**. Working Memory Synthesizer adds
     a mandatory safety hold. Mike is told not to open any enclosure alone.
4. **LLM Response**: Short, concise external checks only. Tells Mike to stop the spindle
   if vibration continues.

7.4 Scenario 4: Fast Fix -- Micro-Debrief Loop
-----------------------------------------------

1. **Event**: Sarah resolves a complex hydraulic alarm in 1.8 minutes. OEM standard
   time is 12 minutes.
2. **Debrief Enqueue**: Shadow Observer detects the unusual speed. Saves a record in
   ``data/pending_debriefs.json``.
3. **Next Session**: When Sarah logs in for her next shift, the assistant asks:
   *"Earlier you resolved Alarm 304 in 1.8 min. Did you use the 'Manifold Bypass Bleed' shortcut? (Yes/No)"*
4. **Outcome**: Sarah clicks *"Yes"*. The procedure is saved in
   ``data/quarantine_sops.json`` with Sarah's Expert validation attached.

7.5 Scenario 5: Overnight Sleep Cycle
--------------------------------------

1. **Trigger**: At 03:00 AM, ``sleep_cycle_evaluator.py`` runs.
2. **Escrow Audit**:

   * Checks John Doe's Alarm 102 fix from Scenario 1. SCADA shows 0 recurring alarms
     in 8 hours. Releases **+1.0** bandit reward and **+5.0** autonomy to John's profile.
   * Checks another operator's quick fix. SCADA shows the alarm came back after 2 hours.
     Flips the reward to a **-5.0** bandit penalty and **-15.0** autonomy deduction.
3. **Knowledge Graph Update**: Updates all operator-machine autonomy scores, recalculates
   derived tiers, and updates UCB weights in ``data/graph_state.json``.
4. **Fault Tree Update**: Updates branch success and failure counts in
   ``data/procedural_fault_trees.json``.
5. **Consensus Check**: Finds a quarantined SOP with 3 Expert validations. Promotes it
   to the active procedural library with ``min_tier_required: 'Expert'``.
6. **Queue Flush**: Archives processed events. Clears ``data/episodic_event_queue.json``.

----------------------------------------------------------------------------------------

8. Codebase Structure
======================

For a full module-by-module and class-by-class breakdown, see
`code_and_modules_guide.rst <code_and_modules_guide.rst>`_.
For setup and run commands, see
`run_and_configuration_guide.rst <run_and_configuration_guide.rst>`_.

.. code-block:: text

   factory-agent-app/
   ├── app.py                          # Streamlit UI & Shopfloor Dashboard
   ├── sleep_cycle_evaluator.py        # Async Sleep Cycle Evaluator & Escrow Engine
   ├── verify_refactor.py              # Tests: Cognitive Decoupling & Queues
   ├── verify_section2.py              # Tests: Escrow, Quarantine & Overrides
   ├── verify_section3.py              # Tests: ECM, Fatigue & Micro-Debriefs
   ├── agents/
   │   ├── bandit_router.py            # UCB1 Bandit: picks format per operator state
   │   ├── chat_agent.py               # Main chat agent orchestrator
   │   ├── shadow_observer.py          # Event logger & escrow manager
   │   └── working_memory.py           # Builds the full LLM prompt
   ├── memory/
   │   ├── semantic_graph.py           # Knowledge Graph: operator-machine-format edges
   │   ├── procedural_memory.py        # Fault Trees: fix paths with success/failure counts
   │   ├── episodic_store.py           # Event queue & audit log writer
   │   └── search.py                   # Hybrid retrieval: ChromaDB + BM25 + RRF
   ├── services/
   │   ├── scada_service.py            # Mock SCADA: sensor stream & repair check
   │   ├── ecm_service.py              # Mock ECM: fatigue index, supervisor, noise
   │   ├── cmms_service.py             # Mock CMMS: work orders & ticket lifecycle
   │   └── hr_lms_service.py           # Mock HR/LMS: rosters, roles & cold-start data
   └── data/
       ├── factory_knowledge_base.json # Official SOPs (read-only at runtime)
       ├── procedural_fault_trees.json # Active Bayesian Fault Trees
       ├── quarantine_sops.json        # Locked shortcuts (awaiting 3-Expert vote)
       ├── escrow_rewards.json         # Reward Escrow Ledger (8-hour hold)
       ├── pending_debriefs.json       # Queued Micro-Debrief prompts
       ├── episodic_event_queue.json   # Shift Event Queue (written in under 5ms)
       ├── episodic_logs.json          # Permanent audit log
       └── graph_state.json            # Knowledge Graph saved state

----------------------------------------------------------------------------------------

9. Conclusion
==============

This system replaces static factory manuals with a smart, self-improving AI assistant.

It combines seven core technologies:

* **Decoupled Knowledge Graph** -- tracks skill per machine, not per person globally.
* **State-Bound Contextual Bandits (UCB1)** -- learns the best response format for each
  operator in each skill state.
* **Dynamic Bayesian Fault Trees** -- ranks fix paths by real success probability.
* **8-Hour Provisional Reward Escrow** -- only rewards fixes that actually last.
* **3-Expert Quarantine Consensus** -- safely adds new shortcuts after expert verification.
* **ECM Fatigue Gating** -- protects tired operators from complex outputs.
* **Sub-100ms Synchronous Event Logging** -- keeps the UI fast by deferring all heavy
  updates to the Sleep Cycle.

Together, these deliver personalized, safety-compliant, and continuously improving guidance
for high-stakes smart manufacturing environments.
