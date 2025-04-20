# risk_management_agents/main.py

import logging
import autogen
import json
import os
from typing import Dict, Any, Optional, List

# Import the refactored agent classes
from agents import (
    InternalDataScannerAgent,
    ExternalEnvironmentMonitorAgent,
    MarketIndustryAnalystAgent,
    QuantitativeRiskAssessorAgent,
    QualitativeRiskAssessorAgent,
    ResponseStrategyAgent,
    MonitoringReportingAgent,
)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Load LLM config from environment variable or file
config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={"model": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"]}, # Adjust models as needed
)

if not config_list:
    logger.error("OAI_CONFIG_LIST environment variable or file not found or invalid. Please configure LLM settings.")
    exit(1)

# Use the first config in the list for the agents that need an LLM
llm_config = {"config_list": config_list, "cache_seed": 42, "temperature": 0.1} # Use None for cache_seed for non-deterministic results

# Configuration for agents needing code execution (use Docker is recommended)
# Ensure docker is running if use_docker=True
code_execution_config = {
    "work_dir": "coding",
    "use_docker": False, # Set to True if Docker is installed and running
}

# Example Risk Policy/Appetite/Matrix Configs (Load from files/DB in a real system)
risk_appetite_config = {
    "Operational": {"Low": "Accept", "Medium": "Mitigate", "High": "Mitigate/Transfer", "Critical": "Avoid/Transfer", "Default": "Accept"},
    "Financial": {"Low": "Accept", "Medium": "Mitigate", "High": "Transfer/Mitigate", "Critical": "Transfer/Avoid", "Default": "Accept"},
    "Reputational": {"Low": "Accept", "Medium": "Mitigate", "High": "Mitigate", "Critical": "Mitigate/Avoid", "Default": "Accept"},
    "Compliance": {"Low": "Mitigate", "Medium": "Mitigate", "High": "Mitigate", "Critical": "Mitigate", "Default": "Mitigate"}, # Compliance often requires mitigation
    "Default": {"Low": "Accept", "Medium": "Accept", "High": "Mitigate", "Critical": "Avoid/Transfer", "Default": "Accept"}
}

risk_matrix_config = {
    "likelihood_scale": ["Very Low", "Low", "Medium", "High", "Very High"],
    "impact_scale": ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"],
    # Example level map (customize based on actual matrix)
    "level_map": {
        (0,0):"Low", (0,1):"Low", (0,2):"Low", (0,3):"Medium", (0,4):"Medium",
        (1,0):"Low", (1,1):"Low", (1,2):"Medium", (1,3):"Medium", (1,4):"High",
        (2,0):"Low", (2,1):"Medium", (2,2):"Medium", (2,3):"High", (2,4):"High",
        (3,0):"Medium", (3,1):"Medium", (3,2):"High", (3,3):"High", (3,4):"Critical",
        (4,0):"Medium", (4,1):"High", (4,2):"High", (4,3):"Critical", (4,4):"Critical",
    }
}

control_library_config = {
     "Operational": [
         {"id": "CTRL-OP-01", "name": "Implement Redundant Server", "cost": "High", "effectiveness": "High"},
         {"id": "CTRL-OP-02", "name": "Regular Data Backups", "cost": "Medium", "effectiveness": "High"},
         {"id": "CTRL-OP-03", "name": "Hardware Maintenance Schedule", "cost": "Medium", "effectiveness": "Medium"},
     ],
     "Financial": [
         {"id": "CTRL-FIN-01", "name": "Hedging Instruments (e.g., Futures, Options)", "cost": "Variable", "effectiveness": "Medium-High"},
         {"id": "CTRL-FIN-02", "name": "Diversification of Investments", "cost": "Low", "effectiveness": "Medium"},
     ],
     "Compliance": [
          {"id": "CTRL-CMP-01", "name": "Mandatory Compliance Training", "cost": "Medium", "effectiveness": "Medium"},
          {"id": "CTRL-CMP-02", "name": "Automated Compliance Checks", "cost": "High", "effectiveness": "High"},
     ]
     # Add more categories and controls
}

kri_definitions_config = {
    'KRI_CPU': {'threshold': 90, 'operator': '>', 'data_source': 'internal_monitoring_system', 'frequency': 'hourly', 'min_val': 0, 'max_val': 100},
    'KRI_ERR': {'threshold': 5, 'operator': '>', 'data_source': 'log_aggregator', 'frequency': 'daily', 'min_val': 0, 'max_val': 100},
    'KRI_VAR': {'threshold': 100000, 'operator': '>', 'data_source': 'quant_assessment_output', 'frequency': 'daily', 'min_val': 0, 'max_val': 500000},
    'KRI_NPS': {'threshold': 30, 'operator': '<', 'data_source': 'customer_survey_platform', 'frequency': 'monthly', 'min_val': -100, 'max_val': 100},
}


