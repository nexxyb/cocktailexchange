from django.contrib import admin
from .models import (
    Cocktail,
    PriceHistory,
    UserPortfolio,
    Position,
    Transaction,
    MarketEvent,
)


@admin.register(Cocktail)
class CocktailAdmin(admin.ModelAdmin):
    list_display = ("name", "current_price", "initial_price", "volatility")
    search_fields = ("name",)


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("cocktail", "price", "timestamp")
    list_filter = ("cocktail", "timestamp")


@admin.register(UserPortfolio)
class UserPortfolioAdmin(admin.ModelAdmin):
    list_display = ("user", "cash_balance", "total_value")
    search_fields = ("user__username",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "portfolio",
        "cocktail",
        "position_type",
        "quantity",
        "entry_price",
        "is_open",
    )
    list_filter = ("is_open", "position_type")
    search_fields = ("portfolio__user__username", "cocktail__name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "cocktail",
        "transaction_type",
        "quantity",
        "price",
        "timestamp",
    )
    list_filter = ("transaction_type", "timestamp")
    search_fields = ("user__username", "cocktail__name")


@admin.register(MarketEvent)
class MarketEventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "is_active", "start_time", "end_time")
    list_filter = ("event_type", "is_active")
    search_fields = ("title",)
