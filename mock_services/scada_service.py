"""
SCADA (Supervisory Control and Data Acquisition) Mock Service.
Simulates machine alarm telemetry, live sensor metrics, and repair verification.
"""

from typing import Dict, Any, Optional
import random


class MockSCADA:
    """
    Mock SCADA interface providing real-time telemetry state and alarm verification.
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
        self, machine_id: str, alarm_code: str, name: str, description: str, telemetry: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Allows simulating a new active alarm state on the shopfloor.
        """
        self._active_alarms[machine_id] = {
            "alarm_code": alarm_code,
            "name": name,
            "severity": "CRITICAL" if "error" in name.lower() or "off" in name.lower() else "WARNING",
            "description": description,
            "telemetry": telemetry or {"air_pressure_psi": 88.0, "status": "Simulated State"},
        }

    def clear_alarm(self, machine_id: str) -> None:
        """
        Clears the active alarm on the specified machine.
        """
        if machine_id in self._active_alarms:
            del self._active_alarms[machine_id]

    def verify_repair(self, machine_id: str) -> bool:
        """
        Simulates shopfloor telemetry verification following an operator troubleshooting attempt.
        Returns True (repair successfully verified, sensors normal) or False (telemetry still failing).
        """
        # In this mock, we simulate high-confidence successful telemetry check
        # (e.g. 90% success rate on verify if an alarm was present, then clear alarm)
        if machine_id in self._active_alarms:
            success = random.random() < 0.95
            if success:
                # Simulate telemetry sensor normalization
                alarm = self._active_alarms[machine_id]
                if "air_pressure_psi" in alarm.get("telemetry", {}):
                    alarm["telemetry"]["air_pressure_psi"] = 92.0
                if "zone_2_temp_c" in alarm.get("telemetry", {}):
                    alarm["telemetry"]["zone_2_temp_c"] = 220.0
                return True
            return False
        return True
