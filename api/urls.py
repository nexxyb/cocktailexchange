from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"cocktails", views.CocktailViewSet)
router.register(r"positions", views.PositionViewSet, basename="position")
router.register(r"transactions", views.TransactionViewSet, basename="transaction")
router.register(r"market-events", views.MarketEventViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("portfolio/", views.PortfolioView.as_view(), name="portfolio"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
    path("user/", views.ActiveUserView.as_view(), name="user"),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
]
