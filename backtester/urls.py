from django.urls import path, include
from rest_framework.routers import DefaultRouter

from backtester.viewsets import StrategyViewSet, BacktestViewSet, AssetsViewSet

router = DefaultRouter()
router.register(r"strategies", StrategyViewSet, basename="strategy")
router.register(r"backtest", BacktestViewSet, basename="backtest")
router.register(r"assets", AssetsViewSet, basename="assets")

urlpatterns = [
    path("", include(router.urls)),
]
