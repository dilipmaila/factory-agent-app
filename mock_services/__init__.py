"""
Mock Services Package for Factory AI Assistant Demo.
Simulates Shopfloor SCADA Telemetry, CMMS Maintenance Ticketing, and HR/LMS Profiles.
"""

from .scada_service import MockSCADA
from .cmms_service import MockCMMS
from .hr_lms_service import MockHRLMS

__all__ = ["MockSCADA", "MockCMMS", "MockHRLMS"]
