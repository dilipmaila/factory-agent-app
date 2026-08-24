# Evaluation Framework: Factory Operator AI Assistant

## 1. Offline Evaluation (Development Phase)
This phase tests the system before it goes live. We use a "simulator" (an automated testing tool) to act like an operator and have multi-turn conversations with the AI. The goal is to catch mistakes in a safe, controlled environment.

| Metric | Explanation |
| :--- | :--- |
| **Goal Success Rate** | Checks if the AI actually solves the operator's simulated problem by the end of the conversation. |
| **Knowledge Retention** | Ensures the AI remembers details from earlier in the chat (e.g., if the user says the pressure is 60 PSI in turn 1, the AI shouldn't ask for the pressure again in turn 4). |
| **Context Retrieval (Precision & Recall)** | Tests if the system finds the exact, correct manuals for the specific machine without pulling in irrelevant documents. |
| **Hallucination Check (Faithfulness)** | Verifies that the AI only gives instructions found in the official manuals and does not make up troubleshooting steps. |
| **Tool Execution Accuracy** | Checks if the AI uses its backend tools in the right order (like checking the SCADA sensor data before giving advice). |
| **Fatigue Gate Persistence** | Verifies that when a worker's Fatigue Index is 0.80 or higher, the AI locks into the shortest, simplest format for the rest of the chat. |
| **Format Adherence** | Ensures the AI strictly follows the format chosen by the Bandit router, such as using checkboxes for visual steps or bullet points for terse technical steps. |
| **Safety Compliance** | A strict pass/fail check ensuring the AI always includes required safety warnings, like Lock-Out/Tag-Out (LOTO) or PPE requirements, before giving instructions. |
| **Quarantine Leakage** | Confirms that unverified shortcuts (stored in the quarantine database) are never shown to novice operators. |

---

## 2. Online Evaluation (Production Phase)
Once the system is live on the shop floor, we cannot perfectly score every response because there is no "correct answer" key. Instead, we monitor system speed, take random samples of chats, and track how the human operators behave.

| Metric | Explanation |
| :--- | :--- |
| **System Latency (Speed)** | Measures how fast the AI responds. Factory workers need immediate answers, so the time it takes for the first word to appear on the screen must be very low. |
| **Live Groundedness (10% Sample)** | A background process reviews a random 10% of daily chats to double-check that the AI's advice matches the official retrieved manuals, catching any live hallucinations. |
| **Format Override Rate** | Tracks how often an operator clicks the button to manually change the format, which applies a -10.0 penalty to the AI's chosen format. A high rate means the AI is guessing the user's preference poorly. |
| **8-Hour Recurrence (Duct-Tape Rate)** | Measures how often a machine alarm is marked as fixed, but triggers again in the SCADA system within the 8-hour waiting window. This catches bad or temporary fixes. |
| **User Correction Rate** | Tracks how often the operator has to correct the AI (e.g., typing "No, I meant the main valve"). A high rate means the AI is misunderstanding the context. |
| **Multi-Turn Abandonment Rate** | The percentage of chats where the operator talks to the AI multiple times but leaves the session and it times out (`ABANDONED_TIMEOUT`) without a fix or an escalation. |
| **Time-to-First-Action (TTFA)** | The time difference between the AI giving instructions and the operator actually doing the physical work (measured via machine sensors). If this takes too long, the AI's instructions might be too confusing to read quickly. |

---

## 3. Operational KPIs (Business Impact)
These metrics determine if the AI is actually saving the factory money, improving worker skills, and capturing lost knowledge.

| Metric | Explanation |
| :--- | :--- |
| **Mean Time to Repair (MTTR)** | Tracks the time from when an alarm goes off to when the machine is running normally again. The target is a 25% or greater reduction in this time. |
| **Independent Resolution Rate (Autonomy)** | The percentage of alarms the operator fixes completely on their own without calling a supervisor. The target is 70% or higher for standard issues. |
| **Escalation Deflection Rate** | Measures the drop in Level-2 support tickets sent to senior maintenance engineers. |
| **Micro-Debrief Conversion Rate** | The percentage of fast operator shortcuts that successfully pass the required 3-Expert voting system and become official, active procedures for everyone. |
| **Bandit Convergence Speed** | Measures how fast the AI learns what format an operator likes. The target is to lock in on a clear preference in 8 interactions or fewer. |