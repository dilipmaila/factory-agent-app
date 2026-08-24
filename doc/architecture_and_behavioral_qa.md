# Architecture, Behavioral Inferences & Technical Design Q&A

## Table of Contents

- [1. Executive Summary & Chosen Architecture](#1-executive-summary--chosen-architecture)
  - [1.1 Two-Loop Cyber-Physical Cognitive Architecture](#11-two-loop-cyber-physical-cognitive-architecture)
  - [1.2 High-Level Architectural Flowchart](#12-high-level-architectural-flowchart)
- [2. Key Design Decisions & Rationale](#2-key-design-decisions--rationale)
- [3. Core Technical & Behavioral Answers](#3-core-technical--behavioral-answers)
  - [Q1: What Behavioural Patterns You Would Capture](#q1-what-behavioural-patterns-you-would-capture)
  - [Q2: What Data Sources You Would Use](#q2-what-data-sources-you-would-use)
  - [Q3: What Agents and Subsystems Are Needed](#q3-what-agents-and-subsystems-are-needed)
  - [Q4: How the System Learns Over Time](#q4-how-the-system-learns-over-time)
  - [Q5: How Memory is Stored, Updated, and Corrected](#q5-how-memory-is-stored-updated-and-corrected)
  - [Q6: How the Assistant Avoids Wrong Assumptions](#q6-how-the-assistant-avoids-wrong-assumptions)
  - [Q7: How the Profile is Used to Personalize Future Support](#q7-how-the-profile-is-used-to-personalize-future-support)
- [4. Assumptions Made](#4-assumptions-made)
- [5. Known Limitations of the Prototype](#5-known-limitations-of-the-prototype)
- [6. Companion Documentation Cross-References](#6-companion-documentation-cross-references)

---

## 1. Executive Summary & Chosen Architecture

The **Adaptive Factory Operator AI Assistant** is designed for high-stakes manufacturing environments (such as CNC machining cells and plastic injection molding floors). It transforms static equipment manuals into an adaptive, self-improving cognitive copilot.

### 1.1 Two-Loop Cyber-Physical Cognitive Architecture

The system operates across two decoupled operational loops to balance sub-100ms real-time responsiveness with rigorous asynchronous learning:

```text
+---------------------------------------------------------------------------------------------------------+
|                                    TWO-LOOP COGNITIVE ARCHITECTURE                                      |
+---------------------------------------------------------------------------------------------------------+
| LOOP 1: SYNCHRONOUS REAL-TIME LOOP (< 100ms)                                                            |
|                                                                                                         |
|   Operator Query / SCADA Alarm                                                                          |
|        │                                                                                                |
|        ▼                                                                                                |
|   ┌─────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────────────────┐   |
|   │ Environmental Matrix│ ── │ Contextual Bandit (UCB1) │ ── │ Hybrid Retrieval (Chroma + BM25 + RRF│   |
|   │ (Fatigue / Spvr)    │    │ (State-Bound Format Arm) │    │ + Bayesian Procedural Fault Trees)   │   |
|   └─────────────────────┘    └──────────────────────────┘    └──────────────────────────────────────┘   |
|                                            │                                                            |
|                                            ▼                                                            |
|                              ┌──────────────────────────┐                                               |
|                              │ Working Memory Synthesis │ ──> LLM Reasoning Agent (Google Gemini)       |
|                              └──────────────────────────┘                                               |
|                                            │                                                            |
|                                            ▼                                                            |
|                              ┌──────────────────────────┐                                               |
|                              │ Shadow Observer Logger   │ ──> Append to Shift Event Queue (< 5ms)       |
|                              │ (Provisional Escrow Hold)│                                               |
|                              └──────────────────────────┘                                               |
+---------------------------------------------------------------------------------------------------------+
| LOOP 2: ASYNCHRONOUS LEARNING LOOP (Sleep Cycle — 03:00 AM Batch Cron)                                  |
|                                                                                                         |
|   ┌──────────────────────────┐    ┌──────────────────────────┐    ┌─────────────────────────────────┐   |
|   │ Durability Audit Engine  │ ── │ Knowledge Graph Mutator  │ ── │ Quarantine Consensus Engine     │   |
|   │ (8-Hour SCADA Recurrence)│    │ (Autonomy & Tier Shift)  │    │ (3 Senior Expert Threshold)     │   |
|   └──────────────────────────┘    └──────────────────────────┘    └─────────────────────────────────┘   |
+---------------------------------------------------------------------------------------------------------+
```

1. **Loop 1 (Real-Time Shopfloor Interaction)**:
   - Evaluates active operator context and machine confidence.
   - Evaluates environmental fatigue and supervisor presence.
   - Selects personalized formatting using a state-bound Multi-Armed Bandit (UCB1).
   - Retrieves authoritative SOPs via Reciprocal Rank Fusion (RRF) and Bayesian fault trees.
   - Synthesizes safety rules, anti-patterns, and live SCADA telemetry into the prompt.
   - Logs operator feedback and buffers provisional rewards in under 5ms.

2. **Loop 2 (Asynchronous Sleep Cycle Consolidation)**:
   - Runs nightly batch evaluation (`sleep_cycle_evaluator.py`).
   - Audits the 8-hour durability window against SCADA sensor streams.
   - Converts durable repairs into permanent autonomy credits and bandit weights.
   - Penalizes temporary "duct-tape" fixes that recurred within 8 hours.
   - Updates Bayesian branch probabilities on procedural fault trees.
   - Promotes quarantined shortcuts that reached 3 verified Senior Expert sign-offs.

---

### 1.2 High-Level Architectural Flowchart

```text
 [Operator on HMI] ───────> [ECM Context Service] ───> [Contextual Bandit Router]
         │                                                        │
         ▼                                                        ▼
 [SCADA Alarm Stream] ────> [Hybrid Retriever & Fault Trees] ──> [Working Memory Synthesizer]
                                                                  │
                                                                  ▼
                                                      [Gemini LLM Generation]
                                                                  │
                                                                  ▼
 [Operator Feedback / Overrides] ───────────────────> [Shadow Observer]
                                                              │
                                                              ▼
                                               [8-Hour Escrow Ledger]
                                                              │ (Overnight)
                                                              ▼
                                               [Sleep Cycle Evaluator]
                                                              │
                     ┌────────────────────────┬───────────────┴────────────────┬────────────────────────┐
                     ▼                        ▼                                ▼                        ▼
             [Knowledge Graph]        [Bandit Weights]                 [Fault Trees]            [Active SOP Library]
             (Autonomy & Tiers)       (UCB Score Update)              (Beta Probabilities)      (3-Expert Promoted)
```

---

## 2. Key Design Decisions & Rationale

| # | Design Decision | Alternative Considered | Technical Rationale & Safety Justification |
|---|---|---|---|
| **1** | **Decoupled Operator-Machine Graph Schema** | Global single-score operator profiling | A 15-year CNC Machining master is a complete novice on a Plastic Injection Molder. Decoupling prevents hazardous skill overestimation and domain leakage. |
| **2** | **State-Bound Multi-Armed Bandit (UCB1)** | Static prompt personas or rule-based templates | Operators learn and evolve. State-bound bandit mathematical routing balances format exploration with proven format exploitation per cognitive state. |
| **3** | **8-Hour Durability Verification Escrow** | Immediate reward attribution upon operator "Solved" click | Operators often perform temporary "duct-tape" fixes that fail 2 hours later. Holding credit in escrow until SCADA verifies 8-hour stability prevents learning bad habits. |
| **4** | **3-Expert Consensus Quarantine Engine** | Automatic LLM self-updating knowledge base | Unvetted shortcuts discovered on the floor can be catastrophic if shared with novices. Requiring 3 senior expert signatures ensures strict safety governance. |
| **5** | **Micro-Debrief Verification Loop** | Passive MTTR telemetry inference | If an operator clears a 10-minute fault in 2 minutes, the AI cannot assume *why*. Directly asking a simple Yes/No question captures tacit shopfloor knowledge safely. |
| **6** | **Environmental Context Matrix (ECM) Fatigue Gate** | Static time-agnostic prompt generation | Operators in hour 11 of a 12-hour shift suffer cognitive overload. Forcing $c=0.0$ (100% exploit) enforces concise, scannable formats when alertness is lowest. |
| **7** | **Unified Anti-Patterns ("What Not To Do")** | Positive-only instruction sets | Factory accidents frequently stem from known intuitive errors (e.g. jumpering pressure switches). Explicitly presenting prohibited actions prevents equipment destruction. |
| **8** | **Sub-100ms Synchronous Logging** | Real-time graph database writes during chat turn | Real-time graph traversals and disk syncs cause UI latency. Fast queue appending ($<5\text{ms}$) maintains instantaneous UI responsiveness. |

---

## 3. Core Technical & Behavioral Answers

### Q1: What Behavioural Patterns You Would Capture

The system captures five distinct categories of operator behavioral signals:

1. **Format & Communication Preferences**:
   - **Explicit Format Overrides**: Direct selection of `Visual Step-by-Step`, `Terse Technical`, or `Detailed Tutorial`.
   - **Cognitive State Rejections**: Formats rejected by the operator receive an immediate **-10.0** weight penalty.
   - **Information Density Tolerance**: Read-through velocity and expansion of grounding reference panels.

2. **Machine-Specific Troubleshooting Autonomy**:
   - **Independent Resolution Rate**: Ratio of alarms resolved independently vs. escalated to maintenance.
   - **Domain Discipline Competence**: Competence tracked separately across mechanical, electrical, hydraulic, and pneumatic subsystems.

3. **Escalation & Diagnostic Difficulty Patterns**:
   - **Time-to-Escalate**: How rapidly an operator identifies that a fault exceeds their clearance level.
   - **Repeated Code Struggles**: Specific recurring alarm codes (e.g. `Alarm 103 Servo Error`) where an operator has historically struggled, triggering proactive support.

4. **Operational Velocity & Shortcut Discovery**:
   - **Mean Time to Repair (MTTR) Deviations**: Substantial speedups compared to OEM standard SOP duration (e.g., resolving a 10-minute task in 2 minutes).

5. **Shift Fatigue & Vigilance Signals**:
   - **Shift Progress & Circadian Position**: Hours elapsed into shift ($t/T$).
   - **Interaction Cadence**: Query frequency, response latency, and evening/night shift telemetry.

---

### Q2: What Data Sources You Would Use

```text
+-----------------------+--------------------------------------------------------------------------------+
| DATA SOURCE           | SPECIFIC SIGNALS & PAYLOAD INGESTED                                            |
+-----------------------+--------------------------------------------------------------------------------+
| SCADA & OT Telemetry  | Live sensor streams (PSI, RPM, Temperature, Vibration), active alarm codes,     |
|                       | timestamped fault resets, and 8-hour post-repair recurrence logs.              |
+-----------------------+--------------------------------------------------------------------------------+
| Environmental Context | Shift start/end times, elapsed shift hours, on-site/remote supervisor status,  |
| Matrix (ECM)          | ambient shopfloor decibels (dB), and cell ambient temperature (°C).            |
+-----------------------+--------------------------------------------------------------------------------+
| CMMS (Maintenance)    | Work order history, Level 2 technician dispatch tickets, Mean Time Between     |
|                       | Failures (MTBF), and spare parts inventory logs.                               |
+-----------------------+--------------------------------------------------------------------------------+
| HR / LMS Systems      | Official certifications, OSHA safety clearances, High-Voltage authorization,   |
|                       | and role seniority levels.                                                     |
+-----------------------+--------------------------------------------------------------------------------+
| Engineering Manuals   | Authoritative OEM technical manuals, machine wiring schematics, LOTO checklists|
| (Knowledge Base)      | stored in vector database (ChromaDB) and BM25 index.                          |
+-----------------------+--------------------------------------------------------------------------------+
| Persistent Shift Logs | Append-only episodic interaction turns, feedback queues, escrow ledgers, and   |
|                       | NetworkX graph serialized state.                                               |
+-----------------------+--------------------------------------------------------------------------------+
```

---

### Q3: What Agents and Subsystems Are Needed

The implementation is structured into nine modular, single-responsibility components:

1. **`ManufacturingChatAgent` (`agents/chat_agent.py`)**:
   Main conversational orchestrator executing grounded generation via LangChain and Google Gemini 2.5 Flash.
2. **`ContextualBandit` (`agents/bandit_router.py`)**:
   Multi-armed bandit implementing the state-bound UCB1 selection algorithm, fatigue override gates, and emergency SOS format enforcement.
3. **`ShadowObserver` (`agents/shadow_observer.py`)**:
   Fast asynchronous logger buffering shift interaction events, managing provisional escrow rewards, and queuing micro-debrief inquiries.
4. **`OperatorKnowledgeGraph` (`memory/semantic_graph.py`)**:
   NetworkX knowledge graph managing decoupled operator-machine competence edges, autonomy score metrics, derived cognitive tiers, and high-voltage domain fencing.
5. **`ProceduralMemory` (`memory/procedural_memory.py`)**:
   Dynamic procedural fault tree manager computing Bayesian Beta-Binomial branch probabilities, enforcing anti-pattern warnings, and staging quarantine candidates.
6. **`DebriefManager` (`memory/debrief_store.py`)**:
   Micro-debrief lifecycle controller tracking rapid MTTR triggers, operator confirmations, and audit trails.
7. **`HybridRetriever` (`memory/search.py`)**:
   Dense (ChromaDB) + Sparse (BM25) search engine combining vector embeddings and keyword matching via Reciprocal Rank Fusion (RRF).
8. **`Working Memory Synthesizer` (`memory/working_memory.py`)**:
   Deterministic token-budgeted prompt compiler enforcing the strict priority hierarchy: *Safety $\rightarrow$ ECM Context $\rightarrow$ Historical Alerts $\rightarrow$ Bandit Directives $\rightarrow$ Fault Trees $\rightarrow$ RAG Manuals*.
9. **`SleepCycleEvaluator` (`sleep_cycle_evaluator.py`)**:
   Asynchronous batch evaluation engine executing overnight durability audits, graph mutations, and quarantine promotions.

---

### Q4: How the System Learns Over Time

Learning operates through a dual-speed reinforcement and Bayesian updating model:

```text
                      REAL-TIME SHIFT                           NIGHTLY SLEEP CYCLE (03:00 AM)
           ┌─────────────────────────────────────┐         ┌──────────────────────────────────────┐
           │ • Explicit Override: -10.0 penalty  │         │ • Durability Audit: +1.0 / -5.0 UCB  │
           │ • Feedback Click: Escrow Deposit    │ ──────> │ • Autonomy Update: +5.0% / -15.0%    │
           │ • Debrief Confirm: Quarantine Staged│         │ • Fault Trees: Beta Probabilities    │
           │ • Fast Shift Queue (<5ms)           │         │ • Consensus: 3-Expert Auto-Promotion │
           └─────────────────────────────────────┘         └──────────────────────────────────────┘
```

1. **Contextual Bandit Format Optimization**:
   The UCB1 algorithm computes selection values for each format arm $i$ in state $s$:
   $$\text{UCB}_i = \bar{\mu}_i + c \sqrt{\frac{2 \ln N_s}{n_i}}$$
   - $\bar{\mu}_i$: Mean historical reward for format $i$.
   - $n_i$: Pull count of format $i$ in this operator's state.
   - $N_s$: Total interactions in state $s$.
   - $c$: Exploration constant ($c = 0.0$ under fatigue, $c = 1.414$ under normal operation).

2. **Bayesian Fault Tree Optimization**:
   Each diagnostic path branch updates its success probability using a Beta-Binomial conjugate prior:
   $$P(\text{Success}) = \frac{s + 1}{s + f + 2}$$
   - When a fix succeeds permanently, $s \leftarrow s + 1$.
   - When a fix fails or recurs, $f \leftarrow f + 1$.
   - The tree dynamically re-ranks the most reliable diagnostic branch to the top.

3. **Machine Autonomy Score Progression**:
   - **Durable Fix (+5.0%)**: If SCADA confirms zero recurring alarms over 8 hours, the operator's machine-specific autonomy increases by $+5.0\%$.
   - **Duct-Tape Penalty (-15.0%)**: If the alarm recurs within 8 hours, autonomy drops by $-15.0\%$.
   - **Tier Thresholds**: Operators automatically advance:
     - **Novice**: $0.0\% \le \text{Autonomy} < 40.0\%$
     - **Intermediate**: $40.0\% \le \text{Autonomy} < 80.0\%$
     - **Expert**: $\text{Autonomy} \ge 80.0\%$

---

### Q5: How Memory is Stored, Updated, and Corrected

```text
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| MEMORY LAYER          | STORAGE MEDIUM & FILE         | RUNTIME UPDATE MECHANISM          | CORRECTION & AUDIT MECHANISM      |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Working Memory        | Ephemeral RAM (Prompt Buffer) | Reconstructed fresh per turn via  | Discarded at turn completion;     |
|                       |                               | token budget priority hierarchy.  | zero persistent state leakage.    |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Episodic Memory       | JSON Files:                   | Synchronous append in < 5ms       | Sleep Cycle archives shift events |
|                       | `episodic_event_queue.json`   | via Shadow Observer during shift. | to permanent log and flushes      |
|                       | `episodic_logs.json`          |                                   | queue.                            |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Semantic Knowledge    | NetworkX DiGraph:             | Provisional rewards queued;       | 8-hour durability audit flips     |
| Graph                 | `graph_state.json`            | permanent node/edge mutations     | false successes into -15.0        |
|                       |                               | occur during Sleep Cycle.         | autonomy penalties.               |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Procedural Memory     | JSON Hierarchical Trees:      | Dynamic Beta ranking computed;    | Anti-pattern rules permanently    |
|                       | `procedural_fault_trees.json` | branch counts updated nightly.    | prevent dangerous actions.        |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Quarantine Memory     | Isolated JSON Staging Store:  | Verified debrief shortcuts staged | Locked from search; rejected if   |
|                       | `quarantine_sops.json`        | here with 0/3 signatures.         | non-expert attempts sign-off.     |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
```

---

### Q6: How the Assistant Avoids Wrong Assumptions

The system employs seven active guardrails to prevent erroneous assumptions and dangerous hallucinations:

1. **Decoupled Machine Nodes**: Prevents cross-discipline skill assumptions (e.g. CNC machining expertise is never assumed to apply to injection molding).
2. **Deterministic RAG Retrieval Boundary**: Responses are strictly bounded by retrieved OEM SOP manuals and verified fault trees. The LLM is constrained to output zero ungrounded steps.
3. **8-Hour Durability Escrow Window**: Replaces subjective operator "it's fixed" claims with objective SCADA sensor verification over an 8-hour period.
4. **3-Expert Consensus Quarantine Engine**: Unvetted shortcuts discovered by individuals cannot be shown to other operators until 3 independent Senior Experts validate them.
5. **Micro-Debrief Explicit Confirmation**: Rapid MTTRs trigger an explicit human confirmation prompt (*"Did you use shortcut X?"*). Clicking "No" immediately discards the telemetry hypothesis with zero memory mutation.
6. **ECM Hard Gates (Fatigue & Supervisor Offline)**: Shuts down bandit exploration under fatigue ($\ge 80\%$) and restricts maintenance escalation when supervisors are off-site.
7. **Severity-1 Deterministic SOS Protocol**: Critical life-safety alarms suspend all personalization and exploration in favor of deterministic E-Stop, LOTO, and evacuation directives.

---

### Q7: How the Profile is Used to Personalize Future Support

The evolved profile directly personalizes four aspects of future shopfloor interactions:

```text
                                       EVOLVING OPERATOR PROFILE
                                 ┌───────────────────────────────────┐
                                 │ • Derived Tier: Intermediate (40%)│
                                 │ • Format: Visual_StepByStep (85%) │
                                 │ • Flag: Failed Alarm 103 (2x)     │
                                 │ • Fencing: Mechanical Authorized  │
                                 └───────────────────────────────────┘
                                                   │
         ┌────────────────────────┬────────────────┴────────────────┬────────────────────────┐
         ▼                        ▼                                 ▼                        ▼
 1. Automatic Format      2. Historical Alert               3. Proactive Dispatch    4. Clearance Fencing
 Serves visual tags and   Displays past struggle banner     Offers early CMMS        Fences high-voltage
 checklists directly      above the chat interface          ticket if triage stalls  repairs to technicians
```

1. **Automatic Format Personalization**:
   The bandit router automatically serves the operator's preferred format (`Visual_StepByStep`, `Terse_Technical`, or `Detailed_Tutorial`) for their active skill tier without requiring manual format selection.
2. **Historical Escalation Warning Injections**:
   When an operator queries an alarm they have historically failed or escalated (e.g. `Alarm 103`), the working memory synthesizer injects a historical warning banner and proactively offers early Level 2 technician dispatch.
3. **Diagnostic Tree Level Filtering**:
   High-risk internal diagnostic branches and advanced shortcuts are filtered out for Novice operators and only surfaced once an operator reaches Certified Expert status.
4. **Domain Fencing & High-Voltage Verification**:
   The knowledge graph verifies subsystem clearance before providing procedures. Non-certified operators querying electrical sub-assemblies are instructed to contact a senior technician.

---

## 4. Assumptions Made

1. **Operator Identity & Authentication**:
   Operators authenticate via unique RFID shopfloor badges or SSO credentials, establishing an unambiguous `operator_id`.
2. **IT/OT Convergence & SCADA Ingestion**:
   The factory network supports read-only SCADA telemetry streaming, allowing the assistant to inspect alarm codes, sensor readings, and post-repair recurrence timestamps.
3. **Advisory-Only Governance (No Direct PLC Actuation)**:
   The AI assistant acts strictly in an advisory capacity on operator HMIs and mobile tablets. It does **not** write to PLCs or actuate machine hardware directly.
4. **Repair Durability Truth Standard**:
   A machine operating for 8 consecutive hours post-resolution without triggering the same alarm code is accepted as ground truth that the repair was successful.
5. **Supervisor Roster Accessibility**:
   The factory CMMS/MES provides real-time shift roster status indicating whether a Level 2 maintenance supervisor is physically on-site.

---

## 5. Known Limitations of the Prototype

1. **Local File Persistence**:
   The prototype utilizes transactional JSON files (`data/graph_state.json`, `data/escrow_rewards.json`, etc.) for persistence. A production deployment would migrate these to a distributed PostgreSQL database, Neo4j graph cluster, and Redis cache.
2. **Mock Service Layer**:
   SCADA telemetry, CMMS ticketing, and ECM fatigue calculations are simulated via local service classes (`mock_services/`). Production integration requires standard industrial protocol connectors (OPC-UA, MQTT, REST).
3. **Simulated Sleep Cycle Execution**:
   In the prototype, the 03:00 AM Sleep Cycle can be triggered on demand via the sidebar button (`🌙 Run Sleep Cycle (Batch)`) or CLI script. In production, this runs as an isolated Celery/Kubernetes cron worker.
4. **Single-Node Vector Store**:
   ChromaDB is executed in-process. Production scale would utilize a centralized vector search service (e.g., Vertex AI Vector Search or Pinecone).

---

## 6. Companion Documentation Cross-References

| Document | Focus Area | Contents |
|---|---|---|
| 🏛️ [`solution_design.md`](solution_design.md) | **System Architecture** | Full mathematical formulas, two-loop architecture, and FMEA safety tables. |
| 🧪 [`demo_and_evaluation_guide.md`](demo_and_evaluation_guide.md) | **Interactive Demo & Test Cases** | Multi-turn behavioral walkthroughs and 10 modular test scenarios for Streamlit evaluation. |
| 📦 [`code_and_modules_guide.md`](code_and_modules_guide.md) | **Technical Specifications** | Module-by-module breakdown of all classes, methods, arguments, and return types. |
| ⚙️ [`run_and_configuration_guide.md`](run_and_configuration_guide.md) | **Setup & Operations** | Environment installation, CLI commands, JSON storage structure, and operations FAQ. |
