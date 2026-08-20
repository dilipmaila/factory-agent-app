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

1.2 The Core Problem with Static AI Assistants
----------------------------------------------
Traditional conversational assistants or static retrieval systems fail in industrial settings
because they treat every operator identically and assume a single conversational context. A
static AI either overwhelms a novice with dense technical jargon or frustrates an expert with
remedial step-by-step instructions.

Furthermore, an operator's true competencies, habits, and preferences **cannot be reliably
captured from a single intake interview or static role title**. They must be dynamically
inferred, tracked, and validated over repeated shopfloor interactions and operational telemetry.

1.3 Solution Mission Statement
------------------------------
This solution designs an **Adaptive Cognitive AI Assistant** that:

1. **Passively Infers Behavioral Patterns**: Tracks preferred instruction presentation
   formats, machine-specific autonomy, and escalation tendencies across repeated shifts.
2. **Maintains Multi-Tiered Memory**: Integrates short-term working context, long-term
   semantic knowledge graphs (tracking competency and preferences), episodic interaction
   logs, and grounded factory SOP repositories.
3. **Optimizes Personalization via Contextual Bandits**: Formulates format personalization
   as an exploration-exploitation problem using the Upper Confidence Bound (UCB) algorithm.
4. **Enforces Closed-Loop Shopfloor Feedback**: Couples operator actions with real-time SCADA
   telemetry verification and CMMS escalation ticketing.
5. **Guarantees Industrial Safety & Zero Hallucination**: Employs Hybrid Reciprocal Rank Fusion
   (RRF) retrieval to ground all responses strictly in authoritative factory manuals.

----------------------------------------------------------------------------------------

2. High-Level Solution Architecture & Conceptual Flow
=====================================================

The system operates across two interlinked operational loops:

1. **The Real-Time Interaction & Personalization Loop (Synchronous)**: Handles operator queries,
   retrieves authoritative SOPs, selects the optimal presentation style via contextual bandits,
   assembles working memory with safety directives, and synthesizes grounded LLM guidance.
2. **The Shadow Observation & Closed-Loop Learning Loop (Asynchronous / Continuous)**: Evaluates
   troubleshooting outcomes, updates the operator's semantic knowledge graph, adjusts bandit
   exploration-exploitation weights, validates machine telemetry via SCADA, and logs audit
   traces into episodic memory.

2.1 End-to-End System Flowchart
-------------------------------

