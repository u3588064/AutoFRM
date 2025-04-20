# risk_management_agents/agents/monitoring_reporter.py
import autogen
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MonitoringReportingAgent(autogen.ConversableAgent):
    """
    An Autogen agent that monitors identified risks, Key Risk Indicators (KRIs),
    and control effectiveness. It can generate reports and identify alerts/issues
    based on its monitoring cycle.
    """
    def __init__(
        self,
        name: str = "Monitoring_Reporting_Agent",
        llm_config: Optional[Dict[str, Any]] = False, # LLM likely not needed for core monitoring logic
        code_execution_config: Optional[Dict[str, Any]] = False, # If fetching data requires code
        # Initial state can be loaded here or via a setup function
        initial_monitored_risks: Optional[Dict[str, Dict]] = None,
        initial_kri_definitions: Optional[Dict[str, Dict]] = None,
        initial_control_effectiveness: Optional[Dict[str, Dict]] = None,
        **kwargs,
    ):
        """
        Initializes the Monitoring & Reporting Agent.

        Args:
            name (str): The name of the agent.
            llm_config (Optional[Dict[str, Any]]): LLM configuration. Can be False.
            code_execution_config (Optional[Dict[str, Any]]): Code execution config. Can be False.
            initial_monitored_risks (Optional[Dict[str, Dict]]): Pre-loaded state for monitored risks.
            initial_kri_definitions (Optional[Dict[str, Dict]]): Pre-loaded KRI definitions.
            initial_control_effectiveness (Optional[Dict[str, Dict]]): Pre-loaded control status.
            **kwargs: Additional arguments for ConversableAgent.
        """
        system_message = """You are the Risk Monitoring & Reporting Agent.
Your primary functions are:
1.  **Setup Monitoring:** Receive instructions to start monitoring specific risks, their Key Risk Indicators (KRIs), and associated controls. You maintain the state of what needs to be monitored.
2.  **Run Monitoring Cycle:** When instructed, execute a monitoring cycle. This involves checking the status of registered KRIs against their thresholds and assessing the effectiveness of registered controls. You report any detected KRI breaches or control issues found during *that specific cycle*.
3.  **Generate Reports:** When requested, generate reports summarizing the current monitoring status (e.g., active risks, KRI values, control effectiveness, recent alerts/issues).

You do not initiate conversations. You respond to requests to perform your functions.
You maintain an internal state of monitored items, but rely on external triggers (like a scheduler or coordinator agent) to run monitoring cycles or generate reports.
When reporting results from a monitoring cycle, clearly list any KRI alerts or control issues detected.
Example Input (Setup Monitoring):
{ "function": "setup_monitoring", "risk_id": "OP001", "kris": ["KRI_CPU"], "controls": ["CTRL_PATCH"], "kri_definitions": {"KRI_CPU": {"threshold": 90, ...}} }
Example Input (Run Cycle):
{ "function": "run_monitoring_cycle" }
Example Input (Generate Report):
{ "function": "generate_report", "report_type": "periodic" }

Example Output (Run Cycle with issues):
{
  "source": "MonitoringReportingAgent",
  "type": "MonitoringCycleResults",
  "timestamp": "...",
  "kri_alerts": [{"kri_id": "KRI_CPU", "risk_id": "OP001", "threshold": 90, "current_value": 95, "message": "KRI 'KRI_CPU' breached threshold..."}],
  "control_issues": [{"control_id": "CTRL_PATCH", "risk_id": "OP001", "status": "Ineffective", "message": "Control 'CTRL_PATCH' appears ineffective..."}],
  "summary": "Monitoring cycle completed with 1 KRI alert and 1 control issue."
}
Example Output (Generate Report):
{
  "source": "MonitoringReportingAgent",
  "type": "PeriodicRiskReport",
  "data": { "report_time": "...", "monitored_risks_count": 5, ... }
}
"""
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=code_execution_config,
            **kwargs,
        )
        # Initialize state
        # In a real system, this state should be persistent (DB, file)
        self.monitored_risks = initial_monitored_risks or {} # {risk_id: {'kris': [], 'controls': [], 'status': 'Active'}}
        self.kri_definitions = initial_kri_definitions or {} # {kri_id: {'threshold': 100, 'data_source': '...', 'frequency': 'daily'}}
        self.control_effectiveness = initial_control_effectiveness or {} # {control_id: {'status': 'Effective', 'last_checked': None}}
        self.recent_alerts = [] # Store recent alerts for reporting

        # Register functions
        self.register_function(
            function_map={
                "setup_monitoring": self.setup_monitoring,
                "run_monitoring_cycle": self.run_monitoring_cycle,
                "generate_report": self.generate_report,
            }
        )
        logger.info(f"Initialized Monitoring & Reporting Agent: {self.name}")

    def setup_monitoring(
        self,
        risk_id: str,
        kris: Optional[List[str]] = None,
        controls: Optional[List[str]] = None,
        kri_definitions: Optional[Dict[str, Dict]] = None,
        # Could add control definitions here too
    ) -> Dict[str, Any]:
        """
        Sets up or updates monitoring for a specific risk, its KRIs, and controls.
        Intended to be called by other agents.

        Args:
            risk_id (str): The unique identifier of the risk.
            kris (Optional[List[str]]): List of KRI IDs to monitor for this risk.
            controls (Optional[List[str]]): List of Control IDs implemented for this risk.
            kri_definitions (Optional[Dict[str, Dict]]): Definitions for any new KRIs being added.

        Returns:
            Dict[str, Any]: Confirmation message.
        """
        logger.info(f"{self.name}: Setting up monitoring for risk '{risk_id}'")
        if risk_id not in self.monitored_risks:
            self.monitored_risks[risk_id] = {'kris': [], 'controls': [], 'status': 'Active'}

        added_kris = []
        if kris:
            for kri_id in kris:
                if kri_id not in self.monitored_risks[risk_id]['kris']:
                    self.monitored_risks[risk_id]['kris'].append(kri_id)
                    added_kris.append(kri_id)
                    # Add or update KRI definition if provided
                    if kri_definitions and kri_id in kri_definitions:
                        self.kri_definitions[kri_id] = kri_definitions[kri_id]
                        logger.debug(f"Added/Updated definition for KRI '{kri_id}'")
                    elif kri_id not in self.kri_definitions:
                         logger.warning(f"KRI '{kri_id}' added for monitoring but definition is missing.")

        added_controls = []
        if controls:
             for control_id in controls:
                 if control_id not in self.monitored_risks[risk_id]['controls']:
                     self.monitored_risks[risk_id]['controls'].append(control_id)
                     added_controls.append(control_id)
                     # Initialize control effectiveness if not already tracked
                     if control_id not in self.control_effectiveness:
                          self.control_effectiveness[control_id] = {'status': 'Unknown', 'last_checked': None}

        return {
            "source": self.name,
            "type": "MonitoringSetupConfirmation",
            "risk_id": risk_id,
            "status": "Success",
            "message": f"Monitoring setup for risk '{risk_id}'. Added KRIs: {added_kris}, Added Controls: {added_controls}."
        }

    def _monitor_kris(self) -> List[Dict[str, Any]]:
        """Placeholder internal method for monitoring Key Risk Indicators (KRIs)."""
        logger.debug(f"{self.name}: Internal - Monitoring KRIs...")
        alerts = []
        # TODO: Implement actual data fetching from sources defined in self.kri_definitions
        # This might involve API calls, DB queries, or code execution if configured.
        for risk_id, details in self.monitored_risks.items():
            if details.get('status') != 'Active': continue
            for kri_id in details.get('kris', []):
                 definition = self.kri_definitions.get(kri_id)
                 if not definition:
                     logger.warning(f"Skipping KRI '{kri_id}' - definition missing.")
                     continue

                 # --- Placeholder Data Fetching & Check ---
                 try:
                     # current_value = fetch_kri_data(definition['data_source']) # Actual fetch logic
                     current_value = random.uniform(definition.get('min_val', 0), definition.get('max_val', 200)) # Dummy fetch
                     threshold = definition.get('threshold', 100)
                     operator = definition.get('operator', '>') # e.g., '>', '<', '=='

                     breached = False
                     if operator == '>' and current_value > threshold: breached = True
                     elif operator == '<' and current_value < threshold: breached = True
                     elif operator == '==' and current_value == threshold: breached = True
                     # Add more operators as needed

                     if breached:
                         message = f"KRI '{kri_id}' breached threshold ({operator} {threshold}). Current value: {current_value:.2f} for Risk '{risk_id}'."
                         logger.warning(f"ALERT DETECTED: {message}")
                         alerts.append({
                             "kri_id": kri_id,
                             "risk_id": risk_id,
                             "threshold": threshold,
                             "operator": operator,
                             "current_value": round(current_value, 2),
                             "message": message
                         })
                 except Exception as e:
                      logger.error(f"Error monitoring KRI '{kri_id}': {e}")
                      alerts.append({
                           "kri_id": kri_id,
                           "risk_id": risk_id,
                           "error": f"Failed to monitor KRI: {str(e)}"
                      })
                 # --- End Placeholder ---
        return alerts

    def _check_control_effectiveness(self) -> List[Dict[str, Any]]:
        """Placeholder internal method for checking control effectiveness."""
        logger.debug(f"{self.name}: Internal - Checking Control Effectiveness...")
        issues = []
        # TODO: Implement actual logic to check control status (system logs, API checks, attestations)
        checked_controls = set()
        for risk_id, details in self.monitored_risks.items():
             if details.get('status') != 'Active': continue
             for control_id in details.get('controls', []):
                 if control_id in checked_controls: continue # Check each control once per cycle

                 # --- Placeholder Check ---
                 try:
                     # is_effective = check_control_api(control_id) # Actual check logic
                     is_effective = random.random() >= 0.05 # Simulate 95% effectiveness
                     status = 'Effective' if is_effective else 'Ineffective'

                     self.control_effectiveness[control_id] = {'status': status, 'last_checked': datetime.now().isoformat()}
                     if not is_effective:
                         message = f"Control '{control_id}' for Risk '{risk_id}' assessed as ineffective."
                         logger.warning(f"CONTROL ISSUE DETECTED: {message}")
                         issues.append({
                             "control_id": control_id,
                             "risk_id": risk_id, # Include risk for context
                             "status": status,
                             "message": message
                         })
                 except Exception as e:
                     logger.error(f"Error checking control '{control_id}': {e}")
                     issues.append({
                          "control_id": control_id,
                          "risk_id": risk_id,
                          "error": f"Failed to check control: {str(e)}"
                     })
                 # --- End Placeholder ---
                 checked_controls.add(control_id)
        return issues

    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """
        Executes one cycle of monitoring KRIs and control effectiveness.
        Returns results including any alerts or issues found in this cycle.
        Intended to be called by other agents or a scheduler.

        Returns:
            Dict[str, Any]: Dictionary containing lists of KRI alerts and control issues detected.
        """
        start_time = datetime.now()
        logger.info(f"{self.name}: Running monitoring cycle at {start_time.isoformat()}")

        kri_alerts = self._monitor_kris()
        control_issues = self._check_control_effectiveness()

        # Store recent alerts/issues for reporting purposes (optional, manage size)
        self.recent_alerts.extend(kri_alerts)
        self.recent_alerts.extend(control_issues)
        self.recent_alerts = self.recent_alerts[-50:] # Keep last 50 alerts/issues

        summary = f"Monitoring cycle completed with {len(kri_alerts)} KRI alert(s) and {len(control_issues)} control issue(s)."
        logger.info(summary)

        return {
            "source": self.name,
            "type": "MonitoringCycleResults",
            "timestamp": start_time.isoformat(),
            "kri_alerts": kri_alerts,
            "control_issues": control_issues,
            "summary": summary
        }

    def generate_report(self, report_type: str = "periodic") -> Dict[str, Any]:
        """
        Generates a risk monitoring report based on current state.
        Intended to be called by other agents.

        Args:
            report_type (str): Type of report ('periodic', 'on_demand', 'dashboard_data').

        Returns:
            Dict[str, Any]: The generated report content.
        """
        logger.info(f"{self.name}: Generating {report_type} report...")
        # TODO: Add more sophisticated aggregation and formatting based on report_type

        report_content = {
            "report_time": datetime.now().isoformat(),
            "report_type": report_type,
            "monitored_risks_summary": {
                "total": len(self.monitored_risks),
                "active": sum(1 for r in self.monitored_risks.values() if r.get('status') == 'Active'),
                # Could add breakdown by status or category
            },
            "kri_summary": {
                "total_defined": len(self.kri_definitions),
                # Could add status summary if KRI values were stored persistently
            },
            "control_effectiveness_summary": {
                "total_tracked": len(self.control_effectiveness),
                "effective": sum(1 for c in self.control_effectiveness.values() if c.get('status') == 'Effective'),
                "ineffective": sum(1 for c in self.control_effectiveness.values() if c.get('status') == 'Ineffective'),
                "unknown": sum(1 for c in self.control_effectiveness.values() if c.get('status') == 'Unknown'),
            },
            "recent_alerts_issues": self.recent_alerts[-10:] # Include last 10 for periodic report
            # For dashboard_data, might return more raw/structured data
        }

        report = {
            "source": self.name,
            "type": f"{report_type.capitalize()}RiskReport",
            "data": report_content
        }
        logger.info(f"{self.name}: Report generation complete.")
        return report
