import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from backtester.models import Strategy
from backtester.serializers import (
    CreateStrategySerializer,
    ListStrategySerializer,
    UpdateStrategySerializer,
)
from backtester.utils.backtester import Backtester
from backtester.utils.strategy_generator import StrategyGenerator

logger = logging.getLogger(__name__)


class StrategyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating and modifying trading strategies.
    """

    queryset = Strategy.objects.all()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strategy_generator = StrategyGenerator()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateStrategySerializer
        elif self.action == "list":
            return ListStrategySerializer
        elif self.action == "partial_update":
            return UpdateStrategySerializer

    def handle_strategy_generation(self, prompt, strategy_code=None):
        """
        Generate or modify a strategy based on prompt and strategy_code.
        """
        try:
            if strategy_code:
                # Modify strategy
                strategy_code, parameters = self.strategy_generator.modify_strategy(
                    strategy_code, prompt
                )
            else:
                # Generate new strategy
                strategy_code, parameters = self.strategy_generator.generate_strategy(
                    prompt
                )

            logger.info(
                f"Strategy processed successfully with parameters: {parameters}"
            )
            return strategy_code, parameters
        except ValueError as e:
            logger.error(f"Error generating strategy: {e}")
            raise

    def create(self, request):
        """
        Create a new trading strategy based on user input.
        """
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)

        # validated data
        data = create_serializer.validated_data
        prompt = data["prompt"]

        try:
            strategy_code, parameters = self.handle_strategy_generation(prompt)
            created_strategy = create_serializer.save(
                strategy_code=strategy_code, parameters=parameters
            )

            return Response(
                ListStrategySerializer(created_strategy).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def partial_update(self, request, pk=None):
        """
        Partially update an existing trading strategy.
        """
        strategy = self.get_object()
        update_serializer = self.get_serializer(
            strategy, data=request.data, partial=True
        )
        update_serializer.is_valid(raise_exception=True)

        # validated data
        data = update_serializer.validated_data
        strategy_code = data.get("strategy_code", strategy.strategy_code)
        prompt = data.get("prompt", strategy.prompt)

        try:
            strategy_code, parameters = self.handle_strategy_generation(
                prompt, strategy_code
            )

            # Save the update serializer with new values
            updates_strategy = update_serializer.save(
                strategy_code=strategy_code, parameters=parameters
            )

            return Response(
                ListStrategySerializer(updates_strategy).data,
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
        if not strategy_code:
            return Response(
                {"error": "No strategy to backtest. Please provide a strategy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parameters = request.data.get("parameters", {})
        assets = request.data.get("assets", [])
        start_date = request.data.get("start_date", "2022-01-01")
        end_date = request.data.get("end_date", "2023-01-01")
        initial_cash = request.data.get("initial_cash", 100000)
        generate_plots = request.data.get("generate_plots", True)

        logger.info(f"Running backtest for strategy: {strategy_code}")

        try:
            backtester = Backtester(
                strategy_code=strategy_code,
                parameters=parameters,
                data_directory="utils/data",
                assets=assets,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                generate_plots=generate_plots,
            )
            results = backtester.run_backtest()
            logger.info(f"Backtest completed successfully with results: {results}")

            return Response({"results": results}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
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
        logger.info(f"Assets changed to: {assets}")

        return Response(
            {"message": "Assets updated successfully!", "assets": assets},
            status=status.HTTP_200_OK,
        )
