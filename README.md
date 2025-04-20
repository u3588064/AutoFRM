# Risk Management Multi-Agent System (using Autogen)

This project implements a Multi-Agent System for risk management using the [Microsoft Autogen](https://microsoft.github.io/autogen/) framework. It automates and enhances the risk management process through collaborative, specialized agents orchestrated via group chat.

## System Overview

The system leverages Autogen to structure the risk management workflow:

- **Orchestration:** A `GroupChatManager` agent, guided by a system prompt defining the workflow, orchestrates the interaction between specialist agents.
- **User Interaction:** A `UserProxyAgent` represents the human Risk Manager, initiating tasks and reviewing results.
- **Specialist Agents:** Each agent is responsible for a specific task in the risk management lifecycle:
    - **InternalDataScannerAgent:** Monitors internal data sources for risk signals.
    - **ExternalEnvironmentMonitorAgent:** Tracks external PESTLE factors.
    - **MarketIndustryAnalystAgent:** Analyzes market and industry-specific risks.
    - **QuantitativeRiskAssessorAgent:** Performs quantitative risk analysis (e.g., VaR, stress tests).
    - **QualitativeRiskAssessorAgent:** Assesses qualitative risks using matrices or rules.
    - **ResponseStrategyAgent:** Suggests risk response strategies (Avoid, Transfer, Mitigate, Accept) based on risk appetite.
    - **MonitoringReportingAgent:** Sets up monitoring for risks/controls, runs checks, and generates reports.

## Project Structure

```
risk_management_agents/
├── agents/
│   ├── __init__.py
│   ├── internal_scanner.py
│   ├── external_monitor.py
│   ├── market_analyst.py
│   ├── quantitative_assessor.py
│   ├── qualitative_assessor.py
│   ├── response_strategist.py
│   └── monitoring_reporter.py
│   # coordinator.py is intentionally blank (orchestration moved to main.py)
├── coding/           # Working directory for code execution by agents
├── data/             # Placeholder for data sources/storage
├── models/           # Placeholder for risk models
├── reports/          # Placeholder for generated reports
├── main.py           # Main script to initialize agents and run the workflow
├── requirements.txt  # Project dependencies
├── OAI_CONFIG_LIST   # Example LLM configuration file (or use environment variable)
└── README.md
```

## Getting Started

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd risk_management_agents
    ```

2.  **Set up Python Environment:** (Recommended)
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure LLM:**
    -   You need access to an OpenAI API key (or compatible API).
    -   Create a file named `OAI_CONFIG_LIST` (or `OAI_CONFIG_LIST.json`) in the `risk_management_agents` directory.
    -   Add your API configuration to this file. Example:
        ```json
        [
            {
                "model": "gpt-4-turbo",
                "api_key": "YOUR_API_KEY_HERE"
            }
        ]
        ```
    -   Replace `YOUR_API_KEY_HERE` with your actual key. Ensure the chosen model supports function calling (required for the `GroupChatManager`).
    -   Alternatively, set the `OAI_CONFIG_LIST` environment variable with the JSON content.

5.  **Docker (Optional but Recommended):**
    -   If you want agents (like the `QuantitativeRiskAssessorAgent`) to execute code in a sandboxed environment, install Docker and ensure it's running.
    -   In `main.py`, set `use_docker: True` within the `code_execution_config` dictionary.

## Usage

1.  **Run the Main Script:**
    ```bash
    python main.py
    ```

2.  **Observe the Workflow:**
    -   The script will initialize the agents and the group chat.
    -   The `Risk_Manager` agent will initiate the "annual risk assessment" workflow.
    -   The `Risk_Assessment_Manager` (GroupChatManager) will orchestrate the conversation, calling functions on the specialist agents according to the defined workflow.
    -   You will see the messages exchanged between the agents and the results of their function calls (data scans, assessments, strategy suggestions, etc.).

3.  **Interact (Optional):**
    -   The `Risk_Manager` (UserProxyAgent) is configured with `human_input_mode="TERMINATE"`. If the conversation flow requires human input or clarification, it might prompt you.
    -   You can type `TERMINATE` when prompted to end the chat gracefully.

4.  **Review Results:**
    -   The final risk assessment summary and response strategies will be presented in the chat output, addressed to the `Risk_Manager`.
    -   The script includes commented-out sections for potentially extracting the final report from the chat history or running monitoring cycles separately.

## Customization

-   **Workflow:** Modify the `system_message` of the `GroupChatManager` in `main.py` to change the orchestration logic or workflow steps.
-   **Agent Logic:** Update the internal methods (e.g., `_scan_financial_system`, `_calculate_var`) within each agent's Python file (`agents/*.py`) to implement real data connections, models, and analysis logic. Replace placeholder logic and dummy data.
-   **Configuration:** Update the risk appetite, risk matrix, control library, and KRI definitions in `main.py` (or load them from external files/databases).
-   **Models:** Change the LLM models used in the `llm_config` in `main.py`.
