"""
SCADA (Supervisory Control and Data Acquisition) Mock Service.
Simulates machine alarm telemetry, live sensor metrics, repair verification,
and historical alarm trigger tracking for durability window evaluation.
"""

from typing import Dict, Any, Optional, List
import datetime
import random


class MockSCADA:
    """
    Mock SCADA interface providing real-time telemetry state, alarm history, and repair verification.
    """

    def __init__(self):
        # Default mock active alarms per machine
        self._active_alarms: Dict[str, Dict[str, Any]] = {
            "Haas VF-2": {
                "alarm_code": "Alarm 102",
                "name": "SERVOS OFF",
                "severity": "CRITICAL",
                "description": "Indicates servo amplifiers disabled. Emergency stop or low air pressure detected.",
                "telemetry": {
                    "air_pressure_psi": 68.5,  # Nominal is > 85 psi
                    "spindle_rpm": 0,
                    "amplifier_temp_c": 54.2,
                    "estop_pressed": False,
                },
            },
            "Engel Victory 330": {
                "alarm_code": "E-201",
                "name": "BARREL OVERHEAT",
                "severity": "WARNING",
                "description": "Zone 2 barrel temperature exceeded operating setpoint.",
                "telemetry": {
                    "zone_1_temp_c": 210.0,
                    "zone_2_temp_c": 268.4,  # High!
                    "hydraulic_pressure_bar": 145.0,
                    "clamping_force_kn": 3300.0,
                },
            },
        }

        # Chronological alarm history tracking: list of {machine_id, alarm_code, timestamp}
        self._alarm_history: List[Dict[str, Any]] = []

    def get_active_alarm(self, machine_id: str) -> str:
        """
        Returns a formatted active alarm string for the specified machine.
        Example: 'Alarm 102: SERVOS OFF'
        """
        alarm_data = self._active_alarms.get(machine_id)
        if alarm_data:
            return f"{alarm_data['alarm_code']}: {alarm_data['name']}"
        return "Normal - No Active Alarms"

    def get_alarm_details(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns full structured telemetry and metadata for the current alarm.
        """
        return self._active_alarms.get(machine_id)

    def set_active_alarm(
        self,
        machine_id: str,
        alarm_code: str,
        name: str,
        description: str,
        telemetry: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Allows simulating a new active alarm state on the shopfloor and logs it to history.
        """
        ts = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._active_alarms[machine_id] = {
            "alarm_code": alarm_code,
            "name": name,
            "severity": "CRITICAL" if "error" in name.lower() or "off" in name.lower() else "WARNING",
            "description": description,
            "telemetry": telemetry or {"air_pressure_psi": 88.0, "status": "Simulated State"},
            "triggered_at": ts,
        }

        # Record in historical log for durability verification
        self._alarm_history.append({
            "machine_id": machine_id,
            "alarm_code": alarm_code,
            "name": name,
            "timestamp": ts,
        })

    def log_alarm_trigger(
        self,
        machine_id: str,
        alarm_code: str,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Manually records an alarm trigger event for durability checking."""
        ts = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "machine_id": machine_id,
            "alarm_code": alarm_code,
            "timestamp": ts,
        }
        self._alarm_history.append(record)
        return record

    def get_alarm_history(
        self,
        machine_id: Optional[str] = None,
        alarm_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves chronological alarm trigger history."""
        results = self._alarm_history
        if machine_id:
            results = [r for r in results if r["machine_id"].lower() == machine_id.lower()]
        if alarm_code:
            results = [
                r for r in results
                if alarm_code.lower() in r["alarm_code"].lower() or r["alarm_code"].lower() in alarm_code.lower()
            ]
        return results

    def clear_alarm(self, machine_id: str) -> None:
        """Clears the active alarm on the specified machine."""
        if machine_id in self._active_alarms:
            del self._active_alarms[machine_id]

    def verify_repair(self, machine_id: str) -> bool:
        """
        Simulates shopfloor telemetry verification following an operator troubleshooting attempt.
        """
        if machine_id in self._active_alarms:
            success = random.random() < 0.95
            if success:
                alarm = self._active_alarms[machine_id]
                if "air_pressure_psi" in alarm.get("telemetry", {}):
                    alarm["telemetry"]["air_pressure_psi"] = 92.0
                if "zone_2_temp_c" in alarm.get("telemetry", {}):
                    alarm["telemetry"]["zone_2_temp_c"] = 220.0
                return True
            return False
        return True
