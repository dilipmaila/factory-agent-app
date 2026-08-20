"""
Shadow Observer Agent Module.
Passively monitors operator session resolutions (independent success vs. supervisor escalation),
computes behavioural learning feedback, updates the Knowledge Graph, and adapts the Contextual Bandit policy.
"""

from typing import Dict, Any, Optional
from memory.semantic_graph import OperatorKnowledgeGraph
from memory.episodic_store import EpisodicMemory
from mock_services.cmms_service import MockCMMS
from mock_services.scada_service import MockSCADA
from agents.bandit_router import ContextualBandit


class ShadowObserver:
    """
    Continuous evaluation agent that updates operator autonomy scores,
    refines format preferences, and initiates CMMS escalation workflows when needed.
    """

    def __init__(
        self,
        knowledge_graph: OperatorKnowledgeGraph,
        bandit_router: ContextualBandit,
        episodic_memory: EpisodicMemory,
        cmms_service: Optional[MockCMMS] = None,
        scada_service: Optional[MockSCADA] = None,
    ):
        self.graph = knowledge_graph
        self.bandit = bandit_router
        self.memory = episodic_memory
        self.cmms = cmms_service or MockCMMS()
        self.scada = scada_service or MockSCADA()

    def evaluate_session(
        self,
        operator_id: str,
        machine_id: str,
        format_used: str,
        escalated: bool,
        issue_desc: str = "Machine malfunction / unresolved alarm",
        query: str = "",
        response: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluates the resolution outcome of an operator troubleshooting turn.
        
        Args:
            operator_id: ID of the operator (e.g. 'OP-001')
            machine_id: Target machine (e.g. 'Haas VF-2')
            format_used: The bandit presentation arm used in the response
            escalated: True if operator escalated to supervisor, False if solved independently
            issue_desc: Summary description for CMMS ticket if escalated
            query: Recent query text
            response: Recent response text
            
        Returns:
            Dictionary containing evaluation metrics, updated scores, tier transitions, and tickets.
        """
        result: Dict[str, Any] = {
            "operator_id": operator_id,
            "machine_id": machine_id,
            "format_used": format_used,
            "escalated": escalated,
        }

        if escalated:
            # --- ESCALATION WORKFLOW ---
            # 1. Update Contextual Bandit with negative reward
            bandit_update = self.bandit.update_reward(operator_id, format_used, reward_value=-1.0)
            result["bandit_reward_applied"] = -1.0
            result["bandit_arm_state"] = bandit_update

            # 2. Apply Autonomy Score penalty (-15 points)
            new_autonomy = self.graph.update_autonomy_score(operator_id, machine_id, delta=-15.0)
            new_tier = self.graph.get_operator_tier(operator_id)
            result["new_autonomy_score"] = new_autonomy
            result["new_tier"] = new_tier

            # 3. Create Escalation Ticket in CMMS
            ticket_id = self.cmms.create_escalation_ticket(
                operator_id=operator_id,
                machine_id=machine_id,
                issue_desc=issue_desc or f"Escalated from AI copilot session for {machine_id}",
                priority="HIGH",
            )
            result["ticket_id"] = ticket_id
            result["message"] = f"⚠️ Escalation logged in CMMS with Ticket ID: {ticket_id}. Autonomy score adjusted (-15)."

            # 4. Update Episodic Memory
            self.memory.update_resolution(
                operator_id=operator_id,
                resolution_status="ESCALATED",
                ticket_id=ticket_id,
            )

        else:
            # --- INDEPENDENT SUCCESS WORKFLOW ---
            # 1. Update Contextual Bandit with positive reward (+1.0)
            bandit_update = self.bandit.update_reward(operator_id, format_used, reward_value=1.0)
            result["bandit_reward_applied"] = 1.0
            result["bandit_arm_state"] = bandit_update

            # 2. Boost Autonomy Score (+5 points)
            new_autonomy = self.graph.update_autonomy_score(operator_id, machine_id, delta=5.0)
            new_tier = self.graph.get_operator_tier(operator_id)
            result["new_autonomy_score"] = new_autonomy
            result["new_tier"] = new_tier

            # 3. Verify repair telemetry with SCADA
            repair_verified = self.scada.verify_repair(machine_id)
            result["scada_telemetry_verified"] = repair_verified
            result["ticket_id"] = None
            result["message"] = f"✅ Issue resolved independently! Autonomy score increased (+5) to {new_autonomy:.1f}. Format '{format_used}' rewarded."

            # 4. Update Episodic Memory
            self.memory.update_resolution(
                operator_id=operator_id,
                resolution_status="SOLVED_INDEPENDENTLY",
            )

        return result