.. code-block:: text

   +-----------------------------------------------------------------------------------+
   |                              SHOPFLOOR OPERATOR                                   |
   |              (Selects Machine, Interacts with AI Assistant on HMI/Tablet)          |
   +-----------------------------------------------------------------------------------+
                                            |
                                            | 1. Query / Alarm Trouble (e.g. "Alarm 102")
                                            v
   +-----------------------------------------------------------------------------------+
   |                                 SHOPFLOOR HUB                                     |
   |  +---------------------------+             +-----------------------------------+  |
   |  |   SCADA Telemetry Stream  |             |      HR / LMS Baseline Roster     |  |
   |  | (Live Pressures, Sensors) |             | (Cold-Start Tiers & Shift Profile)|  |
   |  +---------------------------+             +-----------------------------------+  |
   +-----------------------------------------------------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                                                     |
         v                                                                     v
   +---------------------------------------+                 +---------------------------------+
   |      HYBRID RETRIEVAL ENGINE          |                 |     CONTEXTUAL BANDIT ROUTER    |
   | - Dense Semantic Search (ChromaDB)    |                 | - Upper Confidence Bound (UCB)  |
   | - Sparse Keyword Search (BM25)        |                 | - Multi-Armed Policy:           |
   | - Reciprocal Rank Fusion (RRF Scoring)|                 |   * Visual Step-by-Step         |
   | - Machine & SOP Filtering             |                 |   * Terse Technical             |
   |                                       |                 |   * Detailed Comprehensive      |
   +---------------------------------------+                 +---------------------------------+
         |                                                                     |
         | Retrieved SOP Excerpts                                              | Winning Format Directive
         +----------------------------------+----------------------------------+
                                            |
                                            v
   +-----------------------------------------------------------------------------------+
   |                             WORKING MEMORY SYNTHESIZER                            |
   |  - Injects Mandatory Shopfloor Safety Directives (LOTO, PPE, High-Voltage Rules)  |
   |  - Injects Active SCADA Telemetry & Alarm Status                                  |
   |  - Injects Operator Profile & Current Machine Autonomy Score                      |
   |  - Enforces Contextual Bandit Format Directives & Grounding Rules                 |
   +-----------------------------------------------------------------------------------+
                                            |
                                            | Complete Grounded Prompt
                                            v
   +-----------------------------------------------------------------------------------+
   |                        LLM REASONING AGENT (Google Gemini)                        |
   |         Synthesizes safety-compliant, formatted, grounded troubleshooting text    |
   +-----------------------------------------------------------------------------------+
                                            |
                                            | Formatted Response Delivered to Operator
                                            v
   +-----------------------------------------------------------------------------------+
   |                      CLOSED-LOOP RESOLUTION / FEEDBACK ACTION                     |
   |                                                                                   |
   |       [OPTION A: Independent Success]             [OPTION B: Supervisor Escalation]
   +-----------------------------------------------------------------------------------+
             |                                                       |
             +---------------------------+---------------------------+
                                         |
                                         v
   +-----------------------------------------------------------------------------------+
   |                             SHADOW OBSERVER AGENT                                 |
   |                      (Autonomous Behavioral Evaluator)                            |
   +-----------------------------------------------------------------------------------+
             |                                                       |
             | If Solved Independently:                              | If Escalated:
             | * Bandit Reward: +1.0                                 | * Bandit Reward: -1.0
             | * Autonomy Score: +5.0 points                         | * Autonomy Score: -15.0 points
             | * SCADA: Telemetry Verification Check                 | * CMMS: Auto-Dispatch Work Order
             |                                                       | * Tier Transition Recalculation
             v                                                       v
   +---------------------------------------+                 +---------------------------------+
   |      SEMANTIC KNOWLEDGE GRAPH         |                 |        EPISODIC AUDIT LOG       |
   |  - NetworkX Directed Graph Persistence|                 |  - Append-Only Turn History     |
   |  - Operator Node (Tier, Name, ID)     |                 |  - Query, Response, Format Used |
   |  - Machine Edge (Autonomy & Solves)   |                 |  - Resolution State & Ticket ID |
   |  - Format Edge (Weights & Pull Counts)|                 |  - Traceability & Audit Logs    |
   +---------------------------------------+                 +---------------------------------+

----------------------------------------------------------------------------------------

3. Core Solution Components & Detailed Breakdown
================================================

3.1 Component 1: Multi-Tier Cognitive Memory Architecture
----------------------------------------------------------
Human memory consists of short-term sensory/working buffers, episodic event histories, and
long-term semantic structures. The assistant mirrors this architecture using four specialized
memory tiers:

.. list-table:: Multi-Tier Cognitive Memory System
   :widths: 20 25 30 25
   :header-rows: 1

   * - Memory Tier
     - Underlying Technology
     - Role & Scope
     - Persistence & Update Cadence
   * - **Working Memory**
     - Dynamic In-Memory Assembler
     - Short-term context assembly combining telemetry, retrieved SOPs, safety directives, and bandit formatting.
     - Per-query lifespan; ephemeral.
   * - **Semantic Knowledge Graph**
     - Directed NetworkX Graph (JSON-persisted)
     - Long-term cognitive representation of operator competencies, machine-specific autonomy, and format weights.
     - Persistent; updated after every resolution feedback turn.
   * - **Episodic Memory**
     - Append-Only JSON Log Store
     - Historical event ledger tracking chronological interaction episodes, queries, responses, format arms, and CMMS tickets.
     - Persistent audit trail for compliance, traceability, and offline analysis.
   * - **Authoritative Grounding Store**
     - ChromaDB (Dense) + BM25 (Sparse)
     - Fact-grounding repository containing curated factory SOPs, machine operating manuals, hazard levels, and error codes.
     - Read-only at runtime; updated during offline engineering ingestion.

