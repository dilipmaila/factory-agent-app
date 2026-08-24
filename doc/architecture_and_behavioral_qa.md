# Architecture, Behavioral Learning & System Design Q&A

## Table of Contents

- [1. Summary & Chosen Architecture](#1-summary--chosen-architecture)
  - [1.1 The Two-Loop System Design](#11-the-two-loop-system-design)
  - [1.2 High-Level System Flowchart](#12-high-level-system-flowchart)
- [2. Key Design Decisions & Why We Made Them](#2-key-design-decisions--why-we-made-them)
- [3. Core Technical & Behavioral Answers](#3-core-technical--behavioral-answers)
  - [Q1: What Behavioral Patterns You Would Capture](#q1-what-behavioral-patterns-you-would-capture)
  - [Q2: What Data Sources You Would Use](#q2-what-data-sources-you-would-use)
  - [Q3: What Agents and Components Are Needed](#q3-what-agents-and-components-are-needed)
  - [Q4: How the System Learns Over Time](#q4-how-the-system-learns-over-time)
  - [Q5: How Memory is Stored, Updated, and Corrected](#q5-how-memory-is-stored-updated-and-corrected)
  - [Q6: How the Assistant Avoids Wrong Assumptions](#q6-how-the-assistant-avoids-wrong-assumptions)
  - [Q7: How the Profile is Used to Personalize Future Support](#q7-how-the-profile-is-used-to-personalize-future-support)
- [4. Assumptions Made](#4-assumptions-made)
- [5. Known Limitations of the Design](#5-known-limitations-of-the-design)
- [6. Companion Documentation Links](#6-companion-documentation-links)

---

## 1. Summary & Chosen Architecture

The **Adaptive Factory Operator AI Assistant** is a smart copilot for shopfloor workers running complex machinery (such as CNC milling machines and plastic injection molders). It replaces heavy paper manuals with interactive, step-by-step guidance tailored to each worker's skill level.

### 1.1 The Two-Loop System Design

To keep the screen fast for workers while still learning from real factory outcomes, the system separates work into **two loops**:

```text
+---------------------------------------------------------------------------------------------------------+
|                                    THE TWO-LOOP SYSTEM DESIGN                                           |
+---------------------------------------------------------------------------------------------------------+
| LOOP 1: REAL-TIME SCREEN LOOP (Takes under 100ms)                                                       |
|                                                                                                         |
|   Worker asks a question or Machine Alarm fires                                                         |
|        │                                                                                                |
|        ▼                                                                                                |
|   ┌─────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────────────────┐   |
|   │ Check Shift Context │ ── │ Pick Best Format (Bandit)│ ── │ Find Matching Manuals & Fix Paths    │   |
|   │ (Fatigue & Spvr)    │    │ (Visual / Short / Detail)│    │ (Vector Search + Fix Success Rates)  │   |
|   └─────────────────────┘    └──────────────────────────┘    └──────────────────────────────────────┘   |
|                                            │                                                            |
|                                            ▼                                                            |
|                              ┌──────────────────────────┐                                               |
|                              │ Build Prompt with Safety │ ──> AI Writes Answer (Google Gemini)          |
|                              └──────────────────────────┘                                               |
|                                            │                                                            |
|                                            ▼                                                            |
|                              ┌──────────────────────────┐                                               |
|                              │ Fast Event Logger        │ ──> Save event in under 5ms                   |
|                              │ (Hold credit in escrow)  │                                               |
|                              └──────────────────────────┘                                               |
+---------------------------------------------------------------------------------------------------------+
| LOOP 2: NIGHTLY LEARNING LOOP (Sleep Cycle — Runs at 03:00 AM)                                          |
|                                                                                                         |
|   ┌──────────────────────────┐    ┌──────────────────────────┐    ┌─────────────────────────────────┐   |
|   │ Check if Fixes Lasted    │ ── │ Update Worker Skill Score│ ── │ Check Expert Votes for Shortcuts│   |
|   │ (8-Hour Sensor Check)    │    │ (Give +5% or Take -15%)  │    │ (3 Experts Approve -> Publish)  │   |
|   └──────────────────────────┘    └──────────────────────────┘    └─────────────────────────────────┘   |
+---------------------------------------------------------------------------------------------------------+
```

1. **Loop 1 (Real-Time Shopfloor Help)**:
   - Identifies who the worker is and how experienced they are on *this specific machine*.
   - Checks if the worker is tired (shift hours) or if the supervisor is away.
   - Picks the clearest explanation format (Visual, Short, or Detailed).
   - Pulls exact manufacturer manuals and proven fix paths.
   - Adds safety warnings (LOTO, PPE) and rules on what **not** to do.
   - Saves what happened in under 5ms so the screen never lags.

2. **Loop 2 (Nightly Learning Loop / Sleep Cycle)**:
   - Runs every night at 03:00 AM (`sleep_cycle_evaluator.py`).
   - Checks if machines stayed fixed for at least 8 hours.
   - Gives permanent skill credit if the fix lasted, or deducts points if the alarm came back.
   - Updates which fix steps work best based on real success rates.
   - Publishes new operator shortcuts if at least 3 Senior Experts approved them.

---

### 1.2 High-Level System Flowchart

```text
 [Worker on Screen] ───────> [Check Shift & Fatigue] ──> [Pick Explanation Format]
         │                                                        │
         ▼                                                        ▼
 [Machine Alarm Fires] ────> [Find Manuals & Fix Paths] ───────> [Build Safe Prompt]
                                                                  │
                                                                  ▼
                                                      [AI Writes Helpful Answer]
                                                                  │
                                                                  ▼
 [Worker Gives Feedback / Fixes Issue] ──────────────> [Fast Event Logger]
                                                              │
                                                              ▼
                                               [Hold Credit in 8-Hour Escrow]
                                                              │ (Overnight)
                                                              ▼
                                               [Nightly Sleep Cycle Evaluator]
                                                              │
                     ┌────────────────────────┬───────────────┴────────────────┬────────────────────────┐
                     ▼                        ▼                                ▼                        ▼
             [Update Skill Level]     [Format Preferences]             [Update Fix Rates]       [Publish Approved]
             (Novice/Inter/Expert)    (Learn Winning Formats)          (Best Paths First)       (3-Expert Shortcuts)
```

---

## 2. Key Design Decisions & Why We Made Them

| # | Design Decision | What We Avoided | Why This Is Better & Safer |
|---|---|---|---|
| **1** | **Track skill per machine separately** | Giving workers a single global score | A 15-year CNC milling master is still a novice on an injection molder. Separate tracking prevents giving dangerous advanced tasks to someone unfamiliar with a machine. |
| **2** | **Smart format selection (Bandit Algorithm)** | Using the same text style for everyone | Novices need step-by-step pictures and checklists. Experts just want quick error codes and values. The bandit learns what format each worker prefers in each skill state. |
| **3** | **8-Hour waiting rule before giving credit** | Giving skill points the moment a worker clicks "Fixed" | Quick "duct-tape" patches often break again 2 hours later. The AI waits 8 hours and checks machine sensors to make sure the fix was permanent before giving credit. |
| **4** | **3-Expert vote before sharing new shortcuts** | Letting AI auto-publish any tip it hears | An unverified trick might damage expensive parts or cause injury. Requiring 3 senior experts to review and approve shortcuts keeps the factory safe. |
| **5** | **Asking directly when a fix is unusually fast** | Guessing why a repair was fast | If a 10-minute repair takes only 2 minutes, the AI asks: *"Did you use shortcut X?"* This safely captures helpful tricks without guessing. |
| **6** | **Fatigue gate for tired workers** | Giving long, wordy answers near shift end | In hour 11 of a 12-hour shift, tired workers make mistakes. The system forces short, clear, bullet-point instructions when fatigue is high ($80\%+$). |
| **7** | **Clear warnings on what NOT to do (Anti-Patterns)** | Only showing positive instructions | Many factory accidents happen when people try common bad ideas (like using a jumper wire to bypass an air sensor). Explicitly showing what **not** to do prevents damage. |
| **8** | **Super-fast screen logging (<5ms)** | Doing heavy database updates during a chat | Workers need fast answers. Saving events to a quick shift queue keeps the screen instant, while heavy math runs at night during the Sleep Cycle. |

---

## 3. Core Technical & Behavioral Answers

### Q1: What Behavioral Patterns You Would Capture

The system captures five main types of worker actions:

1. **How they like information presented**:
   - **Format button clicks**: Did the worker click `Visual Step-by-Step`, `Terse Technical`, or `Detailed Tutorial`?
   - **Format rejections**: If a worker switches away from a format, that format gets penalized (**-10.0 points**).
   - **Reading habits**: How fast they read and whether they expand extra reference boxes.

2. **How independently they fix each machine**:
   - **Independent Fix Rate**: How often they fix alarms on their own versus calling maintenance.
   - **Subsystem Strengths**: Are they great at mechanical fixes, but always ask for help with electrical wiring?

3. **When and how they ask for help**:
   - **Escalation Speed**: How quickly they realize an issue is too complex and call a supervisor.
   - **Struggle History**: Repeating alarm codes (e.g. `Alarm 103 Servo Error`) where the worker previously had trouble, so the AI can offer proactive support.

4. **Speed and shortcut discoveries**:
   - **Fast Repair Times (MTTR)**: When an operator finishes a 10-minute task in 2 minutes, flagging a potential shortcut.

5. **Fatigue and tiredness signals**:
   - **Shift Progress**: How many hours into the shift they are ($t / T$).
   - **Time of Day**: Night shift vs. morning shift patterns.

---

### Q2: What Data Sources You Would Use

```text
+-----------------------+--------------------------------------------------------------------------------+
| DATA SOURCE           | WHAT INFORMATION WE READ                                                       |
+-----------------------+--------------------------------------------------------------------------------+
| Machine Sensors       | Live readings (air pressure, temperature, RPM, vibration), active alarm codes, |
| (SCADA / OT)          | reset timestamps, and sensor checks 8 hours after a fix.                      |
+-----------------------+--------------------------------------------------------------------------------+
| Shift & Environment   | Shift start/end times, hours worked, whether a supervisor is in the building,  |
| Matrix (ECM)          | ambient noise level (dB), and room temperature.                                |
+-----------------------+--------------------------------------------------------------------------------+
| Maintenance System    | Past repair work orders, technician tickets, recurring breakdown history,      |
| (CMMS)                | and spare parts logs.                                                          |
+-----------------------+--------------------------------------------------------------------------------+
| Training & HR Records | Official operator certifications, safety training clearances, and high-voltage |
| (HR / LMS)            | electrical permissions.                                                        |
+-----------------------+--------------------------------------------------------------------------------+
| Official Manuals      | Factory OEM equipment manuals, wiring diagrams, and safety checklists stored   |
| (Knowledge Base)      | in vector search (ChromaDB) and keyword search (BM25).                         |
+-----------------------+--------------------------------------------------------------------------------+
| Shift Activity Logs   | Fast record of questions asked, buttons clicked, escrow rewards, and the       |
|                       | saved knowledge graph.                                                         |
+-----------------------+--------------------------------------------------------------------------------+
```

---

### Q3: What Agents and Components Are Needed

The system uses nine modular components:

1. **`ManufacturingChatAgent` (`agents/chat_agent.py`)**:
   The main AI conversation engine that uses Google Gemini to write safe, grounded answers.
2. **`ContextualBandit` (`agents/bandit_router.py`)**:
   The format picker that selects the best style (Visual, Short, or Detailed) using the UCB1 algorithm and enforces fatigue limits.
3. **`ShadowObserver` (`agents/shadow_observer.py`)**:
   The fast background logger that records actions in under 5ms, holds rewards in escrow, and queues quick debrief questions.
4. **`OperatorKnowledgeGraph` (`memory/semantic_graph.py`)**:
   The skill map that tracks how confident each worker is on each machine, their skill level (Novice/Inter/Expert), and safety clearances.
5. **`ProceduralMemory` (`memory/procedural_memory.py`)**:
   The fix library that ranks fix paths by real success probability and lists dangerous anti-patterns.
6. **`DebriefManager` (`memory/debrief_store.py`)**:
   The question manager that asks operators to confirm unusually fast fixes.
7. **`HybridRetriever` (`memory/search.py`)**:
   The search engine combining vector search (ChromaDB) and keyword search (BM25) so manuals are always found accurately.
8. **`Working Memory Synthesizer` (`memory/working_memory.py`)**:
   The prompt builder that puts Safety first, followed by shift context, history warnings, format rules, and manuals.
9. **`SleepCycleEvaluator` (`sleep_cycle_evaluator.py`)**:
   The nightly update engine that checks 8-hour fix durability, updates skill scores, and publishes expert-approved shortcuts.

---

### Q4: How the System Learns Over Time

Learning happens in two stages: live during the shift, and overnight during the Sleep Cycle.

```text
                      DURING THE SHIFT (LIVE)                     NIGHTLY SLEEP CYCLE (03:00 AM)
           ┌─────────────────────────────────────┐         ┌──────────────────────────────────────┐
           │ • Worker changes format: -10 penalty│         │ • Check 8h durability: +1.0 / -5.0   │
           │ • Worker solves issue: Put in escrow│ ──────> │ • Update autonomy: +5.0% / -15.0%    │
           │ • Worker confirms trick: Put on hold│         │ • Update fix success rates (Beta)    │
           │ • Fast event saved in under 5ms     │         │ • 3 Experts approved? -> Publish SOP │
           └─────────────────────────────────────┘         └──────────────────────────────────────┘
```

1. **Learning What Format Works Best (Bandit Math)**:
   The system calculates a score for each format arm $i$ using the UCB1 formula:
   $$\text{UCB}_i = \bar{\mu}_i + c \sqrt{\frac{2 \ln N_s}{n_i}}$$
   - $\bar{\mu}_i$: Average reward for this format.
   - $n_i$: How many times this format was shown.
   - $N_s$: Total interactions in this skill state.
   - $c$: Exploration factor ($c = 0.0$ when tired, $c = 1.414$ when normal).

2. **Learning What Fix Steps Work Best (Bayesian Math)**:
   Each fix branch in a fault tree updates its success probability:
   $$P(\text{Success}) = \frac{s + 1}{s + f + 2}$$
   - $s$: Number of times this fix permanently solved the problem.
   - $f$: Number of times this fix failed or the alarm came back.
   - The steps with the highest success rate are shown first.

3. **Updating Worker Skill Scores**:
   - **Permanent Fix (+5.0%)**: If the machine runs clean for 8 hours, the worker gains $+5.0\%$ autonomy on that machine.
   - **Duct-Tape Penalty (-15.0%)**: If the alarm comes back within 8 hours, the worker loses $-15.0\%$.
   - **Skill Levels**:
     - **Novice**: $0\% \text{ to } 39\%$ autonomy score.
     - **Intermediate**: $40\% \text{ to } 79\%$ autonomy score.
     - **Expert**: $80\% \text{ to } 100\%$ autonomy score.

---

### Q5: How Memory is Stored, Updated, and Corrected

```text
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| MEMORY TYPE           | WHERE IT IS STORED            | HOW IT UPDATES DURING SHIFT       | HOW IT GETS CORRECTED             |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Working Memory        | Temporary RAM (Prompt Buffer) | Rebuilt fresh for each turn with  | Erased when turn ends; no         |
|                       |                               | safety rules and manuals.         | leftover data leaks.              |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Shift Activity Logs   | Fast JSON Files:              | Added in under 5ms when worker    | Sleep Cycle archives shift events |
| (Episodic Memory)     | `episodic_event_queue.json`   | clicks buttons or asks questions. | and clears the queue each night.  |
|                       | `episodic_logs.json`          |                                   |                                   |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Worker Skill Graph    | Graph Database File:          | Rewards held in escrow ledger     | 8-hour check turns false fixes    |
| (Semantic Graph)      | `graph_state.json`            | during the shift.                 | into -15.0% skill penalties.      |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Fix Trees & Rules     | JSON Tree File:               | Ranked by success rate;           | Dangerous anti-pattern rules      |
| (Procedural Memory)   | `procedural_fault_trees.json` | success counts updated at night.  | can never be overridden.          |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
| Quarantine Staging    | Isolated Staging File:        | New shortcuts saved here with     | Hidden from search; rejected if a |
| (Unverified Tricks)   | `quarantine_sops.json`        | 0/3 expert signatures.            | non-expert tries to approve it.   |
+-----------------------+-------------------------------+-----------------------------------+-----------------------------------+
```

---

### Q6: How the Assistant Avoids Wrong Assumptions

The system uses seven safeguards to prevent mistakes and hallucinations:

1. **Separate Machine Profiles**: Being an expert on a CNC mill never gives you expert status on an injection molder.
2. **Strict Manual Grounding (Zero Hallucination)**: The AI is only allowed to use official manuals and verified fix trees. It cannot make up repair steps.
3. **8-Hour Sensor Check**: The AI does not trust a verbal "it's fixed" claim until sensors prove the machine ran clean for 8 hours.
4. **3-Expert Vote on Shortcuts**: Personal shortcuts cannot be seen by other workers until 3 Senior Experts check and sign off on them.
5. **Direct Confirmation for Fast Fixes**: If a repair was fast, the AI asks *"Did you use shortcut X?"* If the worker clicks "No", the idea is dropped immediately.
6. **Fatigue & Offline Supervisor Gates**: Automatically switches to simple bullet points when workers are tired, and blocks dangerous DIY steps if the supervisor is away.
7. **Emergency SOS Mode**: In dangerous situations (smoke, heavy vibrations), the AI stops normal troubleshooting and immediately commands: *1. Press E-Stop, 2. Apply Lock-Out/Tag-Out padlock, 3. Evacuate area*.

---

### Q7: How the Profile is Used to Personalize Future Support

```text
                                       EVOLVING WORKER PROFILE
                                 ┌───────────────────────────────────┐
                                 │ • Skill Level: Intermediate (40%) │
                                 │ • Prefers: Visual Step-by-Step    │
                                 │ • Problem Area: Failed Alarm 103  │
                                 │ • Clearance: Mechanical OK        │
                                 └───────────────────────────────────┘
                                                   │
         ┌────────────────────────┬────────────────┴────────────────┬────────────────────────┐
         ▼                        ▼                                 ▼                        ▼
 1. Automatic Format      2. Past Trouble Alert             3. Proactive Dispatch    4. Safety Clearance
 Automatically shows     Displays banner: "You had         Offers early technician  Blocks high-voltage
 visual tags & steps      trouble with Alarm 103 before"    help if initial fix fails wiring for novices
```

1. **Automatic Format Selection**:
   The assistant automatically serves the worker's preferred style (`Visual Step-by-Step`, `Terse Technical`, or `Detailed Tutorial`) without requiring them to ask.
2. **Warnings on Past Problem Alarms**:
   If a worker has previously struggled with an alarm (e.g. `Alarm 103`), the AI shows a warning banner and offers to call a maintenance technician right away if basic steps fail.
3. **Hiding Advanced Steps from Novices**:
   Dangerous internal diagnostic shortcuts are hidden from Novices and only shown to certified Experts.
4. **Safety Clearance Checks**:
   The system checks whether the worker is certified before showing electrical wiring steps. If not certified, it instructs them to call a certified electrician.

---

## 4. Assumptions Made

1. **Worker Login**: Every worker logs in with their own RFID badge or employee ID so the system knows who is operating the machine.
2. **Connected Machine Sensors**: The factory network allows the AI to read live SCADA sensor data and alarm timestamps.
3. **AI Only Gives Advice (Advisory Only)**: The AI assistant cannot press buttons or start/stop machines on its own. It only provides guidance on screen.
4. **8-Hour Success Standard**: If a machine runs for 8 hours without triggering the same alarm, the repair is considered successful.
5. **Supervisor Roster Info**: The system knows whether a supervisor is on the shopfloor or off-site.

---

## 5. Known Limitations of the Design

While this system introduces strong innovations in smart guidance and safety, there are several conceptual and design trade-offs:

### 5.1 Splitting Skills into 3 Simple Buckets (Novice, Intermediate, Expert)
* **What the design assumes**: A worker's skill on a machine can be boiled down to one number ($0\dots100\%$) and grouped into three tiers: Novice, Intermediate, or Expert.
* **The limitation**: Real human skills are complex. A worker might be a master at mechanical tool changes, but have no idea how to fix a pneumatic valve on the same machine. Grouping their entire machine skill into one score means the AI might sometimes pick a format that is slightly too simple or too advanced for a specific sub-task.

### 5.2 Using a Fixed 8-Hour Timer for All Machine Fixes
* **What the design assumes**: Waiting 8 hours without an alarm proves a fix was permanent.
* **The limitation**: Not all machine failures behave the same way:
  - **Slow-wearing parts**: A damaged bearing or contaminated hydraulic oil might take 3 to 4 days of heavy running to fail again. An 8-hour window might prematurely give credit for a fix that actually fails 2 days later.
  - **Unrelated issues**: If a totally different worker loads bad raw materials 6 hours later and trips the same alarm, the earlier worker is unfairly penalized for a fix that was actually fine.

### 5.3 Hard to Tell Who Caused an Alarm When Shifts Change
* **What the design assumes**: If an alarm recurs within 8 hours, it was caused by the worker who last fixed it.
* **The limitation**: Factories run 24/7 across multiple shifts. If Worker A fixes a machine at hour 7 and hands over to Worker B at hour 8, an alarm at hour 10 will penalize Worker A. However, Worker B might have caused the issue by pushing the machine too fast or using the wrong tools. The design cannot easily separate multi-worker blame across shift handovers.

### 5.4 Relying on Workers to Honestly Admit Shortcuts
* **What the design assumes**: When asked *"Did you use shortcut X?"*, workers will answer honestly.
* **The limitation**: Real shopfloor psychology can get in the way:
  - **Fear of getting in trouble**: If a factory has a strict culture, workers might fear punishment for breaking official rules and click "No", causing useful tricks to be lost.
  - **Rushing through prompts**: Workers trying to hit production targets might quickly tap "Yes" or "No" just to clear the screen, adding inaccurate data to the review list.

### 5.5 Requiring 3 Experts When a Small Plant Might Only Have 1 or 2
* **What the design assumes**: Every machine has at least 3 certified Experts who can review and approve new shortcuts.
* **The limitation**: In small manufacturing shops or niche workcells, there may only be 1 or 2 senior experts in the entire company. In this case, new shortcuts will stay stuck in the quarantine list forever because 3 signatures can never be reached.

### 5.6 Focusing on Text Style Instead of Step-by-Step Coaching
* **What the design assumes**: Changing the explanation style (Visual vs. Short vs. Detailed) is the main way to help different skill levels.
* **The limitation**: True teaching is more than just changing text style. It requires interactive coaching—such as asking the worker to confirm Step 1 before showing Step 2, or asking quiz questions to verify they understand what they are doing.

### 5.7 The AI Cannot Physically Stop an Unsafe Action (Advisory Only)
* **What the design assumes**: The AI acts purely as an advisor on a screen and cannot send commands to the machine PLC.
* **The limitation**: While this is safe for software design, it means the AI cannot physically lock the machine doors or stop a worker who decides to ignore a safety warning and press Start anyway. Safety still depends 100% on human obedience.

### 5.8 Brand New Machines Start with No Fix History (Cold Start)
* **What the design assumes**: Fix paths are ranked by real past success rates ($P = \frac{s+1}{s+f+2}$).
* **The limitation**: When a brand new machine is installed, it has zero past repair data ($s=0, f=0$, so every path starts at $50\%$). Until the machine has broken down and been fixed several times, the AI cannot know which fix steps work best and must rely purely on standard manual order.

---

## 6. Companion Documentation Links

| Document | Focus Area | Contents |
|---|---|---|
| 🏛️ [`solution_design.md`](solution_design.md) | **System Architecture** | Full mathematical formulas, two-loop architecture, and FMEA safety tables. |
| 📊 [`evaluation_framework_design.md`](evaluation_framework_design.md) | **Evaluation Framework** | Offline development metrics, online production telemetry, and business impact KPIs. |
| 🧪 [`demo_and_evaluation_guide.md`](demo_and_evaluation_guide.md) | **Interactive Demo & Test Cases** | Multi-turn behavioral walkthroughs and modular test scenarios for Streamlit evaluation. |
| 📦 [`code_and_modules_guide.md`](code_and_modules_guide.md) | **Technical Specifications** | Module-by-module breakdown of all classes, methods, arguments, and return types. |
| ⚙️ [`run_and_configuration_guide.md`](run_and_configuration_guide.md) | **Setup & Operations** | Environment installation, CLI commands, JSON storage structure, and operations FAQ. |
