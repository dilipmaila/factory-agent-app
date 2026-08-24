# Evaluation Framework: Factory Operator AI Assistant Pilot

This framework outlines how we will validate whether the assistant successfully learns useful behavioural patterns and provides meaningful personalization during a manufacturing pilot.

## 1. Primary Hypothesis
**Hypothesis:** The Contextual Bandit personalization and 5-Layer Cognitive Memory will reduce operator Mean Time to Repair (MTTR) by at least 25% and decrease format override rates to near zero (convergence) within 8 interactions per operator, without sacrificing safety or introducing untested shortcuts.

## 2. Key Metrics & Evaluation Phases
We track metrics across three distinct phases to measure the success of personalization, learning, and business impact.

### Phase 1: Offline Evaluation (Development Simulator)
This phase tests the system before it goes live using a simulator to catch mistakes in a safe environment.

| Metric | Explanation |
| :--- | :--- |
| **Goal Success Rate** | Checks if the AI actually solves the operator's simulated problem. |
| **Knowledge Retention** | Ensures the AI remembers details from earlier in the chat. |
| **Context Retrieval (Precision & Recall)** | Tests if the system finds the exact, correct manuals. |
| **Hallucination Check (Faithfulness)** | Verifies that the AI only gives instructions found in the official manuals. |
| **Tool Execution Accuracy** | Checks if the AI uses its backend tools in the right order. |
| **Fatigue Gate Persistence** | Verifies that when a worker's Fatigue Index is 0.80 or higher, the AI locks into the shortest format. |
| **Format Adherence** | Ensures the AI strictly follows the format chosen by the Bandit router. |
| **Safety Compliance** | A strict pass/fail check ensuring the AI always includes required LOTO/PPE warnings. |
| **Quarantine Leakage** | Confirms that unverified shortcuts are never shown to novice operators. |

### Phase 2: Online Evaluation (Production Telemetry)
Once live, we monitor system speed, take random samples, and track human-AI behavioural convergence.

| Metric | Explanation |
| :--- | :--- |
| **System Latency (Speed)** | Measures how fast the AI responds (Time-to-First-Token). |
| **Format Override Rate & Bandit Convergence** | Tracks manual format overrides (-10.0 penalty). Target is approaching zero within 8 interactions. |
| **Time-to-First-Action (TTFA)** | Time between AI instructions and physical work (via SCADA). Evaluates if the chosen format is easy to read. |
| **8-Hour Recurrence (Duct-Tape Rate)** | Measures how often a fixed alarm triggers again within 8 hours. Catches bad/temporary fixes. |
| **Live Groundedness (10% Sample)** | Random audits to double-check that live advice matches retrieved manuals. |
| **User Correction Rate** | Tracks how often the operator types corrections (e.g., "No, I meant the main valve"). |
| **Multi-Turn Abandonment Rate** | Chats where the operator leaves and it times out without a fix or escalation. |

### Phase 3: Operational KPIs (Business Impact)
These metrics determine the actual factory floor value of the personalized behavioural profiles.

| Metric | Explanation |
| :--- | :--- |
| **Mean Time to Repair (MTTR)** | Tracks time from alarm to normal operation. Target is a 25% or greater reduction. |
| **Independent Resolution Rate** | Percentage of alarms fixed without a supervisor (Level-2 deflection). Target is 70%+. |
| **Micro-Debrief Conversion Rate** | Percentage of rapid operator shortcuts that pass the 3-Expert Quarantine Consensus. |

## 3. Verifying the Accuracy of the Behavioural Profile
To ensure the AI's learned profiles match reality, we use the following validation techniques:

* **A/B Testing Against Uniform Baseline:** Run a control group of operators receiving standard static manuals vs. a test group using the personalized UCB1 Bandit model.
* **SCADA Ground-Truth Validation (8-Hour Escrow):** A behavioural profile is only deemed "accurate" if the repairs it guides hold up in physical reality. We use the 8-Hour Durability Escrow to ensure the operator's chosen format actually led to a permanent fix, not just a temporary silencing of the alarm.
* **Supervisor Ride-Alongs (Shadow Audits):** Have expert supervisors physically observe random sessions to cross-verify if the AI's assessed skill tier (Novice/Intermediate/Expert) matches the operator's actual shopfloor competence.

## 4. Potential Risks, Failure Modes, and Loopholes

These are genuine gaps the current solution **has not fully addressed** and could cause failure in a real pilot.

### RF-1: SCADA Becomes the Single Point of Failure
**What the solution assumes:** SCADA sensor logs are always available and accurate. The entire 8-hour durability verification, fault tree updates, and autonomy score adjustments depend on SCADA data being correct.

