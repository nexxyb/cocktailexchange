from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Cocktail, MarketEvent
from decimal import Decimal


class Command(BaseCommand):
    help = "Seeds the database with initial cocktails and market events"

    def handle(self, *args, **options):
        # Create initial cocktails
        cocktails = [
            {
                "name": "Margarita",
                "description": "A classic tequila-based cocktail with lime juice and orange liqueur.",
                "image": "https://example.com/images/margarita.jpg",
                "initial_price": Decimal("14.99"),
                "volatility": Decimal("1.2"),
            },
            {
                "name": "Old Fashioned",
                "description": "A timeless whiskey cocktail with sugar, bitters, and a twist of citrus.",
                "image": "https://example.com/images/old-fashioned.jpg",
                "initial_price": Decimal("12.50"),
                "volatility": Decimal("0.8"),
            },
            {
                "name": "Mojito",
                "description": "A refreshing rum cocktail with lime, mint, and soda water.",
                "image": "https://example.com/images/mojito.jpg",
                "initial_price": Decimal("11.25"),
                "volatility": Decimal("1.5"),
            },
            {
                "name": "Martini",
                "description": "An elegant mix of gin and vermouth, garnished with an olive or lemon twist.",
                "image": "https://example.com/images/martini.jpg",
                "initial_price": Decimal("16.75"),
                "volatility": Decimal("0.9"),
            },
            {
                "name": "Negroni",
                "description": "A bitter Italian cocktail made with gin, vermouth rosso, and Campari.",
                "image": "https://example.com/images/negroni.jpg",
                "initial_price": Decimal("13.50"),
                "volatility": Decimal("1.1"),
            },
            {
                "name": "Daiquiri",
                "description": "A simple but sophisticated rum cocktail with lime juice and sugar.",
                "image": "https://example.com/images/daiquiri.jpg",
                "initial_price": Decimal("10.99"),
                "volatility": Decimal("1.3"),
            },
            {
                "name": "Whiskey Sour",
                "description": "A mixed drink containing whiskey, lemon juice, sugar, and egg white.",
                "image": "https://example.com/images/whiskey-sour.jpg",
                "initial_price": Decimal("12.25"),
                "volatility": Decimal("1.0"),
            },
            {
                "name": "Espresso Martini",
                "description": "A cold, coffee-flavored cocktail made with vodka, espresso, and coffee liqueur.",
                "image": "https://example.com/images/espresso-martini.jpg",
                "initial_price": Decimal("15.50"),
                "volatility": Decimal("1.8"),
            },
            {
                "name": "Moscow Mule",
                "description": "A cocktail made with vodka, spicy ginger beer, and lime juice.",
                "image": "https://example.com/images/moscow-mule.jpg",
                "initial_price": Decimal("11.75"),
                "volatility": Decimal("1.4"),
            },
            {
                "name": "Piña Colada",
                "description": "A sweet cocktail made with rum, coconut cream, and pineapple juice.",
                "image": "https://example.com/images/pina-colada.jpg",
                "initial_price": Decimal("13.25"),
                "volatility": Decimal("1.6"),
            },
        ]

        created_count = 0
        for cocktail_data in cocktails:
            cocktail, created = Cocktail.objects.get_or_create(
                name=cocktail_data["name"],
                defaults={
                    "description": cocktail_data["description"],
                    "image": cocktail_data["image"],
                    "initial_price": cocktail_data["initial_price"],
                    "current_price": cocktail_data["initial_price"],
                    "volatility": cocktail_data["volatility"],
                },
            )
            if created:
                created_count += 1
                # Create initial price history entry
                cocktail.update_price(0)

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} new cocktails"))

        # Create market events
        events = [
            {
                "title": "Cocktail Festival",
                "description": "Annual cocktail festival causing prices to rise across the board.",
                "event_type": "BOOM",
                "impact_factor": Decimal("2.5"),
                "is_active": False,
            },
            {
                "title": "Supply Chain Issues",
                "description": "Difficulty sourcing ingredients is causing market instability.",
                "event_type": "VOLATILITY",
                "impact_factor": Decimal("1.8"),
                "is_active": False,
            },
            {
                "title": "Health Trend",
                "description": "A new health movement is causing alcohol sales to plummet.",
                "event_type": "CRASH",
                "impact_factor": Decimal("3.0"),
                "is_active": False,
            },
            {
                "title": "Market Stabilization",
                "description": "Regulatory changes have led to more predictable pricing.",
                "event_type": "STABILITY",
                "impact_factor": Decimal("0.5"),
                "is_active": False,
            },
        ]

        events_created = 0
        for event_data in events:
            event, created = MarketEvent.objects.get_or_create(
                title=event_data["title"],
                defaults={
                    "description": event_data["description"],
                    "event_type": event_data["event_type"],
                    "impact_factor": event_data["impact_factor"],
                    "is_active": event_data["is_active"],
                },
            )
            if created:
                events_created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {events_created} new market events")
        )

        # Create superuser if it doesn't exist
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin")
            self.stdout.write(
                self.style.SUCCESS('Created admin user with password "admin"')
            )
