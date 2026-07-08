from django.contrib import admin
from .models import Category, Equipment, EquipmentCategory, EquipmentImage, Booking, Payment


class EquipmentImageInline(admin.TabularInline):
    model = EquipmentImage
    extra = 1


class EquipmentCategoryInline(admin.TabularInline):
    model = EquipmentCategory
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'daily_rate', 'condition', 'is_available', 'created_at')
    list_filter = ('condition', 'is_available')
    search_fields = ('name', 'description')
    inlines = [EquipmentImageInline, EquipmentCategoryInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'equipment', 'start_date', 'end_date', 'total_cost', 'status')
    list_filter = ('status', 'pickup_method', 'payment_method')
    search_fields = ('customer__email', 'equipment__name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'payment_method', 'payment_status', 'payment_date')
    list_filter = ('payment_method', 'payment_status')