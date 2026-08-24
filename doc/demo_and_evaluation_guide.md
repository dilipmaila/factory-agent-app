# Interactive Demo & Test Evaluation Guide: Factory Operator AI Assistant

## Table of Contents

- [1. Overview & Setup](#1-overview--setup)
  - [1.1 Launching the Application](#11-launching-the-application)
  - [1.2 UI Layout Map](#12-ui-layout-map)
- [2. Featured Demo: Behavioral Profile Evolution (The 5-Step Adaptive Loop)](#2-featured-demo-behavioral-profile-evolution-the-5-step-adaptive-loop)
  - [2.1 The 5-Stage Behavioral Architecture](#21-the-5-stage-behavioral-architecture)
  - [2.2 Multi-Turn Operator Walkthrough (Operator A / John Doe)](#22-multi-turn-operator-walkthrough-operator-a--john-doe)
    - [Turn 1: Extracting Visual Instruction Preference Signal](#turn-1-extracting-visual-instruction-preference-signal)
    - [Turn 2: Extracting Basic Troubleshooting Autonomy Signal](#turn-2-extracting-basic-troubleshooting-autonomy-signal)
    - [Turn 3: Extracting Complex Fault Escalation Signal](#turn-3-extracting-complex-fault-escalation-signal)
    - [Turn 4: Nightly Sleep Cycle (Profile Mutation & Confidence Assignment)](#turn-4-nightly-sleep-cycle-profile-mutation--confidence-assignment)
    - [Turn 5: Future Turn Verification (Personalized Grounding in Action)](#turn-5-future-turn-verification-personalized-grounding-in-action)
- [3. Design Claims vs. Demo Verification Matrix](#3-design-claims-vs-demo-verification-matrix)
- [4. Detailed Modular Test Scenarios](#4-detailed-modular-test-scenarios)
  - [Test Scenario 1: Decoupled Domain Competence & Machine Independence](#test-scenario-1-decoupled-domain-competence--machine-independence)
  - [Test Scenario 2: State-Bound Contextual Bandit Format Selection (UCB1)](#test-scenario-2-state-bound-contextual-bandit-format-selection-ucb1)
  - [Test Scenario 3: Human Format Override & Mathematical Penalization (-10.0)](#test-scenario-3-human-format-override--mathematical-penalization--100)
  - [Test Scenario 4: Dynamic Bayesian Fault Trees & Anti-Pattern Warnings](#test-scenario-4-dynamic-bayesian-fault-trees--anti-pattern-warnings)
  - [Test Scenario 5: ECM Fatigue Gate (100% Exploitation Mode)](#test-scenario-5-ecm-fatigue-gate-100-exploitation-mode)
  - [Test Scenario 6: ECM Supervisor Offline Gate (Safe Independent Triage)](#test-scenario-6-ecm-supervisor-offline-gate-safe-independent-triage)
  - [Test Scenario 7: Micro-Debrief Loop & 3-Expert Consensus Auto-Promotion](#test-scenario-7-micro-debrief-loop--3-expert-consensus-auto-promotion)
  - [Test Scenario 8: 8-Hour Durability Escrow & Nightly Sleep Cycle Processing](#test-scenario-8-8-hour-durability-escrow--nightly-sleep-cycle-processing)
  - [Test Scenario 9: Emergency Severity-1 SOS Shutdown Protocol](#test-scenario-9-emergency-severity-1-sos-shutdown-protocol)
  - [Test Scenario 10: Domain Fencing & Mechanical Similarity Traversal](#test-scenario-10-domain-fencing--mechanical-similarity-traversal)
- [5. Automated Terminal Verification Suites](#5-automated-terminal-verification-suites)
- [6. Demo Reset & State Cleanup](#6-demo-reset--state-cleanup)

---

## 1. Overview & Setup

This guide provides end-to-end test scenarios to demonstrate and evaluate all architectural claims and mathematical behaviors described in [`solution_design.md`](solution_design.md).

### 1.1 Launching the Application

1. **Verify Environment**:
   Ensure `.env` contains your `GOOGLE_API_KEY`:
   ```bash
   GOOGLE_API_KEY="your_api_key_here"
   ```

2. **Start the Streamlit Web Interface**:
   ```bash
   uv run streamlit run app.py
   ```
   *The browser opens automatically at `http://localhost:8501`.*

---

### 1.2 UI Layout Map

```text
+---------------------------------------------------------------------------------------------------------+
|                                    FACTORY OPERATOR AI ASSISTANT                                        |
+------------------------------+---------------------------------------------------+----------------------+
| SIDEBAR CONTROLS             | MAIN SHOPFLOOR CHAT AREA                          | INSPECTOR PANEL (Tab)|
|                              |                                                   | (Click "▶️ Inspector")|
| 👤 Active Operator Selector   | 💬 Chat Message History                           |                      |
|    - John Doe (OP-001)       |    - Format Badges [Terse / Visual / Detailed]    | 🛡️ Active Safety      |
|    - Sarah Jenkins (OP-002)  |    - Fault Tree Badges [🌳 Alarm 102]             |    - Quarantine SOPs |
|    - Mike Chen (OP-003)      |    - Fatigue Badges [⚡ Fatigue Gate]             |    - 3-Expert Sign-off|
|                              |    - Grounding & Working Memory Expanders         |    - Skill Library   |
| ⚙️ Workcell Machine Selector  |                                                   |                      |
|    - Haas VF-2 (CNC Mill)    | ⚡ Format Override Bar                            | ⚙️ Model State        |
|    - Engel Victory 330 (Mold)|    [Terse] [Visual] [Detailed]                    |    - Assembled Prompt|
|                              |                                                   |    - UCB Score Table |
| 📡 SCADA Telemetry Box       | 💡 Quick Diagnostic Buttons                       |                      |
|    [Trigger Alarm] [Clear]   |    [Alarm 102] [Alarm 103] [G-Code]               | 📋 Logs              |
|                              |                                                   |    - ECM Fatigue %   |
| ⚙️ Context Parameters (ECM)  | ------------------------------------------------- |    - Debrief Records |
|    - Shift Hours Slider      | ⌨️ Fixed Bottom Chat Input Bar                    |                      |
|    - Supervisor On-Site (Y/N)|                                                   |                      |
|    - Critical Severity-1     |                                                   |                      |
|                              |                                                   |                      |
| 🛡️ Escrow & Sleep Cycle      |                                                   |                      |
|    [🌙 Run Sleep Cycle]      |                                                   |                      |
|    [♻️ Reset Defaults]       |                                                   |                      |
+------------------------------+---------------------------------------------------+----------------------+
```

---

## 2. Featured Demo: Behavioral Profile Evolution (The 5-Step Adaptive Loop)

This core walkthrough demonstrates how the assistant observes an operator across multiple turns, infers behavioral traits and domain confidence, updates their persistent profile, and tailors future responses.

### 2.1 The 5-Stage Behavioral Architecture

```text
  [1. Receive Interactions] ──> [2. Extract Signals] ──> [3. Mutate Profile] ──> [4. Assign Confidence] ──> [5. Personalize Response]
  - Repeated queries            - Explicit format        - Episodic logging      - Machine Autonomy %        - Default to Visual
  - Simple vs complex alarms      overrides (Visual)     - Event queue append    - Bandit UCB scores         - Direct basic fix paths
  - Resolution feedback         - Independent solve      - Sleep Cycle batch     - Historical failure        - Proactive L2 escalation
                                - Quick CMMS escalation    state persistence       counter (Alarm 103)         offer on complex faults
```

---

### 2.2 Multi-Turn Operator Walkthrough (Operator A / John Doe)

In this scenario, we observe **Operator A (`John Doe / OP-001`)** on the **`Haas VF-2`** CNC Machine:
* **Behavior 1**: Operator A repeatedly prefers and selects **Visual Instructions**.
* **Behavior 2**: Operator A resolves **simple machine alarms** (e.g. pneumatic resets) independently.
* **Behavior 3**: Operator A quickly escalates **complex machine alarms** (e.g. encoder/servo faults).

**System Inferences Formed**:
1. **Format Profile**: Prefers visual step-by-step guidance.
2. **Domain Skill**: Highly confident with basic shopfloor triage.
3. **Escalation Profile**: Requires proactive Level 2 maintenance support for complex fault diagnosis.

---

#### Turn 1: Extracting Visual Instruction Preference Signal

1. **Setup**:
   - In the sidebar, set **Active Operator**: `John Doe (OP-001)`.
   - Set **Active Machine**: `Haas VF-2`.
2. **Action**:
   - Ask: `What G-code is used for peck drilling cycles?`.
3. **Observation**:
   - If the bandit serves an alternative format, look below the assistant's response at the **`⚡ Format Override`** bar.
   - Click the button: **`Visual Step-by-Step`**.
4. **Behavioral Signal Extracted**:
   - **Rejection Signal**: Operator rejected the non-visual format $\rightarrow$ applies a hard **-10.0** weight penalty.
   - **Reinforcement Signal**: Operator selected Visual $\rightarrow$ applies a **+2.0** reward boost to `Visual_StepByStep`.
5. **Confidence Verification**:
   - Open **`▶️ Inspector`** $\rightarrow$ **`⚙️ Model State`** tab.
   - Look at the **`🎰 UCB Scores — Novice Tier`** table: `Visual_StepByStep` now dominates the UCB ranking ($W \ge 5.0$, Highest UCB Score).

---

#### Turn 2: Extracting Basic Troubleshooting Autonomy Signal

1. **Action**:
   - In the chat, click the quick button: **`Alarm 102: Servos Off`** (or type `How do I clear SERVOS OFF (Alarm 102)?`).
2. **Assistant Guidance**:
   - Responds in structured visual steps: `[SAFETY]`, `[INSPECT]`, `[ACTION]` (instructs checking the rear pneumatic regulator for $\ge 85\text{ PSI}$).
3. **Resolution Action**:
   - Operator resolves the simple issue and clicks **`✅ Solved Independently`** in the resolution feedback bar.
4. **Behavioral Signal Extracted**:
   - Fast, successful resolution on basic pneumatic triage $\rightarrow$ tags status `SUCCESS`.
   - Places provisional positive reward (**+1.0 bandit reward, +5.0 autonomy**) into the 8-hour durability holding escrow ledger (`data/escrow_rewards.json`).
5. **Observation**:
   - Notice in the sidebar: `Escrow Held: 1`. Autonomy is buffered safely to verify repair permanence before granting credit.

---

#### Turn 3: Extracting Complex Fault Escalation Signal

1. **Action**:
   - In the chat, click the quick button: **`Alarm 103: Servo Error`** (or type `X Axis SERVO ERROR TOO LARGE (Alarm 103)`).
2. **Assistant Guidance**:
   - Displays diagnostic steps for X-axis encoder feedback, timing belt deflection, and Maincon PCB ribbon connectors.
3. **Resolution Action**:
   - Operator realizes this is a complex internal electromechanical fault requiring Level 2 support.
   - Clicks **`⚠️ Escalate to Supervisor`** in the feedback bar.
4. **Behavioral Signal Extracted**:
   - Immediate CMMS work order dispatched (`TICK-2026-XXXXXX`) assigned to `L2_ELECTROMECHANICAL_MAINTENANCE`.
   - Event logged into `data/episodic_event_queue.json` tagged with `outcome_status: ESCALATED_CMMS` on `error_code: Alarm 103`.
5. **Observation**:
   - In the sidebar: `Shift Events: 1 | Escrow Held: 1`.

---

#### Turn 4: Nightly Sleep Cycle (Profile Mutation & Confidence Assignment)

1. **Action**:
   - In the sidebar, click the button: **`🌙 Run Sleep Cycle (Batch)`** (simulates the 03:00 AM overnight cron job).
2. **Backend Profile Mutations Applied**:
   - **Durability Verification**: Evaluates Alarm 102 escrow record against SCADA logs $\rightarrow$ Zero recurrent alarms found $\rightarrow$ Releases **+5.0 Autonomy Score** and **+1.0 Bandit Reward**.
   - **Skill Tier Promotion**: John Doe's machine autonomy increases from `35.0%` to **`40.0%`**, crossing the threshold to promote his derived tier from **`Novice` ➔ `Intermediate`**!
   - **Escalation Logging**: Archives Alarm 103 escalation into `data/episodic_logs.json` to track historical difficulty.
   - **Queue Flush**: Flushes shift queues (`Shift Events: 0 | Escrow Held: 0`).
3. **Resulting Persistent Profile State**:
   - **Format Preference**: High confidence for `Visual_StepByStep` ($>85\%$ selection probability).
   - **Basic Autonomy**: Certified Intermediate on basic machine triage ($40.0\%$).
   - **Complex Diagnosis**: Persistent escalation flag active for `Alarm 103`.

---

#### Turn 5: Future Turn Verification (Personalized Grounding in Action)

1. **Action**:
   - Query `Alarm 103` again: `How do I troubleshoot Alarm 103 servo error?`.
2. **Observe the Assistant's Evolved Behavior**:
   - **1. Automatic Format Personalization**: Outputs directly in `Visual_StepByStep` mode with checklists and flow arrows without requiring manual override.
   - **2. Historical Escalation Warning Banner**: Displays a prominent alert above the chat:
     > ⚠️ **Historical Failure Pattern**: *John Doe has historically experienced repeated difficulties and escalated Alarm 103 (1 prior escalation recorded). Proactive assistance enabled.*
   - **3. Proactive Dispatch Protocol**: The AI response proactively acknowledges the difficult history and offers to open an early CMMS dispatch if initial checks do not clear the fault.
   - **4. Clearance Filtering**: Safely keeps hazardous internal PCB component replacement fenced to certified technicians while guiding the operator through safe external way-lube checks.

---

## 3. Design Claims vs. Demo Verification Matrix

| # | Architectural Claim | Demo Test Scenario | Key UI Actions | Expected Output & Verification |
|---|---|---|---|---|
| **1** | **Decoupled Domain Competence** | [Scenario 1](#test-scenario-1-decoupled-domain-competence--machine-independence) | Switch Sarah Jenkins between Haas VF-2 and Engel 330. | CNC Expert (95%) gets `Terse_Technical`; Injection Molding Novice (12%) gets `Visual_StepByStep`. |
| **2** | **State-Bound Bandit Personalization** | [Scenario 2](#test-scenario-2-state-bound-contextual-bandit-format-selection-ucb1) | Query Alarm 102 as John Doe (Novice) vs Sarah (Expert). | John gets visual tags `[INSPECT]`, `[ACTION]`; Sarah gets concise M/G-codes under 45 words. |
| **3** | **Instant Format Override & Penalties** | [Scenario 3](#test-scenario-3-human-format-override--mathematical-penalization--100) | Click "Visual Step-by-Step" override button. | Instant response rewrite; rejected format penalized **-10.0** in UCB table. |
| **4** | **Bayesian Fault Trees & Anti-Patterns** | [Scenario 4](#test-scenario-4-dynamic-bayesian-fault-trees--anti-pattern-warnings) | Ask about Alarm 102 / E-201. | Primary fix ranked by Bayesian probability ($P=0.76$); explicit anti-pattern warnings ("❌ DO NOT"). |
| **5** | **ECM Fatigue Gate (100% Exploit)** | [Scenario 5](#test-scenario-5-ecm-fatigue-gate-100-exploitation-mode) | Drag shift slider to $\ge 80\%$ (10.5 hrs). | Red badge `⚡ Fatigue Gate ACTIVE`; exploration bonus drops to $0.0$; concise output enforced. |
| **6** | **Supervisor Offline Safety Gate** | [Scenario 6](#test-scenario-6-ecm-supervisor-offline-gate-safe-independent-triage) | Uncheck "Supervisor On-Site". | Prompts instruct safe independent triage or safe shutdown; blocks Level 2 maintenance escalation. |
| **7** | **Micro-Debrief & 3-Expert Consensus** | [Scenario 7](#test-scenario-7-micro-debrief-loop--3-expert-consensus-auto-promotion) | Confirm rapid fix $\rightarrow$ Sign off as Expert. | Shortcut sent to Quarantine; 3rd Expert signature triggers auto-promotion with `min_tier_required: 'Expert'`. |
| **8** | **8-Hour Durability & Sleep Cycle** | [Scenario 8](#test-scenario-8-8-hour-durability-escrow--nightly-sleep-cycle-processing) | Click "Solved Independently" $\rightarrow$ Run Sleep Cycle. | Rewards placed in escrow; Sleep Cycle verifies SCADA logs: awards **+1/+5** (durable) or penalizes **-5/-15** (recurrent). |
| **9** | **Emergency Severity-1 SOS Mode** | [Scenario 9](#test-scenario-9-emergency-severity-1-sos-shutdown-protocol) | Check "Critical Severity-1 Hazard". | Personalization suspended; deterministic E-Stop, LOTO, and evacuation protocol triggered. |
| **10**| **Domain Fencing & Graph Traversal** | [Scenario 10](#test-scenario-10-domain-fencing--mechanical-similarity-traversal) | Inspect high-voltage subsystem clearance. | Fencing blocks non-certified operators; mechanical similarity ($0.85$ CNC family) inferred across machines. |

---

## 4. Detailed Modular Test Scenarios

---

### Test Scenario 1: Decoupled Domain Competence & Machine Independence

**Objective**: Verify that operator skill is learned per machine and expertise on one machine does not leak to an unfamiliar machine.

#### Step-by-Step Actions:
1. In the sidebar, select **Active Operator**: `Sarah Jenkins (OP-002)`.
2. Select **Active Machine**: `Haas VF-2`.
   - *Sidebar Observation*: `MACHINE CONFIDENCE: Haas VF-2: Expert (95.0%)`.
3. In the chat area, click the quick button: `Alarm 102: Servos Off`.
   - *Chat Observation*: Response badge reads `Bandit Arm: Terse_Technical (Expert State)`. Output is strictly concise bullet points under 45 words with raw setpoints.
4. Now, without changing the operator, switch **Active Machine** in the sidebar to `Engel Victory 330`.
   - *Sidebar Observation*: `MACHINE CONFIDENCE: Engel Victory 330: Novice (12.0%)`.
5. Click the quick button: `E-201: Barrel Overheat`.
   - *Chat Observation*: Response badge reads `Bandit Arm: Visual_StepByStep (Novice State)`. Output switches to numbered steps with `[INSPECT]`, `[ACTION]`, and `[SAFETY]` tags.

#### Verification in Inspector:
* Click **`▶️ Inspector`** in the top right $\rightarrow$ open the **`🛡️ Active Safety`** tab.
* Expand **`👤 Operator Machine Profile`**: Notice Sarah has two distinct gauges: `Haas VF-2: 95.0% (Expert)` vs. `Engel Victory 330: 12.0% (Novice)`.

---

### Test Scenario 2: State-Bound Contextual Bandit Format Selection (UCB1)

**Objective**: Verify that the multi-armed bandit dynamically selects different formatting structures tailored to the operator's derived cognitive state.

#### Step-by-Step Actions:
1. In the sidebar, select **Active Operator**: `John Doe (OP-001)` (Novice, Autonomy: 35.0%) and **Active Machine**: `Haas VF-2`.
2. Type or click: `How do I clear SERVOS OFF (Alarm 102)?`.
3. Observe the response structure:
   - Visual tags: `[SAFETY]`, `[INSPECT]`, `[ACTION]`, `[VERIFY]`.
   - Markdown checklists `[ ]` and sequential step numbering.
4. Open the **`▶️ Inspector`** $\rightarrow$ select the **`⚙️ Model State`** tab.
5. In the **`🎰 UCB Scores — Novice Tier`** table, verify the scoring breakdown:
   - `Visual_StepByStep` has the highest UCB score.
   - Mean Reward, Pull Count, and Exploration Bonus are mathematically calculated.

---

### Test Scenario 3: Human Format Override & Mathematical Penalties (-10.0)

**Objective**: Verify that operator agency always takes precedence, and manual overrides immediately rewrite output and apply a **-10.0** penalty to the rejected bandit arm.

#### Step-by-Step Actions:
1. Select `Sarah Jenkins (OP-002)` + `Haas VF-2`.
2. Ask: `Alarm 102: Servos Off` (AI responds in `Terse_Technical`).
3. Below the response, look at the **`⚡ Format Override`** button bar:
   - Click the button: **`Visual Step-by-Step`**.
4. Observe the immediate changes:
   - A toast appears: `Format override applied.`
   - The assistant's response is rewritten into full numbered visual steps.
   - The message badge updates to `OVERRIDE: Visual_StepByStep (Expert)`.
5. Open **`▶️ Inspector`** $\rightarrow$ **`⚙️ Model State`** tab:
   - Look at the UCB Table for `Expert` tier.
   - Verify that `Terse_Technical` weight decreased by **-10.0** and its pull count incremented.

---

### Test Scenario 4: Dynamic Bayesian Fault Trees & Anti-Pattern Warnings

**Objective**: Verify that the AI ranks diagnostic paths by historical Bayesian success probability ($P(\text{Success}) = \frac{s + 1}{s + f + 2}$) and strictly warns against anti-patterns.

#### Step-by-Step Actions:
1. Select `John Doe (OP-001)` + `Haas VF-2`.
2. Ask: `How do I clear SERVOS OFF (Alarm 102)?`.
3. Review the assistant's output:
   - **Recommended Primary Fix**: Recommends `PATH_102_A: Pneumatic Pressure Verification` ($P \approx 76\%$) before electrical checks.
   - **Anti-Pattern Warning**: Prominently highlights:
     *"❌ DO NOT: Bypassing rear pneumatic pressure switch with an electrical jumper wire (Causes servo amplifier burnout, uncontrolled axis drop, and voids machine warranty)."*
4. Open **`▶️ Inspector`** $\rightarrow$ **`🛡️ Active Safety`** tab:
   - Expand **`🌳 Active Verified Skill Library`**.
   - Inspect the live probability progress bar and anti-pattern escalation risk levels.

---

### Test Scenario 5: ECM Fatigue Gate (100% Exploitation Mode)

**Objective**: Verify that when fatigue reaches $\ge 80\%$, the system shuts down exploration ($c = 0.0$) and enforces ultra-scannable terse formatting.

#### Step-by-Step Actions:
1. In the sidebar, expand **`⚙️ Context Parameters`**.
2. Drag the **`Shift Hour (Fatigue Gauge)`** slider to **`10.5`** hours (for a 12-hour shift, Fatigue Index = $88\%$).
3. Observe the sidebar alert:
   - `⚡ Fatigue Gate ACTIVE — 100% Exploit (88%)`.
4. Ask any question: `What G-code is used for peck drilling cycles?`.
5. Observe the response:
   - Badge displays: `⚡ Fatigue Gate: 100% Exploit`.
   - Output contains zero conversational filler, restricted strictly to `G83` peck drilling parameters.
6. Open **`▶️ Inspector`** $\rightarrow$ **`⚙️ Model State`** tab:
   - Check the UCB Score table: the exploration bonus column is forced to `0.000` (100% exploitation).

---

### Test Scenario 6: ECM Supervisor Offline Gate (Safe Independent Triage)

**Objective**: Verify that when the supervisor is offline, the AI injects safety holds and instructs safe independent triage or halt, rather than suggesting Level 2 escalation.

#### Step-by-Step Actions:
1. In the sidebar expander **`⚙️ Context Parameters`**, uncheck **`Supervisor On-Site`**.
2. Notice the sidebar warning: `🚨 Supervisor Gate ACTIVE (Offline Override)`.
3. Ask: `Alarm 102: Servos Off`.
4. Review the response:
   - The AI explicitly cautions that supervisor/Level 2 support is off-site.
   - It provides safe external verification steps and warns to safely halt the machine if unresolved.
5. In the chat message, expand **`🧠 View Assembled Working Memory Prompt`**:
   - Verify the injected directive:
     *"🚨 SYSTEM OVERRIDE (SUPERVISOR OFFLINE): Shift Supervisor is currently OFFLINE... do NOT suggest escalating to Level 2 Maintenance. Operator must resolve independently or safely halt production."*

---

### Test Scenario 7: Micro-Debrief Loop & 3-Expert Consensus Auto-Promotion

**Objective**: Verify that fast resolution triggers a human Yes/No verification inquiry and that 3 Senior Expert signatures promote a quarantined shortcut to the active library.

#### Part A: Trigger & Confirm Micro-Debrief
1. Select `John Doe (OP-001)` + `Haas VF-2`.
2. Look at the top of the chat area. A prominent golden inquiry banner appears:
   > 🤖 **Copilot Micro-Debrief Inquiry**  
   > *Earlier you resolved Alarm 102 in ~2.0 min (Standard SOP takes ~10.0 min). Did you use the 'Manual High-Pressure Solenoid Bypass'?*
3. Click **`✅ Yes, used shortcut`**.
4. Toast notification confirms: `Operator confirmed shortcut... Successfully routed to Quarantine Database`.

#### Part B: Expert Consensus Sign-Off
5. Open **`▶️ Inspector`** $\rightarrow$ **`🛡️ Active Safety`** tab.
6. Look at **`🧪 Quarantine Candidates`**:
   - Locate the shortcut. Notice the count: `Expert Sign-offs: 1/3` (or `2/3`).
   - Notice John Doe (Novice) has the caption: `⚠️ Expert tier required to sign off.`
7. In the sidebar, switch active operator to **`Sarah Jenkins (OP-002)`** (who is `Expert` on Haas VF-2).
8. In the Inspector panel, the button **`✍️ Sign Off (Sarah Jenkins)`** is now active!
9. Click **`✍️ Sign Off (Sarah Jenkins)`**:
   - Signature is recorded.
   - When the 3rd Expert signature is added, the banner celebrates: `🎉 Promoted to Active Skill Library!`
   - The shortcut immediately moves into the Active Verified Skill Library with `[min_tier_required: 'Expert']`.

---

### Test Scenario 8: 8-Hour Durability Escrow & Nightly Sleep Cycle Processing

**Objective**: Verify the "Duct-Tape Safeguard": positive rewards are held in escrow for 8 hours and only awarded if no recurrent alarms occur in SCADA logs.

#### Step-by-Step Actions:
1. Select `John Doe (OP-001)` + `Haas VF-2` (Autonomy: `35.0%`, Tier: `Novice`).
2. Ask: `Alarm 102: Servos Off`.
3. In the feedback bar below the response, click **`✅ Solved Independently`**.
4. Look at the sidebar:
   - Notice: `Escrow Held: 1`.
   - Notice John's autonomy score has **not** jumped yet (held in escrow to prevent duct-tape rewards).
5. In the sidebar, click the button: **`🌙 Run Sleep Cycle (Batch)`**.
6. Observe the batch evaluation:
   - Toast notification: `Sleep Cycle completed: 1 events, 1 escrow records.`
   - Durability window verified with zero recurring alarms.
   - John Doe's autonomy increases: **`35.0% ➔ 40.0%`**.
   - John Doe's tier automatically advances from **`Novice` ➔ `Intermediate`**!
   - Escrow queue is flushed (`Escrow Held: 0`).

---

### Test Scenario 9: Emergency Severity-1 SOS Shutdown Protocol

**Objective**: Verify that critical E-stop/emergency hazards immediately suspend personalization and output deterministic safety halt directives.

#### Step-by-Step Actions:
1. In the sidebar expander **`⚙️ Context Parameters`**, check **`🚨 Critical Severity-1 Hazard`**.
2. In the chat, type: `Machine is making grinding noise and smoke is visible`.
3. Observe the output:
   - Format badge displays: `Bandit Arm: SOS_SHUTDOWN`.
   - Response contains mandatory emergency halt steps:
     1. **Depress physical E-Stop pushbutton immediately**.
     2. **Disconnect main power breaker and apply Lock-Out/Tag-Out (LOTO) padlock**.
     3. **Evacuate machine cell and dispatch emergency Level 2 maintenance**.
   - Standard troubleshooting suggestions are completely suppressed.

---

### Test Scenario 10: Domain Fencing & Mechanical Similarity Traversal

**Objective**: Verify that high-voltage electrical actions are domain-fenced to prevent mechanical experts from performing unauthorized electrical work.

#### Step-by-Step Actions:
1. Select `Sarah Jenkins (OP-002)` + `Haas VF-2` (Mechanical Expert).
2. Open **`▶️ Inspector`** $\rightarrow$ **`🛡️ Active Safety`** tab $\rightarrow$ expand **`👤 Operator Machine Profile`**.
3. Observe the **Domain Fencing** check:
   - If High-Voltage electrical clearance is checked: `✅ High-Voltage: Authorized` (since Sarah is Expert $>80\%$).
4. Switch operator to `John Doe (OP-001)` (Novice):
   - Domain Fencing check updates to: `⚠️ High-Voltage: LOTO Senior required`.
   - Novice operators are blocked from accessing hazardous internal electrical sub-assemblies.

---

## 5. Automated Terminal Verification Suites

To run automated programmatic tests verifying all mathematical formulas, UCB algorithms, Bayesian probability calculations, and escrow durability checks without opening the browser:

```bash
# 1. Verify Section 2 (Decoupled Graph, State-bound Bandit, Fast Queue, Escrow)
uv run python verify_section2.py

# 2. Verify Section 3 (ECM Fatigue Gate, Supervisor Gate, Micro-Debrief Loop)
uv run python verify_section3.py

# 3. Verify Omni-Cognitive Guardrails (Anti-patterns, SOS Shutdown, Domain Fencing)
uv run python verify_omni_concepts.py

# 4. Run Batch Sleep Cycle Evaluator CLI
uv run python sleep_cycle_evaluator.py --verbose --force-mature
```

---

## 6. Demo Reset & State Cleanup

To return the entire demo environment to its pristine baseline state at any time:

1. **Via the UI**:
   Click the **`♻️ Reset Defaults`** button in the sidebar. This clears all session states, pending escrow rewards, debriefs, and restores default graph weights.
2. **Via Command Line**:
   ```bash
   uv run python -c "from memory.semantic_graph import OperatorKnowledgeGraph; OperatorKnowledgeGraph()._seed_default_graph()"
   ```

---

## 7. Companion Documentation Suite

| Document | Focus Area | Contents |
|---|---|---|
| 🏛️ [`solution_design.md`](solution_design.md) | **System Architecture** | Full mathematical formulas, two-loop architecture, and FMEA safety tables. |
| 💡 [`architecture_and_behavioral_qa.md`](architecture_and_behavioral_qa.md) | **Architecture & Behavioral Q&A** | Deep-dive answers on pattern extraction, learning mechanisms, data sources, and safety. |
| 📦 [`code_and_modules_guide.md`](code_and_modules_guide.md) | **Technical Specifications** | Module-by-module breakdown of all classes, methods, arguments, and return types. |
| ⚙️ [`run_and_configuration_guide.md`](run_and_configuration_guide.md) | **Setup & Operations** | Environment installation, CLI commands, JSON storage structure, and operations FAQ. |
