"""
Contextual Bandit Format Router using Upper Confidence Bound (UCB).
Dynamically selects and learns optimal presentation styles decoupled by Cognitive State.
Includes:
1. Hard Format Overrides (-10.0 penalty).
2. The Fatigue Gate (Environmental Context Matrix): When fatigue_index >= 0.80, forces 100% exploitation (c=0.0).
"""

import math
from typing import Dict, Any, Tuple, Optional
from memory.semantic_graph import OperatorKnowledgeGraph


class ContextualBandit:
    """
    Multi-Armed Bandit router that balances Exploration vs. Exploitation
    independently across Cognitive States and handles Environmental Context Matrix (ECM) overrides.
    """

    ARMS = ["Visual_StepByStep", "Terse_Technical", "Detailed_Text"]

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
        self.graph = knowledge_graph
        self.c = exploration_c

    def calculate_ucb_scores(
        self,
        operator_id: str,
        cognitive_tier: str,
        exploration_override_c: Optional[float] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates UCB scores for each format arm for a specific operator cognitive state.
        If exploration_override_c is provided (e.g. 0.0 for Fatigue Gate), forces 100% exploitation.
        """
        effective_c = exploration_override_c if exploration_override_c is not None else self.c
        stats = self.graph.get_state_format_weights(operator_id, cognitive_tier)
        total_pulls = sum(data.get("pull_count", 0) for data in stats.values())

        ucb_metrics = {}
        for arm in self.ARMS:
            arm_data = stats.get(arm, {"weight": 0.0, "pull_count": 0, "success_count": 0, "escalation_count": 0})
            pulls = arm_data.get("pull_count", 0)
            weight = arm_data.get("weight", 0.0)

            mean_reward = (weight / pulls) if pulls > 0 else 0.0

            if effective_c <= 0.0:
                # 100% EXPLOITATION (Fatigue Gate)
                exploration_bonus = 0.0
            elif pulls == 0:
                exploration_bonus = effective_c * math.sqrt(math.log(total_pulls + 2) / 0.1)
            else:
                exploration_bonus = effective_c * math.sqrt(math.log(total_pulls + 1) / pulls)

            total_ucb = mean_reward + exploration_bonus

            ucb_metrics[arm] = {
                "cognitive_tier": cognitive_tier,
                "pull_count": pulls,
                "weight": round(weight, 2),
                "mean_reward": round(mean_reward, 3),
                "exploration_bonus": round(exploration_bonus, 3),
                "ucb_score": round(total_ucb, 3),
                "success_count": arm_data.get("success_count", 0),
                "escalation_count": arm_data.get("escalation_count", 0),
            }

        return ucb_metrics

    def select_format(
        self,
        operator_id: str,
        machine_id: str,
        ecm_payload: Optional[Dict[str, Any]] = None,
        forced_format: Optional[str] = None,
    ) -> Tuple[str, str, Dict[str, Any], str]:
        """
        Selects format arm using UCB policy or ECM Fatigue Gate overrides.
        
        Fatigue Gate Rule:
        If fatigue_index >= 0.80 (operator is fatigued late in shift), force exploration_c = 0.0.
        Strictly exploit the fastest format (Terse_Technical or highest mean reward).
        """
        derived_tier = self.graph.get_machine_tier(operator_id, machine_id)

        # Check ECM Fatigue Gate
        is_fatigued = False
        if ecm_payload and ecm_payload.get("fatigue_index", 0.0) >= 0.80:
            is_fatigued = True

        exploration_c = 0.0 if is_fatigued else self.c
        ucb_scores = self.calculate_ucb_scores(operator_id, derived_tier, exploration_override_c=exploration_c)

        if forced_format and forced_format in self.ARMS:
            best_arm = forced_format
        elif is_fatigued:
            # Under extreme fatigue, pick arm with highest empirical mean reward; if tied/empty, exploit Terse_Technical
            best_arm = max(self.ARMS, key=lambda arm: (ucb_scores[arm]["mean_reward"], 1 if arm == "Terse_Technical" else 0))
        else:
            best_arm = max(self.ARMS, key=lambda arm: ucb_scores[arm]["ucb_score"])

        instruction = self.ARM_INSTRUCTIONS.get(best_arm, self.ARM_INSTRUCTIONS["Visual_StepByStep"])
        return best_arm, instruction, ucb_scores, derived_tier

    def update_reward(
        self,
        operator_id: str,
        cognitive_tier: str,
        format_used: str,
        reward_value: float,
    ) -> Dict[str, Any]:
        """Updates bandit reward (+1.0 / -1.0) on the cognitive state's format edge."""
        if format_used not in self.ARMS:
            format_used = "Visual_StepByStep"

        return self.graph.update_state_format_weight(
            operator_id=operator_id,
            cognitive_tier=cognitive_tier,
            format_name=format_used,
            reward=reward_value,
        )

    def trigger_format_override(
        self,
        operator_id: str,
        machine_id: str,
        rejected_format: str,
        requested_format: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Applies hard format override with -10.0 penalty to rejected format."""
        derived_tier = self.graph.get_machine_tier(operator_id, machine_id)

        if rejected_format in self.ARMS:
            self.graph.update_state_format_weight(
                operator_id=operator_id,
                cognitive_tier=derived_tier,
                format_name=rejected_format,
                reward=-10.0,
            )

        if requested_format in self.ARMS:
            self.graph.update_state_format_weight(
                operator_id=operator_id,
                cognitive_tier=derived_tier,
                format_name=requested_format,
                reward=2.0,
            )

        updated_ucb = self.calculate_ucb_scores(operator_id, derived_tier)
        instruction = self.ARM_INSTRUCTIONS.get(requested_format, self.ARM_INSTRUCTIONS["Visual_StepByStep"])

        return requested_format, instruction, updated_ucb
