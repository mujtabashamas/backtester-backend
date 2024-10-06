import logging

from decouple import config

from .code_validator import CodeValidator
from .llm_interface import LLMInterface

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyGenerator:
    """
    A class to generate and modify trading strategies using a language model interface.

    Attributes:
        llm_interface (LLMInterface): Interface for interacting with the language model.
        code_validator (CodeValidator): Validator for checking and correcting strategy code.
        current_strategy_description (str): Description of the current trading strategy.
    """

    def __init__(self):
        """
        Initializes the StrategyGenerator, loading environment variables and
        initializing the LLMInterface and CodeValidator.

        Raises:
            ValueError: If the OPENAI_API_KEY is not found in the environment variables.
        """
        # Initialize LLMInterface
        api_key = config("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables.")
            raise ValueError("OPENAI_API_KEY not found in environment variables.")

        self.llm_interface = LLMInterface(api_key)
        self.code_validator = CodeValidator(self.llm_interface)
        self.current_strategy_description = None

    def generate_strategy(self, user_input: str) -> tuple[str, dict]:
        """
        Generates a trading strategy based on user input.

        Args:
            user_input (str): The user's prompt for generating a strategy.

        Returns:
            tuple[str, dict]: A tuple containing the validated strategy code and its parameters.

        Raises:
            ValueError: If the user input is not related to creating a trading strategy.
        """
        if not self.llm_interface.check_strategy_relevance(user_input):
            logger.error(
                "The provided prompt is not related to creating a trading strategy."
            )
            raise ValueError(
                "The provided prompt is not related to creating a trading strategy."
            )

        strategy_code = self.llm_interface.generate_strategy(user_input)
        validated_code, parameters = self.code_validator.check_and_correct_strategy(
            strategy_code
        )
        self._update_strategy_description(validated_code)
        logger.info("Successfully generated strategy.")
        return validated_code, parameters

    def modify_strategy(
        self, current_strategy: str, modification_prompt: str
    ) -> tuple[str, dict]:
        """
        Modifies an existing trading strategy based on a modification prompt.

        Args:
            current_strategy (str): The current trading strategy code.
            modification_prompt (str): The user's prompt for modifying the strategy.

        Returns:
            tuple[str, dict]: A tuple containing the validated modified strategy code and its parameters.

        Raises:
            ValueError: If the modification prompt is not related to modifying a trading strategy.
        """
        if not self.llm_interface.check_strategy_relevance(modification_prompt):
            logger.error(
                "The provided prompt is not related to modifying a trading strategy."
            )
            raise ValueError(
                "The provided prompt is not related to modifying a trading strategy."
            )

        modified_strategy = self.llm_interface.modify_strategy(
            current_strategy, modification_prompt
        )
        validated_code, parameters = self.code_validator.check_and_correct_strategy(
            modified_strategy
        )
        self._update_strategy_description(validated_code)
        logger.info("Successfully modified strategy.")
        return validated_code, parameters

    def _update_strategy_description(self, strategy_code: str):
        """
        Updates the current strategy description based on the given strategy code.

        Args:
            strategy_code (str): The code of the strategy to describe.
        """
        self.current_strategy_description = self.llm_interface.describe_strategy(
            strategy_code
        )
        logger.info("Updated Strategy Description:")
        logger.info(self.current_strategy_description)

    def get_current_strategy_description(self) -> str:
        """
        Retrieves the current strategy description.

        Returns:
            str: The current strategy description.
        """
        return self.current_strategy_description
