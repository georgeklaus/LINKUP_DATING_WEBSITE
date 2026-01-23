from django.core.management.base import BaseCommand
from payments.models import CoinPackage


class Command(BaseCommand):
    help = 'Seed coin packages into the database'

    def handle(self, *args, **options):
        packages = [
            {'amount': 50, 'coins': 50, 'description': 'Starter Pack - Try it out!'},
            {'amount': 100, 'coins': 110, 'description': 'Basic Pack - 10% bonus!'},
            {'amount': 200, 'coins': 230, 'description': 'Popular Pack - 15% bonus!'},
            {'amount': 500, 'coins': 600, 'description': 'Value Pack - 20% bonus!'},
            {'amount': 1000, 'coins': 1300, 'description': 'Premium Pack - 30% bonus!'},
            {'amount': 2000, 'coins': 2800, 'description': 'Ultimate Pack - 40% bonus!'},
        ]

        created_count = 0
        updated_count = 0

        for pkg_data in packages:
            package, created = CoinPackage.objects.update_or_create(
                amount=pkg_data['amount'],
                defaults={
                    'coins': pkg_data['coins'],
                    'description': pkg_data['description'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {package}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {package}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {created_count}, Updated {updated_count} packages.'
        ))
