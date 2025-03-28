from django.core.management.base import BaseCommand
from api.models import Cocktail, MarketEvent
import random
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Simulates market movements for cocktail prices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Interval between price updates in seconds (default: 60)",
        )

        parser.add_argument(
            "--runtime",
            type=int,
            default=0,
            help="How long to run the simulation in minutes (0 for indefinitely)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        runtime = options["runtime"]
        end_time = time.time() + (runtime * 60) if runtime > 0 else None

        self.stdout.write(
            self.style.SUCCESS(f"Starting market simulation (interval: {interval}s)")
        )

        try:
            while True:
                if end_time and time.time() > end_time:
                    break

                # Get active market events
                active_events = MarketEvent.objects.filter(is_active=True)
                event_impact = 0

                for event in active_events:
                    if event.event_type == "BOOM":
                        event_impact = float(event.impact_factor)
                    elif event.event_type == "CRASH":
                        event_impact = -float(event.impact_factor)
                    elif event.event_type == "VOLATILITY":
                        # Will be handled separately for each cocktail
                        pass

                # Update all cocktail prices
                cocktails = Cocktail.objects.all()
                for cocktail in cocktails:
                    # Base random movement
                    volatility = float(cocktail.volatility)

                    # Increase volatility if there's a VOLATILITY event
                    if active_events.filter(event_type="VOLATILITY").exists():
                        volatility_event = active_events.filter(
                            event_type="VOLATILITY"
                        ).first()
                        volatility *= float(volatility_event.impact_factor)

                    # Random demand changes (-2 to +2)
                    random_demand = random.uniform(-2, 2)

                    # Add event impact to demand
                    total_demand = random_demand + event_impact

                    # Update price
                    new_price = cocktail.update_price(total_demand)
                    self.stdout.write(f"Updated {cocktail.name} price to ${new_price}")

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("Stopping market simulation"))
