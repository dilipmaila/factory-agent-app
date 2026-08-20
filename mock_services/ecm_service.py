"""
Environmental Context Matrix (ECM) Service.
Simulates real-time shopfloor environmental and operator physical context:
1. Shift progress & operator fatigue tracking (Hours since clock-in vs total shift hours).
2. Supervisor on-site availability (for escalation gating).
3. Factory ambient conditions (noise, ambient temp, shift phase).
"""

from typing import Dict, Any, Optional
import datetime


def generate_ecm_payload(
    operator_id: str,
    machine_id: str,
    hours_since_clock_in: float = 2.5,
    total_shift_hours: float = 8.0,
    supervisor_available: bool = True,
    ambient_noise_db: float = 78.0,
    ambient_temp_c: float = 22.5,
) -> Dict[str, Any]:
    """
    Generates a real-time Environmental Context Matrix (ECM) payload for the current interaction turn.
    
    Args:
        operator_id: ID of active operator (e.g. 'OP-001')
        machine_id: Machine being queried (e.g. 'Haas VF-2')
        hours_since_clock_in: Hours elapsed since operator clocked in (e.g. 10.5 for late shift)
        total_shift_hours: Scheduled shift duration (e.g. 8.0 or 12.0)
        supervisor_available: True if shift supervisor is on-site; False if supervisor is offline/at lunch.
        ambient_noise_db: Shopfloor acoustic level in decibels
        ambient_temp_c: Shopfloor ambient temperature in Celsius
        
    Returns:
        Structured ECM payload dictionary with calculated fatigue_index and active gates.
    """
    safe_total = max(1.0, float(total_shift_hours))
    raw_fatigue = float(hours_since_clock_in) / safe_total
    fatigue_index = round(min(1.5, max(0.0, raw_fatigue)), 3)

    is_fatigued = fatigue_index >= 0.80
    supervisor_offline = not supervisor_available

    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "operator_id": operator_id,
        "machine_id": machine_id,
        "hours_since_clock_in": round(float(hours_since_clock_in), 1),
        "total_shift_hours": round(float(total_shift_hours), 1),
        "fatigue_index": fatigue_index,
        "fatigue_gate_active": is_fatigued,
        "supervisor_available": supervisor_available,
        "supervisor_gate_active": supervisor_offline,
        "ambient_noise_db": ambient_noise_db,
        "ambient_temp_c": ambient_temp_c,
        "shift_phase": (
            "END_OF_SHIFT" if fatigue_index >= 0.80
            else ("MID_SHIFT" if fatigue_index >= 0.40 else "START_OF_SHIFT")
        ),
    }


class ECMService:
    """
    Stateful ECM service maintaining shift state per operator.
    """

    def __init__(self):
        # Default operator shift states
        self._operator_states: Dict[str, Dict[str, Any]] = {
            "OP-001": {"hours_in": 2.0, "total_hours": 8.0, "supervisor_on_site": True},
            "OP-002": {"hours_in": 10.5, "total_hours": 12.0, "supervisor_on_site": True},
            "OP-003": {"hours_in": 7.5, "total_hours": 8.0, "supervisor_on_site": False},
        }

    def get_ecm_payload(
        self,
        operator_id: str,
        machine_id: str,
        override_hours: Optional[float] = None,
        override_supervisor: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Returns the current real-time ECM payload for an operator."""
        st = self._operator_states.get(operator_id, {"hours_in": 3.0, "total_hours": 8.0, "supervisor_on_site": True})
        hrs = override_hours if override_hours is not None else st["hours_in"]
        sup = override_supervisor if override_supervisor is not None else st["supervisor_on_site"]

        return generate_ecm_payload(
            operator_id=operator_id,
            machine_id=machine_id,
            hours_since_clock_in=hrs,
            total_shift_hours=st.get("total_hours", 8.0),
            supervisor_available=sup,
        )

    def update_operator_shift(
        self,
        operator_id: str,
        hours_since_clock_in: float,
        supervisor_available: bool,
    ) -> None:
        """Updates the simulated shift progression."""
        if operator_id not in self._operator_states:
            self._operator_states[operator_id] = {"total_hours": 8.0}
        self._operator_states[operator_id]["hours_in"] = hours_since_clock_in
        self._operator_states[operator_id]["supervisor_on_site"] = supervisor_available
