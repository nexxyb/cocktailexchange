from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import F, Sum, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from .models import (
    Cocktail,
    PriceHistory,
    UserPortfolio,
    Position,
    Transaction,
    MarketEvent,
)
from .serializers import (
    UserSerializer,
    CocktailSerializer,
    CocktailListSerializer,
    PriceHistorySerializer,
    PortfolioSerializer,
    PositionSerializer,
    TransactionSerializer,
    MarketEventSerializer,
    PositionCreateSerializer,
    PositionCloseSerializer,
    LeaderboardEntrySerializer,
)


class CocktailViewSet(viewsets.ModelViewSet):
    """
    API endpoint for cocktails (stocks)
    """

    queryset = Cocktail.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return CocktailListSerializer
        return CocktailSerializer

    @action(detail=True, methods=["get"])
    def price_history(self, request, pk=None):
        cocktail = self.get_object()
        # Get time period from query params, default to 7 days
        days = int(request.query_params.get("days", 7))
        cutoff_date = timezone.now() - timedelta(days=days)

        price_history = cocktail.price_history.filter(timestamp__gte=cutoff_date)
        serializer = PriceHistorySerializer(price_history, many=True)
        return Response(serializer.data)


class PortfolioView(APIView):
    """
    API endpoint for user portfolio information
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        portfolio = get_object_or_404(UserPortfolio, user=request.user)
        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data)


class PositionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for position management
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PositionSerializer

    def get_queryset(self):
        user_portfolio = get_object_or_404(UserPortfolio, user=self.request.user)
        return Position.objects.filter(portfolio=user_portfolio)

    @action(detail=False, methods=["post"])
    def open_position(self, request):
        """Open a new position (buy/sell)"""
        serializer = PositionCreateSerializer(data=request.data)
        if serializer.is_valid():
            portfolio = get_object_or_404(UserPortfolio, user=request.user)
            cocktail = serializer.validated_data["cocktail"]
            position_type = serializer.validated_data["position_type"]
            quantity = serializer.validated_data["quantity"]

            # Calculate cost
            price = cocktail.current_price
            position_cost = price * Decimal(str(quantity))

            # Check if user has enough cash
            if portfolio.cash_balance < position_cost:
                return Response(
                    {"error": "Insufficient funds to open position"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create position
            position = Position.objects.create(
                portfolio=portfolio,
                cocktail=cocktail,
                position_type=position_type,
                quantity=quantity,
                entry_price=price,
            )

            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                portfolio=portfolio,
                cocktail=cocktail,
                position=position,
                transaction_type="OPEN",
                quantity=quantity,
                price=price,
            )

            # Update portfolio balance
            portfolio.cash_balance -= position_cost
            portfolio.save()

            # Update cocktail price based on trading activity
            demand_change = quantity if position_type == "LONG" else -quantity
            cocktail.update_price(demand_change)

            # Return updated position
            return Response(
                PositionSerializer(position).data, status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def close_position(self, request, pk=None):
        """Close an existing position (partially or fully)"""
        position = self.get_object()

        if not position.is_open:
            return Response(
                {"error": "This position is already closed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PositionCloseSerializer(data=request.data)
        if serializer.is_valid():
            close_quantity = serializer.validated_data["quantity"]

            if close_quantity > position.quantity:
                return Response(
                    {"error": "Cannot close more shares than position holds"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            portfolio = position.portfolio
            cocktail = position.cocktail
            current_price = cocktail.current_price

            # Calculate PnL for this closing transaction
            if position.position_type == "LONG":
                pnl = close_quantity * (current_price - position.entry_price)
            else:  # SHORT
                pnl = close_quantity * (position.entry_price - current_price)

            # Calculate proceeds
            if position.position_type == "LONG":
                proceeds = current_price * Decimal(str(close_quantity))
            else:  # SHORT
                # For shorts, we return the initial margin plus any profit (or minus any loss)
                initial_margin = position.entry_price * Decimal(str(close_quantity))
                proceeds = initial_margin + pnl

            # Update portfolio balance
            portfolio.cash_balance += proceeds
            portfolio.save()

            # Create transaction record
            Transaction.objects.create(
                user=portfolio.user,
                portfolio=portfolio,
                cocktail=cocktail,
                position=position,
                transaction_type="CLOSE",
                quantity=close_quantity,
                price=current_price,
                realized_pnl=pnl,
            )

            # Update position
            if close_quantity == position.quantity:
                position.is_open = False
                position.closed_at = timezone.now()
            else:
                position.quantity -= close_quantity
            position.save()

            # Update cocktail price based on trading activity
            demand_change = (
                -close_quantity if position.position_type == "LONG" else close_quantity
            )
            cocktail.update_price(demand_change)

            return Response(PositionSerializer(position).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for transaction history
    """

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by("-timestamp")


class LeaderboardView(APIView):
    """
    API endpoint for leaderboard
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        portfolios = UserPortfolio.objects.all()

        leaderboard_entries = []
        for portfolio in portfolios:
            # Calculate total positions value
            positions_value = sum(
                position.current_value
                for position in portfolio.positions.filter(is_open=True)
            )

            # Create leaderboard entry
            entry = {
                "user_id": portfolio.user.id,
                "username": portfolio.user.username,
                "total_value": portfolio.cash_balance + positions_value,
                "realized_pnl": portfolio.realized_pnl,
                "position_count": portfolio.positions.filter(is_open=True).count(),
            }
            leaderboard_entries.append(entry)

        # Sort by total value, descending
        leaderboard_entries.sort(key=lambda x: x["total_value"], reverse=True)

        serializer = LeaderboardEntrySerializer(leaderboard_entries, many=True)
        return Response(serializer.data)


class MarketEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for market events
    """

    queryset = MarketEvent.objects.filter(is_active=True)
    serializer_class = MarketEventSerializer
    permission_classes = [permissions.IsAuthenticated]


class ActiveUserView(APIView):
    """
    API endpoint for current user information
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
