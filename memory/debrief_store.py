"""
Micro-Debrief Manager Module.
Replaces probabilistic telemetry guesswork with deterministic human verification:
1. Flags unusually rapid machine resolutions (faster than SOP average) into pending_debriefs.json.
2. Intercepts the operator's next chat session with a simple Yes/No verification question.
3. Routes confirmed shortcuts to the Quarantine Database (quarantine_sops.json) and discards rejected ones.
"""

import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from memory.procedural_memory import ProceduralMemory


class DebriefManager:
    """
    Manages the lifecycle of micro-debrief verification inquiries.
    """

    def __init__(self, debrief_file: Optional[str] = None):
        if debrief_file:
            self.debrief_file = Path(debrief_file)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            self.debrief_file = base_dir / "data" / "pending_debriefs.json"

        self.debrief_file.parent.mkdir(parents=True, exist_ok=True)
        self.debriefs: List[Dict[str, Any]] = []
        self.load_from_file()

    def load_from_file(self) -> None:
        """Loads debrief records from disk."""
        if self.debrief_file.exists():
            try:
                with open(self.debrief_file, "r", encoding="utf-8") as f:
                    self.debriefs = json.load(f)
            except Exception as e:
                print(f"[DebriefManager] Error loading debriefs: {e}")
                self.debriefs = []

    def save_to_file(self) -> None:
        """Serializes debrief records to disk."""
        with open(self.debrief_file, "w", encoding="utf-8") as f:
            json.dump(self.debriefs, f, indent=2)

    def enqueue_debrief(
        self,
        operator_id: str,
        machine_id: str,
        fault_code: str,
        suspected_shortcut_title: str,
        suspected_path_payload: Dict[str, Any],
        actual_time_mins: float = 2.0,
        sop_avg_time_mins: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Enqueues an unverified rapid-resolution event for human verification.
        """
        record = {
            "debrief_id": f"DEBRIEF-{uuid.uuid4().hex[:8].upper()}",
            "operator_id": operator_id,
            "machine_id": machine_id,
            "fault_code": fault_code,
            "suspected_shortcut_title": suspected_shortcut_title,
            "suspected_path_payload": suspected_path_payload,
            "actual_time_mins": round(actual_time_mins, 1),
            "sop_avg_time_mins": round(sop_avg_time_mins, 1),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PENDING",
        }

        self.debriefs.append(record)
        self.save_to_file()
        return record

    def get_pending_debriefs(self, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves active pending debriefs for an operator."""
        self.load_from_file()
        pending = [d for d in self.debriefs if d.get("status") == "PENDING"]
        if operator_id:
            pending = [d for d in pending if d.get("operator_id") == operator_id]
        return pending

    def dismiss_debrief(self, debrief_id: str) -> None:
        """Dismisses a pending debrief inquiry without confirmation."""
        self.load_from_file()
        for d in self.debriefs:
            if d.get("debrief_id") == debrief_id:
                d["status"] = "DISMISSED"
                d["resolved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        self.save_to_file()

    def clear_all_pending(self, operator_id: Optional[str] = None) -> int:
        """Clears all pending debrief inquiries for an operator or globally."""
        self.load_from_file()
        count = 0
        for d in self.debriefs:
            if d.get("status") == "PENDING":
                if not operator_id or d.get("operator_id") == operator_id:
                    d["status"] = "DISMISSED"
                    d["resolved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    count += 1
        self.save_to_file()
        return count

    def process_debrief_response(
        self,
        debrief_id: str,
        confirmed: bool,
        procedural_memory: ProceduralMemory,
    ) -> Dict[str, Any]:
        """
        Processes human verification response:
        - If confirmed (Yes): routes the shortcut to quarantine_sops.json with operator ID attached.
        - If rejected (No): discards the assumption with zero procedural mutation.
        
        Returns:
            Summary dictionary with action result.
        """
        target_debrief = None
        for d in self.debriefs:
            if d.get("debrief_id") == debrief_id:
                target_debrief = d
                break

        if not target_debrief:
            return {"status": "NOT_FOUND", "message": f"Debrief ID {debrief_id} not found."}

        op_id = target_debrief.get("operator_id")
        m_id = target_debrief.get("machine_id")
        f_code = target_debrief.get("fault_code")
        shortcut_title = target_debrief.get("suspected_shortcut_title")
        path_payload = target_debrief.get("suspected_path_payload", {})

        if confirmed:
            # 1. Human Confirmed: Route shortcut to Quarantine Database
            quarantine_res = procedural_memory.add_to_quarantine(
                error_code=f_code,
                machine=m_id,
                title=f_code,
                path_payload=path_payload,
                operator_id=op_id,
            )
            target_debrief["status"] = "CONFIRMED_QUARANTINED"
            target_debrief["resolved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_to_file()

            return {
                "status": "CONFIRMED",
                "debrief_id": debrief_id,
                "action": "ROUTED_TO_QUARANTINE",
                "message": f"Operator confirmed shortcut ('{shortcut_title}'). Successfully routed to Quarantine Database for senior consensus review.",
                "quarantine_payload": quarantine_res,
            }
        else:
            # 2. Human Rejected: Discard assumption without modifying procedural memory
            target_debrief["status"] = "DISCARDED"
            target_debrief["resolved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_to_file()

            return {
                "status": "DISCARDED",
                "debrief_id": debrief_id,
                "action": "DISCARDED_NO_MUTATION",
                "message": f"Operator indicated standard procedure was used. Telemetry assumption discarded with zero memory mutation.",
            }
