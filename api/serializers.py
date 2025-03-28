from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Cocktail,
    PriceHistory,
    UserPortfolio,
    Position,
    Transaction,
    MarketEvent,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ("id", "price", "timestamp")


class CocktailSerializer(serializers.ModelSerializer):
    price_history = PriceHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Cocktail
        fields = (
            "id",
            "name",
            "description",
            "image",
            "initial_price",
            "current_price",
            "volatility",
            "price_history",
        )


class CocktailListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""

    class Meta:
        model = Cocktail
        fields = ("id", "name", "current_price", "image")


class PositionSerializer(serializers.ModelSerializer):
    cocktail_name = serializers.ReadOnlyField(source="cocktail.name")
    current_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    unrealized_pnl = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Position
        fields = (
            "id",
            "cocktail",
            "cocktail_name",
            "position_type",
            "quantity",
            "entry_price",
            "is_open",
            "opened_at",
            "closed_at",
            "current_value",
            "unrealized_pnl",
        )
        read_only_fields = ("portfolio", "opened_at", "closed_at", "is_open")


class TransactionSerializer(serializers.ModelSerializer):
    cocktail_name = serializers.ReadOnlyField(source="cocktail.name")

    class Meta:
        model = Transaction
        fields = (
            "id",
            "cocktail",
            "cocktail_name",
            "transaction_type",
            "quantity",
            "price",
            "timestamp",
            "realized_pnl",
        )
        read_only_fields = ("user", "portfolio", "position", "timestamp")


class PortfolioSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)
    total_value = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    unrealized_pnl = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    realized_pnl = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = UserPortfolio
        fields = (
            "id",
            "user",
            "cash_balance",
            "positions",
            "total_value",
            "unrealized_pnl",
            "realized_pnl",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("user", "created_at", "updated_at")


class MarketEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketEvent
        fields = (
            "id",
            "title",
            "description",
            "event_type",
            "impact_factor",
            "is_active",
            "start_time",
            "end_time",
        )


class PositionCreateSerializer(serializers.Serializer):
    cocktail = serializers.PrimaryKeyRelatedField(queryset=Cocktail.objects.all())
    position_type = serializers.ChoiceField(choices=Position.POSITION_TYPES)
    quantity = serializers.IntegerField(min_value=1)


class PositionCloseSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class LeaderboardEntrySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    realized_pnl = serializers.DecimalField(max_digits=10, decimal_places=2)
    position_count = serializers.IntegerField()
