# This file makes the 'agents' directory a Python package.

# Import refactored Autogen agent classes for easier access
from .internal_scanner import InternalDataScannerAgent
from .external_monitor import ExternalEnvironmentMonitorAgent
from .market_analyst import MarketIndustryAnalystAgent
from .quantitative_assessor import QuantitativeRiskAssessorAgent
from .qualitative_assessor import QualitativeRiskAssessorAgent
from .response_strategist import ResponseStrategyAgent
from .monitoring_reporter import MonitoringReportingAgent

# The RiskCoordinatorAgent class is no longer used in the Autogen structure.
# from .coordinator import RiskCoordinatorAgent

__all__ = [
    "InternalDataScannerAgent",
    "ExternalEnvironmentMonitorAgent",
    "MarketIndustryAnalystAgent",
    "QuantitativeRiskAssessorAgent",
    "QualitativeRiskAssessorAgent",
    "ResponseStrategyAgent",
    "MonitoringReportingAgent",
]
