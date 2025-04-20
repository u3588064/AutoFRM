# risk_management_agents/agents/qualitative_assessor.py
import autogen
import logging
import random
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class QualitativeRiskAssessorAgent(autogen.ConversableAgent):
    """
    An Autogen agent that assesses risks difficult to quantify (operational,
    strategic, reputational, compliance) using methods like risk matrices,
    rule-based reasoning, or potentially LLM-based judgment.
    """
    def __init__(
        self,
        name: str = "Qualitative_Risk_Assessor",
        llm_config: Optional[Dict[str, Any]] = None, # LLM can help interpret text, apply rules
        code_execution_config: Optional[Dict[str, Any]] = False, # Set to config if using rule engine libs
        risk_matrix_config: Optional[Dict[str, Any]] = None, # Config for likelihood/impact scales
        **kwargs,
    ):
        """
        Initializes the Qualitative Risk Assessor Agent.

        Args:
            name (str): The name of the agent.
            llm_config (Optional[Dict[str, Any]]): LLM configuration. Can be False.
            code_execution_config (Optional[Dict[str, Any]]): Code execution config. Can be False.
            risk_matrix_config (Optional[Dict[str, Any]]): Configuration for the risk matrix.
                Example: {
                    "likelihood_scale": ["Very Low", "Low", "Medium", "High", "Very High"],
                    "impact_scale": ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"],
                    "level_map": { # Defines how L/I maps to overall level
                        (0,0): "Low", (0,1): "Low", ..., (4,4): "Critical"
                    }
                }
            **kwargs: Additional arguments for ConversableAgent.
        """
        system_message = """You are the Qualitative Risk Assessor Agent.
Your purpose is to assess risks that are difficult to quantify, such as operational, strategic, reputational, or compliance risks.
You receive information about a risk (description, category, context, potential impacts) and are asked to assess it, often using a specified method like 'RiskMatrix' or 'RuleBased'.
Based on the provided information and your configured knowledge (like risk matrix definitions or rule sets), you determine factors like likelihood and impact, and assign an overall risk level or assessment.
You report your assessment in a structured format.
You do not initiate conversations; you respond to assessment requests.
Example Input (passed via function call arguments):
{
  "risk_id": "OP001",
  "risk_info": {
      "description": "Potential for server outage due to aging hardware",
      "category": "Operational",
      "potential_impact_description": "Service disruption for up to 4 hours, minor data loss possibility",
      "contributing_factors": ["Hardware age > 5 years", "No recent maintenance"]
  },
  "assessment_method": "RiskMatrix"
}
Example Output Format (returned by function call):
{
  "source": "QualitativeRiskAssessorAgent",
  "type": "QualitativeAssessment",
  "risk_id": "OP001",
  "assessment_method_used": "RiskMatrix",
  "assessment": {
    "likelihood": "Medium",
    "impact": "Major",
    "risk_level": "High",
    "justification": "Aging hardware increases failure probability; service disruption has major business impact."
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
        # Register the function for assessment
        self.register_function(
            function_map={
                "perform_qualitative_assessment": self.perform_qualitative_assessment
            }
        )
        # Default/Example Risk Matrix Config
        self.risk_matrix_config = risk_matrix_config or {
            "likelihood_scale": ["Very Low", "Low", "Medium", "High", "Very High"],
            "impact_scale": ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"],
            "level_map": self._default_level_map(5, 5) # Generate a default map
        }
        logger.info(f"Initialized Qualitative Risk Assessor Agent: {self.name}")
        # TODO: Load knowledge bases, rule sets, historical case data if needed

    @staticmethod
    def _default_level_map(num_likelihood, num_impact):
        """Generates a simple default risk level map."""
        level_map = {}
        levels = ["Low", "Medium", "High", "Critical"]
        for l in range(num_likelihood):
            for i in range(num_impact):
                # Simple example: level increases with sum of indices
                level_index = min((l + i) // ((num_likelihood + num_impact - 2) // (len(levels)-1)), len(levels)-1) if (num_likelihood + num_impact - 2) > 0 else 0
                level_map[(l, i)] = levels[level_index]
        return level_map


    def _apply_risk_matrix(self, risk_info: Dict[str, Any]) -> Dict[str, Any]:
        """Applies the configured likelihood/impact risk matrix."""
        logger.info(f"{self.name}: Applying risk matrix...")
        # TODO: Implement more sophisticated logic to determine likelihood/impact
        # This could involve keyword analysis of description/impact, checking factors, or even LLM judgment if configured.

        # Dummy assessment - Randomly choose for now
        likelihood_scale = self.risk_matrix_config["likelihood_scale"]
        impact_scale = self.risk_matrix_config["impact_scale"]
        likelihood = random.choice(likelihood_scale)
        impact = random.choice(impact_scale)

        l_idx = likelihood_scale.index(likelihood)
        i_idx = impact_scale.index(impact)
        risk_level = self.risk_matrix_config["level_map"].get((l_idx, i_idx), "Undefined")

        # Basic justification
        justification = f"Assessed based on general understanding. Likelihood estimated as {likelihood}, Impact as {impact}."
        if "contributing_factors" in risk_info:
             justification += f" Factors considered: {', '.join(risk_info['contributing_factors'])}."
        if "potential_impact_description" in risk_info:
             justification += f" Potential Impact: {risk_info['potential_impact_description']}."


        return {
            "likelihood": likelihood,
            "impact": impact,
            "risk_level": risk_level,
            "justification": justification
        }

    def _apply_rule_based_reasoning(self, risk_info: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for using a rule engine or expert system logic."""
        logger.info(f"{self.name}: Applying rule-based reasoning...")
        # TODO: Implement rule engine interaction (e.g., using external library or LLM with rules in prompt)
        # Rules might check combinations: e.g., IF category is 'Compliance' AND impact description contains 'fine' THEN risk_level is 'High'.

        # Dummy assessment
        triggered_rules = []
        risk_level = "Low" # Default
        justification = "No specific rules triggered."

        # Example dummy rule check
        if risk_info.get("category") == "Operational" and "outage" in risk_info.get("description", "").lower():
            triggered_rules.append("Rule_OperationalOutage")
            risk_level = "Medium"
            justification = "Rule triggered for potential operational outage."
        if "compliance" in risk_info.get("description", "").lower() or risk_info.get("category") == "Compliance":
             triggered_rules.append("Rule_ComplianceMention")
             risk_level = "High" # Compliance often high priority
             justification = "Rule triggered due to compliance keyword or category."


        return {
            "triggered_rules": triggered_rules,
            "risk_level": risk_level,
            "justification": justification
        }

    def perform_qualitative_assessment(
        self,
        risk_id: str,
        risk_info: Dict[str, Any],
        assessment_method: str = "RiskMatrix" # Default method
    ) -> Dict[str, Any]:
        """
        Performs qualitative assessment based on the provided information and method.
        Intended to be called by other agents via autogen's function calling.

        Args:
            risk_id (str): A unique identifier for the risk being assessed.
            risk_info (Dict[str, Any]): Information about the risk (description, category, context, impacts, factors).
            assessment_method (str): Specifies the method ('RiskMatrix', 'RuleBased', etc.).

        Returns:
            Dict[str, Any]: A dictionary containing the structured assessment results.
        """
        logger.info(f"{self.name}: Received request for {assessment_method} assessment for risk '{risk_id}'")

        assessment = {}
        method_used = assessment_method

        try:
            if assessment_method.upper() == "RISKMATRIX":
                assessment = self._apply_risk_matrix(risk_info)
            elif assessment_method.upper() == "RULEBASED":
                assessment = self._apply_rule_based_reasoning(risk_info)
            # Add more assessment methods as needed
            else:
                logger.warning(f"Unsupported assessment method requested: {assessment_method}. Defaulting to RiskMatrix.")
                assessment = self._apply_risk_matrix(risk_info)
                method_used = "RiskMatrix (Defaulted)"

        except Exception as e:
            logger.error(f"Error during {assessment_method} assessment for risk '{risk_id}': {e}", exc_info=True)
            assessment = {"error": f"An error occurred during assessment: {str(e)}"}
            method_used = f"{assessment_method}_Failed"

        report = {
            "source": self.name,
            "type": "QualitativeAssessment",
            "risk_id": risk_id,
            "assessment_method_used": method_used,
            "assessment": assessment
        }
        logger.info(f"{self.name}: Completed {method_used} assessment for risk '{risk_id}'.")
        return report
