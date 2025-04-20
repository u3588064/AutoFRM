# risk_management_agents/agents/quantitative_assessor.py
import autogen
import logging
import random  # For dummy calculations
import numpy as np # Example import for actual calculations
import scipy.stats as st # Example import
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class QuantitativeRiskAssessorAgent(autogen.ConversableAgent):
    """
    An Autogen agent that performs quantitative assessment of risks using
    mathematical and statistical models (e.g., VaR, Stress Tests, Monte Carlo).
    Focuses on quantifiable risks like financial and market risks.
    """
    def __init__(
        self,
        name: str = "Quantitative_Risk_Assessor",
        llm_config: Optional[Dict[str, Any]] = False, # LLM likely not needed, focus is code execution
        code_execution_config: Optional[Dict[str, Any]] = None, # Needs code execution
        **kwargs,
    ):
        """
        Initializes the Quantitative Risk Assessor Agent.

        Args:
            name (str): The name of the agent.
            llm_config (Optional[Dict[str, Any]]): LLM configuration. Set to False if not needed.
            code_execution_config (Optional[Dict[str, Any]]): Configuration for code execution.
                Should specify a working directory and potentially package installations if needed.
                Example: {"work_dir": "coding", "use_docker": False} # Use_docker True recommended
            **kwargs: Additional arguments for ConversableAgent.
        """
        system_message = """You are the Quantitative Risk Assessor Agent.
Your role is to perform quantitative risk assessments using mathematical and statistical models when requested.
You receive input data describing the risk (e.g., financial data, market parameters) and the type of assessment required (e.g., 'VaR', 'StressTest', 'MonteCarlo').
You execute the appropriate models (Value at Risk, stress tests, simulations, etc.) based on the request and data.
You report the quantitative results of your assessment in a structured format.
You do not initiate conversations; you respond to requests to perform assessments.
Ensure your calculations are sound and clearly state any assumptions made.
Example Input (passed via function call arguments):
{
  "risk_description": "Potential loss on equity portfolio due to market downturn",
  "data": {"portfolio_value": 1000000, "volatility": 0.2, "correlation_matrix": [...]},
  "assessment_type": "VaR",
  "parameters": {"confidence_level": 0.99, "time_horizon_days": 1}
}
Example Output Format (returned by function call):
{
  "source": "QuantitativeRiskAssessorAgent",
  "type": "QuantitativeAssessment",
  "assessment_type_performed": "VaR",
  "results": {
    "VaR_99_1day": 150000.50,
    "method": "Parametric VaR",
    "assumptions": ["Normal distribution of returns"]
  },
  "input_data_summary": {"portfolio_value": 1000000, "volatility": 0.2} # Optional summary
}
"""
        if code_execution_config is None:
             logger.warning(f"Initializing {name} without code_execution_config. Agent may not be able to run calculations.")
             exec_config = False
        else:
             exec_config = code_execution_config

        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=exec_config,
            **kwargs,
        )
        # Register the function for assessment
        self.register_function(
            function_map={
                "perform_quantitative_assessment": self.perform_quantitative_assessment
            }
        )
        logger.info(f"Initialized Quantitative Risk Assessor Agent: {self.name}")
        # TODO: Load pre-defined models, parameters, historical data sets if needed at init

    def _calculate_var(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for Value at Risk (VaR) calculation."""
        logger.info(f"{self.name}: Calculating VaR...")
        # TODO: Implement actual VaR calculation (e.g., historical, parametric, Monte Carlo)
        # Example using parametric VaR (requires numpy, scipy)
        value = data.get("portfolio_value", 0)
        volatility = data.get("volatility", 0)
        confidence_level = parameters.get("confidence_level", 0.95)
        time_horizon_days = parameters.get("time_horizon_days", 1)

        if value > 0 and volatility > 0:
            z_score = st.norm.ppf(confidence_level)
            var = value * volatility * z_score * np.sqrt(time_horizon_days / 252) # Assuming 252 trading days
            return {
                f"VaR_{int(confidence_level*100)}_{time_horizon_days}day": round(var, 2),
                "method": "Parametric VaR",
                "assumptions": ["Normal distribution of returns", f"{time_horizon_days} day horizon", f"{confidence_level*100}% confidence"]
            }
        else:
            logger.warning("Insufficient data for Parametric VaR calculation.")
            return {"error": "Insufficient data for Parametric VaR"}


    def _perform_stress_test(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for performing stress tests."""
        logger.info(f"{self.name}: Performing stress test...")
        # TODO: Implement stress testing logic (apply extreme scenarios to models)
        scenario_name = parameters.get("scenario_name", "Generic Stress")
        scenario_details = parameters.get("scenario_details", {"market_shock": -0.1}) # e.g., -10% market shock

        # Dummy calculation based on portfolio value and shock
        value = data.get("portfolio_value", 0)
        shock = scenario_details.get("market_shock", 0)
        estimated_impact = value * shock # Simplified impact

        return {
            "scenario": scenario_name,
            "estimated_impact": round(estimated_impact, 2),
            "details": scenario_details
        }

    def _perform_monte_carlo(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for Monte Carlo simulations."""
        logger.info(f"{self.name}: Performing Monte Carlo simulation...")
        # TODO: Implement Monte Carlo simulation logic (e.g., for option pricing, portfolio projection)
        num_simulations = parameters.get("num_simulations", 10000)
        # Dummy result
        simulated_mean = data.get("portfolio_value", 0) * (1 + random.uniform(-0.05, 0.05))
        simulated_std_dev = data.get("portfolio_value", 0) * random.uniform(0.01, 0.1)
        return {
            "method": "Monte Carlo Simulation",
            "num_simulations": num_simulations,
            "result_summary": {
                "mean_outcome": round(simulated_mean, 2),
                "std_dev": round(simulated_std_dev, 2)
                # Could include quantiles, etc.
            }
        }

    def perform_quantitative_assessment(
        self,
        risk_description: str,
        data: Dict[str, Any],
        assessment_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Performs quantitative assessment based on the provided data and type.
        Intended to be called by other agents via autogen's function calling.

        Args:
            risk_description (str): Description of the risk being assessed.
            data (Dict[str, Any]): Data relevant to the risk (e.g., market data, financial figures).
            assessment_type (str): Specifies the type of assessment (e.g., 'VaR', 'StressTest', 'MonteCarlo').
            parameters (Optional[Dict[str, Any]]): Specific parameters for the assessment (e.g., confidence level for VaR).

        Returns:
            Dict[str, Any]: A dictionary containing the structured assessment results.
        """
        logger.info(f"{self.name}: Received request for {assessment_type} assessment for '{risk_description}'")
        if parameters is None:
            parameters = {}

        results = {}
        assessment_performed = assessment_type

        try:
            if assessment_type.upper() == "VAR":
                results = self._calculate_var(data, parameters)
            elif assessment_type.upper() == "STRESSTEST":
                results = self._perform_stress_test(data, parameters)
            elif assessment_type.upper() == "MONTECARLO":
                 results = self._perform_monte_carlo(data, parameters)
            # Add more assessment types as needed
            else:
                logger.warning(f"Unsupported assessment type requested: {assessment_type}")
                results = {"error": f"Unsupported assessment type: {assessment_type}"}
                assessment_performed = "Unsupported"

        except Exception as e:
            logger.error(f"Error during {assessment_type} assessment: {e}", exc_info=True)
            results = {"error": f"An error occurred during {assessment_type} assessment: {str(e)}"}
            assessment_performed = f"{assessment_type}_Failed"


        report = {
            "source": self.name,
            "type": "QuantitativeAssessment",
            "assessment_type_performed": assessment_performed,
            "results": results,
            "input_risk_description": risk_description,
            # Optional: Include a summary of key input data/params for context
            "input_summary": {"data_keys": list(data.keys()), "params": parameters}
        }
        logger.info(f"{self.name}: Completed {assessment_performed} assessment.")
        return report
