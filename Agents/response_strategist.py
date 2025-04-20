# risk_management_agents/agents/response_strategist.py
import autogen
import logging
import random
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ResponseStrategyAgent(autogen.ConversableAgent):
    """
    An Autogen agent that suggests or designs risk response strategies
    (Avoid, Transfer, Mitigate, Accept) based on assessed risks,
    company policy (risk appetite), and potentially resource constraints.
    """
    def __init__(
        self,
        name: str = "Response_Strategy_Agent",
        llm_config: Optional[Dict[str, Any]] = None, # LLM could help generate rationales or creative controls
        code_execution_config: Optional[Dict[str, Any]] = False, # If using external libs for cost-benefit etc.
        risk_appetite: Optional[Dict[str, Any]] = None, # Company's risk appetite statements/thresholds
        control_library: Optional[Dict[str, Any]] = None, # Reference to available controls
        **kwargs,
    ):
        """
        Initializes the Response Strategy Agent.

        Args:
            name (str): The name of the agent.
            llm_config (Optional[Dict[str, Any]]): LLM configuration. Can be False.
            code_execution_config (Optional[Dict[str, Any]]): Code execution config. Can be False.
            risk_appetite (Optional[Dict[str, Any]]): Defines tolerance for different risk levels/categories.
                Example: {"Operational": {"High": "Mitigate", "Critical": "Avoid/Transfer"}, "Financial": ...}
            control_library (Optional[Dict[str, Any]]): A structured library of potential controls.
                Example: {"Operational": [{"id": "CTRL-OP-01", "name": "Implement Redundant Server", "cost": "High", "effectiveness": "High"}, ...]}
            **kwargs: Additional arguments for ConversableAgent.
        """
        system_message = """You are the Response Strategy Agent.
Your role is to develop and suggest appropriate risk response strategies (Avoid, Transfer, Mitigate, Accept) for prioritized risks.
You receive a list of assessed risks, including their ID, description, category, assessed level (e.g., Low, Medium, High, Critical), and potentially quantitative/qualitative details.
You also consider the company's defined risk appetite and may consult a library of standard controls.
For each high-priority risk, you recommend a primary strategy and suggest specific actions or controls, especially for mitigation. You provide a brief rationale for your suggestions.
You do not initiate conversations; you respond to requests to develop strategies.
Example Input (passed via function call arguments):
{
  "prioritized_risks": [
    {"risk_id": "OP001", "description": "Server outage risk", "category": "Operational", "assessment": {"risk_level": "High", ...}},
    {"risk_id": "FIN002", "description": "Market volatility impact", "category": "Financial", "assessment": {"risk_level": "Critical", "VaR_99_1day": 150000.50, ...}}
  ],
  "risk_appetite": {"Operational": {"High": "Mitigate", "Critical": "Avoid/Transfer"}, ...},
  "control_library": {"Operational": [...], ...} // Optional
}
Example Output Format (returned by function call):
{
  "source": "ResponseStrategyAgent",
  "type": "ResponseStrategies",
  "strategies": {
    "OP001": {
      "suggested_strategy": "Mitigate",
      "control_suggestions": ["Implement Redundant Server (CTRL-OP-01)", "Increase monitoring frequency"],
      "rationale": "Risk level is High for Operational category. Appetite suggests Mitigation. Controls aim to reduce likelihood/impact."
    },
    "FIN002": {
      "suggested_strategy": "Transfer",
      "control_suggestions": ["Explore hedging instruments", "Purchase market risk insurance"],
      "rationale": "Risk level is Critical for Financial category. Appetite suggests Avoid/Transfer. Transfer via hedging/insurance seems feasible."
    }
    // ... strategies for other risks
  }
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
        # Register the function for strategy development
        self.register_function(
            function_map={
                "develop_response_strategies": self.develop_response_strategies
            }
        )
        self.risk_appetite = risk_appetite or {} # Load default or passed config
        self.control_library = control_library or {} # Load default or passed config
        logger.info(f"Initialized Response Strategy Agent: {self.name}")
        # TODO: Load more complex configs if needed (cost models, historical data)

    def _get_appetite_guidance(self, category: str, level: str) -> str:
        """Retrieves suggested strategy from risk appetite config."""
        category_appetite = self.risk_appetite.get(category, {})
        # Check specific level, then potentially a default for the category
        guidance = category_appetite.get(level, category_appetite.get("Default", "Accept")) # Default to Accept if not specified
        return guidance

    def _suggest_controls(self, risk_info: Dict[str, Any]) -> List[str]:
        """Suggests specific control measures based on risk and control library."""
        # TODO: Implement more sophisticated lookup in self.control_library
        # Match controls based on category, keywords in description, effectiveness vs. cost trade-off
        category = risk_info.get('category', 'General')
        suggestions = []

        # Example lookup in a hypothetical control library structure
        category_controls = self.control_library.get(category, [])
        if category_controls:
            # Simple: suggest the first one or two relevant controls
            # Advanced: Filter by effectiveness, cost, applicability based on risk_info details
            relevant_controls = [c for c in category_controls if c.get('effectiveness') in ['High', 'Medium']] # Example filter
            suggestions = [f"{c.get('name', 'Unnamed Control')} ({c.get('id', 'N/A')})" for c in relevant_controls[:2]] # Take top 2

        # Add generic suggestions if no specific controls found
        if not suggestions:
            suggestions.append(f"Implement enhanced monitoring for {category} risks")
            suggestions.append(f"Develop contingency plan for {risk_info.get('description', 'this risk')}")

        return suggestions[:3] # Limit suggestions for brevity

    def _generate_strategy_for_risk(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a strategy for a single risk."""
        risk_id = risk.get('risk_id', 'unknown_risk')
        category = risk.get('category', 'General')
        # Extract risk level from assessment structure
        assessment = risk.get('assessment', {})
        risk_level = assessment.get('risk_level', 'Medium') # Default if assessment or level missing

        logger.debug(f"Generating strategy for Risk ID: {risk_id}, Category: {category}, Level: {risk_level}")

        # 1. Get guidance from risk appetite
        appetite_guidance = self._get_appetite_guidance(category, risk_level)
        logger.debug(f"Risk Appetite Guidance for {category}/{risk_level}: {appetite_guidance}")

        # 2. Determine primary strategy based on guidance
        # Guidance might be direct ("Mitigate") or suggestive ("Avoid/Transfer")
        possible_strategies = appetite_guidance.split('/')
        suggested_strategy = random.choice(possible_strategies) # Simple choice if multiple options

        # Refine strategy based on level (e.g., always Accept Low risk unless appetite says otherwise)
        if risk_level == "Low" and suggested_strategy != "Accept" and "Low" not in self.risk_appetite.get(category, {}):
             suggested_strategy = "Accept"
             logger.debug("Overriding strategy to 'Accept' for Low risk level based on default policy.")

        # 3. Suggest controls based on strategy
        control_suggestions = []
        if suggested_strategy == "Mitigate":
            control_suggestions = self._suggest_controls(risk)
        elif suggested_strategy == "Transfer":
            control_suggestions = ["Explore relevant insurance options", "Assess outsourcing possibilities", "Review contractual risk transfer clauses"]
        elif suggested_strategy == "Avoid":
            control_suggestions = ["Evaluate ceasing the associated activity", "Re-scope project/process to eliminate risk source", "Reject the proposed initiative"]
        elif suggested_strategy == "Accept":
             control_suggestions = ["Acknowledge risk and monitor", "Allocate contingency budget if applicable"]

        # 4. Generate Rationale
        rationale = f"Risk level assessed as '{risk_level}' for '{category}' category. "
        rationale += f"Company risk appetite suggests '{appetite_guidance}'. "
        rationale += f"Primary strategy chosen: {suggested_strategy}."
        if control_suggestions and suggested_strategy != "Accept":
             rationale += f" Suggested actions focus on {suggested_strategy.lower()}ing the risk."
        elif suggested_strategy == "Accept":
             rationale += " Risk accepted based on level and appetite."

        return {
            "suggested_strategy": suggested_strategy,
            "control_suggestions": control_suggestions,
            "rationale": rationale
        }

    def develop_response_strategies(
        self,
        prioritized_risks: List[Dict[str, Any]],
        # Allow appetite/library override at call time if needed
        risk_appetite: Optional[Dict[str, Any]] = None,
        control_library: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Develops response strategies for a list of prioritized risks.
        Intended to be called by other agents via autogen's function calling.

        Args:
            prioritized_risks (List[Dict[str, Any]]): List of assessed risks, typically sorted by priority.
                                                     Each dict should contain at least 'risk_id', 'category', 'assessment' (with 'risk_level').
            risk_appetite (Optional[Dict[str, Any]]): Override for the agent's configured risk appetite.
            control_library (Optional[Dict[str, Any]]): Override for the agent's configured control library.

        Returns:
            Dict[str, Any]: A dictionary containing the suggested strategies keyed by risk_id.
        """
        logger.info(f"{self.name}: Received request to develop strategies for {len(prioritized_risks)} risks.")

        # Use overrides if provided, else use agent's config
        current_appetite = risk_appetite or self.risk_appetite
        current_controls = control_library or self.control_library
        # Temporarily set for the duration of this call if overrides are given
        original_appetite = self.risk_appetite
        original_controls = self.control_library
        self.risk_appetite = current_appetite
        self.control_library = current_controls

        strategies = {}
        try:
            for risk in prioritized_risks:
                risk_id = risk.get('risk_id')
                if not risk_id:
                    logger.warning("Skipping risk with missing 'risk_id'.")
                    continue
                if not risk.get('assessment') or 'risk_level' not in risk.get('assessment', {}):
                     logger.warning(f"Skipping risk '{risk_id}' due to missing assessment level.")
                     continue

                strategies[risk_id] = self._generate_strategy_for_risk(risk)

        except Exception as e:
             logger.error(f"Error during strategy development: {e}", exc_info=True)
             # Restore original config in case of error
             self.risk_appetite = original_appetite
             self.control_library = original_controls
             return {"error": f"An error occurred during strategy development: {str(e)}"}

        # Restore original config
        self.risk_appetite = original_appetite
        self.control_library = original_controls

        report = {
            "source": self.name,
            "type": "ResponseStrategies",
            "strategies": strategies
        }
        logger.info(f"{self.name}: Completed strategy development for {len(strategies)} risks.")
        return report
