# Step-by-Step Interactive Demo & Evaluation Guide

## Table of Contents

- [1. Important UI Navigation Notes](#1-important-ui-navigation-notes)
  - [1.1 How to Open the Sidebar (Collapsed by Default)](#11-how-to-open-the-sidebar-collapsed-by-default)
  - [1.2 How to Open the Inspector Panel (Hidden by Default)](#12-how-to-open-the-inspector-panel-hidden-by-default)
  - [1.3 Understanding What Updates Immediately vs. What Requires the Sleep Cycle](#13-understanding-what-updates-immediately-vs-what-requires-the-sleep-cycle)
- [2. Pre-Seeded Factory State Reference](#2-pre-seeded-factory-state-reference)
- [3. The End-to-End Incremental Learning Journey (Featured Walkthrough)](#3-the-end-to-end-incremental-learning-journey-featured-walkthrough)
  - [Act 1: Initial Baseline Query (Novice Visual Guidance)](#act-1-initial-baseline-query-novice-visual-guidance)
  - [Act 2: Human Agency & Instant Format Override (-10.0 Penalty)](#act-2-human-agency--instant-format-override--100-penalty)
  - [Act 3: Independent Fix & 8-Hour Durability Escrow (Live Shift Buffering)](#act-3-independent-fix--8-hour-durability-escrow-live-shift-buffering)
  - [Act 4: Overnight Sleep Cycle Execution (Batch Durability Audit & Tier Promotion)](#act-4-overnight-sleep-cycle-execution-batch-durability-audit--tier-promotion)
  - [Act 5: Next-Shift Query with Cumulative Multi-Signal Personalization](#act-5-next-shift-query-with-cumulative-multi-signal-personalization)
  - [Act 6: Rapid Triage & Micro-Debrief Inquiry (Capturing Shopfloor Shortcuts)](#act-6-rapid-triage--micro-debrief-inquiry-capturing-shopfloor-shortcuts)
  - [Act 7: 3-Expert Consensus & Automatic Skill Library Promotion](#act-7-3-expert-consensus--automatic-skill-library-promotion)
- [4. Specialized Deep-Dive Test Scenarios](#4-specialized-deep-dive-test-scenarios)
  - [Scenario A: Decoupled Domain Competence (Sarah on CNC vs. Injection Molder)](#scenario-a-decoupled-domain-competence-sarah-on-cnc-vs-injection-molder)
  - [Scenario B: Historical Failure Warnings & Proactive Maintenance Escalation](#scenario-b-historical-failure-warnings--proactive-maintenance-escalation)
  - [Scenario C: ECM Fatigue Gate (100% Exploitation Mode)](#scenario-c-ecm-fatigue-gate-100-exploitation-mode)
  - [Scenario D: ECM Supervisor Offline Gate (Safe Independent Triage)](#scenario-d-ecm-supervisor-offline-gate-safe-independent-triage)
  - [Scenario E: Critical Severity-1 Emergency SOS Shutdown Protocol](#scenario-e-critical-severity-1-emergency-sos-shutdown-protocol)
- [5. Demo Reset & State Cleanup](#5-demo-reset--state-cleanup)
- [6. Automated Command-Line Verification](#6-automated-command-line-verification)

---

## 1. Important UI Navigation Notes

Before running any test, please note these essential UI navigation details:

### 1.1 How to Open the Sidebar (Collapsed by Default)
* In the Streamlit app, the sidebar is **collapsed by default** to give maximum screen space to the chat.
* **To open the sidebar**: Click the small arrow **`>`** in the top-left corner of the browser window.
* The sidebar contains operator selection, machine selection, SCADA telemetry triggers, ECM sliders, and the **`🌙 Run Sleep Cycle (Batch)`** button.

```text
  [ > ] ─────────────────────────────────────────────────────────── [ ▶️ Inspector ]
  (Click to OPEN SIDEBAR)                                    (Click to OPEN INSPECTOR)
```

### 1.2 How to Open the Inspector Panel (Hidden by Default)
* The Inspector panel is **hidden by default**.
* **To open the Inspector**: Look at the top-right of the chat header and click **`▶️ Inspector`**.
* The screen will split into two columns:
  - **Left**: Main Chat Area, Format Overrides, Feedback buttons.
  - **Right**: Inspector with 3 tabs (`🛡️ Active Safety`, `⚙️ Model State`, `📋 Logs`).
* **To close the Inspector**: Click **`◀️ Hide`** in the header.

### 1.3 Understanding What Updates Immediately vs. What Requires the Sleep Cycle

To understand what you will see in the UI and Inspector, keep this rule in mind:

| Action in UI | When Does State Update? | Where to Look in UI |
|---|---|---|
| **⚡ Format Override Buttons** | **INSTANT** (Real-Time in Shift) | Inspector Tab 2 (`⚙️ Model State`) immediately shows -10.0 penalty and new UCB weights. |
| **🤖 Micro-Debrief "Yes/No"** | **INSTANT** (Real-Time in Shift) | Inspector Tab 1 (`🛡️ Active Safety`) immediately shows shortcut in Quarantine. |
| **✍️ Expert Sign-Off Buttons** | **INSTANT** (Real-Time in Shift) | Inspector Tab 1 (`🛡️ Active Safety`) immediately increments signatures ($1/3 \rightarrow 2/3 \rightarrow 3/3$). |
| **⚙️ ECM Fatigue / Supervisor Gates** | **INSTANT** (Real-Time in Shift) | Main chat badge and working memory prompt immediately adapt. |
| **✅ "Solved Independently" Feedback** | **HELD IN ESCROW** (Requires Sleep Cycle) | Sidebar shows `Escrow Held: 1`. Autonomy score stays unchanged until Sleep Cycle runs. |
| **⚠️ "Escalate to Supervisor" Feedback** | **QUEUED IN SHIFT LOGS** (Requires Sleep Cycle) | Sidebar shows `Shift Events: 1`. Penalty stays queued until Sleep Cycle runs. |
| **🌙 "Run Sleep Cycle (Batch)" Button** | **EXECUTES OVERNIGHT BATCH MATH** | Processes escrow, verifies 8h durability, mutates autonomy score (+5% or -15%), advances tiers (Novice $\rightarrow$ Intermediate), and flushes queues. |

---

## 2. Pre-Seeded Factory State Reference

The application is pre-seeded with the following realistic factory baseline state:

| Operator | Machine | Pre-Seeded Autonomy | Pre-Seeded Tier | Winning Format Arm | Notes |
|---|---|---|---|---|---|
| **John Doe (`OP-001`)** | **Haas VF-2 (CNC)** | **35.0%** | **Novice** | `Visual_StepByStep` | Junior CNC machinist; has escalated Alarm 103 twice. |
| **John Doe (`OP-001`)** | **Engel Victory 330** | **30.0%** | **Novice** | `Visual_StepByStep` | Junior operator. |
| **Sarah Jenkins (`OP-002`)** | **Haas VF-2 (CNC)** | **95.0%** | **Expert** | `Terse_Technical` | 10+ years CNC experience. |
| **Sarah Jenkins (`OP-002`)** | **Engel Victory 330** | **12.0%** | **Novice** | `Visual_StepByStep` | Brand new to plastic injection molding. |
| **Mike Chen (`OP-003`)** | **Haas VF-2 (CNC)** | **58.0%** | **Intermediate** | `Detailed_Text` | Mid-level machinist. |
| **Mike Chen (`OP-003`)** | **Engel Victory 330** | **62.0%** | **Intermediate** | `Detailed_Text` | Mid-level technician. |

---

## 3. The End-to-End Incremental Learning Journey (Featured Walkthrough)

> **No Resets Required**: Follow these 7 acts sequentially. Each step builds cumulatively on the previous step, showing how the assistant evolves its understanding of **John Doe (`OP-001`)** from a junior novice on Shift 1 to an intermediate operator on Shift 2.

```text
  [Act 1: Novice Query] ──> [Act 2: Format Override] ──> [Act 3: Escrow Buffer]
                                                                │
                                                                ▼
  [Act 5: Next-Shift Query] <── [Act 4: Overnight Sleep Cycle Evaluator]
          │
          ▼
  [Act 6: Micro-Debrief] ──> [Act 7: 3-Expert Auto-Promotion]
```

---

### Act 1: Initial Baseline Query (Novice Visual Guidance)

**Context**: It is morning on Shift 1. John Doe (Novice, 35% Autonomy) encounters an alarm on the Haas VF-2 CNC machine.

1. **Open Sidebar**: Click the arrow **`>`** in the top-left corner.
2. **Select Operator & Machine**:
   - Under **👤 Active Operator**, choose `John Doe (OP-001)`.
   - Under **⚙️ Workcell Machine**, choose `Haas VF-2`.
   - *Sidebar Observation*: Notice `MACHINE CONFIDENCE: Haas VF-2: Novice (35.0%)`.
3. **Ask a Question**: In the chat, click the quick diagnostic button **`Alarm 102: Servos Off`**.
4. **Observe Response**:
   - Format Badge: `Bandit Arm: Visual_StepByStep (Novice State)`.
   - The assistant serves step-by-step visual guidance with `[SAFETY]`, `[INSPECT]`, and `[ACTION]` checkboxes.

---

### Act 2: Human Agency & Instant Format Override (-10.0 Penalty)

**Context**: John prefers a detailed textual explanation rather than bulleted visual checkboxes. He exercises human agency to override the AI.

1. **Trigger Override**: Below the assistant's response, look at the **`⚡ Format Override`** bar and click **`Detailed Tutorial`**.
2. **Observe Instant Response Rewrite**:
   - Toast appears: `Format override applied.`
   - The response instantly rewrites into an in-depth electro-mechanical tutorial.
   - Badge updates to: `OVERRIDE: Detailed_Text (Novice)`.
3. **Observe Instant UCB State Penalty (No Sleep Cycle Needed)**:
   - In the top-right header, click **`▶️ Inspector`** $\rightarrow$ open Tab 2 (**`⚙️ Model State`**).
   - Under **`🎰 UCB Scores — Novice Tier`**, observe the live table:
     - The rejected `Visual_StepByStep` weight has dropped by **`-10.0`** (from `3.0` $\rightarrow$ **`-7.0`**).
     - The requested `Detailed_Text` weight has surged by **`+2.0`** (from `0.2` $\rightarrow$ **`2.2`**).
     - The active policy instantly flips to **`Detailed_Text`**!

---

### Act 3: Independent Fix & 8-Hour Durability Escrow (Live Shift Buffering)

**Context**: John applies the guidance and successfully clears the alarm. He reports resolution, but the AI holds credit in escrow to guard against temporary "duct-tape" fixes.

1. **Report Resolution**: Below the response, click **`✅ Solved Independently`**.
2. **Observe Escrow Buffering (Live Shift State)**:
   - Toast appears: `Resolution held in 8-hr durability escrow.`
   - Look at the Sidebar under **🛡️ Safety Escrow & Batch**:
     - `Escrow Held: 1`
     - Notice John's autonomy score is **STILL `35.0%`** (credit is buffered in `data/escrow_rewards.json` to verify durability).

---

### Act 4: Overnight Sleep Cycle Execution (Batch Durability Audit & Tier Promotion)

**Context**: Shift 1 concludes. The factory runs its overnight Sleep Cycle batch job (03:00 AM) via `SleepCycleEvaluator`.

1. **Run Sleep Cycle**: In the Sidebar, click the button **`🌙 Run Sleep Cycle (Batch)`**.
2. **Observe Durability Audit & Permanent State Mutation**:
   - Toast appears: `Sleep Cycle completed: 1 events, 1 escrow records.`
   - Look at the Sidebar:
     - Escrow queue is verified and flushed: `Escrow Held: 0`.
     - SCADA telemetry confirms 0 recurring alarms during the 8-hour window.
     - John Doe's machine autonomy permanently increases: **`35.0% ➔ 40.0%`**!
     - John Doe's derived tier automatically crosses the threshold: **`Novice ➔ Intermediate`**!
3. **Verify in Inspector**:
   - In Inspector Tab 1 (**`🛡️ Active Safety`**), expand **`👤 Operator Machine Profile`**.
   - Verify John's new standing: `Haas VF-2: 40.0% (Intermediate)`.

---

### Act 5: Next-Shift Query with Cumulative Multi-Signal Personalization

**Context**: It is the next morning (Shift 2). John returns to work. When he asks a question, the assistant considers **BOTH** his newly promoted Intermediate skill tier and his learned format preferences.

1. **Ask a New Question**: In the chat, click **`G-code: Peck Drilling`** (or type `What G-code is used for peck drilling cycles?`).
2. **Observe Cumulative Personalization**:
   - Format Badge: `Bandit Arm: Detailed_Text (Intermediate State)`.
   - The assistant serves intermediate-level CNC machining parameters (`G83`, `Q-peck`, `R-plane`, `F-feed`) in his preferred detailed structure, with zero novice handholding.

---

### Act 6: Rapid Triage & Micro-Debrief Inquiry (Capturing Shopfloor Shortcuts)

**Context**: John clears a pneumatic alarm in only ~2.0 minutes (standard SOP takes ~10.0 minutes). The system detects the unusually fast repair and triggers a human verification debrief.

1. **Observe Micro-Debrief Banner**: At the top of the chat area, look at the golden inquiry box:
   > 🤖 **Copilot Micro-Debrief Inquiry**  
   > *Earlier you resolved Alarm 102 in ~2.0 min (Standard SOP takes ~10.0 min).*  
   > **Did you use the 'Manual High-Pressure Solenoid Bypass'?**
2. **Confirm Shortcut**: Click **`✅ Yes, used shortcut`**.
   - Toast appears: `Operator confirmed shortcut... Successfully routed to Quarantine Database.`
3. **Inspect Quarantine Candidate**:
   - In Inspector Tab 1 (**`🛡️ Active Safety`**), look under **`🧪 Quarantine Candidates`**.
   - Locate `Manual High-Pressure Solenoid Bypass`.
   - Notice the status: `Expert Sign-offs: 2/3`.
   - Notice John Doe (Intermediate) sees: `⚠️ Expert tier required to sign off.` (Non-experts cannot approve shortcuts).

---

### Act 7: 3-Expert Consensus & Automatic Skill Library Promotion

**Context**: Senior Machinist Sarah Jenkins (`OP-002`) reviews the quarantined shortcut and provides the 3rd expert signature.

1. **Switch to Senior Expert**:
   - Open Sidebar (`>`) $\rightarrow$ under **👤 Active Operator**, select `Sarah Jenkins (OP-002)` (Expert on Haas VF-2).
2. **Provide 3rd Signature**:
   - In Inspector Tab 1 (**`🛡️ Active Safety`**), the button **`✍️ Sign Off (Sarah Jenkins)`** is now active!
   - Click **`✍️ Sign Off (Sarah Jenkins)`**.
3. **Observe Automatic Skill Library Promotion**:
   - The banner celebrates: `🎉 Promoted to Active Skill Library!`
   - The shortcut immediately moves from `quarantine_sops.json` into the active fault tree library (`procedural_fault_trees.json`) with `[min_tier_required: 'Expert']`.

---

## 4. Specialized Deep-Dive Test Scenarios

These modular tests demonstrate additional safety guardrails, contextual matrix gates, and domain fencing mechanisms.

---

### Scenario A: Decoupled Domain Competence (Sarah on CNC vs. Injection Molder)

**Claim**: Machine skills are strictly decoupled. An Expert on CNC Machining is treated as a Novice on Injection Molding without cross-machine leakage.

1. **CNC Test**: Select `Sarah Jenkins (OP-002)` + `Haas VF-2` (Expert: 95.0%).
   - Ask `Alarm 102: Servos Off` $\rightarrow$ AI responds in **`Terse_Technical`** ($<45$ words, raw setpoints).
2. **Molding Test**: Switch machine to `Engel Victory 330` (Novice: 12.0%).
   - Ask `E-201: Barrel Overheat` $\rightarrow$ AI automatically responds in **`Visual_StepByStep`** (detailed numbered safety checklists).
3. **Inspect**: Open Inspector Tab 1 $\rightarrow$ `👤 Operator Machine Profile` to view her two independent competence bars (`95.0%` vs `12.0%`).

---

### Scenario B: Historical Failure Warnings & Proactive Maintenance Escalation

**Claim**: The system inspects episodic logs for recurring trouble codes and injects proactive warnings and early Level 2 technician support when an operator struggles.

1. **Setup**: Select `John Doe (OP-001)` + `Haas VF-2`.
2. **Trigger SCADA Alarm**: In Sidebar, click **`Trigger Alarm`** (sets active alarm to `Alarm 102`).
   - Chat header displays golden alert: `⚠️ Historical Failure Pattern: John Doe has escalated Alarm 102 2 time(s). Proactive assistance enabled.`
3. **Ask & Escalate**: Click **`Alarm 103: Servo Error`** $\rightarrow$ click **`⚠️ Escalate to Supervisor`**.
4. **Observe**: Generates CMMS escalation ticket (`TICK-2026-XXXXXX`) and queues penalty for Sleep Cycle.

---

### Scenario C: ECM Fatigue Gate (100% Exploitation Mode)

**Claim**: Late in a 12-hour shift ($80\%+$ fatigue), the AI stops exploring new formats ($c=0.0$), removes conversational filler, and locks to ultra-scannable bullet points.

1. **Setup**: Open Sidebar (`>`) $\rightarrow$ expand **`⚙️ Context Parameters`**.
2. **Simulate Fatigue**: Drag **`Shift Hour (Fatigue Gauge)`** slider to **`10.5`** hours (Fatigue Index = $88\%$).
   - Sidebar displays red alert: `⚡ Fatigue Gate ACTIVE — 100% Exploit (88%)`.
3. **Ask Question**: Click **`G-code: Peck Drilling`**.
   - Output contains zero conversational filler, restricted strictly to `G83` parameters.
4. **Inspect**: In Inspector Tab 2, verify exploration bonus is forced to `0.000`.

---

### Scenario D: ECM Supervisor Offline Gate (Safe Independent Triage)

**Claim**: When the supervisor is off-site, the AI restricts Level 2 maintenance escalation and guides the worker through safe external checks or safe machine shutdown.

1. **Setup**: Open Sidebar (`>`) $\rightarrow$ expand **`⚙️ Context Parameters`** $\rightarrow$ uncheck **`Supervisor On-Site`**.
   - Warning appears: `🚨 Supervisor Gate ACTIVE (Offline Override)`.
2. **Ask Question**: Click **`Alarm 102: Servos Off`**.
3. **Inspect Working Memory**: Expand `🧠 View Assembled Working Memory Prompt` in the chat message to verify the mandatory injected constraint:
   > *"🚨 SYSTEM OVERRIDE (SUPERVISOR OFFLINE): Shift Supervisor is currently OFFLINE... do NOT suggest escalating to Level 2 Maintenance. Operator must resolve independently or safely halt production."*

---

### Scenario E: Critical Severity-1 Emergency SOS Shutdown Protocol

**Claim**: During life-safety or catastrophic machine events (smoke, vibration), personalization and exploration are completely suspended in favor of deterministic E-Stop, LOTO, and evacuation steps.

1. **Setup**: In Sidebar `⚙️ Context Parameters`, check **`🚨 Critical Severity-1 Hazard`**.
2. **Ask Any Question**: Type `Spindle grinding noise and smoke detected` (or click any quick button).
3. **Observe Deterministic Output**:
   - Format Badge: `Bandit Arm: SOS_SHUTDOWN`.
   - Normal troubleshooting is suspended; outputs mandatory 3-step emergency halt (E-Stop $\rightarrow$ LOTO $\rightarrow$ Evacuate).

---

## 5. Demo Reset & State Cleanup

To return the entire demo environment to its pristine baseline state at any time:

1. **Via the UI**:
   - Open Sidebar (`>`) $\rightarrow$ click the **`♻️ Reset Defaults`** button.
2. **Via Command Line**:
   ```bash
   uv run python -c "from memory.semantic_graph import OperatorKnowledgeGraph; from memory.episodic_store import EpisodicMemory; from memory.debrief_store import DebriefManager; OperatorKnowledgeGraph()._seed_default_graph(); EpisodicMemory().clear_event_queue(); EpisodicMemory().clear_escrow_records(); DebriefManager().clear_all_pending()"
   ```

---

## 6. Companion Documentation Suite

| Document | Focus Area | Contents |
|---|---|---|
| 🏛️ [`solution_design.md`](solution_design.md) | **System Architecture** | Full mathematical formulas, two-loop architecture, and FMEA safety tables. |
| 📊 [`evaluation_framework_design.md`](evaluation_framework_design.md) | **Evaluation Framework** | Offline development metrics, online production telemetry, and business impact KPIs. |
| 💡 [`architecture_and_behavioral_qa.md`](architecture_and_behavioral_qa.md) | **Architecture & Behavioral Q&A** | Deep-dive answers on pattern extraction, learning mechanisms, data sources, and safety. |
| 📦 [`code_and_modules_guide.md`](code_and_modules_guide.md) | **Technical Specifications** | Module-by-module breakdown of all classes, methods, arguments, and return types. |
| ⚙️ [`run_and_configuration_guide.md`](run_and_configuration_guide.md) | **Setup & Operations** | Environment installation, CLI commands, JSON storage structure, and operations FAQ. |
