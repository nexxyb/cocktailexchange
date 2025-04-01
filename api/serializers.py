from django.contrib.auth.models import User

# In serializers.py
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Cocktail,
    MarketEvent,
    Position,
    PriceHistory,
    Transaction,
    UserPortfolio,
)


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        fields = ("id", "username", "email", "password", "first_name", "last_name")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        refresh = RefreshToken.for_user(instance)
        representation["tokens"] = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        return representation


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # The default result (access/refresh tokens)
        data = super().validate(attrs)

        # Add user data to the response
        # self.user is set by the parent serializer after successful authentication
        user_data = UserSerializer(self.user).data
        data["user"] = user_data

        return data


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


# class TransactionSerializer(serializers.ModelSerializer):
#     cocktail_name = serializers.ReadOnlyField(source="cocktail.name")

#     class Meta:
#         model = Transaction
#         fields = (
#             "id",
#             "cocktail",
#             "cocktail_name",
#             "transaction_type",
#             "quantity",
#             "price",
#             "timestamp",
#             "realized_pnl",
#         )
#         read_only_fields = ("user", "portfolio", "position", "timestamp")


class TransactionSerializer(serializers.ModelSerializer):
    trade_type = serializers.SerializerMethodField()
    cocktail_name = serializers.ReadOnlyField(source="cocktail.name")

    class Meta:
        model = Transaction
        fields = (
            "id",
            "cocktail",
            "cocktail_name",
            "transaction_type",
            "trade_type",
            "quantity",
            "price",
            "timestamp",
            "realized_pnl",
        )

    def get_trade_type(self, obj):
        if obj.transaction_type == "OPEN":
            return "BUY" if obj.position.position_type == "LONG" else "SELL"
        else:  # transaction_type == "CLOSE"
            return "SELL" if obj.position.position_type == "LONG" else "BUY"


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