3.1.1 The Semantic Knowledge Graph Topology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The knowledge graph uses a directed graph structure ($G = (V, E)$) to represent relationships
between operators, shopfloor equipment, and cognitive format arms:

* **Nodes ($V$)**:
  * `OPERATOR:<ID>`: Attributes include `operator_id`, `name`, and dynamic `tier` (`Novice`, `Intermediate`, `Expert`).
  * `MACHINE:<ID>`: Attributes include `machine_id` (e.g., `Haas VF-2`, `Engel Victory 330`).
  * `FORMAT:<Arm>`: Attributes include `arm_name` (`Visual_StepByStep`, `Terse_Technical`, `Detailed_Text`).
* **Edges ($E$)**:
  * `OPERATES (Operator -> Machine)`: Tracks machine-specific `autonomy_score` (0.0 to 100.0), `success_count`, and `escalation_count`.
  * `PREFERS (Operator -> Format)`: Tracks cumulative bandit `weight`, `pull_count`, `success_count`, and `escalation_count`.

3.1.2 Dynamic Operator Skill Tier Thresholding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An operator's overall skill tier is not hardcoded; it is computed dynamically by averaging their
autonomy scores across all assigned machines:

.. code-block:: text

   Average Autonomy Score (A_avg) = Sum(Machine Autonomy Scores) / Total Machines

   +-------------------------------------------------------------------+
   | A_avg >= 75.0          --> Tier = "Expert"                        |
   | 40.0 <= A_avg < 75.0   --> Tier = "Intermediate"                  |
   | A_avg < 40.0           --> Tier = "Novice"                        |
   +-------------------------------------------------------------------+

This ensures that as an operator gains experience and successfully resolves issues without
escalation, their profile smoothly transitions from Novice to Expert. Conversely, repeated
escalations appropriately lower the autonomy score and tier.

---

3.2 Component 2: Contextual Multi-Armed Bandit Personalization Engine
---------------------------------------------------------------------

