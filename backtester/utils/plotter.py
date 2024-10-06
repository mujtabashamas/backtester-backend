import logging
import os

from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Blackly

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_and_save_plot(cerebro, filename):
    """
    Generates and saves an interactive Bokeh plot of the trading results.

    Args:
        cerebro (backtrader.Cerebro): The Cerebro instance containing the strategy and data.
        filename (str): The name of the file to save the plot as.

    Raises:
        Exception: Raises an exception if the plot generation fails.
    """
    logger.info("Generating interactive Bokeh plot...")

    # Create a 'plots' directory if it doesn't exist
    os.makedirs("plots", exist_ok=True)

    plot_path = os.path.join("plots", filename)

    # Create a Bokeh object with desired settings, including filename
    b = Bokeh(
        style="bar",
        plot_mode="multi",
        scheme=Blackly(),
        output_mode="save",
        filename=plot_path,
    )

    try:
        # Generate and save the plot
        cerebro.plot(b)
        logger.info(f"Interactive Bokeh plot saved as: {plot_path}")
    except Exception as e:
        logger.error(f"Error generating plot: {str(e)}")
        raise
