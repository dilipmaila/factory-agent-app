"""
Asynchronous Sleep Cycle Evaluator (Batch Processor).
Simulates an overnight cron job (e.g. at 03:00 AM) that processes:
1. Shift Feedback Event Queue (episodic_event_queue.json).
2. Reward Escrow Queue (escrow_rewards.json) with Durability Window Verification (The Duct-Tape Safeguard).
Performs mathematical updates:
- Penalizes unstable "duct-tape" fixes (-5.0 bandit reward, -15.0 autonomy) if a fault recurs within 8 hours.
- Releases positive rewards (+1.0 bandit reward, +5.0 autonomy) if the fix was durable past the threshold.
- Persists all states to Knowledge Graph, Procedural Memory, and clears queues.
"""

import sys
import json
import argparse
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Fix Windows console UTF-8 output if needed
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from memory.semantic_graph import OperatorKnowledgeGraph
from memory.procedural_memory import ProceduralMemory
from memory.episodic_store import EpisodicMemory
from mock_services.scada_service import MockSCADA
from agents.bandit_router import ContextualBandit


class SleepCycleEvaluator:
    """
    Asynchronous batch processing engine that evaluates durability windows,
    applies mathematical profile and knowledge updates, and persists state.
    """

    DURABILITY_THRESHOLD_HOURS = 8.0

    def __init__(
        self,
        knowledge_graph: Optional[OperatorKnowledgeGraph] = None,
        procedural_memory: Optional[ProceduralMemory] = None,
        episodic_memory: Optional[EpisodicMemory] = None,
        scada_service: Optional[MockSCADA] = None,
    ):
        self.graph = knowledge_graph or OperatorKnowledgeGraph()
        self.procedural = procedural_memory or ProceduralMemory()
        self.episodic = episodic_memory or EpisodicMemory()
        self.scada = scada_service or MockSCADA()
        self.bandit = ContextualBandit(knowledge_graph=self.graph)

    def evaluate_durability(
        self,
        machine_id: str,
        fault_code: str,
        resolved_time_str: str,
        current_time: Optional[datetime.datetime] = None,
        threshold_hours: float = 8.0,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Compares the timestamp of a resolved issue against subsequent alarm triggers in SCADA history.
        
        Returns:
            Tuple of (status, matching_alarm_record):
            - 'RECURRENCE_DETECTED': Duplicate alarm occurred within threshold_hours (unstable fix).
            - 'MATURED_DURABLE': Elapsed time >= threshold_hours with zero recurrent alarms.
            - 'PENDING': Still within durability window, no alarm yet.
        """
        now = current_time or datetime.datetime.now()
        try:
            resolved_dt = datetime.datetime.strptime(resolved_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            resolved_dt = now - datetime.timedelta(hours=threshold_hours + 1)

        # Check SCADA historical alarms for recurrence
        alarm_history = self.scada.get_alarm_history(machine_id=machine_id, alarm_code=fault_code)
        for alarm in alarm_history:
            try:
                alarm_dt = datetime.datetime.strptime(alarm["timestamp"], "%Y-%m-%d %H:%M:%S")
                # If alarm occurred after resolution and within the durability window
                if alarm_dt > resolved_dt:
                    hours_diff = (alarm_dt - resolved_dt).total_seconds() / 3600.0
                    if hours_diff <= threshold_hours:
                        return "RECURRENCE_DETECTED", alarm
            except Exception:
                continue

        # Check if durability window has elapsed
        elapsed_hours = (now - resolved_dt).total_seconds() / 3600.0
        if elapsed_hours >= threshold_hours:
            return "MATURED_DURABLE", None

        return "PENDING", None

    def run_sleep_cycle(
        self,
        current_time: Optional[datetime.datetime] = None,
        force_mature_escrow: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes the full sleep cycle batch evaluation:
        1. Ingests and processes immediate shift events from episodic_event_queue.json.
        2. Evaluates the Escrow Queue for Durability Windows (The Duct-Tape Safeguard):
           - Inverts to -5.0 bandit / -15.0 autonomy penalty if recurring fault occurred.
           - Releases +1.0 bandit / +5.0 autonomy if durability window matured.
        3. Persists Knowledge Graph and Procedural Memory.
        4. Clears processed queues and archives logs.
        """
        now = current_time or datetime.datetime.now()
        pending_events = self.episodic.get_pending_events()
        escrow_records = self.episodic.get_escrow_records()

        if not pending_events and not escrow_records:
            return {
                "status": "NO_EVENTS",
                "message": "Both event queue and escrow queue are empty. No updates required.",
                "processed_count": 0,
                "escrow_processed": 0,
                "mutations": [],
            }

        autonomy_mutations: Dict[Tuple[str, str], float] = {}
        durability_results = []
        remaining_escrow = []

        # --- 1. Process Immediate Shift Events (Escalations) ---
        for event in pending_events:
            op_id = event.get("operator_id")
            m_id = event.get("machine_id")
            fmt = event.get("format_used")
            tier = event.get("cognitive_tier", "Novice")
            status = event.get("outcome_status", "SUCCESS")
            err_code = event.get("error_code")
            path_id = event.get("path_id")

            # Escalations are processed immediately with penalties
            if status == "ESCALATED_CMMS":
                key = (op_id, m_id)
                autonomy_mutations[key] = autonomy_mutations.get(key, 0.0) - 15.0

                self.bandit.update_reward(
                    operator_id=op_id,
                    cognitive_tier=tier,
                    format_used=fmt,
                    reward_value=-1.0,
                )

                if err_code and path_id:
                    self.procedural.update_path_telemetry(
                        error_code=err_code,
                        path_id=path_id,
                        success=False,
                    )

        # --- 2. Process Escrow Rewards with Durability Window Check ---
        for record in escrow_records:
            op_id = record.get("operator_id")
            m_id = record.get("machine_id")
            f_code = record.get("fault_code", "General")
            fmt = record.get("format_used")
            tier = record.get("cognitive_tier", "Novice")
            path_id = record.get("path_id")
            res_time = record.get("timestamp")

            if force_mature_escrow:
                durability_status, matching_alarm = ("MATURED_DURABLE", None)
            else:
                durability_status, matching_alarm = self.evaluate_durability(
                    machine_id=m_id,
                    fault_code=f_code,
                    resolved_time_str=res_time,
                    current_time=now,
                    threshold_hours=self.DURABILITY_THRESHOLD_HOURS,
                )

            key = (op_id, m_id)

            if durability_status == "RECURRENCE_DETECTED":
                # DUCT-TAPE FIX DETECTED: Apply heavy retroactive penalty
                autonomy_mutations[key] = autonomy_mutations.get(key, 0.0) - 15.0

                # -5.0 heavy penalty to bandit arm for generating an unstable fix
                self.bandit.update_reward(
                    operator_id=op_id,
                    cognitive_tier=tier,
                    format_used=fmt,
                    reward_value=-5.0,
                )

                if f_code and path_id:
                    self.procedural.update_path_telemetry(
                        error_code=f_code,
                        path_id=path_id,
                        success=False,
                    )

                durability_results.append({
                    "escrow_id": record.get("escrow_id"),
                    "operator_id": op_id,
                    "machine_id": m_id,
                    "fault_code": f_code,
                    "status": "PENALIZED_RECURRENCE",
                    "bandit_penalty": -5.0,
                    "autonomy_penalty": -15.0,
                    "trigger_alarm": matching_alarm,
                })

            elif durability_status == "MATURED_DURABLE":
                # DURABLE FIX VERIFIED: Release standard +1.0 reward and +5.0 autonomy
                autonomy_mutations[key] = autonomy_mutations.get(key, 0.0) + 5.0

                self.bandit.update_reward(
                    operator_id=op_id,
                    cognitive_tier=tier,
                    format_used=fmt,
                    reward_value=1.0,
                )

                if f_code and path_id:
                    self.procedural.update_path_telemetry(
                        error_code=f_code,
                        path_id=path_id,
                        success=True,
                    )

                durability_results.append({
                    "escrow_id": record.get("escrow_id"),
                    "operator_id": op_id,
                    "machine_id": m_id,
                    "fault_code": f_code,
                    "status": "MATURED_SUCCESS",
                    "bandit_reward": 1.0,
                    "autonomy_reward": 5.0,
                })

            else:
                # Still pending durability window
                remaining_escrow.append(record)

        # --- 3. Mutate Autonomy Scores and Derived Tiers in Knowledge Graph ---
        applied_mutations = []
        for (op_id, m_id), net_delta in autonomy_mutations.items():
            old_comp = self.graph.get_machine_competence(op_id, m_id)
            new_score, new_tier = self.graph.update_autonomy_score(op_id, m_id, delta=net_delta)
            applied_mutations.append({
                "operator_id": op_id,
                "machine_id": m_id,
                "net_delta": net_delta,
                "previous_score": old_comp["autonomy_score"],
                "new_score": new_score,
                "previous_tier": old_comp["derived_tier"],
                "new_tier": new_tier,
            })

        # --- 4. Persist States and Clear Processed Queues ---
        self.graph.save_to_file()
        self.procedural.save_to_file()

        self.episodic.archive_batch_events(pending_events)
        self.episodic.clear_event_queue()
        self.episodic._save_escrow(remaining_escrow)

        return {
            "status": "SUCCESS",
            "processed_count": len(pending_events) + len(durability_results),
            "processed_events": len(pending_events),
            "processed_escrow": len(durability_results),
            "pending_escrow_remaining": len(remaining_escrow),
            "durability_evaluations": durability_results,
            "autonomy_mutations": applied_mutations,
            "message": f"Processed {len(pending_events)} events and {len(durability_results)} escrow records.",
        }


def main():
    """CLI Entrypoint for running Sleep Cycle Evaluator."""
    parser = argparse.ArgumentParser(description="Run Factory Assistant Overnight Sleep Cycle Evaluator")
    parser.add_argument("--verbose", action="store_true", help="Print detailed mutation summary")
    parser.add_argument("--force-mature", action="store_true", help="Force maturation of all pending escrow rewards")
    args = parser.parse_args()

    print("[SLEEP CYCLE] Starting Factory AI Assistant Sleep Cycle Batch Evaluator...")
    evaluator = SleepCycleEvaluator()
    result = evaluator.run_sleep_cycle(force_mature_escrow=args.force_mature)

    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    if args.verbose or result.get("processed_events", 0) > 0 or result.get("processed_escrow", 0) > 0:
        print("\n--- Summary of Durability Evaluations ---")
        for d in result.get("durability_evaluations", []):
            print(f"- Escrow {d['escrow_id']} on {d['machine_id']} ({d['fault_code']}): {d['status']}")

        print("\n--- Summary of Autonomy Mutations ---")
        for mut in result.get("autonomy_mutations", []):
            print(
                f"- Operator {mut['operator_id']} on {mut['machine_id']}: "
                f"{mut['previous_score']:.1f} -> {mut['new_score']:.1f} "
                f"({mut['previous_tier']} -> {mut['new_tier']})"
            )

    print("[SLEEP CYCLE] Evaluation Completed Successfully.")


if __name__ == "__main__":
    main()
