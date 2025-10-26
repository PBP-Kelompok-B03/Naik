from django.test import TestCase, Client
from django.urls import reverse
from main.models import Product, User


class SearchAppTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create sample products
        self.product1 = Product.objects.create(
            title="Nike Air Zoom",
            price=1500000,
            category="Men's Shoes",
            stock=5
        )
        self.product2 = Product.objects.create(
            title="Nike Air Max",
            price=2000000,
            category="Women's Shoes",
            stock=3
        )
        self.product3 = Product.objects.create(
            title="Jordan Kids Classic",
            price=800000,
            category="Kids' Shoes",
            stock=2
        )

        self.url = reverse('search:search_products')

    # ---------------- BASIC TESTS ----------------

    def test_search_page_loads_successfully(self):
        """Ensure the search page loads with status 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/search_results.html')

    def test_search_query_returns_expected_results(self):
        """Search query should return matching products."""
        response = self.client.get(self.url, {'q': 'Nike Air'})
        self.assertContains(response, "Nike Air Zoom")
        self.assertContains(response, "Nike Air Max")
        self.assertNotContains(response, "Jordan Kids Classic")

    def test_filter_by_category(self):
        """Filter results by category."""
        response = self.client.get(self.url, {'category': "Women's Shoes"})
        self.assertContains(response, "Nike Air Max")
        self.assertNotContains(response, "Nike Air Zoom")
        self.assertNotContains(response, "Jordan Kids Classic")

    def test_filter_by_price_range(self):
        """Filter results by min and max price."""
        response = self.client.get(self.url, {'min_price': 1000000, 'max_price': 1800000})
        self.assertContains(response, "Nike Air Zoom")
        self.assertNotContains(response, "Nike Air Max")
        self.assertNotContains(response, "Jordan Kids Classic")

    def test_filter_by_multiple_conditions(self):
        """Filter by query and category together."""
        response = self.client.get(self.url, {'q': 'Nike', 'category': "Women's Shoes"})
        self.assertContains(response, "Nike Air Max")
        self.assertNotContains(response, "Nike Air Zoom")

    def test_empty_query_returns_all_products(self):
        """No query should return all products."""
        response = self.client.get(self.url)
        self.assertContains(response, "Nike Air Zoom")
        self.assertContains(response, "Nike Air Max")
        self.assertContains(response, "Jordan Kids Classic")

    def test_ajax_request_returns_partial_html(self):
        """AJAX requests should still render valid HTML."""
        response = self.client.get(
            self.url,
            {'q': 'Nike'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/search_results.html')

    def test_no_results_found(self):
        """Query with no matches should show empty list."""
        response = self.client.get(self.url, {'q': 'Adidas'})
        self.assertNotContains(response, "Nike")
        self.assertNotContains(response, "Jordan")
        self.assertEqual(response.status_code, 200)
