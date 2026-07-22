from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('needs_repair', 'Needs Repair'),
    ]

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    specs = models.TextField(blank=True)
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    is_available = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, through='EquipmentCategory', related_name='equipment_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img or self.images.first()


class EquipmentCategory(models.Model):
    """Junction table: one equipment can belong to multiple categories (M:M)."""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='equipment_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_equipment')

    class Meta:
        verbose_name_plural = 'Equipment Categories'
        unique_together = ('equipment', 'category')

    def __str__(self):
        return f"{self.equipment.name} \u2192 {self.category.name}"


class EquipmentImage(models.Model):
    """Multiple photos per equipment item; one may be flagged primary/thumbnail."""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='equipment_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"Image for {self.equipment.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            EquipmentImage.objects.filter(equipment=self.equipment).exclude(pk=self.pk).update(is_primary=False)


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PICKUP_CHOICES = [
        ('pickup', 'Store Pickup'),
        ('delivery', 'Delivery'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        ('gotyme', 'GoTyme Bank'),
        ('maribank', 'Maribank'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='bookings')
    addons = models.ManyToManyField(
        Equipment, blank=True, related_name='addon_bookings',
        help_text="Optional add-on accessories included with this booking."
    )
    contact_facebook = models.CharField(
        max_length=255, blank=True,
        help_text="Facebook profile URL or name, used as a backup contact method."
    )
    start_date = models.DateField()
    end_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    pickup_method = models.CharField(max_length=20, choices=PICKUP_CHOICES, default='pickup')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(
        max_digits=10, decimal_places=2, default=1000,
        help_text="Refundable deposit collected at pickup, returned on safe return of the gear."
    )
    down_payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Amount required upfront to secure the booking (e.g. 50% of total cost)."
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.equipment.name} - {self.customer}"

    @property
    def balance_due(self):
        """Remaining amount owed after the down payment, excluding the refundable deposit."""
        return self.total_cost - self.down_payment_amount


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        ('gotyme', 'GoTyme Bank'),
        ('maribank', 'Maribank'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    reference_no = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment for Booking #{self.booking_id}"


class BookingStatusLog(models.Model):
    """Audit trail entry for a booking status change. `note` is required (enforced
    in the form) whenever the change skips a step, reverses, or moves to/from a
    side-branch status like Cancelled — see rentals/status_rules.py."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20, choices=Booking.STATUS_CHOICES, blank=True)
    new_status = models.CharField(max_length=20, choices=Booking.STATUS_CHOICES)
    note = models.TextField(blank=True)
    is_automatic = models.BooleanField(
        default=False,
        help_text="True when the system made this change on its own (e.g. auto-confirming a booking after payment was marked Paid)."
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='booking_status_changes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.booking_id}: {self.old_status} → {self.new_status}"


class PaymentStatusLog(models.Model):
    """Audit trail entry for a payment status change. Same note-required rule as
    BookingStatusLog, evaluated against PAYMENT_SEQUENCE."""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20, choices=Payment.STATUS_CHOICES, blank=True)
    new_status = models.CharField(max_length=20, choices=Payment.STATUS_CHOICES)
    note = models.TextField(blank=True)
    is_automatic = models.BooleanField(default=False)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payment_status_changes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment #{self.payment_id}: {self.old_status} → {self.new_status}"