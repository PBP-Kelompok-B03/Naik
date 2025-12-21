from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Product

class Command(BaseCommand):
    help = 'Update auction winners for ended auctions'

    def handle(self, *args, **options):
        # Find all auction products that have ended but don't have a winner set
        ended_auctions = Product.objects.filter(
            is_auction=True,
            auction_end_time__lte=timezone.now(),
            auction_winner__isnull=True
        )

        updated_count = 0
        for product in ended_auctions:
            winner = product.get_auction_winner()
            if winner:
                product.auction_winner = winner
                product.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Set winner for auction "{product.title}": {winner.username}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No bids found for auction "{product.title}"'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} auction winners'
            )
        )