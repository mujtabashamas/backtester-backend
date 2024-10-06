import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from backtester.models import Strategy
from backtester.serializers import StrategySerializer
from backtester.utils.backtester import Backtester
from backtester.utils.strategy_generator import StrategyGenerator

# Initialize logging
logger = logging.getLogger(__name__)


class StrategyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating and modifying trading strategies.
    """

    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strategy_generator = StrategyGenerator()

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request):
        """
        Create a new trading strategy based on user input.
        """
        prompt = request.data.get("prompt")
        if not prompt:
            return Response(
                {"error": "Prompt is required to create a strategy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            strategy_code, parameters = self.strategy_generator.generate_strategy(
                prompt
            )
            logger.info("Strategy created successfully with parameters: %s", parameters)
            serializer = StrategySerializer(
                data={
                    "prompt": prompt,
                    "strategy_code": strategy_code,
                    "parameters": parameters,
                }
            )
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(
                {
                    "message": "Strategy created successfully!",
                    "prompt": prompt,
                    "strategy_code": strategy_code,
                    "parameters": parameters,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            logger.error("Error generating strategy: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """
        Partially update an existing trading strategy.
        """
        strategy = self.get_object()
        prompt = request.data.get("prompt")
        strategy_code = request.data.get("strategy_code")

        if not strategy_code:
            return Response(
                {"error": "Strategy code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not prompt:
            return Response(
                {"error": "Prompt is required to modify the strategy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Generate the new strategy code and parameters
            strategy_code, parameters = self.strategy_generator.modify_strategy(
                strategy_code, prompt
            )

            logger.info(
                "Strategy modified successfully. New parameters: %s", parameters
            )

            # Update the serializer data with the new strategy_code and parameters
            partial_data = {
                "strategy_code": strategy_code,
                "parameters": parameters,
                "prompt": prompt,
            }

            serializer = self.get_serializer(strategy, data=partial_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(
                {
                    "message": "Strategy modified successfully!",
                    "prompt": prompt,
                    "strategy_code": strategy_code,
                    "parameters": parameters,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            logger.error("Error modifying strategy: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BacktestViewSet(viewsets.ViewSet):
    """
    ViewSet for running backtests on trading strategies.
    """

    @action(detail=False, methods=["post"], url_path="run")
    def run(self, request):
        """
        Run a backtest on a given strategy.
        """
        strategy_code = request.data.get("strategy_code")
        parameters = request.data.get("parameters", {})
        assets = request.data.get("assets", [])
        start_date = request.data.get("start_date", "2022-01-01")
        end_date = request.data.get("end_date", "2023-01-01")
        initial_cash = request.data.get("initial_cash", 100000)
        generate_plots = request.data.get("generate_plots", True)
        data_directory = "utils/data"

        if not strategy_code:
            return Response(
                {"error": "No strategy to backtest. Please provide a strategy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Running backtest with strategy: %s, assets: %s", strategy_code, assets
        )
        try:
            backtester = Backtester(
                strategy_code=strategy_code,
                parameters=parameters,
                data_directory=data_directory,
                assets=assets,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                generate_plots=generate_plots,
            )
            results = backtester.run_backtest()
            logger.info("Backtest completed successfully with results: %s", results)
            return Response({"results": results}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error running backtest: %s", str(e))
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssetsViewSet(viewsets.ViewSet):
    """
    ViewSet for managing assets used in strategies and backtesting.
    """

    @action(detail=False, methods=["post"], url_path="change-assets")
    def change_assets(self, request):
        """
        Change the list of assets for the backtest.
        """
        new_assets = request.data.get("assets")
        if not new_assets:
            return Response(
                {"error": "No assets provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        assets = [asset.strip() for asset in new_assets.split(",")]
        logger.info("Assets changed to: %s", assets)
        return Response(
            {"message": "Assets updated successfully!", "assets": assets},
            status=status.HTTP_200_OK,
        )
