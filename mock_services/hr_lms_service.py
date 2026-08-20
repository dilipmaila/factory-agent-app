"""
HR & LMS (Learning Management System) Mock Service.
Provides operator baseline competencies, shift assignments, and cold-start tiers.
"""

from typing import Dict, Any, List, Optional


class MockHRLMS:
    """
    Mock HR/LMS interface providing baseline operator tier classifications
    to solve the cold-start problem before empirical behavioral data is gathered.
    """

    def __init__(self):
        # Baseline operator roster with initial qualification tiers
        self._operators: Dict[str, Dict[str, Any]] = {
            "OP-001": {
                "name": "John Doe",
                "role": "Junior Shopfloor Operator",
                "default_tier": "Novice",
                "shift": "Shift A (Morning)",
                "experience_months": 3,
                "certifications": ["Basic Shopfloor Safety", "5S Workplace Organization"],
            },
            "OP-002": {
                "name": "Sarah Jenkins",
                "role": "Senior CNC Machinist",
                "default_tier": "Expert",
                "shift": "Shift B (Afternoon)",
                "experience_months": 72,
                "certifications": ["Haas Level 3 CNC", "Hydraulics & Pneumatics L2", "OSHA 30"],
            },
            "OP-003": {
                "name": "Mike Chen",
                "role": "Process Technician",
                "default_tier": "Intermediate",
                "shift": "Shift C (Night)",
                "experience_months": 24,
                "certifications": ["Engel Injection Molding Basic", "Electrical Troubleshooting 101"],
            },
        }

    def get_operator_tier(self, operator_id: str) -> str:
        """
        Returns the baseline proficiency tier ("Novice", "Intermediate", "Expert")
        for the given operator_id to initialize the cold-start state.
        """
        op = self._operators.get(operator_id)
        if op:
            return op.get("default_tier", "Novice")
        return "Novice"

    def get_operator_profile(self, operator_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns full HR profile for an operator.
        """
        return self._operators.get(operator_id)

    def get_all_operators(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all known operators with ID and profile info.
        """
        return [
            {"operator_id": op_id, **profile}
            for op_id, profile in self._operators.items()
        ]
