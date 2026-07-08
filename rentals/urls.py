from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    # Category
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Equipment
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/add/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.equipment_update, name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),
    path('equipment/<int:pk>/images/<int:image_id>/primary/', views.equipment_image_set_primary, name='equipment_image_set_primary'),
    path('equipment/<int:pk>/images/<int:image_id>/delete/', views.equipment_image_delete, name='equipment_image_delete'),

    # Booking
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/add/', views.booking_create, name='booking_create'),
    path('bookings/<int:pk>/edit/', views.booking_update, name='booking_update'),
    path('bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),

    # Payment
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/edit/', views.payment_update, name='payment_update'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
]
