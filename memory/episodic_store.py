"""
Episodic Memory Store Module.
Maintains three data streams:
1. Synchronous Episodic Event Queue (episodic_event_queue.json): Lightweight append-only queue for real-time shift feedback (<100ms).
2. Escrow Reward Queue (escrow_rewards.json): Holds provisional positive rewards in escrow during the Durability Window (The Duct-Tape Safeguard).
3. Persistent Interaction Log (episodic_logs.json): Long-term immutable audit trail with strict status tagging (SUCCESS, ESCALATED_CMMS, ABANDONED_TIMEOUT).
"""

import json
import datetime
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional


class EpisodicMemory:
    """
    Episodic Memory system managing real-time event queues, reward escrow for durability verification,
    and persistent interaction audit logs with strict failure tracking.
    """

    VALID_STATUSES = ["SUCCESS", "ESCALATED_CMMS", "ABANDONED_TIMEOUT", "IN_PROGRESS"]

    def __init__(
        self,
        log_file: Optional[str] = None,
        queue_file: Optional[str] = None,
        escrow_file: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.log_file = Path(log_file) if log_file else base_dir / "data" / "episodic_logs.json"
        self.queue_file = Path(queue_file) if queue_file else base_dir / "data" / "episodic_event_queue.json"
        self.escrow_file = Path(escrow_file) if escrow_file else base_dir / "data" / "escrow_rewards.json"

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.escrow_file.parent.mkdir(parents=True, exist_ok=True)

        self.episodes: List[Dict[str, Any]] = []

        if self.log_file.exists():
            self.load_from_file()
        if not self.queue_file.exists():
            self._save_queue([])
        if not self.escrow_file.exists():
            self._save_escrow([])

    # --- 1. SYNCHRONOUS FAST EVENT QUEUE (<100ms) ---
    def enqueue_feedback_event(
        self,
        operator_id: str,
        machine_id: str,
        format_used: str,
        outcome_status: str,
        cognitive_tier: Optional[str] = None,
        error_code: Optional[str] = None,
        path_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Appends a lightweight feedback payload to episodic_event_queue.json (<100ms).
        """
        # Normalize status to strict enum
        status_norm = outcome_status
        if status_norm == "SOLVED_INDEPENDENTLY":
            status_norm = "SUCCESS"
        elif status_norm == "ESCALATED":
            status_norm = "ESCALATED_CMMS"

        event = {
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "session_id": session_id or f"SESS-{uuid.uuid4().hex[:6].upper()}",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator_id": operator_id,
            "machine_id": machine_id,
            "format_used": format_used,
            "cognitive_tier": cognitive_tier or "Novice",
            "outcome_status": status_norm,
            "error_code": error_code,
            "path_id": path_id,
            "ticket_id": ticket_id,
            "processed": False,
        }

        current_queue = self.get_pending_events()
        current_queue.append(event)
        self._save_queue(current_queue)
        return event

    def get_pending_events(self) -> List[Dict[str, Any]]:
        """Reads all pending events waiting in the episodic event queue."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[EpisodicMemory] Error loading queue: {e}")
                return []
        return []

    def clear_event_queue(self) -> None:
        """Flushes the shift event queue after batch processing."""
        self._save_queue([])

    def _save_queue(self, queue_data: List[Dict[str, Any]]) -> None:
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, indent=2)

    # --- 2. DURABILITY ESCROW QUEUE (The Duct-Tape Safeguard) ---
    def enqueue_escrow_reward(
        self,
        operator_id: str,
        machine_id: str,
        fault_code: str,
        format_used: str,
        cognitive_tier: str,
        path_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        provisional_reward: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Holds a provisional positive reward in escrow until durability window passes without recurrent alarms.
        """
        escrow_record = {
            "escrow_id": f"ESC-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator_id": operator_id,
            "machine_id": machine_id,
            "fault_code": fault_code,
            "format_used": format_used,
            "cognitive_tier": cognitive_tier,
            "path_id": path_id,
            "provisional_reward": provisional_reward,
            "status": "PENDING_DURABILITY",
        }

        escrow_list = self.get_escrow_records()
        escrow_list.append(escrow_record)
        self._save_escrow(escrow_list)
        return escrow_record

    def get_escrow_records(self) -> List[Dict[str, Any]]:
        """Reads all records from the escrow rewards file."""
        if self.escrow_file.exists():
            try:
                with open(self.escrow_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[EpisodicMemory] Error loading escrow: {e}")
                return []
        return []

    def _save_escrow(self, escrow_data: List[Dict[str, Any]]) -> None:
        with open(self.escrow_file, "w", encoding="utf-8") as f:
            json.dump(escrow_data, f, indent=2)

    def clear_escrow_records(self) -> None:
        """Flushes the escrow queue."""
        self._save_escrow([])

    # --- 3. PERSISTENT AUDIT LOGS & STATUS TRACKING ---
    def log_turn(
        self,
        operator_id: str,
        machine_id: str,
        query: str,
        response: str,
        format_used: str,
        resolution_status: str = "IN_PROGRESS",
        ticket_id: Optional[str] = None,
        error_code: Optional[str] = None,
        retrieved_sop_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Appends a new interaction turn to persistent audit log with strict status tagging."""
        status_norm = resolution_status
        if status_norm == "SOLVED_INDEPENDENTLY":
            status_norm = "SUCCESS"
        elif status_norm == "ESCALATED":
            status_norm = "ESCALATED_CMMS"

        episode = {
            "episode_id": f"EP-{len(self.episodes) + 1:04d}",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator_id": operator_id,
            "machine_id": machine_id,
            "error_code": error_code,
            "query": query,
            "response": response,
            "format_used": format_used,
            "resolution_status": status_norm,
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
        """Updates the resolution status of the most recent turn for an operator."""
        status_norm = resolution_status
        if status_norm == "SOLVED_INDEPENDENTLY":
            status_norm = "SUCCESS"
        elif status_norm == "ESCALATED":
            status_norm = "ESCALATED_CMMS"

        for ep in reversed(self.episodes):
            if ep["operator_id"] == operator_id:
                ep["resolution_status"] = status_norm
                if ticket_id:
                    ep["ticket_id"] = ticket_id
                self.save_to_file()
                return ep
        return None

    def get_operator_fault_history(
        self,
        operator_id: str,
        error_code: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves historical failed/escalated sessions (ESCALATED_CMMS or ABANDONED_TIMEOUT)
        for this operator on the specific error code to detect failure patterns.
        """
        if not error_code:
            return []

        err_clean = error_code.strip().lower()
        failures = []
        for ep in self.episodes:
            if ep.get("operator_id") == operator_id:
                ep_err = (ep.get("error_code") or ep.get("query", "")).lower()
                if err_clean in ep_err or any(part in ep_err for part in err_clean.split() if len(part) > 2):
                    if ep.get("resolution_status") in ["ESCALATED_CMMS", "ABANDONED_TIMEOUT"]:
                        failures.append(ep)
        return failures

    def archive_batch_events(self, events: List[Dict[str, Any]]) -> None:
        """Archives batch processed events into long-term history."""
        for ev in events:
            ev["processed"] = True
            ev["archived_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_to_file()

    def get_recent_history(
        self,
        operator_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Retrieves recent interaction logs."""
        filtered = self.episodes
        if operator_id:
            filtered = [e for e in filtered if e["operator_id"] == operator_id]
        if machine_id:
            filtered = [e for e in filtered if e["machine_id"] == machine_id]

        return filtered[-limit:]

    def save_to_file(self) -> None:
        """Serializes all episodes to disk."""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.episodes, f, indent=2)

    def load_from_file(self) -> None:
        """Loads episodes from disk."""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    self.episodes = json.load(f)
            except Exception as e:
                print(f"[EpisodicMemory] Warning loading file: {e}")
                self.episodes = []
