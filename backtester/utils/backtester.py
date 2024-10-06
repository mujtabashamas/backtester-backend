import logging
from datetime import datetime

import backtrader as bt

from backtester.utils.data_loader import DataLoader
from backtester.utils.metrics import Metrics
from backtester.utils.plotter import generate_and_save_plot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Backtester:
    """
    Class to run a backtest on a trading strategy using the Backtrader framework.

    Attributes:
        strategy_code (str): The code for the strategy to be tested.
        parameters (dict): Parameters for the strategy.
        assets (list): List of assets to backtest the strategy on.
        start_date (datetime): The start date for the backtest.
        end_date (datetime): The end date for the backtest.
        initial_cash (float): The initial cash for the backtest portfolio.
        data_loader (DataLoader): Utility to load historical data for assets.
        generate_plots (bool): Whether to generate plots after the backtest.
    """

    def __init__(
        self,
        strategy_code,
        parameters,
        data_directory,
        assets,
        start_date,
        end_date,
        initial_cash=10000,
        generate_plots=False,
    ):
        """
        Initializes the Backtester class with the given parameters.

        Args:
            strategy_code (str): The code for the strategy.
            parameters (dict): The parameters for the strategy.
            data_directory (str): The directory where data is stored.
            assets (list): List of assets to backtest.
            start_date (str): The start date for the backtest (YYYY-MM-DD format).
            end_date (str): The end date for the backtest (YYYY-MM-DD format).
            initial_cash (float, optional): The starting cash for the portfolio. Defaults to 10000.
            generate_plots (bool, optional): Whether to generate plots. Defaults to False.
        """
        self.strategy_code = strategy_code
        self.parameters = parameters
        self.assets = assets  # List of assets
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.initial_cash = initial_cash
        self.data_loader = DataLoader(data_directory)
        self.generate_plots = generate_plots

    def run_backtest(self):
        """
        Runs the backtest for the strategy across the provided assets and date range.

        Returns:
            dict: The calculated metrics for the backtest.
        """
        logger.info("Starting Backtest")
        logger.info("Assets: %s", ", ".join(self.assets))
        logger.info(
            "Date Range: %s to %s", self.start_date.date(), self.end_date.date()
        )
        logger.info("Initial Cash: $%.2f", self.initial_cash)
        logger.info("Strategy Parameters: %s", self.parameters)

        all_results = []
        for asset in self.assets:
            logger.info("Backtesting asset: %s", asset)
            results = self._run_single_asset_backtest(asset)
            all_results.append(results)

        metrics = Metrics.calculate(all_results)
        self._print_results(metrics)

        return metrics

    def _run_single_asset_backtest(self, asset):
        """
        Runs the backtest on a single asset.

        Args:
            asset (str): The asset to run the backtest on.

        Returns:
            list: The results of the backtest for the asset.
        """
        cerebro = bt.Cerebro()

        # Add the strategy
        strategy_class = self._load_strategy()
        cerebro.addstrategy(strategy_class, **self.parameters)
        logger.info("Using Strategy: %s", strategy_class.__name__)

        # Add the data
        data_feed = self._load_data(asset)
        cerebro.adddata(data_feed, name=asset)
        df = data_feed.p.dataname
        logger.info("Loaded data for asset: %s", asset)
        logger.info("  Timeframe: %s", data_feed.p.timeframe)
        logger.info("  Compression: %s", data_feed.p.compression)
        logger.info("  From: %s", df.index.min())
        logger.info("  To: %s", df.index.max())
        logger.info("  Number of bars: %d", len(df))

        # Set the initial cash
        cerebro.broker.set_cash(self.initial_cash)
        logger.info("Starting Portfolio Value: $%.2f", cerebro.broker.getvalue())

        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        # Run the backtest
        results = cerebro.run()

        # Generate and save plots if requested
        if self.generate_plots:
            plot_filename = f"backtest_plot_{asset}_{self.start_date.date()}_{self.end_date.date()}.html"
            generate_and_save_plot(cerebro, plot_filename)
            logger.info("Generated plot: %s", plot_filename)

        return results

    def _print_results(self, metrics):
        """
        Prints the calculated metrics for the backtest.

        Args:
            metrics (dict): The metrics to print.
        """
        if "average_metrics" in metrics:
            logger.info("=== Overall Results ===")
            self._print_metrics(metrics["average_metrics"])

            for i, result in enumerate(metrics["individual_results"]):
                logger.info("=== Results for %s ===", self.assets[i])
                self._print_metrics(result)
        else:
            logger.info("=== Results ===")
            self._print_metrics(metrics)

    def _print_metrics(self, metrics):
        """
        Prints individual metrics from the backtest.

        Args:
            metrics (dict): The metrics to print.
        """
        for key, value in metrics.items():
            if key != "trade_analysis":
                if isinstance(value, float):
                    logger.info("%s: %.4f", key, value)
                else:
                    logger.info("%s: %s", key, value)

        logger.info("Trade Analysis:")
        for key, value in metrics["trade_analysis"].items():
            if isinstance(value, float):
                logger.info("  %s: %.4f", key, value)
            else:
                logger.info("  %s: %s", key, value)

    def _load_strategy(self):
        """
        Dynamically loads the strategy class from the provided strategy code.

        Returns:
            class: The strategy class.

        Raises:
            ValueError: If no valid strategy class is found in the provided code.
        """
        namespace = {}
        exec(self.strategy_code, globals(), namespace)
        strategy_class = next(
            (
                v
                for v in namespace.values()
                if isinstance(v, type) and issubclass(v, bt.Strategy)
            ),
            None,
        )
        if not strategy_class:
            logger.error("No valid strategy class found in the provided code.")
            raise ValueError("No valid strategy class found in the provided code.")
        return strategy_class

    def _load_data(self, asset):
        """
        Loads the historical data for the given asset.

        Args:
            asset (str): The asset to load data for.

        Returns:
            bt.feeds.DataBase: The data feed for the asset.
        """
        logger.info("Loading data for asset: %s", asset)
        return self.data_loader.load_data([asset], self.start_date, self.end_date)[0]
