from django.urls import path
from .views import BarcodeGeneratorView

urlpatterns = [
    path('generate/', BarcodeGeneratorView.as_view(), name='generate_barcode'),
]
