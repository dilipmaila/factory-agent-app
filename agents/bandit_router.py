"""
Contextual Bandit Format Router using Upper Confidence Bound (UCB).
Dynamically selects and learns the optimal response presentation style for each operator.
"""

import math
from typing import Dict, Any, Tuple, Optional
from memory.semantic_graph import OperatorKnowledgeGraph


class ContextualBandit:
    """
    Multi-Armed Bandit router that balances Exploration vs. Exploitation
    to discover each operator's preferred instruction format over time.
    """

    ARMS = ["Visual_StepByStep", "Terse_Technical", "Detailed_Text"]

    # Formatting prompt directives associated with each bandit arm
    ARM_INSTRUCTIONS = {
        "Visual_StepByStep": (
            "PRESENTATION STYLE: VISUAL & STEP-BY-STEP GUIDANCE (VISUAL LEARNER MODE).\n"
            "- Structure response into sequential numbered steps (Step 1, Step 2, ...).\n"
            "- Use bold visual bracket tags: `[INSPECT]`, `[ACTION]`, `[VERIFY]`, `[SAFETY]`.\n"
            "- Include markdown checklists `[ ]` or ASCII flow arrows (-->) for physical clarity.\n"
            "- Keep sentences short, visual, and immediately scannable on the shopfloor."
        ),
        "Terse_Technical": (
            "PRESENTATION STYLE: STRICTLY TERSE & TECHNICAL (EXPERT OPERATOR MODE).\n"
            "- CRITICAL CONSTRAINT: Output MUST be ultra-concise (MAXIMUM 2-3 bullet points or 1-2 direct sentences, under 45 words total).\n"
            "- NEVER include greetings ('Hello John'), pleasantries, conversational filler, or lengthy narrative.\n"
            "- Provide ONLY raw technical values, sensor thresholds, M/G-codes, and direct corrective actions."
        ),
        "Detailed_Text": (
            "PRESENTATION STYLE: IN-DEPTH COMPREHENSIVE TUTORIAL (DEEP LEARNER MODE).\n"
            "- Provide a thorough, pedagogical explanation covering the underlying electro-mechanical root cause, physics/sensor principles, step-by-step corrective actions, and preventive maintenance.\n"
            "- Explain both the 'HOW' and the 'WHY' to build operator domain mastery."
        ),
    }

    def __init__(self, knowledge_graph: OperatorKnowledgeGraph, exploration_c: float = 1.2):
        """
        Args:
            knowledge_graph: The OperatorKnowledgeGraph instance holding PREFERS edges.
            exploration_c: UCB exploration hyperparameter (c >= 1.0 encourages exploration of untested arms).
        """
        self.graph = knowledge_graph
        self.c = exploration_c

    def calculate_ucb_scores(self, operator_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Calculates the UCB (Upper Confidence Bound) score for each format arm for a given operator.
        
        Formula:
            UCB_i = empirical_mean_reward + c * sqrt( ln(total_pulls + 1) / (pulls_i + 1e-4) )
        """
        stats = self.graph.get_format_weights(operator_id)
        total_pulls = sum(data.get("pull_count", 0) for data in stats.values())

        ucb_metrics = {}
        for arm in self.ARMS:
            arm_data = stats.get(arm, {"weight": 0.0, "pull_count": 0, "success_count": 0, "escalation_count": 0})
            pulls = arm_data.get("pull_count", 0)
            weight = arm_data.get("weight", 0.0)

            # Calculate empirical mean reward (normalized)
            mean_reward = (weight / pulls) if pulls > 0 else 0.0

            # Calculate exploration bonus
            if pulls == 0:
                # Untried arm gets high exploration priority
                exploration_bonus = self.c * math.sqrt(math.log(total_pulls + 2) / 0.1)
            else:
                exploration_bonus = self.c * math.sqrt(math.log(total_pulls + 1) / pulls)

            total_ucb = mean_reward + exploration_bonus

            ucb_metrics[arm] = {
                "pull_count": pulls,
                "weight": round(weight, 2),
                "mean_reward": round(mean_reward, 3),
                "exploration_bonus": round(exploration_bonus, 3),
                "ucb_score": round(total_ucb, 3),
                "success_count": arm_data.get("success_count", 0),
                "escalation_count": arm_data.get("escalation_count", 0),
            }

        return ucb_metrics

    def select_format(self, operator_id: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Selects the winning format arm using the UCB policy.
        
        Returns:
            Tuple of:
            - selected_arm_name (e.g. 'Visual_StepByStep')
            - prompt_instruction_string
            - ucb_debug_stats (Dictionary of scores for all arms for UI inspection)
        """
        ucb_scores = self.calculate_ucb_scores(operator_id)

        # Pick arm with highest UCB score (break ties deterministically)
        best_arm = max(self.ARMS, key=lambda arm: ucb_scores[arm]["ucb_score"])
        instruction = self.ARM_INSTRUCTIONS.get(best_arm, self.ARM_INSTRUCTIONS["Visual_StepByStep"])

        return best_arm, instruction, ucb_scores

    def update_reward(self, operator_id: str, format_used: str, reward_value: float) -> Dict[str, Any]:
        """
        Updates the reward in the knowledge graph for the format arm used.
        
        Args:
            operator_id: Operator ID (e.g. OP-001)
            format_used: Arm name (e.g. 'Visual_StepByStep')
            reward_value: +1.0 for independent success, -1.0 for escalation/failure
            
        Returns:
            Updated edge state dictionary.
        """
        if format_used not in self.ARMS:
            format_used = "Visual_StepByStep"

        return self.graph.update_format_weight(operator_id, format_used, reward_value)
