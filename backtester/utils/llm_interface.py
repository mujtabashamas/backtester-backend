import logging
import re

import openai
import requests

from backtester.utils.prompt_templates import (
    STRATEGY_RELEVANCE_CHECK,
    STRATEGY_GENERATION,
    STRATEGY_MODIFICATION,
    STRATEGY_CORRECTION,
    CODE_GENERATOR_SYSTEM_MESSAGE,
    STRATEGY_DESCRIPTION,
    SYSTEM_MESSAGE_STRATEGY_DESCRIPTION,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_code(output: str) -> str:
    """
    Extracts Python code from the LLM's output.
    Handles both code blocks marked with ``` and unmarked code.

    Args:
        output (str): The text output from the model containing code.

    Returns:
        str: The extracted Python code.
    """
    logging.info("Extracting code from output.")

    # Check if the output is wrapped in code block markers
    code_block_match = re.search(r"```(?:python)?\n(.*?)```", output, re.DOTALL)
    if code_block_match:
        logging.info("Code found within ``` blocks.")
        return code_block_match.group(1).strip()

    # If no code block markers, extract lines that look like code
    code_lines = []
    recording = False
    for line in output.split("\n"):
        if (
            line.strip().startswith(("import", "from", "class", "def", "#"))
            or recording
        ):
            recording = True
            code_lines.append(line)
    extracted_code = "\n".join(code_lines)
    logging.info("Code extracted without ``` blocks.")
    return extracted_code


class LLMInterface:
    """
    A class that interfaces with the OpenAI API to perform various tasks such as
    generating strategies, modifying them, checking relevance, and more.

    Attributes:
        api_key (str): OpenAI API key for authentication.
    """

    def __init__(self, api_key: str):
        """
        Initializes the LLMInterface with the provided API key.

        Args:
            api_key (str): The API key for accessing OpenAI services.
        """
        openai.api_key = api_key
        logger.info(f"LLMInterface initialized with API key: {api_key[:5]}...")

    def generate_completion(
        self,
        prompt: str,
        model: str = "gpt-4o",
        max_tokens: int = 500,
        system_message: str = None,
    ) -> str:
        """
        Sends a prompt to the OpenAI API and returns the completion.

        Args:
            prompt (str): The prompt to send to the model.
            model (str): The model to use (default is 'gpt-4o').
            max_tokens (int): Maximum number of tokens for the response.
            system_message (str, optional): Optional system-level message for contextual guidance.

        Returns:
            str: The completion response from the API.
        """
        logger.info(f"Sending prompt to LLM (model: {model}, max_tokens: {max_tokens})")
        logger.debug(f"Prompt: {prompt}")

        messages = [{"role": "user", "content": prompt}]
        if system_message:
            messages.insert(0, {"role": "system", "content": system_message})

        try:
            response = openai.ChatCompletion.create(
                model=model, messages=messages, temperature=0.3, max_tokens=max_tokens
            )
            result = response.choices[0].message["content"]
            logger.info("Received response from LLM.")
            logger.debug(f"Response: {result}")
            return result
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    def check_strategy_relevance(self, prompt: str) -> bool:
        """
        Checks the relevance of a given strategy prompt.

        Args:
            prompt (str): The user-provided strategy prompt.

        Returns:
            bool: True if the strategy is relevant, otherwise False.
        """
        logger.info("Checking strategy relevance for prompt.")
        check_prompt = STRATEGY_RELEVANCE_CHECK.format(prompt=prompt)
        response = self.generate_completion(check_prompt, max_tokens=10)
        is_relevant = response.strip().lower() == "yes"
        logger.info(f"Strategy relevance: {is_relevant}")
        return is_relevant

    def generate_strategy(self, user_input: str) -> str:
        """
        Generates a strategy based on the user's input.

        Args:
            user_input (str): The input provided by the user.

        Returns:
            str: The generated strategy code.
        """
        logger.info("Generating strategy for user input.")
        strategy_prompt = STRATEGY_GENERATION.format(user_input=user_input)
        raw_output = self.generate_completion(
            strategy_prompt, system_message=CODE_GENERATOR_SYSTEM_MESSAGE
        )
        code = extract_code(raw_output)
        logger.info("Strategy generated successfully.")
        return code

    def modify_strategy(self, current_strategy: str, modification_prompt: str) -> str:
        """
        Modifies an existing strategy based on the modification prompt.

        Args:
            current_strategy (str): The current strategy code.
            modification_prompt (str): The modifications the user wants.

        Returns:
            str: The modified strategy code.
        """
        logger.info("Modifying strategy.")
        full_prompt = STRATEGY_MODIFICATION.format(
            current_strategy=current_strategy, modification_prompt=modification_prompt
        )
        raw_output = self.generate_completion(
            full_prompt, system_message=CODE_GENERATOR_SYSTEM_MESSAGE
        )
        modified_code = extract_code(raw_output)
        logger.info("Strategy modified successfully.")
        return modified_code

    def correct_strategy(self, strategy_code: str, error_message: str) -> str:
        """
        Corrects a strategy based on an error message.

        Args:
            strategy_code (str): The original strategy code.
            error_message (str): The error message that needs to be fixed.

        Returns:
            str: The corrected strategy code.
        """
        logger.info("Correcting strategy based on error.")
        correction_prompt = STRATEGY_CORRECTION.format(
            strategy_code=strategy_code, error_message=error_message
        )
        raw_output = self.generate_completion(correction_prompt)
        corrected_code = extract_code(raw_output)
        logger.info("Strategy corrected successfully.")
        return corrected_code

    def describe_strategy(self, strategy_code: str) -> str:
        """
        Provides a description of the given strategy code.

        Args:
            strategy_code (str): The code of the strategy to describe.

        Returns:
            str: A description of the strategy.
        """
        logger.info("Describing strategy.")
        description_prompt = STRATEGY_DESCRIPTION.format(strategy_code=strategy_code)
        description = self.generate_completion(
            description_prompt,
            max_tokens=150,
            system_message=SYSTEM_MESSAGE_STRATEGY_DESCRIPTION,
        )
        logger.info("Strategy description generated successfully.")
        return description