3.2.1 Why Multi-Armed Bandits instead of Static Classification?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If the system used a static rule (e.g., "Novices always receive Visual, Experts always receive
Terse"), it would create significant failure modes:

1. **Misclassification Trap**: An operator classified as Novice might already possess deep
   electro-mechanical expertise and become frustrated by verbose step-by-step checklists.
2. **Cognitive Stagnation**: As an operator masters a machine, their preferred learning style
   shifts. Static systems cannot detect this transition.
3. **Exploration vs. Exploitation Dilemma**: The system must exploit formats that have
   proven successful, but must periodically explore alternative presentation styles to verify
   if another format improves resolution speed.

3.2.2 Mathematical Formulation of the Upper Confidence Bound (UCB)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Contextual Bandit router implements the **UCB1 Algorithm**. For each operator $u$ and
presentation arm $i \in \{\text{Visual\_StepByStep}, \text{Terse\_Technical}, \text{Detailed\_Text}\}$:

.. math::

   UCB_i(u) = \bar{X}_i(u) + c \cdot \sqrt{\frac{\ln(N(u) + 1)}{N_i(u) + \epsilon}}

Where:

* $\bar{X}_i(u) = \frac{W_i(u)}{N_i(u)}$ represents the **Empirical Mean Reward** for arm $i$
  (exploitative component, where $W_i$ is cumulative reward and $N_i$ is pull count).
* $N(u) = \sum_{j} N_j(u)$ represents the **Total Interaction Pulls** across all arms for operator $u$.
* $c = 1.2$ is the **Exploration Hyperparameter**, determining the weight given to uncertainty.
* $\sqrt{\frac{\ln(N + 1)}{N_i + \epsilon}}$ represents the **Uncertainty / Exploration Bonus**.
  Arms that have rarely been tried have a small $N_i$, producing a high exploration bonus that
  forces the system to test them.

3.2.3 Description of Bandit Presentation Arms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Bandit Presentation Arms & Cognitive Objectives
   :widths: 25 35 40
   :header-rows: 1

   * - Bandit Arm
     - Target Persona & Context
     - Structural Directive Injected into Prompt
   * - **Visual_StepByStep**
     - Visual learners, novice operators, high-stress complex procedures.
     - Sequential numbered steps, bold visual tags (`[INSPECT]`, `[ACTION]`, `[VERIFY]`, `[SAFETY]`), markdown checklists `[ ]`, and ASCII flow arrows.
   * - **Terse_Technical**
     - Expert machinists, seasoned technicians, rapid production triage.
     - Maximum 2-3 bullet points or under 45 words. Zero greetings, zero pleasantries. Raw technical setpoints, M/G-codes, and direct corrective actions only.
   * - **Detailed_Text**
     - In-depth training, deep conceptual learners, root-cause investigation.
     - Comprehensive tutorial detailing the underlying physical/electrical root cause, sensor operating principles, corrective sequence, and preventive maintenance.

---

3.3 Component 3: Hybrid SOP Retrieval Engine (ChromaDB + BM25 + RRF)
--------------------------------------------------------------------
Industrial troubleshooting queries often contain a mix of natural language symptoms (e.g.,
*"machine stops moving when cutting"*) and strict technical alphanumeric identifiers (e.g.,
*"Alarm 102"*, *"M06"*, *"G83"*, *"Zone 2 Overheat"*).

* **Dense Vector Search (ChromaDB + Gemini Embeddings)**: Excels at capturing semantic concepts,
  synonyms, and broad intent, but can dilute exact keyword matches for specific error codes.
* **Sparse Keyword Search (BM25)**: Excels at exact alphanumeric token matching (e.g., exact
  fault code `"Alarm 102"`), but fails when operators describe symptoms in colloquial terms.

3.3.1 Reciprocal Rank Fusion (RRF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To achieve optimal retrieval precision, the system fuses both ranking streams using
**Reciprocal Rank Fusion (RRF)**:

.. math::

   RRF\_Score(d) = \sum_{m \in \{\text{Dense}, \text{Sparse}\}} \frac{1}{k_{rrf} + \text{rank}_m(d)}

Where $k_{rrf} = 60$ is the standard smoothing constant, and $\text{rank}_m(d)$ is the 1-based
rank of document $d$ in retrieval stream $m$.

In addition, metadata filtering is applied to ensure that queries initiated for a Haas CNC
machine prioritize Haas-specific SOPs and do not retrieve injection molding procedures.

---

3.4 Component 4: Working Memory Synthesizer & LLM Reasoning Agent
-----------------------------------------------------------------
The LLM (Google Gemini Flash Lite) is never prompted in an unconstrained manner. The
**Working Memory Synthesizer** dynamically constructs a structured multi-section prompt that
enforces industrial grounding and safety guardrails:

.. code-block:: text

   ========================= MASTER WORKING MEMORY PROMPT =========================
   1. SYSTEM IDENTITY & ROLE:
      Expert Shopfloor AI Copilot for CNC Milling & Injection Molding Equipment.

   2. CURRENT OPERATOR & TELEMETRY CONTEXT:
      - Operator: Sarah Jenkins (Tier: Expert | Autonomy Score: 88.0%)
      - Target Machine: Haas VF-2
      - Active SCADA Alarm: Alarm 102: SERVOS OFF (Air Pressure: 68.5 PSI)

   3. MANDATORY SAFETY PROTOCOLS:
      - Lock-Out / Tag-Out (LOTO) mandatory before electrical enclosure access.
      - PPE and high-pressure pneumatic hazard notices.

   4. AUTHORITATIVE GROUNDING SOURCES (Retrieved SOPs):
      - [Source 1: SOP-HAAS-001 | Machine: Haas VF-2 | Hazard: Standard]
        Resolution steps, required checks, prohibited actions.

   5. REQUIRED OUTPUT FORMATTING DIRECTIVE (Bandit Winner):
      - Injected formatting directive (e.g., Strictly Terse & Technical).

   6. STRICT GROUNDING CONSTRAINTS:
      - Zero Hallucination: Rely exclusively on retrieved sources.
      - Highlight hazards prior to physical actions.
   ================================================================================

---

3.5 Component 5: Shadow Observer & Closed-Loop Feedback Evaluator
-----------------------------------------------------------------
The **Shadow Observer** is an autonomous background evaluator that monitors the outcome of each
assistance turn. When an operator finishes interacting, two primary feedback pathways occur:

.. list-table:: Feedback Pathways & System Adjustments
   :widths: 20 40 40
   :header-rows: 1

   * - Event Type
     - Operator Action
     - System Adaptations Executed
   * - **Independent Resolution**
     - Operator clicks *"Solved Independently"*.
     - 1. **Bandit Reward**: $+1.0$ applied to the active format arm.
       2. **Autonomy Adjustment**: $+5.0$ points added to machine autonomy.
       3. **SCADA Telemetry Check**: System simulates/queries sensor verification (e.g., pressure restored to nominal $>85\text{ PSI}$).
       4. **Episodic Store**: Turn logged as `SOLVED_INDEPENDENTLY`.
       5. **Tier Recalculation**: Recomputes operator tier if autonomy crosses thresholds.
   * - **Supervisor Escalation**
     - Operator clicks *"Escalate to Supervisor"*.
     - 1. **Bandit Penalty**: $-1.0$ applied to the active format arm (format failed to enable independent resolution).
       2. **Autonomy Penalty**: $-15.0$ points deducted from machine autonomy (asymmetric penalty for conservative safety).
       3. **CMMS Ticket Creation**: Auto-dispatches a formal work order with priority `HIGH` and assigns to Level 2 Maintenance.
       4. **Episodic Store**: Turn logged as `ESCALATED` with linked `ticket_id`.
       5. **Tier Recalculation**: Downgrades operator tier if threshold breached.

---

3.6 Component 6: Mock Shopfloor Integration Services
----------------------------------------------------
To simulate a real enterprise factory ecosystem without requiring physical manufacturing
hardware, the solution encapsulates shopfloor systems into dedicated service interfaces:

1. **SCADA Mock Service (`MockSCADA`)**:
   * Simulates real-time telemetry: air pressure (PSI), spindle RPM, amplifier temperature (°C),
     barrel zone temperatures (°C), hydraulic pressure (bar), clamping force (kN), and E-stop status.
   * Generates active machine alarms (e.g., `Alarm 102: SERVOS OFF`, `E-201: BARREL OVERHEAT`).
   * Provides a `verify_repair()` method that validates whether sensor metrics returned to nominal
     operating bands after troubleshooting.
2. **CMMS Mock Service (`MockCMMS`)**:
   * Simulates Computerized Maintenance Management System work-order lifecycle.
   * Generates unique ticket tracking IDs (e.g., `TICK-2026-A83B`), records timestamps, operator
     IDs, machine IDs, issue descriptions, and assigns maintenance dispatch groups.
3. **HR / LMS Mock Service (`MockHRLMS`)**:
   * Maintains employee records, role titles, shift assignments (Morning, Afternoon, Night),
     months of tenure, and verified safety certifications.
   * Provides baseline qualification tiers (`Novice`, `Intermediate`, `Expert`) to bootstrap
     the cold-start phase before empirical behavioral data is collected.

----------------------------------------------------------------------------------------

4. Comprehensive Answers to Core Architectural Questions
=========================================================

This section directly addresses the 7 core design requirements established for the adaptive
learning assistant:

4.1 Question 1: What Behavioural Patterns Are Captured?
-------------------------------------------------------
The system captures four distinct dimensions of operator behavior over time:

1. **Instruction Format & Presentation Preference**:
   * Does the operator resolve issues faster with visual checklists, terse parameters, or detailed tutorials?
   * Captured via cumulative bandit arm rewards and pull histories.
2. **Machine-Specific Autonomy & Competence**:
   * How proficient is the operator on a specific machine type (e.g., high autonomy on Haas CNC vs. low autonomy on Engel Injection Molding)?
   * Captured via machine-specific autonomy scores (0–100%) and success/escalation ratios.
3. **Escalation Propensity vs. Independent Triage Habits**:
   * Does the operator attempt basic triage independently or escalate immediately upon alarm onset?
   * Captured via CMMS escalation frequency and episodic resolution states.
4. **Shift & Operational Context**:
   * How do behavioral patterns correlate with shift timing (Morning vs. Night shift cognitive fatigue) and equipment types?

4.2 Question 2: What Data Sources Are Utilized?
-----------------------------------------------
The architecture unifies five heterogeneous industrial data sources:

1. **Live SCADA Telemetry & PLC Alarms**: Real-time sensor readings, error codes, and equipment states.
2. **Authoritative Engineering Knowledge Base**: Curated Standard Operating Procedures (SOPs),
   original equipment manufacturer (OEM) manuals, LOTO protocols, and hazard matrices.
3. **HR & Learning Management Systems (LMS)**: Shift rosters, formal job titles, tenure, and safety certifications.
4. **Computerized Maintenance Management Systems (CMMS)**: Historical work orders, repair logs,
   and maintenance escalation tickets.
5. **Operator Interaction Streams**: Operator queries, dialogue turns, format arm selections,
   and explicit feedback signals.

4.3 Question 3: What Agents and Components Are Needed?
------------------------------------------------------
The system utilizes a modular multi-agent structure:

* **Chat / Reasoning Agent (Google Gemini)**: Handles grounded natural language understanding,
  SOP synthesis, and formatting compliance.
* **Contextual Bandit Router (Policy Agent)**: Evaluates UCB scores and selects the winning
  presentation format arm per operator.
* **Shadow Observer Agent (Evaluator Agent)**: Monitors resolution outcomes, computes reward
  signals, updates autonomy scores, triggers SCADA verification, and initiates CMMS dispatches.
* **Working Memory Synthesizer**: Dynamically constructs grounded prompts with safety directives.
* **Hybrid Search Retriever**: Fuses dense semantic vector search and sparse BM25 keyword matching via RRF.
* **Semantic Knowledge Graph**: Manages persistent operator competency nodes, machine edges, and format preferences.
* **Episodic Audit Store**: Maintains immutable interaction history for compliance and traceability.

4.4 Question 4: How Does the System Learn Over Time?
----------------------------------------------------
Learning occurs through a dual mathematical mechanism:

1. **Policy Optimization via UCB Bandit Updates**:
   * Each successful independent resolution reinforces the used format arm ($+1.0$), increasing its
     empirical mean reward $\bar{X}_i$.
   * Each escalation penalizes the arm ($-1.0$), prompting the bandit to explore alternate formats.
   * As interaction count $N$ grows, the exploration bonus decays, converging toward the operator's
     optimal learning format.
2. **Competency Evolution via Knowledge Graph Edge Updates**:
   * Autonomy scores dynamically adjust ($+5.0$ on success, $-15.0$ on escalation).
   * Operator skill tiers dynamically transition across Novice, Intermediate, and Expert thresholds,
     altering the depth of guidance injected into future prompts.

4.5 Question 5: How Is Memory Stored, Updated, and Corrected?
-------------------------------------------------------------

.. list-table:: Memory Management Lifecycle
   :widths: 20 40 40
   :header-rows: 1

   * - Memory Aspect
     - Storage Mechanism
     - Update & Correction Protocol
   * - **Storage**
     - Graph state persisted in `graph_state.json` (NetworkX node-link structure); episodic logs persisted in `episodic_logs.json`.
     - Atomic JSON disk serialization after every feedback turn ensures persistence across application restarts.
   * - **Updates**
     - Triggered automatically by the Shadow Observer upon resolution event (`Solved` vs `Escalated`).
     - Incremental mathematical updates to edge weights, pull counts, and autonomy metrics.
   * - **Correction**
     - Manual Administrator Reset Button (`Reset Graph Defaults`) allows restoring baseline HR state if corrupted.
     - Natural exploration bonus prevents permanent lock-in to erroneous initial assumptions.

4.6 Question 6: How Does the Assistant Avoid Wrong Assumptions?
---------------------------------------------------------------
To prevent cognitive bias, incorrect pigeonholing, or unsafe assumptions, the architecture incorporates
five key safeguards:

1. **UCB Exploration Parameter ($c=1.2$)**: Even if an operator has had success with visual instructions,
   the UCB exploration bonus ensures that other formats are periodically tested as total pulls increase.
2. **Cold-Start Bootstrapping via HR/LMS**: New operators are not assigned random profiles; they are
   seeded with verified HR qualification tiers, preventing unsafe overestimation of novice skills.
3. **Asymmetric Penalty Function**: Escalations penalize autonomy by $-15.0$ points, whereas successes
   award $+5.0$ points. This conservative ratio ensures that an operator must demonstrate repeated,
   consistent competence before advancing to higher autonomy tiers.
4. **Closed-Loop SCADA Telemetry Verification**: The system checks live sensor readings to confirm
   repair validity, preventing false success logging if an alarm remains active.
5. **Machine-Specific Competency Isolation**: Autonomy is tracked per machine edge. An operator who is
   an Expert on a Haas CNC is still treated with appropriate caution on an unfamiliar Engel injection
   molding machine.

4.7 Question 7: How Is the Profile Used to Personalize Future Support?
----------------------------------------------------------------------
When an operator initiates a query, the system personalizes the response across three distinct layers:

1. **Presentation Structure**: The Contextual Bandit dictates whether the LLM responds in
   visual step-by-step checklists, ultra-terse technical parameters, or deep conceptual tutorials.
2. **Safety & Autonomy Framing**: The operator's current tier and autonomy score are injected into the
   working memory, guiding the LLM on whether to include detailed precautionary checks or concise
   operational commands.
3. **Machine Contextualization**: Active SCADA alarms and equipment-specific metadata filter the
   hybrid retrieval space, ensuring that guidance is precisely tailored to the active machine.

----------------------------------------------------------------------------------------

5. Design of Experiment (Pilot Validation Plan)
===============================================

If this adaptive AI assistant is expanded into a shopfloor pilot involving manufacturing operators,
the following experimental framework will validate its efficacy.

5.1 Core Hypotheses
-------------------
* **Primary Hypothesis ($H_1$)**: Operators supported by the adaptive AI assistant will achieve a
  statistically significant reduction in **Mean Time to Repair (MTTR)** and **Unplanned Machine Downtime**
  compared to operators using static manuals or unpersonalized assistants.
* **Secondary Hypothesis ($H_2$)**: The Contextual Bandit router will converge to operator-preferred
  instruction formats within 5–10 interaction turns, resulting in higher independent resolution rates
  and lower unnecessary supervisor escalations.

5.2 Key Metrics to Track
------------------------

.. list-table:: Pilot Evaluation Metrics
   :widths: 25 35 40
   :header-rows: 1

   * - Metric Category
     - Key Indicator
     - Measurement Method & Target
   * - **Operational Efficiency**
     - Mean Time to Repair (MTTR)
     - Timestamp delta between alarm trigger and SCADA telemetry normalization. Target: $\ge 25\%$ reduction.
   * - **Autonomy & Escalation**
     - Independent Resolution Ratio
     - Ratio of `SOLVED_INDEPENDENTLY` to total sessions. Target: $\ge 70\%$ for standard alarms.
   * - **Policy Convergence**
     - Bandit Arm Convergence Rate
     - Number of turns required for the winning arm's UCB score to stabilize $\ge 0.5$ points above competing arms. Target: $\le 8$ turns.
   * - **Safety & Grounding**
     - SOP Hallucination Rate
     - Manual audit of LLM responses against grounding SOPs. Target: $0.0\%$ ungrounded procedures.
   * - **Operator Experience**
     - Cognitive Load & Usability Score
     - Post-shift NASA-TLX cognitive load index and System Usability Scale (SUS). Target: SUS $\ge 80$.

5.3 Verification of Behavioral Profile Accuracy
-----------------------------------------------
1. **Correlation Analysis**: Correlate learned machine autonomy scores with supervisor quarterly
   competency reviews to verify that AI-inferred tiers match ground-truth shopfloor performance.
2. **Format Preference Validation**: Conduct blind A/B testing where operators are occasionally
   served alternative formats; measure whether task completion time increases when non-preferred formats are used.
3. **Drift Detection**: Monitor moving averages of autonomy scores to detect skill degradation or
   identify when newly introduced machine models require refresher training.

5.4 Potential Risks, Failure Modes, and Mitigation Strategies
-------------------------------------------------------------

.. list-table:: Industrial Failure Modes & Safeguards
   :widths: 25 35 40
   :header-rows: 1

   * - Failure Mode
     - Operational Risk
     - Mitigation Strategy
   * - **1. Premature Autonomy Escalation**
     - A novice gets lucky on 2 simple fixes and is prematurely classified as Intermediate, leading to unsafe guidance on complex tasks.
     - **Asymmetric Penalties & Tenure Floors**: Autonomy gains are capped at $+5.0$, escalations penalize $-15.0$, and minimum interaction thresholds are required before tier promotions occur.
   * - **2. Feedback Gaming / False Reporting**
     - An operator clicks *"Solved Independently"* to boost their score without actually fixing the machine.
     - **Closed-Loop SCADA Verification**: The Shadow Observer verifies sensor normalization in SCADA telemetry before granting autonomy points.
   * - **3. Operator Trapped in Suboptimal Format**
     - Early negative feedback locks an operator into an unsuitable format arm.
     - **UCB Exploration Bonus ($c=1.2$)**: The logarithmic exploration term guarantees that untried or poorly-sampled arms are periodically re-tested as overall session count increases.
   * - **4. Critical Safety Hallucination**
     - LLM suggests bypassing an interlock or omitting LOTO during high-voltage work.
     - **Hardcoded Safety Injection & Hybrid RRF**: Mandatory safety headers are pre-injected by the Working Memory Synthesizer regardless of LLM generation, and prompts strictly mandate source adherence.

----------------------------------------------------------------------------------------

6. End-to-End Execution Scenarios
=================================

6.1 Scenario A: Novice Operator on Haas CNC (Alarm 102 - Servos Off)
--------------------------------------------------------------------
1. **Operator Context**: John Doe (`OP-001`), Novice Tier, Autonomy: 35.0%.
2. **Event**: Haas VF-2 triggers `Alarm 102: SERVOS OFF`. SCADA telemetry indicates air pressure at 64 PSI (nominal $>85\text{ PSI}$).
3. **Retrieval**: Hybrid retriever matches `SOP-HAAS-001` (Air Pressure & Servo Troubleshooting) with high RRF score.
4. **Bandit Policy**: Bandit selects `Visual_StepByStep` based on highest UCB score.
5. **Generation**: LLM outputs a structured numbered guide with `[SAFETY]`, `[INSPECT]`, and `[ACTION]` tags, instructing John to check the regulator gauge on the rear panel.
6. **Action & Resolution**: John adjusts the regulator to 90 PSI and clicks *"Solved Independently"*.
7. **Observer Outcome**: Bandit rewards `Visual_StepByStep` ($+1.0$), autonomy increases to $40.0\%$, SCADA verifies 92 PSI, and episode is logged.

6.2 Scenario B: Expert Machinist on Haas CNC (M06 Tool Unclamp Issue)
---------------------------------------------------------------------
1. **Operator Context**: Sarah Jenkins (`OP-002`), Expert Tier, Autonomy: 88.0%.
2. **Event**: Tool changer unclamp stuck during M06 tool change cycle.
3. **Retrieval**: Hybrid retriever fetches `SOP-HAAS-003` (Tool Changer Solenoid & Limit Switch Triage).
4. **Bandit Policy**: Bandit selects `Terse_Technical` based on highest UCB score.
5. **Generation**: LLM outputs a 2-bullet response: *"1. Inspect Solenoid 2-B (120VAC line). 2. Verify carousel retracted limit switch discrete input bit #12."*
6. **Action & Resolution**: Sarah tests the solenoid, frees the mechanical detent, and clears the fault within 45 seconds.
7. **Observer Outcome**: Bandit reinforces `Terse_Technical` ($+1.0$), autonomy score updates to $93.0\%$, and audit trail is recorded.

----------------------------------------------------------------------------------------

7. Summary & Future Roadmap
===========================
The proposed adaptive learning assistant transforms static industrial troubleshooting into an
intelligent, closed-loop cognitive system. By marrying **Contextual Multi-Armed Bandits**,
**Semantic Knowledge Graphs**, **Hybrid RRF Grounding**, and **SCADA/CMMS Integrations**, the
solution delivers personalized, safety-compliant, and self-improving operational intelligence
tailored to the modern smart factory.
