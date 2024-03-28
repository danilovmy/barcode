from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_barcode, name='generate_barcode'),
]
