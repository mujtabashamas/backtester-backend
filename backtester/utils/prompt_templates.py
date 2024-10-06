STRATEGY_RELEVANCE_CHECK = """
Is the following prompt related to creating or modifying a trading strategy? 
Answer with only 'Yes' or 'No'.

Prompt: {prompt}
"""

STRATEGY_GENERATION = """
Generate a Python trading strategy class using Backtrader named `MyStrategy` based on the following description:

{user_input}

The code should:

- Be a complete, runnable Python class.
- Include all necessary imports.
- Use Backtrader's structure for strategies.
- **Provide only the code for the `MyStrategy` class and necessary imports. Do not include any explanations, comments, or additional text.**

Here is a simple strategy template for reference:
import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ('sma_period', 20),
    )

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.sma_period)

    def next(self):
        if not self.position:  # If not in the market
            if self.data.close[0] > self.sma[0]: # Buy condition
                self.buy()
        elif self.data.close[0] < self.sma[0]:  # Sell condition
            self.close()

Only respond with the code, no additional text, and do not include any introductory phrases or code indicators.
The lookahead bias is a common issue in backtesting, be aware of that.
To fix this, we need to use the previous candle's high and low for our calculations.
Always only use indicators that are part of the Backtrader library or ta-lib.
Begin your response now.
"""

STRATEGY_MODIFICATION = """
Modify the following Python strategy code according to this request:

Modification request:
{modification_prompt}

Original code:
{current_strategy}

The modified code should:

- Be a complete, runnable Python class named `MyStrategy`.
- Include all necessary imports.
- Reflect the requested modifications accurately.
- **Provide only the updated code for the `MyStrategy` class and necessary imports. Do not include any explanations, comments, or additional text.**

Only respond with the code, no additional text, and do not include any introductory phrases or code indicators.
The lookahead bias is a common issue in backtesting, be aware of that.
To fix this, we need to use the previous candle's high and low for our calculations.
Always only use indicators that are part of the Backtrader library or ta-lib.
Begin your response now.
"""

STRATEGY_CORRECTION = """
The following strategy code has a compilation error:

{strategy_code}

Compilation error: {error_message}

Is it possible that you are using indicators that are not part of the Backtrader library? If so please use only Backtrader indicators or create your own. Available backtrader indicators are:
Please correct the error and provide only the corrected code. Ensure all necessary imports are included and that the code follows Backtrader's structure for strategies.
"""

STRATEGY_DESCRIPTION = """
Please provide a concise, clear, and simple natural language description of the trading strategy defined in the code below. Focus on summarizing the strategy's behavior and actions in the market from the perspective of a trader. Do not include any code snippets, variable names, or explanations about the code structure or implementation details. The description should be no longer than a few sentences.
Example: "Buy when the 10-period SMA crosses above the 20-period SMA. 
Sell when the 10-period SMA crosses below the 20-period SMA."

describe the following strategy:
{strategy_code}
"""

SYSTEM_MESSAGE_STRATEGY_DESCRIPTION = "You are a financial analyst who describes trading strategies in simple terms."

CODE_GENERATOR_SYSTEM_MESSAGE = "You are an AI language model that generates only code based on user requests. You do not provide explanations or additional text. All outputs should be code-only."

