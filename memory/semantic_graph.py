"""
Semantic Knowledge Graph Module using NetworkX.
Maintains persistent operator behavioural profiles, machine autonomy scores, and format preference weights.
Serializes to/from config/graph_state.json.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import networkx as nx


class OperatorKnowledgeGraph:
    """
    Directed Knowledge Graph tracking operator competencies, autonomy scores per machine,
    and contextual format preferences (Multi-Armed Bandit state).
    """

    FORMAT_ARMS = ["Visual_StepByStep", "Terse_Technical", "Detailed_Text"]

    def __init__(self, state_file: Optional[str] = None):
        self.graph = nx.DiGraph()

        # Resolve default persistence path
        if state_file:
            self.state_file = Path(state_file)
        else:
            # Default to data/graph_state.json relative to project root
            base_dir = Path(__file__).resolve().parent.parent
            self.state_file = base_dir / "data" / "graph_state.json"

        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing graph or seed defaults
        if self.state_file.exists():
            self.load_from_file(str(self.state_file))
        else:
            self._seed_default_graph()
            self.save_to_file(str(self.state_file))

    def _seed_default_graph(self) -> None:
        """
        Populates initial graph nodes for standard machines, format arms, and baseline operators.
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

        # 3. Seed Standard Operators with HR baseline tiers
        default_operators = [
            {
                "operator_id": "OP-001",
                "name": "John Doe",
                "tier": "Novice",
                "autonomy_defaults": {"Haas VF-2": 35.0, "Engel Victory 330": 30.0},
                "format_weights": {
                    "Visual_StepByStep": {"weight": 1.0, "pulls": 1, "successes": 1, "escalations": 0},
                    "Terse_Technical": {"weight": 0.0, "pulls": 0, "successes": 0, "escalations": 0},
                    "Detailed_Text": {"weight": 0.5, "pulls": 1, "successes": 0, "escalations": 0},
                },
            },
            {
                "operator_id": "OP-002",
                "name": "Sarah Jenkins",
                "tier": "Expert",
                "autonomy_defaults": {"Haas VF-2": 88.0, "Engel Victory 330": 82.0},
                "format_weights": {
                    "Visual_StepByStep": {"weight": 0.2, "pulls": 1, "successes": 0, "escalations": 0},
                    "Terse_Technical": {"weight": 1.5, "pulls": 2, "successes": 2, "escalations": 0},
                    "Detailed_Text": {"weight": 0.1, "pulls": 0, "successes": 0, "escalations": 0},
                },
            },
            {
                "operator_id": "OP-003",
                "name": "Mike Chen",
                "tier": "Intermediate",
                "autonomy_defaults": {"Haas VF-2": 58.0, "Engel Victory 330": 62.0},
                "format_weights": {
                    "Visual_StepByStep": {"weight": 0.8, "pulls": 1, "successes": 1, "escalations": 0},
                    "Terse_Technical": {"weight": 0.7, "pulls": 1, "successes": 1, "escalations": 0},
                    "Detailed_Text": {"weight": 0.4, "pulls": 1, "successes": 0, "escalations": 0},
                },
            },
        ]

        for op in default_operators:
            op_node = f"OPERATOR:{op['operator_id']}"
            self.graph.add_node(
                op_node,
                node_type="Operator",
                operator_id=op["operator_id"],
                name=op["name"],
                tier=op["tier"],
            )

            # Add OPERATES edges to machines
            for m_id, auto_score in op["autonomy_defaults"].items():
                m_node = f"MACHINE:{m_id}"
                self.graph.add_edge(
                    op_node,
                    m_node,
                    relation="OPERATES",
                    autonomy_score=float(auto_score),
                    success_count=int(auto_score / 10),
                    escalation_count=0,
                )

            # Add PREFERS edges to format arms
            for arm_name, stats in op["format_weights"].items():
                f_node = f"FORMAT:{arm_name}"
                self.graph.add_edge(
                    op_node,
                    f_node,
                    relation="PREFERS",
                    weight=float(stats["weight"]),
                    pull_count=int(stats["pulls"]),
                    success_count=int(stats["successes"]),
                    escalation_count=int(stats["escalations"]),
                )

    def get_or_create_operator(
        self, operator_id: str, name: str = "", default_tier: str = "Novice"
    ) -> str:
        """
        Retrieves or registers an operator in the knowledge graph.
        """
        op_node = f"OPERATOR:{operator_id}"
        if not self.graph.has_node(op_node):
            self.graph.add_node(
                op_node,
                node_type="Operator",
                operator_id=operator_id,
                name=name or f"Operator {operator_id}",
                tier=default_tier,
            )

            # Initialize baseline autonomy for standard machines
            for m in ["Haas VF-2", "Engel Victory 330"]:
                m_node = f"MACHINE:{m}"
                if not self.graph.has_node(m_node):
                    self.graph.add_node(m_node, node_type="Machine", machine_id=m)

                baseline_score = 30.0 if default_tier == "Novice" else (55.0 if default_tier == "Intermediate" else 85.0)
                self.graph.add_edge(
                    op_node,
                    m_node,
                    relation="OPERATES",
                    autonomy_score=baseline_score,
                    success_count=0,
                    escalation_count=0,
                )

            # Initialize format preference edges
            for arm in self.FORMAT_ARMS:
                f_node = f"FORMAT:{arm}"
                if not self.graph.has_node(f_node):
                    self.graph.add_node(f_node, node_type="Format", arm_name=arm)

                self.graph.add_edge(
                    op_node,
                    f_node,
                    relation="PREFERS",
                    weight=0.0,
                    pull_count=0,
                    success_count=0,
                    escalation_count=0,
                )

            self.save_to_file()
        return op_node

    def get_autonomy_score(self, operator_id: str, machine_id: str) -> float:
        """
        Returns the autonomy score (0-100) for an operator on a specific machine.
        """
        op_node = f"OPERATOR:{operator_id}"
        m_node = f"MACHINE:{machine_id}"

        if not self.graph.has_edge(op_node, m_node):
            self.get_or_create_operator(operator_id)

        edge_data = self.graph.get_edge_data(op_node, m_node, default={})
        return edge_data.get("autonomy_score", 40.0)

    def update_autonomy_score(
        self, operator_id: str, machine_id: str, delta: float
    ) -> float:
        """
        Updates the autonomy score (+5 for success, -15 for escalation),
        clamps between 0 and 100, updates tier accordingly, and persists.
        """
        op_node = f"OPERATOR:{operator_id}"
        m_node = f"MACHINE:{machine_id}"

        if not self.graph.has_edge(op_node, m_node):
            self.get_or_create_operator(operator_id)

        edge_data = self.graph[op_node][m_node]
        current_score = edge_data.get("autonomy_score", 40.0)
        new_score = max(0.0, min(100.0, current_score + delta))
        edge_data["autonomy_score"] = round(new_score, 2)

        if delta > 0:
            edge_data["success_count"] = edge_data.get("success_count", 0) + 1
        else:
            edge_data["escalation_count"] = edge_data.get("escalation_count", 0) + 1

        # Recompute and update tier based on new score
        self.update_tier_based_on_score(operator_id, machine_id)
        self.save_to_file()
        return new_score

    def update_tier_based_on_score(self, operator_id: str, machine_id: str) -> str:
        """
        Dynamically adjusts operator tier based on aggregate machine autonomy scores:
        Score >= 75: 'Expert'
        40 <= Score < 75: 'Intermediate'
        Score < 40: 'Novice'
        """
        op_node = f"OPERATOR:{operator_id}"
        if not self.graph.has_node(op_node):
            self.get_or_create_operator(operator_id)

        # Average autonomy score across all machines operated
        scores = []
        for _, target, data in self.graph.out_edges(op_node, data=True):
            if data.get("relation") == "OPERATES":
                scores.append(data.get("autonomy_score", 40.0))

        avg_score = sum(scores) / len(scores) if scores else 40.0

        if avg_score >= 75.0:
            new_tier = "Expert"
        elif avg_score >= 40.0:
            new_tier = "Intermediate"
        else:
            new_tier = "Novice"

        self.graph.nodes[op_node]["tier"] = new_tier
        return new_tier

    def get_operator_tier(self, operator_id: str) -> str:
        """
        Returns the current learned tier for the operator from the graph.
        """
        op_node = f"OPERATOR:{operator_id}"
        if not self.graph.has_node(op_node):
            self.get_or_create_operator(operator_id)
        return self.graph.nodes[op_node].get("tier", "Novice")

    def get_format_weights(self, operator_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Returns the PREFERS edge weights and statistics for all format arms.
        """
        op_node = f"OPERATOR:{operator_id}"
        if not self.graph.has_node(op_node):
            self.get_or_create_operator(operator_id)

        format_stats = {}
        for arm in self.FORMAT_ARMS:
            f_node = f"FORMAT:{arm}"
            if self.graph.has_edge(op_node, f_node):
                format_stats[arm] = dict(self.graph[op_node][f_node])
            else:
                format_stats[arm] = {
                    "weight": 0.0,
                    "pull_count": 0,
                    "success_count": 0,
                    "escalation_count": 0,
                }
        return format_stats

    def update_format_weight(
        self, operator_id: str, format_name: str, reward: float
    ) -> Dict[str, Any]:
        """
        Updates the bandit preference edge for a specific format arm.
        Reward is +1.0 for success, -1.0 for escalation.
        """
        op_node = f"OPERATOR:{operator_id}"
        f_node = f"FORMAT:{format_name}"

        if not self.graph.has_edge(op_node, f_node):
            self.get_or_create_operator(operator_id)

        edge_data = self.graph[op_node][f_node]
        edge_data["pull_count"] = edge_data.get("pull_count", 0) + 1
        edge_data["weight"] = round(edge_data.get("weight", 0.0) + reward, 2)

        if reward > 0:
            edge_data["success_count"] = edge_data.get("success_count", 0) + 1
        else:
            edge_data["escalation_count"] = edge_data.get("escalation_count", 0) + 1

        self.save_to_file()
        return dict(edge_data)

    def save_to_file(self, filepath: Optional[str] = None) -> None:
        """
        Serializes the NetworkX graph to a JSON file.
        """
        target_path = Path(filepath) if filepath else self.state_file
        data = nx.node_link_data(self.graph)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: Optional[str] = None) -> None:
        """
        Loads the graph state from a JSON file.
        """
        target_path = Path(filepath) if filepath else self.state_file
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data, directed=True)

    def to_summary_dict(self, operator_id: str, machine_id: str) -> Dict[str, Any]:
        """
        Helper method returning key metrics for UI Cognitive Inspector dashboard.
        """
        op_node = f"OPERATOR:{operator_id}"
        tier = self.get_operator_tier(operator_id)
        autonomy = self.get_autonomy_score(operator_id, machine_id)
        formats = self.get_format_weights(operator_id)

        m_edge = self.graph.get_edge_data(op_node, f"MACHINE:{machine_id}", default={})

        return {
            "operator_id": operator_id,
            "operator_name": self.graph.nodes.get(op_node, {}).get("name", operator_id),
            "tier": tier,
            "machine_id": machine_id,
            "autonomy_score": autonomy,
            "success_count": m_edge.get("success_count", 0),
            "escalation_count": m_edge.get("escalation_count", 0),
            "format_preferences": formats,
        }
