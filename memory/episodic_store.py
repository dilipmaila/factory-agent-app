"""
Episodic Memory Store Module.
Maintains an append-only audit log of operator interactions, chat queries, resolution states, and CMMS ticket dispatches.
"""

import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class EpisodicMemory:
    """
    Lightweight episodic memory tracker logging discrete troubleshooting events and chat turns.
    """

    def __init__(self, log_file: Optional[str] = None):
        if log_file:
            self.log_file = Path(log_file)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            self.log_file = base_dir / "data" / "episodic_logs.json"

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.episodes: List[Dict[str, Any]] = []

        if self.log_file.exists():
            self.load_from_file()

    def log_turn(
        self,
        operator_id: str,
        machine_id: str,
        query: str,
        response: str,
        format_used: str,
        resolution_status: str = "IN_PROGRESS",
        ticket_id: Optional[str] = None,
        retrieved_sop_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Appends a new interaction episode to the memory log.
        
        Args:
            operator_id: Operator ID (e.g. OP-001)
            machine_id: Machine ID (e.g. Haas VF-2)
            query: Operator question / issue report
            response: AI generated response text
            format_used: Arm format applied (e.g. Visual_StepByStep)
            resolution_status: 'IN_PROGRESS', 'SOLVED_INDEPENDENTLY', 'ESCALATED'
            ticket_id: Optional CMMS escalation ticket ID
            retrieved_sop_ids: Optional list of retrieved SOP document IDs
        """
        episode = {
            "episode_id": f"EP-{len(self.episodes) + 1:04d}",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator_id": operator_id,
            "machine_id": machine_id,
            "query": query,
            "response": response,
            "format_used": format_used,
            "resolution_status": resolution_status,
            "ticket_id": ticket_id,
            "retrieved_sop_ids": retrieved_sop_ids or [],
        }

        self.episodes.append(episode)
        self.save_to_file()
        return episode

    def update_resolution(
        self,
        operator_id: str,
        resolution_status: str,
        ticket_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the resolution status of the most recent turn for the specified operator.
        """
        for ep in reversed(self.episodes):
            if ep["operator_id"] == operator_id:
                ep["resolution_status"] = resolution_status
                if ticket_id:
                    ep["ticket_id"] = ticket_id
                self.save_to_file()
                return ep
        return None

    def get_recent_history(
        self,
        operator_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent interaction logs, optionally filtered by operator or machine.
        """
        filtered = self.episodes
        if operator_id:
            filtered = [e for e in filtered if e["operator_id"] == operator_id]
        if machine_id:
            filtered = [e for e in filtered if e["machine_id"] == machine_id]

        return filtered[-limit:]

    def save_to_file(self) -> None:
        """
        Serializes all episodes to disk.
        """
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.episodes, f, indent=2)

    def load_from_file(self) -> None:
        """
        Loads episodes from disk.
        """
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    self.episodes = json.load(f)
            except Exception as e:
                print(f"[EpisodicMemory] Warning loading file: {e}")
                self.episodes = []
