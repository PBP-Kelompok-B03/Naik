from django.test import TestCase
from .models import User, Auction, Bid

class AuctionModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', role='seller')
        self.auction = Auction.objects.create(
            title='Test Auction',
            description='This is a test auction.',
            starting_price=100.00,
            current_bid=100.00,
            increment=10.00,
            duration=60,
            status='active',
            seller=self.user
        )

    def test_auction_creation(self):
        self.assertEqual(self.auction.title, 'Test Auction')
        self.assertEqual(self.auction.starting_price, 100.00)
        self.assertEqual(self.auction.status, 'active')

    def test_bid_creation(self):
        bid = Bid.objects.create(auction=self.auction, user=self.user, bid_amount=110.00)
        self.assertEqual(bid.bid_amount, 110.00)
        self.assertEqual(bid.auction, self.auction)

    def test_auction_status_update(self):
        self.auction.current_bid = 110.00
        self.auction.save()
        self.assertEqual(self.auction.current_bid, 110.00)

    def test_bid_increment(self):
        bid = Bid.objects.create(auction=self.auction, user=self.user, bid_amount=110.00)
        self.auction.current_bid = bid.bid_amount
        self.auction.save()
        self.assertGreater(self.auction.current_bid, self.auction.starting_price)