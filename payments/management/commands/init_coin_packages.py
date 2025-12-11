from django.core.management.base import BaseCommand
from payments.models import CoinPackage
from django.conf import settings

class Command(BaseCommand):
    help = 'Initialize coin packages'
    
    def handle(self, *args, **options):
        packages = [
            (100, 100, "Perfect for trying out basic features"),
            (250, 250, "Good for casual chatting"), 
            (500, 700, "Most popular - 40% bonus coins"),
            (1000, 1500, "Great value - 50% more coins"),
            (5000, 8000, "Premium package - 60% bonus"),
            (10000, 25000, "Best value - 150% bonus coins"),
        ]
        
        created_count = 0
        for amount, coins, description in packages:
            obj, created = CoinPackage.objects.get_or_create(
                amount=amount,
                defaults={
                    'coins': coins,
                    'description': description
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created package: {amount} KES = {coins} coins')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} coin packages')
        )