# --- Agent Initialization ---
logger.info("Initializing Agents...")

# User Proxy Agent representing the Risk Manager
risk_manager = autogen.UserProxyAgent(
    name="Risk_Manager",
    human_input_mode="TERMINATE",  # Allow human input if needed, TERMINATE ends chat on empty input
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=code_execution_config, # May need to execute code to process final results/save reports
    system_message="You are the Risk Manager. Your role is to initiate risk management tasks like 'annual risk assessment'. Review the final reports and strategy suggestions provided by the team. Ask clarifying questions if needed. Type TERMINATE to end the process.",
    # llm_config=llm_config # Usually UserProxyAgent doesn't need LLM unless it needs to summarize/process replies
)

# Specialist Agents
internal_scanner = InternalDataScannerAgent(
    name="Internal_Data_Scanner",
    # llm_config=llm_config, # Optional: If LLM needed for complex internal data analysis
    code_execution_config=False # Or True if running specific scripts
)

external_monitor = ExternalEnvironmentMonitorAgent(
    name="External_Environment_Monitor",
    # llm_config=llm_config, # Optional: If LLM needed for news summarization/sentiment
    code_execution_config=False # Or True if using APIs via code
)

market_analyst = MarketIndustryAnalystAgent(
    name="Market_Industry_Analyst",
    # llm_config=llm_config, # Optional: If LLM needed for SWOT/report summarization
    code_execution_config=False # Or True if running specific analysis scripts
)

quant_assessor = QuantitativeRiskAssessorAgent(
    name="Quantitative_Risk_Assessor",
    llm_config=False, # Focus is on code execution
    code_execution_config=code_execution_config # Needs code execution for models
)

qual_assessor = QualitativeRiskAssessorAgent(
    name="Qualitative_Risk_Assessor",
    llm_config=llm_config, # Can use LLM for interpretation or rule application
    risk_matrix_config=risk_matrix_config,
    code_execution_config=False # Or True if using specific rule engine libs
)

response_strategist = ResponseStrategyAgent(
    name="Response_Strategy_Agent",
    llm_config=llm_config, # Can use LLM for rationale/control ideas
    risk_appetite=risk_appetite_config,
    control_library=control_library_config,
    code_execution_config=False # Or True if complex cost-benefit analysis needed
)

monitor_reporter = MonitoringReportingAgent(
    name="Monitoring_Reporting_Agent",
    llm_config=False,
    initial_kri_definitions=kri_definitions_config, # Preload definitions
    code_execution_config=code_execution_config # May need code to fetch KRI data
)

logger.info("Agents Initialized.")

# --- Group Chat Setup ---
agents = [
    risk_manager,
    internal_scanner,
    external_monitor,
    market_analyst,
    quant_assessor,
    qual_assessor,
    response_strategist,
    monitor_reporter,
]

# Define the group chat
groupchat = autogen.GroupChat(
    agents=agents,
    messages=[],
    max_round=50, # Limit the number of rounds
    # speaker_selection_method="auto" # Default: LLM decides next speaker
    # For more control, implement a custom speaker selection function:
    # speaker_selection_method=custom_speaker_selector_function
    # This function would manage the workflow state and select agents based on it.
)

# Define the Group Chat Manager (Orchestrator)
# The system message guides the LLM in orchestrating the flow.
# This requires a capable LLM (like GPT-4) and careful prompting.
manager_llm_config = llm_config.copy()
# Ensure the manager's LLM can use the tools/functions defined by the agents
manager_llm_config["tools"] = [
    {"type": "function", "function": {"name": f, "description": "Call function " + f, "parameters": {"type": "object", "properties": {}}}}
    for agent in agents if agent != risk_manager for f in agent.function_map.keys()
]


