from django.test import TestCase, Client
from django.urls import reverse


class BarcodeGeneratorTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('generate_barcode')

    def test_default_generate_ean8_barcode_from_code(self):
        response = self.client.get(self.url, {
            'code': '1234567',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_default_generate_barcode_from_invalid_code(self):
        response = self.client.get(self.url, {
            'code': '123456',
        })
        self.assertEqual(response.status_code, 500)
        self.assertIn("Error generating barcode", response.content.decode())

    def test_non_float_height(self):
        response = self.client.get(self.url, {
            'code': '1234567',
            'height': 'one'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Height and width must be valid numbers.", response.content.decode())

    def test_zero_width(self):
        response = self.client.get(self.url, {
            'code': '1234567',
            'width': '0'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Height and width must be numbers greater than zero", response.content.decode())

    def test_negative_height(self):
        response = self.client.get(self.url, {
            'code': '1234567',
            'height': '-1'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Height and width must be numbers greater than zero", response.content.decode())

    def test_non_hex_colour_entry(self):
        response = self.client.get(self.url, {
            'code': '1234567',
            'foreground': '004AAD7',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Foreground and background colors must be valid hex RRGGBB or CCMMYYKK values", response.content.decode())

    def test_all_parameters_defined(self):
        response = self.client.get(self.url, {
            'code': '1234567',
            'image_type': 'png',
            'height': '21.38',
            'width': '17.05',
            'foreground': '004AAD',
            'background': 'FF0000CC'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')