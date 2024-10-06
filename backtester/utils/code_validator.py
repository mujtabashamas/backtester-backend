import ast
import logging
import os
import subprocess
import sys
import tempfile
from typing import Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeValidator:
    """
    A class to validate and correct Python code through an LLM interface.
    It allows executing the code in a sandbox and extracting parameters from it.

    Attributes:
        llm_interface: An interface that provides LLM-driven corrections to the code.
    """

    def __init__(self, llm_interface):
        """
        Initializes the CodeValidator with a given LLM interface.

        Args:
            llm_interface: The LLM interface to correct strategies.
        """
        self.llm_interface = llm_interface

    def validate_code(self, code: str) -> Tuple[bool, str]:
        """
        Validates the provided Python code by executing it in a sandbox.

        Args:
            code (str): The Python code to validate.

        Returns:
            Tuple[bool, str]: A tuple where the first element indicates whether the code is valid,
                              and the second element contains the error message if validation fails.
        """
        logger.info("Validating the code.")
        try:
            self.execute_in_sandbox(code)
            logger.info("Code validated successfully.")
            return True, ""
        except Exception as e:
            error_message = f"Validation error: {str(e)}"
            logger.error(error_message)
            return False, error_message

    def execute_in_sandbox(self, code: str) -> None:
        """
        Executes the given code in a temporary sandbox environment.

        Args:
            code (str): The Python code to execute.

        Raises:
            RuntimeError: If the code execution fails or times out.
        """
        logger.info("Executing the code in a sandbox.")
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=True,
                text=True,
            )
            logger.info(f"Execution Output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Execution error: {e.stderr}")
            raise RuntimeError(f"Execution error: {e.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Execution timed out.")
            raise RuntimeError("Execution timed out.")
        finally:
            os.remove(tmp_file_path)
            logger.info(f"Temporary file {tmp_file_path} deleted.")

    def extract_parameters(self, code: str) -> Dict[str, Any]:
        """
        Extracts parameters from the 'MyStrategy' class in the given Python code.

        Args:
            code (str): The Python code to parse and extract parameters from.

        Returns:
            Dict[str, Any]: A dictionary of parameter names and their respective values.
        """
        logger.info("Extracting parameters from the code.")
        tree = ast.parse(code)
        parameters = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "MyStrategy":
                for subnode in node.body:
                    if isinstance(subnode, ast.Assign):
                        for target in subnode.targets:
                            if isinstance(target, ast.Name) and target.id == "params":
                                if isinstance(subnode.value, ast.Tuple):
                                    for elt in subnode.value.elts:
                                        if (
                                            isinstance(elt, ast.Tuple)
                                            and len(elt.elts) == 2
                                        ):
                                            key = (
                                                elt.elts[0].s
                                                if isinstance(elt.elts[0], ast.Str)
                                                else elt.elts[0].value
                                            )
                                            value = (
                                                elt.elts[1].n
                                                if isinstance(elt.elts[1], ast.Num)
                                                else elt.elts[1].value
                                            )
                                            parameters[key] = value
        logger.info(f"Extracted parameters: {parameters}")
        return parameters

    def check_and_correct_strategy(
        self, strategy_code: str, max_attempts: int = 3
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Validates the provided strategy code and attempts to correct it using the LLM interface if validation fails.

        Args:
            strategy_code (str): The Python code to validate and correct.
            max_attempts (int): The maximum number of validation attempts. Default is 3.

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing the corrected code and a dictionary of extracted parameters.

        Raises:
            ValueError: If the strategy could not be validated after the maximum number of attempts.
        """
        logger.info(
            f"Checking and correcting strategy with a maximum of {max_attempts} attempts."
        )
        attempts = 0
        while attempts < max_attempts:
            is_valid, validation_error = self.validate_code(strategy_code)
            if is_valid:
                logger.info("Strategy validated successfully.")
                parameters = self.extract_parameters(strategy_code)
                return strategy_code, parameters

            attempts += 1
            logger.warning(
                f"Validation failed on attempt {attempts}. Error: {validation_error}"
            )
            if attempts == max_attempts:
                error_msg = f"Failed to validate the strategy after {max_attempts} attempts. Last error: {validation_error}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            strategy_code = self.llm_interface.correct_strategy(
                strategy_code, validation_error
            )
            logger.info(f"Strategy corrected by LLM interface. Retrying...")

        logger.error("Unexpected error in strategy correction.")
        raise ValueError("Unexpected error in strategy correction.")