manager = autogen.GroupChatManager(
    groupchat=groupchat,
    name="Risk_Assessment_Manager",
    llm_config=manager_llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") != -1,
    # System message defining the workflow for the LLM orchestrator
    system_message="""You are the manager of a risk assessment team. Your goal is to orchestrate the agents to complete a risk assessment workflow.
Workflow Steps:
1.  **Initiation:** The Risk_Manager initiates the process (e.g., "Start annual risk assessment").
2.  **Data Collection:** Instruct Internal_Data_Scanner, External_Environment_Monitor, and Market_Industry_Analyst to perform their scans/analysis using their respective functions (`scan_internal_data`, `monitor_external_environment`, `analyze_market_industry`). Wait for their reports (function call results).
3.  **Risk Identification & Assessment Tasking:** Briefly summarize the key findings from the data collection phase. Identify potential risks mentioned. For each potential risk, decide if it needs quantitative or qualitative assessment (or both). Instruct the appropriate assessor(s) (`Quantitative_Risk_Assessor`, `Qualitative_Risk_Assessor`) using their `perform_quantitative_assessment` or `perform_qualitative_assessment` functions. Provide necessary input data extracted from the collection phase and assign a temporary risk ID (e.g., RISK-001, RISK-002).
4.  **Integration & Prioritization:** Once assessment results are back, integrate them. Create a prioritized list of risks (e.g., based on assessed risk level: Critical, High, Medium, Low). Present this list clearly.
5.  **Response Strategy Development:** Instruct the Response_Strategy_Agent using `develop_response_strategies`, providing the prioritized list of risks (including their ID, category, and assessment details).
6.  **Reporting to User:** Present the final prioritized risk list and the suggested response strategies from Response_Strategy_Agent to the Risk_Manager for review.
7.  **Monitoring Setup:** After Risk_Manager review (assume approval for now), instruct the Monitoring_Reporting_Agent using `setup_monitoring` for the high/critical risks and their associated controls (from the response strategies). Pass relevant KRI definitions if available.
8.  **Conclusion:** Inform the Risk_Manager that the assessment workflow is complete and monitoring is set up.

General Instructions:
- Call agent functions using the 'function_call' field. Ensure you provide the correct arguments based on the function's definition (visible in agent system messages or previous function calls).
- Wait for function results before proceeding to the next step. Function results will appear as messages from the respective agent.
- Keep track of the data flow (e.g., findings from scanners feed into assessment).
- Be concise but clear in your instructions to agents.
- Address agents by their names.
- If an agent reports an error, acknowledge it and decide if the workflow can continue or needs intervention.
- Conclude the process by summarizing the outcome for the Risk_Manager.
"""
)

# --- Workflow Initiation ---
logger.info("Initiating Risk Assessment Workflow...")

# Initial message from the Risk Manager (User Proxy) to start the process
initial_message = """
Start the annual risk assessment process. Please follow the standard workflow:
1. Collect data (Internal, External, Market).
2. Assess identified risks (Quantitative & Qualitative).
3. Integrate and prioritize risks.
4. Develop response strategies for high/critical risks.
5. Report findings and strategies.
6. Set up monitoring for key risks/controls.
"""

# Start the chat
risk_manager.initiate_chat(
    manager,
    message=initial_message,
)

logger.info("Risk Assessment Workflow Chat Ended.")

# --- Optional: Post-Chat Analysis ---
# You can access the chat history via groupchat.messages
# final_report = extract_final_report_from_history(groupchat.messages)
# if final_report:
#     print("\n--- Final Generated Report ---")
#     print(json.dumps(final_report, indent=2))
# else:
#     print("\n--- Could not extract final report from chat history ---")

```python
# Placeholder function for extracting final report (needs implementation)
def extract_final_report_from_history(messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    # Logic to parse messages and find the final summary/report presented to the Risk_Manager
    # Look for messages from the GroupChatManager addressed to Risk_Manager near the end.
    for msg in reversed(messages):
        if msg.get("name") == "Risk_Assessment_Manager" and "prioritized risk list" in msg.get("content", "").lower() and "response strategies" in msg.get("content", "").lower():
             # Basic extraction - needs refinement
             try:
                 # This is tricky - the report might be text. Ideally, manager formats it as JSON.
                 # For now, just return the content.
                 return {"report_summary_content": msg.get("content")}
             except Exception:
                 continue
    return None

# --- Example of running a monitoring cycle post-assessment ---
# This would typically be run separately, perhaps triggered by a scheduler.
# print("\n--- Running a sample monitoring cycle ---")
# monitoring_results = monitor_reporter.run_monitoring_cycle() # Call function directly for demo
# print(json.dumps(monitoring_results, indent=2))
# if monitoring_results.get("kri_alerts") or monitoring_results.get("control_issues"):
#      print("Alerts or issues detected, further action may be needed.")

# print("\n--- Generating a sample monitoring report ---")
# monitoring_report = monitor_reporter.generate_report(report_type="periodic")
# print(json.dumps(monitoring_report, indent=2))
