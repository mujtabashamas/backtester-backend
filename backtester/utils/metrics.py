import logging

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Metrics:
    """
    A utility class for calculating financial metrics from backtesting results,
    supporting both individual and multiple result sets.
    """

    @staticmethod
    def calculate(results):
        """
        Calculate metrics for one or multiple backtesting results.

        Args:
            results (list or tuple): A list of multiple backtesting results or a single result tuple.

        Returns:
            dict: Calculated metrics for either a single result or multiple averages if a list of results is provided.
        """
        if isinstance(results, list):
            logger.info("Calculating metrics for multiple results")
            return Metrics._calculate_multiple(results)
        else:
            logger.info("Calculating metrics for a single result")
            return Metrics._calculate_single(results[0])

    @staticmethod
    def _calculate_single(result):
        """
        Calculate metrics for a single backtesting result.

        Args:
            result: A backtesting result object.

        Returns:
            dict: Calculated metrics such as portfolio value, Sharpe ratio, max drawdown, and trade analysis.
        """
        portfolio_value = result.broker.getvalue()
        logger.info(f"Final portfolio value: {portfolio_value}")

        sharpe_analysis = result.analyzers.sharpe.get_analysis()
        sharpe_ratio = sharpe_analysis.get("sharpe", None)
        logger.info(f"Sharpe ratio: {sharpe_ratio}")

        drawdown_analysis = result.analyzers.drawdown.get_analysis()
        max_drawdown = drawdown_analysis.get("max", {}).get("drawdown", None)
        logger.info(f"Max drawdown: {max_drawdown}")

        returns_analysis = result.analyzers.returns.get_analysis()
        total_return = returns_analysis.get("rtot", None)
        logger.info(f"Total return: {total_return}")

        trade_analysis = result.analyzers.trades.get_analysis()
        logger.info(f"Trade analysis: {trade_analysis}")

        metrics = {
            "final_portfolio_value": portfolio_value,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_return": total_return,
            "trade_analysis": Metrics._process_trade_analysis(trade_analysis),
        }

        return metrics

    @staticmethod
    def _calculate_multiple(results):
        """
        Calculate metrics for multiple backtesting results and compute the average metrics.

        Args:
            results (list): A list of tuples where each tuple contains a backtesting result object.

        Returns:
            dict: A dictionary containing both individual metrics for each result and averaged metrics across results.
        """
        logger.info("Processing multiple results for average metrics.")
        individual_results = [
            Metrics._calculate_single(result[0]) for result in results
        ]

        def safe_mean(values):
            valid_values = [v for v in values if v is not None]
            return np.mean(valid_values) if valid_values else None

        avg_metrics = {
            "final_portfolio_value": safe_mean(
                [r["final_portfolio_value"] for r in individual_results]
            ),
            "sharpe_ratio": safe_mean([r["sharpe_ratio"] for r in individual_results]),
            "max_drawdown": safe_mean([r["max_drawdown"] for r in individual_results]),
            "total_return": safe_mean([r["total_return"] for r in individual_results]),
        }

        trade_analyses = [r["trade_analysis"] for r in individual_results]
        avg_trade_analysis = {
            "total_trades": safe_mean([ta["total_trades"] for ta in trade_analyses]),
            "winning_trades": safe_mean(
                [ta["winning_trades"] for ta in trade_analyses]
            ),
            "losing_trades": safe_mean([ta["losing_trades"] for ta in trade_analyses]),
            "win_rate": safe_mean([ta["win_rate"] for ta in trade_analyses]),
            "avg_trade": safe_mean([ta["avg_trade"] for ta in trade_analyses]),
            "avg_win": safe_mean([ta["avg_win"] for ta in trade_analyses]),
            "avg_loss": safe_mean([ta["avg_loss"] for ta in trade_analyses]),
            "largest_win": safe_mean([ta["largest_win"] for ta in trade_analyses]),
            "largest_loss": safe_mean([ta["largest_loss"] for ta in trade_analyses]),
            "avg_trade_length": safe_mean(
                [ta["avg_trade_length"] for ta in trade_analyses]
            ),
            "profit_factor": safe_mean([ta["profit_factor"] for ta in trade_analyses]),
        }

        avg_metrics["trade_analysis"] = avg_trade_analysis

        logger.info("Average metrics calculated.")
        return {
            "individual_results": individual_results,
            "average_metrics": avg_metrics,
        }

    @staticmethod
    def _process_trade_analysis(trade_analysis):
        """
        Process trade analysis metrics from a backtesting result.

        Args:
            trade_analysis: Trade analysis object containing statistics about trades made during backtesting.

        Returns:
            dict: Processed trade analysis metrics including total trades, win rate, average trade, and profit factor.
        """
        total_trades = trade_analysis.total.total
        logger.info(f"Total trades: {total_trades}")

        if total_trades == 0:
            logger.info("No trades to analyze.")
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_trade": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "largest_win": 0,
                "largest_loss": 0,
                "avg_trade_length": 0,
                "profit_factor": 0,
            }

        winning_trades = trade_analysis.won.total
        losing_trades = trade_analysis.lost.total
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        avg_trade = trade_analysis.pnl.net.average
        avg_win = trade_analysis.won.pnl.average if winning_trades > 0 else 0
        avg_loss = trade_analysis.lost.pnl.average if losing_trades > 0 else 0
        largest_win = trade_analysis.won.pnl.max if winning_trades > 0 else 0
        largest_loss = trade_analysis.lost.pnl.max if losing_trades > 0 else 0
        avg_trade_length = trade_analysis.len.average

        gross_profits = trade_analysis.won.pnl.total if winning_trades > 0 else 0
        gross_losses = abs(trade_analysis.lost.pnl.total) if losing_trades > 0 else 0
        profit_factor = (
            gross_profits / gross_losses if gross_losses != 0 else float("inf")
        )

        logger.info(
            f"Processed trade analysis: Win rate = {win_rate}, Profit factor = {profit_factor}"
        )

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_trade": avg_trade,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "avg_trade_length": avg_trade_length,
            "profit_factor": profit_factor,
        }