**The risk:** If SCADA sensors drift, are miscalibrated, or the OT/IT network has an outage, the system silently loses its only ground-truth mechanism. A bad fix could earn full reward points because SCADA never saw the recurring alarm. The system will then systematically promote a wrong repair procedure into the knowledge base.

**What is not designed:** There is no sensor health check, no SCADA availability watchdog, and no fallback degraded-mode for when ground truth is absent.

---

### RF-2: Multi-Operator Blame Attribution (Shift Handover Blind Spot)
**What the solution assumes:** If the same alarm recurs within 8 hours, it was caused by the operator who last fixed it, and they should be penalized.

**The risk:** Factories run 24/7. Operator A fixes a machine at the end of their shift. Operator B takes over. If Operator B runs the machine incorrectly (wrong feed rate, wrong toolpath) and triggers the same alarm code 2 hours later, Operator A receives an unjust -15% autonomy penalty. Their behavioural profile is now corrupted with false-negative data.

**What is not designed:** There is no shift handover event logged in the system, and no way to attribute the recurring alarm to Operator B instead of Operator A. Over time this unfairly suppresses good operators' skill scores.

---

### RF-3: Bayesian Fault Tree Data Never Decays (Stale History Problem)
**What the solution assumes:** A fix path's success count ($s$) and failure count ($f$) are accurate indicators of current reliability, accumulated over the lifetime of the system.

**The risk:** Manufacturing environments change. A fix that worked 30 times last year might have a 90% chance of success in the historical record but fail repeatedly today because the machine was refurbished, a component was swapped, or a new raw material supplier introduced variability. The system will still confidently recommend the old path as Primary (P=0.93) because it has never been told history might be stale.

**What is not designed:** There is no time-decay or sliding window on success/failure counts. Old data carries the same weight as yesterday's fix.

---

### RF-4: The 3-Expert Consensus Can Be Gamed by Shared Cognitive Bias
**What the solution assumes:** Three expert operators independently verifying the same shortcut provides a reliable safety gate.

**The risk:** In a factory with a strong shop-floor culture, three senior machinists on the same team might all share the same incorrect mental model of how a machine works. They will each confirm a shortcut that is genuinely unsafe or suboptimal because their shared experience is wrong. The consensus mechanism cannot distinguish between three independent correct judgements and three correlated wrong ones.

**What is not designed:** There is no external validation step (e.g., an engineering supervisor sign-off, or comparison against OEM specifications) before a quarantined SOP is promoted to active procedures.

---

### RF-5: The Bandit Never Forgets Bad Early Data (Irreversible Weight Anchoring)
**What the solution assumes:** Bandit weights accumulate over time and always converge to the correct preference.

**The risk:** If the very first format interaction for a new operator gets a -10.0 penalty (e.g., they accidentally clicked the wrong override button, or the app glitched), that format arm's average reward is permanently dragged down. Because the UCB formula relies on a running average ($\bar{X}_i$), a single large negative weight in early interactions takes hundreds of successful interactions to overcome. The operator could be locked into a suboptimal format for weeks.

**What is not designed:** There is no mechanism to reset or decay old bandit weights when an operator's skill tier changes. An operator promoted from Novice to Intermediate inherits the Novice-state bandit's exploration history, which may not be appropriate for their new skill context.

---

### RF-6: Micro-Debrief Confirmation is Susceptible to Social Compliance Bias
**What the solution assumes:** When the system asks *"Did you use shortcut X?"*, the operator answers truthfully.

**The risk:** Workers under production pressure will click "Yes" to dismiss the banner quickly, even if they used a completely different technique. Workers in a strict safety culture will click "No" to avoid any risk of disciplinary attention, even if they genuinely found a better method. Both behaviours pollute the Quarantine SOP store with inaccurate data.

**What is not designed:** There is no cross-validation of the answer (e.g., comparing the operator's repair time against the expected time for the claimed shortcut). A worker who says "Yes" to a shortcut that normally takes 8 minutes but only spent 30 seconds on the fix should trigger a warning, not an automatic acceptance.

---

### RF-7: LLM Version Drift Can Silently Break Grounding
**What the solution assumes:** The underlying LLM (Google Gemini) will consistently follow the grounding directive (*"Answer using ONLY the retrieved manuals above"*) and respect format constraints.

**The risk:** LLM providers regularly update their models (e.g., Gemini 1.5 → Gemini 2.0). A new model version might follow instructions differently, be more "helpful" by adding context not in the retrieved SOP, or format markdown differently. This can silently break format adherence, introduce hallucinations, or cause safety warnings to be rendered in unexpected ways — all without any error being thrown by the system.

**What is not designed:** There is no LLM version pinning, no regression test suite triggered on model updates, and no hallucination-drift monitoring that would detect a change in grounding behaviour over time.