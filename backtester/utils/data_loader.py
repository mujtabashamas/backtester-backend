import logging
import os

import backtrader as bt
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    A class responsible for loading financial data from CSV files into Backtrader feed format.

    Attributes:
        data_directory (str): The directory where the CSV data files are located.
    """

    def __init__(self, data_directory: str):
        """
        Initializes the DataLoader with the given data directory.

        Args:
            data_directory (str): The directory relative to the project root where CSV files are stored.
        """
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_directory = os.path.join(project_root, data_directory)
        logger.info(
            f"DataLoader initialized with data directory: {self.data_directory}"
        )

    def load_data(self, assets: list, start_date: str, end_date: str) -> list:
        """
        Loads the historical data for the given assets within the date range.

        Args:
            assets (list): List of asset names (e.g., ['AAPL', 'GOOG']) to load.
            start_date (str): Start date in YYYY-MM-DD format.
            end_date (str): End date in YYYY-MM-DD format.

        Returns:
            list: A list of Backtrader data feeds for each asset.
        """
        logger.info(
            f"Loading data for assets: {assets} from {start_date} to {end_date}"
        )
        return [self._load_asset(asset, start_date, end_date) for asset in assets]

    def _load_asset(
        self, asset: str, start_date: str, end_date: str
    ) -> bt.feeds.PandasData:
        """
        Loads data for a single asset and converts it to a Backtrader PandasData feed.

        Args:
            asset (str): The name of the asset.
            start_date (str): Start date in YYYY-MM-DD format.
            end_date (str): End date in YYYY-MM-DD format.

        Returns:
            bt.feeds.PandasData: The Backtrader data feed for the asset.
        """
        logger.info(f"Loading data for asset: {asset}")
        df = self._load_csv(asset)
        df = df.loc[start_date:end_date]
        logger.info(f"Data for asset {asset} loaded from {start_date} to {end_date}")
        return bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open="Open",
            high="High",
            low="Low",
            close="Close",
            volume="Volume",
            timeframe=bt.TimeFrame.Minutes,
            compression=60,
        )

    def _load_csv(self, asset: str) -> pd.DataFrame:
        """
        Loads the CSV file for a given asset into a Pandas DataFrame.

        Args:
            asset (str): The name of the asset to load from CSV.

        Returns:
            pd.DataFrame: The loaded DataFrame containing asset data.

        Raises:
            FileNotFoundError: If the CSV file for the asset is not found.
        """
        file_path = os.path.join(self.data_directory, f"{asset}_1h.csv")
        if not os.path.exists(file_path):
            logger.error(f"Data file for {asset} not found at {file_path}")
            raise FileNotFoundError(f"Data file for {asset} not found at {file_path}")
        df = pd.read_csv(file_path, parse_dates=["datetime"], index_col="datetime")
        logger.info(f"CSV file for {asset} loaded from {file_path}")
        return df.sort_index()

    def get_available_assets(self) -> list:
        """
        Returns the list of available assets based on the CSV files present in the data directory.

        Returns:
            list: A list of asset names corresponding to available data files.
        """
        logger.info("Fetching available assets from data directory.")
        assets = [
            f.split("_")[0]
            for f in os.listdir(self.data_directory)
            if f.endswith("_1h.csv")
        ]
        logger.info(f"Available assets: {assets}")
        return assets
