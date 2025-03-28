from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import random


class Cocktail(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.URLField(blank=True)
    initial_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    volatility = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def update_price(self, demand_change=0):
        """
        Update cocktail price based on trading activity and random market movements.

        demand_change: Positive for buying pressure, negative for selling pressure
        """
        # Base random movement (0.5% to 1.5% volatility)
        random_factor = random.uniform(-1, 1) * float(self.volatility) / 100

        # Impact from trading activity (0.1% to 0.5% per unit of demand)
        demand_impact = float(demand_change) * random.uniform(0.001, 0.005)

        # Combined price change
        price_change = float(self.current_price) * (random_factor + demand_impact)
        new_price = float(self.current_price) + price_change

        # Ensure price doesn't go below a minimum (e.g., $0.50)
        new_price = max(0.5, new_price)

        self.current_price = Decimal(str(round(new_price, 2)))
        self.save()

        # Create price history entry
        PriceHistory.objects.create(cocktail=self, price=self.current_price)

        return self.current_price


class PriceHistory(models.Model):
    cocktail = models.ForeignKey(
        Cocktail, on_delete=models.CASCADE, related_name="price_history"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]


class UserPortfolio(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="portfolio"
    )
    cash_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=10000.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

    @property
    def total_positions_value(self):
        """Calculate total value of all open positions"""
        total = 0
        for position in self.positions.filter(is_open=True):
            total += position.current_value
        return total

    @property
    def total_value(self):
        """Calculate total portfolio value (cash + positions)"""
        return self.cash_balance + self.total_positions_value

    @property
    def unrealized_pnl(self):
        """Calculate unrealized profit/loss across all open positions"""
        total = 0
        for position in self.positions.filter(is_open=True):
            total += position.unrealized_pnl
        return total

    @property
    def realized_pnl(self):
        """Calculate total realized profit/loss from closed positions"""
        return sum(
            t.realized_pnl for t in self.transactions.filter(transaction_type="CLOSE")
        )


class Position(models.Model):
    POSITION_TYPES = [
        ("LONG", "Long"),
        ("SHORT", "Short"),
    ]

    portfolio = models.ForeignKey(
        UserPortfolio, on_delete=models.CASCADE, related_name="positions"
    )
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE)
    position_type = models.CharField(max_length=5, choices=POSITION_TYPES)
    quantity = models.PositiveIntegerField()
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_open = models.BooleanField(default=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.position_type} {self.quantity} {self.cocktail.name} @ {self.entry_price}"

    @property
    def current_value(self):
        """Calculate current position value based on type"""
        if not self.is_open:
            return Decimal("0.00")

        if self.position_type == "LONG":
            return self.quantity * self.cocktail.current_price
        else:  # SHORT
            # For shorts, value increases as price decreases
            entry_value = self.quantity * self.entry_price
            current_cost = self.quantity * self.cocktail.current_price
            return entry_value + (entry_value - current_cost)

    @property
    def unrealized_pnl(self):
        """Calculate unrealized profit/loss"""
        if not self.is_open:
            return Decimal("0.00")

        if self.position_type == "LONG":
            return self.quantity * (self.cocktail.current_price - self.entry_price)
        else:  # SHORT
            return self.quantity * (self.entry_price - self.cocktail.current_price)


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("OPEN", "Open Position"),
        ("CLOSE", "Close Position"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    portfolio = models.ForeignKey(
        UserPortfolio, on_delete=models.CASCADE, related_name="transactions"
    )
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE)
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=5, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    realized_pnl = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.cocktail.name} @ {self.price}"


class MarketEvent(models.Model):
    EVENT_TYPES = [
        ("BOOM", "Market Boom"),
        ("CRASH", "Market Crash"),
        ("VOLATILITY", "High Volatility"),
        ("STABILITY", "Market Stability"),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    impact_factor = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


# Create user portfolio automatically when a new user registers
@receiver(post_save, sender=User)
def create_user_portfolio(sender, instance, created, **kwargs):
    if created:
        UserPortfolio.objects.create(user=instance)
