from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Company, ProductsInfo, User, LogProduct, ScanInfo

class ScanInfoViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="Toyota")
        self.product = ProductsInfo.objects.create(name="Bolt", company=self.company)
        self.user = User.objects.create_user(email="testuser@example.com", password="password123")
        self.log_product = LogProduct.objects.create(
            company_code=self.company.name,
            product_code=self.product.name,
            batch_code="b24",
            code_key="45679876",
            message="Product is valid",
        )

    def test_scan_info_view(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "qr_code": "Toyota/Bolt/b24/45679876",
            "email": "testuser@example.com",
            "location": "51.509865,-0.118092"  # Sample latitude and longitude
        }
        response = self.client.post(reverse('scan_info'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Product is valid")
        self.assertTrue(ScanInfo.objects.filter(code_key="45679876").exists())
