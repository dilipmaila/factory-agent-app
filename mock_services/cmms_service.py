"""
CMMS (Computerized Maintenance Management System) Mock Service.
Handles escalation tickets dispatched to maintenance technicians and supervisors.
"""

from typing import Dict, Any, List
import uuid
import datetime


class MockCMMS:
    """
    Mock CMMS interface for logging maintenance escalations, work orders, and technician dispatches.
    """

    def __init__(self):
        self._tickets: List[Dict[str, Any]] = []

    def create_escalation_ticket(
        self,
        operator_id: str,
        machine_id: str,
        issue_desc: str,
        priority: str = "HIGH"
    ) -> str:
        """
        Simulates logging an escalation ticket to a maintenance supervisor.
        Returns a unique ticket ID string (e.g. 'TICK-2026-A83B').
        """
        ticket_uid = uuid.uuid4().hex[:6].upper()
        ticket_id = f"TICK-2026-{ticket_uid}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ticket_record = {
            "ticket_id": ticket_id,
            "timestamp": timestamp,
            "operator_id": operator_id,
            "machine_id": machine_id,
            "issue_description": issue_desc,
            "priority": priority,
            "status": "DISPATCHED_TO_SUPERVISOR",
            "assigned_team": "L2_ELECTROMECHANICAL_MAINTENANCE",
        }

        self._tickets.append(ticket_record)
        return ticket_id

    def get_ticket_details(self, ticket_id: str) -> Dict[str, Any]:
        """
        Retrieves ticket details by ID.
        """
        for t in self._tickets:
            if t["ticket_id"] == ticket_id:
                return t
        return {"error": "Ticket not found"}

    def get_tickets_for_operator(self, operator_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all escalation tickets logged by or associated with an operator.
        """
        return [t for t in self._tickets if t["operator_id"] == operator_id]

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """
        Returns all created escalation tickets.
        """
        return list(self._tickets)
