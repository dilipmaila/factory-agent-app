"""
Shadow Observer Agent Module.
Synchronous Event Logger: Passively monitors operator session feedback during the live shift.
Integrates:
1. Durability Escrow Queue (<100ms) for holding positive rewards during the Durability Window.
2. Micro-Debrief Loop: Flags unusually fast machine resolutions into pending_debriefs.json rather than guessing.
"""

import time
from typing import Dict, Any, Optional
from memory.episodic_store import EpisodicMemory
from memory.debrief_store import DebriefManager
from mock_services.cmms_service import MockCMMS
from mock_services.scada_service import MockSCADA


class ShadowObserver:
    """
    Lightweight, low-latency Shadow Observer that synchronously captures resolution events,
    places positive rewards in escrow, and flags rapid resolutions for micro-debrief verification.
    """

    def __init__(
        self,
        episodic_memory: EpisodicMemory,
        cmms_service: Optional[MockCMMS] = None,
        scada_service: Optional[MockSCADA] = None,
        debrief_manager: Optional[DebriefManager] = None,
    ):
        self.memory = episodic_memory
        self.cmms = cmms_service or MockCMMS()
        self.scada = scada_service or MockSCADA()
        self.debrief = debrief_manager or DebriefManager()

    def evaluate_session(
        self,
        operator_id: str,
        machine_id: str,
        format_used: str,
        escalated: bool,
        cognitive_tier: str = "Novice",
        error_code: Optional[str] = None,
        path_id: Optional[str] = None,
        execution_time_mins: Optional[float] = None,
        sop_avg_time_mins: float = 10.0,
        suspected_shortcut_title: Optional[str] = None,
        suspected_shortcut_payload: Optional[Dict[str, Any]] = None,
        issue_desc: str = "Machine malfunction / unresolved alarm",
        query: str = "",
        response: str = "",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronously captures the resolution outcome into the event queue and escrow queue (<100ms).
        If resolution is unusually fast (< 50% of SOP average), flags a micro-debrief.
        """
        start_time = time.perf_counter()

        outcome_status = "ESCALATED_CMMS" if escalated else "SUCCESS"
        ticket_id = None
        scada_verified = None
        escrow_id = None
        debrief_flagged = False
        debrief_id = None

        if escalated:
            # 1. Dispatch Escalation Ticket in CMMS
            ticket_id = self.cmms.create_escalation_ticket(
                operator_id=operator_id,
                machine_id=machine_id,
                issue_desc=issue_desc or f"Escalated AI copilot session for {machine_id}",
                priority="HIGH",
            )
            message = (
                f"⚠️ Escalation logged in CMMS (Ticket: {ticket_id}). "
                f"Event queued for Sleep Cycle processing (Autonomy -15 pending)."
            )
        else:
            # 2. Verify repair telemetry with SCADA
            scada_verified = self.scada.verify_repair(machine_id)
            message = (
                f"✅ Issue resolved independently! Telemetry verified. "
                f"Reward placed in Durability Escrow (8-hr durability window active)."
            )

            # 3. Place provisional reward into Escrow Queue
            escrow_rec = self.memory.enqueue_escrow_reward(
                operator_id=operator_id,
                machine_id=machine_id,
                fault_code=error_code or "General",
                format_used=format_used,
                cognitive_tier=cognitive_tier,
                path_id=path_id,
                provisional_reward=1.0,
            )
            escrow_id = escrow_rec.get("escrow_id")

            # 4. Micro-Debrief Flagging
            # If resolution time is significantly faster than SOP average (< 50%) or suspected shortcut provided
            actual_time = execution_time_mins if execution_time_mins is not None else 2.0
            if actual_time <= (sop_avg_time_mins * 0.5) or suspected_shortcut_payload:
                shortcut_title = suspected_shortcut_title or f"Rapid Manual Bypass for {error_code or 'Fault'}"
                default_payload = suspected_shortcut_payload or {
                    "path_id": f"PATH_FAST_{error_code or 'ANOMALY'}",
                    "title": shortcut_title,
                    "description": f"Fast {actual_time}-min resolution detected by Shadow Observer.",
                    "avg_execution_time_mins": actual_time,
                    "success_count": 1,
                    "failure_count": 0,
                    "resolution_steps": f"1. Rapid bypass / reset sequence performed by {operator_id}.",
                    "prohibited_actions": "Verify safety protocols before applying.",
                    "validated_by_senior_operators": [],
                }

                debrief_rec = self.debrief.enqueue_debrief(
                    operator_id=operator_id,
                    machine_id=machine_id,
                    fault_code=error_code or "Alarm 102",
                    suspected_shortcut_title=shortcut_title,
                    suspected_path_payload=default_payload,
                    actual_time_mins=actual_time,
                    sop_avg_time_mins=sop_avg_time_mins,
                )
                debrief_flagged = True
                debrief_id = debrief_rec.get("debrief_id")
                message += " [Fast Resolution Flagged: Pending Micro-Debrief Created]"

        # 5. Fast Synchronous Queue Append
        queued_event = self.memory.enqueue_feedback_event(
            operator_id=operator_id,
            machine_id=machine_id,
            format_used=format_used,
            cognitive_tier=cognitive_tier,
            outcome_status=outcome_status,
            error_code=error_code,
            path_id=path_id,
            ticket_id=ticket_id,
            session_id=session_id,
        )

        # 6. Update active episode in persistent store
        self.memory.update_resolution(
            operator_id=operator_id,
            resolution_status=outcome_status,
            ticket_id=ticket_id,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "operator_id": operator_id,
            "machine_id": machine_id,
            "format_used": format_used,
            "cognitive_tier": cognitive_tier,
            "outcome_status": outcome_status,
            "ticket_id": ticket_id,
            "escrow_id": escrow_id,
            "debrief_flagged": debrief_flagged,
            "debrief_id": debrief_id,
            "scada_verified": scada_verified,
            "queued_event_id": queued_event.get("event_id"),
            "latency_ms": round(elapsed_ms, 2),
            "message": message,
        }
