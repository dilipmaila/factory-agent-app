"""
Semantic Knowledge Graph Module using NetworkX.
Maintains decoupled cognitive states:
1. Operator Domain Confidence (OPERATES edge -> Machine with autonomy_score and derived_tier)
2. State-Bound Cognitive Format Preferences (Operator -> STATE_CONFIDENCE -> State Node -> PREFERS -> Format Node)
Serializes to/from data/graph_state.json.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import networkx as nx


class OperatorKnowledgeGraph:
    """
    Directed Knowledge Graph tracking operator competencies, autonomy scores per machine,
    and state-bound format preferences (Contextual Bandit state decoupled by cognitive tier).
    """

    FORMAT_ARMS = ["Visual_StepByStep", "Terse_Technical", "Detailed_Text"]
    COGNITIVE_TIERS = ["Novice", "Intermediate", "Expert"]

    def __init__(self, state_file: Optional[str] = None):
        self.graph = nx.DiGraph()

        # Resolve default persistence path
        if state_file:
            self.state_file = Path(state_file)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            self.state_file = base_dir / "data" / "graph_state.json"

        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing graph or seed defaults
        if self.state_file.exists():
            self.load_from_file(str(self.state_file))
        else:
            self._seed_default_graph()
            self.save_to_file(str(self.state_file))

    @staticmethod
    def calculate_tier_from_score(score: float) -> str:
        """
        Determines cognitive proficiency tier strictly based on machine autonomy score:
        - Score >= 75.0: 'Expert'
        - 40.0 <= Score < 75.0: 'Intermediate'
        - Score < 40.0: 'Novice'
        """
        if score >= 75.0:
            return "Expert"
        elif score >= 40.0:
            return "Intermediate"
        else:
            return "Novice"

    def _seed_default_graph(self) -> None:
        """
        Populates initial graph nodes:
        - Format Nodes
        - Machine Nodes
        - Operator Nodes
        - Cognitive State Nodes (per operator per tier)
        - OPERATES Edges (Operator -> Machine with autonomy_score and derived_tier)
        - STATE_CONFIDENCE Edges (Operator -> State Node)
        - PREFERS Edges (State Node -> Format Node)
        """
        self.graph.clear()

        # 1. Format Nodes
        for arm in self.FORMAT_ARMS:
            self.graph.add_node(
                f"FORMAT:{arm}",
                node_type="Format",
                arm_name=arm,
            )

        # 2. Machine Nodes
        machines = ["Haas VF-2", "Engel Victory 330"]
        for m in machines:
            self.graph.add_node(
                f"MACHINE:{m}",
                node_type="Machine",
                machine_id=m,
            )

        # 3. Seed Operators with Decoupled Machine Competence & State-Bound Preferences
        default_operators = [
            {
                "operator_id": "OP-001",
                "name": "John Doe",
                "global_baseline_tier": "Novice",
                "machine_autonomy": {
                    "Haas VF-2": {"autonomy_score": 35.0, "success_count": 3, "escalation_count": 0},
                    "Engel Victory 330": {"autonomy_score": 30.0, "success_count": 2, "escalation_count": 0},
                },
                "state_preferences": {
                    "Novice": {
                        "Visual_StepByStep": {"weight": 3.0, "pulls": 3, "successes": 3, "escalations": 0},
                        "Terse_Technical": {"weight": -1.0, "pulls": 1, "successes": 0, "escalations": 1},
                        "Detailed_Text": {"weight": 0.2, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                    "Intermediate": {
                        "Visual_StepByStep": {"weight": 1.0, "pulls": 1, "successes": 1, "escalations": 0},
                        "Terse_Technical": {"weight": 1.0, "pulls": 1, "successes": 1, "escalations": 0},
                        "Detailed_Text": {"weight": 0.3, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                    "Expert": {
                        "Visual_StepByStep": {"weight": 0.0, "pulls": 1, "successes": 0, "escalations": 0},
                        "Terse_Technical": {"weight": 3.0, "pulls": 3, "successes": 3, "escalations": 0},
                        "Detailed_Text": {"weight": 0.0, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                },
            },
            {
                # Sarah Jenkins: EXPERT on Haas VF-2 (autonomy 95.0), NOVICE on Engel (autonomy 12.0)
                "operator_id": "OP-002",
                "name": "Sarah Jenkins",
                "global_baseline_tier": "Expert",
                "machine_autonomy": {
                    "Haas VF-2": {"autonomy_score": 95.0, "success_count": 19, "escalation_count": 0},
                    "Engel Victory 330": {"autonomy_score": 12.0, "success_count": 1, "escalation_count": 2},
                },
                "state_preferences": {
                    "Novice": {
                        "Visual_StepByStep": {"weight": 3.0, "pulls": 3, "successes": 3, "escalations": 0},
                        "Terse_Technical": {"weight": -1.0, "pulls": 1, "successes": 0, "escalations": 1},
                        "Detailed_Text": {"weight": 0.2, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                    "Intermediate": {
                        "Visual_StepByStep": {"weight": 1.0, "pulls": 1, "successes": 1, "escalations": 0},
                        "Terse_Technical": {"weight": 1.0, "pulls": 1, "successes": 1, "escalations": 0},
                        "Detailed_Text": {"weight": 0.3, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                    "Expert": {
                        "Visual_StepByStep": {"weight": 0.0, "pulls": 1, "successes": 0, "escalations": 0},
                        "Terse_Technical": {"weight": 4.0, "pulls": 4, "successes": 4, "escalations": 0},
                        "Detailed_Text": {"weight": 0.0, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                },
            },
            {
                "operator_id": "OP-003",
                "name": "Mike Chen",
                "global_baseline_tier": "Intermediate",
                "machine_autonomy": {
                    "Haas VF-2": {"autonomy_score": 58.0, "success_count": 5, "escalation_count": 0},
                    "Engel Victory 330": {"autonomy_score": 62.0, "success_count": 6, "escalation_count": 0},
                },
                "state_preferences": {
                    "Novice": {
                        "Visual_StepByStep": {"weight": 2.0, "pulls": 2, "successes": 2, "escalations": 0},
                        "Terse_Technical": {"weight": 0.0, "pulls": 1, "successes": 0, "escalations": 0},
                        "Detailed_Text": {"weight": 0.4, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                    "Intermediate": {
                        "Visual_StepByStep": {"weight": 2.0, "pulls": 2, "successes": 2, "escalations": 0},
                        "Terse_Technical": {"weight": 2.0, "pulls": 2, "successes": 2, "escalations": 0},
                        "Detailed_Text": {"weight": 0.5, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                    "Expert": {
                        "Visual_StepByStep": {"weight": 0.0, "pulls": 1, "successes": 0, "escalations": 0},
                        "Terse_Technical": {"weight": 2.0, "pulls": 2, "successes": 2, "escalations": 0},
                        "Detailed_Text": {"weight": 0.0, "pulls": 1, "successes": 0, "escalations": 0},
                    },
                },
            },
        ]

        for op in default_operators:
            op_id = op["operator_id"]
            op_node = f"OPERATOR:{op_id}"
            self.graph.add_node(
                op_node,
                node_type="Operator",
                operator_id=op_id,
                name=op["name"],
                baseline_tier=op["global_baseline_tier"],
            )

            # A. Add OPERATES edge to each machine with machine-specific autonomy & derived tier
            for m_id, m_data in op["machine_autonomy"].items():
                m_node = f"MACHINE:{m_id}"
                score = float(m_data["autonomy_score"])
                tier = self.calculate_tier_from_score(score)
                self.graph.add_edge(
                    op_node,
                    m_node,
                    relation="OPERATES",
                    autonomy_score=score,
                    derived_tier=tier,
                    success_count=int(m_data.get("success_count", 0)),
                    escalation_count=int(m_data.get("escalation_count", 0)),
                )

            # B. Add Cognitive State Nodes & PREFERS format edges
            for tier in self.COGNITIVE_TIERS:
                state_node = f"STATE:{op_id}:{tier}"
                self.graph.add_node(
                    state_node,
                    node_type="CognitiveState",
                    operator_id=op_id,
                    tier=tier,
                )

                # Connect Operator -> Cognitive State via STATE_CONFIDENCE
                self.graph.add_edge(
                    op_node,
                    state_node,
                    relation="STATE_CONFIDENCE",
                    tier=tier,
                )

                # Connect State Node -> Format Node via PREFERS
                tier_prefs = op["state_preferences"].get(tier, {})
                for arm in self.FORMAT_ARMS:
                    f_node = f"FORMAT:{arm}"
                    arm_stats = tier_prefs.get(arm, {"weight": 0.0, "pulls": 0, "successes": 0, "escalations": 0})
                    self.graph.add_edge(
                        state_node,
                        f_node,
                        relation="PREFERS",
                        weight=float(arm_stats.get("weight", 0.0)),
                        pull_count=int(arm_stats.get("pulls", 0)),
                        success_count=int(arm_stats.get("successes", 0)),
                        escalation_count=int(arm_stats.get("escalations", 0)),
                    )

    def get_or_create_operator(
        self, operator_id: str, name: str = "", default_tier: str = "Novice"
    ) -> str:
        """
        Ensures operator exists in the knowledge graph with decoupled machine edges and state nodes.
        """
        op_node = f"OPERATOR:{operator_id}"
        if not self.graph.has_node(op_node):
            self.graph.add_node(
                op_node,
                node_type="Operator",
                operator_id=operator_id,
                name=name or f"Operator {operator_id}",
                baseline_tier=default_tier,
            )

            baseline_score = 30.0 if default_tier == "Novice" else (55.0 if default_tier == "Intermediate" else 85.0)
            baseline_derived = self.calculate_tier_from_score(baseline_score)

            for m in ["Haas VF-2", "Engel Victory 330"]:
                m_node = f"MACHINE:{m}"
                if not self.graph.has_node(m_node):
                    self.graph.add_node(m_node, node_type="Machine", machine_id=m)

                self.graph.add_edge(
                    op_node,
                    m_node,
                    relation="OPERATES",
                    autonomy_score=baseline_score,
                    derived_tier=baseline_derived,
                    success_count=0,
                    escalation_count=0,
                )

            for tier in self.COGNITIVE_TIERS:
                state_node = f"STATE:{operator_id}:{tier}"
                if not self.graph.has_node(state_node):
                    self.graph.add_node(
                        state_node,
                        node_type="CognitiveState",
                        operator_id=operator_id,
                        tier=tier,
                    )
                self.graph.add_edge(
                    op_node,
                    state_node,
                    relation="STATE_CONFIDENCE",
                    tier=tier,
                )

                for arm in self.FORMAT_ARMS:
                    f_node = f"FORMAT:{arm}"
                    if not self.graph.has_node(f_node):
                        self.graph.add_node(f_node, node_type="Format", arm_name=arm)
                    self.graph.add_edge(
                        state_node,
                        f_node,
                        relation="PREFERS",
                        weight=0.0,
                        pull_count=0,
                        success_count=0,
                        escalation_count=0,
                    )

            self.save_to_file()
        return op_node

    def get_machine_competence(self, operator_id: str, machine_id: str) -> Dict[str, Any]:
        """
        Retrieves the OPERATES edge attributes for an operator on a specific machine.
        Returns:
            Dict with autonomy_score (float), derived_tier (str), success_count, escalation_count.
        """
        op_node = f"OPERATOR:{operator_id}"
        m_node = f"MACHINE:{machine_id}"

        if not self.graph.has_edge(op_node, m_node):
            self.get_or_create_operator(operator_id)

        edge_data = self.graph.get_edge_data(op_node, m_node, default={})
        score = float(edge_data.get("autonomy_score", 35.0))
        tier = edge_data.get("derived_tier", self.calculate_tier_from_score(score))

        return {
            "autonomy_score": score,
            "derived_tier": tier,
            "success_count": edge_data.get("success_count", 0),
            "escalation_count": edge_data.get("escalation_count", 0),
        }

    def get_autonomy_score(self, operator_id: str, machine_id: str) -> float:
        """Returns the machine-specific autonomy score."""
        return self.get_machine_competence(operator_id, machine_id)["autonomy_score"]

    def get_machine_tier(self, operator_id: str, machine_id: str) -> str:
        """Returns the machine-specific derived tier (Novice, Intermediate, Expert)."""
        return self.get_machine_competence(operator_id, machine_id)["derived_tier"]

    def get_operator_tier(self, operator_id: str, machine_id: Optional[str] = None) -> str:
        """
        Returns the derived tier for the specified machine, or average tier across machines.
        """
        if machine_id:
            return self.get_machine_tier(operator_id, machine_id)
        
        op_node = f"OPERATOR:{operator_id}"
        if not self.graph.has_node(op_node):
            self.get_or_create_operator(operator_id)

        scores = []
        for _, target, data in self.graph.out_edges(op_node, data=True):
            if data.get("relation") == "OPERATES":
                scores.append(data.get("autonomy_score", 40.0))

        avg = sum(scores) / len(scores) if scores else 40.0
        return self.calculate_tier_from_score(avg)

    def update_autonomy_score(
        self, operator_id: str, machine_id: str, delta: float
    ) -> Tuple[float, str]:
        """
        Updates machine-specific autonomy score (+5 for success, -15 for escalation),
        clamps between 0 and 100, recomputes derived_tier, and persists.
        
        Returns:
            Tuple of (new_autonomy_score, new_derived_tier)
        """
        op_node = f"OPERATOR:{operator_id}"
        m_node = f"MACHINE:{machine_id}"

        if not self.graph.has_edge(op_node, m_node):
            self.get_or_create_operator(operator_id)

        edge_data = self.graph[op_node][m_node]
        current_score = edge_data.get("autonomy_score", 40.0)
        new_score = max(0.0, min(100.0, current_score + delta))
        new_tier = self.calculate_tier_from_score(new_score)

        edge_data["autonomy_score"] = round(new_score, 2)
        edge_data["derived_tier"] = new_tier

        if delta > 0:
            edge_data["success_count"] = edge_data.get("success_count", 0) + 1
        else:
            edge_data["escalation_count"] = edge_data.get("escalation_count", 0) + 1

        self.save_to_file()
        return new_score, new_tier

    def get_state_format_weights(
        self, operator_id: str, cognitive_tier: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves format statistics for a specific cognitive state (e.g. Novice vs Expert).
        """
        state_node = f"STATE:{operator_id}:{cognitive_tier}"
        if not self.graph.has_node(state_node):
            self.get_or_create_operator(operator_id)

        format_stats = {}
        for arm in self.FORMAT_ARMS:
            f_node = f"FORMAT:{arm}"
            if self.graph.has_edge(state_node, f_node):
                format_stats[arm] = dict(self.graph[state_node][f_node])
            else:
                format_stats[arm] = {
                    "weight": 0.0,
                    "pull_count": 0,
                    "success_count": 0,
                    "escalation_count": 0,
                }
        return format_stats

    def update_state_format_weight(
        self,
        operator_id: str,
        cognitive_tier: str,
        format_name: str,
        reward: float,
    ) -> Dict[str, Any]:
        """
        Updates the format preference edge connected to the operator's specific cognitive state.
        Reward is +1.0 for success, -1.0 for escalation.
        """
        state_node = f"STATE:{operator_id}:{cognitive_tier}"
        f_node = f"FORMAT:{format_name}"

        if not self.graph.has_edge(state_node, f_node):
            self.get_or_create_operator(operator_id)

        edge_data = self.graph[state_node][f_node]
        edge_data["pull_count"] = edge_data.get("pull_count", 0) + 1
        edge_data["weight"] = round(edge_data.get("weight", 0.0) + reward, 2)

        if reward > 0:
            edge_data["success_count"] = edge_data.get("success_count", 0) + 1
        else:
            edge_data["escalation_count"] = edge_data.get("escalation_count", 0) + 1

        self.save_to_file()
        return dict(edge_data)

    def save_to_file(self, filepath: Optional[str] = None) -> None:
        """Serializes the NetworkX graph to a JSON file."""
        target_path = Path(filepath) if filepath else self.state_file
        data = nx.node_link_data(self.graph)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: Optional[str] = None) -> None:
        """Loads the graph state from a JSON file."""
        target_path = Path(filepath) if filepath else self.state_file
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data, directed=True)

    def to_summary_dict(self, operator_id: str, machine_id: str) -> Dict[str, Any]:
        """Helper method returning decoupled metrics for UI Cognitive Inspector."""
        op_node = f"OPERATOR:{operator_id}"
        competence = self.get_machine_competence(operator_id, machine_id)
        current_tier = competence["derived_tier"]
        formats = self.get_state_format_weights(operator_id, current_tier)

        # Also get all machine competencies
        machine_breakdown = {}
        for m in ["Haas VF-2", "Engel Victory 330"]:
            machine_breakdown[m] = self.get_machine_competence(operator_id, m)

        # Also get state preferences for all cognitive tiers
        all_state_preferences = {
            t: self.get_state_format_weights(operator_id, t) for t in self.COGNITIVE_TIERS
        }

        return {
            "operator_id": operator_id,
            "operator_name": self.graph.nodes.get(op_node, {}).get("name", operator_id),
            "selected_machine": machine_id,
            "active_machine_competence": competence,
            "all_machines_competence": machine_breakdown,
            "active_state_tier": current_tier,
            "active_state_format_preferences": formats,
            "all_cognitive_states_format_preferences": all_state_preferences,
        }
