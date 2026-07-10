from decimal import Decimal

from django import forms
from django.db.models import Q
from .models import Category, Equipment, EquipmentImage, Booking, Payment

# Booking statuses that actually block the equipment's calendar
ACTIVE_BOOKING_STATUSES = ['pending', 'confirmed', 'ongoing']

WIDGET_ATTRS = {'class': 'form-control-kc'}


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs=WIDGET_ATTRS),
            'description': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
        }


class EquipmentForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="An item can belong to more than one category."
    )

    class Meta:
        model = Equipment
        fields = ['name', 'description', 'specs', 'daily_rate', 'condition', 'is_available', 'categories']
        widgets = {
            'name': forms.TextInput(attrs=WIDGET_ATTRS),
            'description': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
            'specs': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
            'daily_rate': forms.NumberInput(attrs=WIDGET_ATTRS),
            'condition': forms.Select(attrs=WIDGET_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['categories'].initial = self.instance.categories.all()

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            instance.categories.set(self.cleaned_data['categories'])
        return instance


class EquipmentImageForm(forms.ModelForm):
    class Meta:
        model = EquipmentImage
        fields = ['image', 'is_primary']


class AddonModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class BookingForm(forms.ModelForm):
    addons = AddonModelMultipleChoiceField(
        queryset=Equipment.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Optional extras for this booking.",
    )

    class Meta:
        model = Booking
        # total_cost and down_payment_amount are intentionally excluded — both are
        # always derived from equipment/addon daily_rate x number of rental days.
        fields = ['equipment', 'start_date', 'end_date', 'addons', 'contact_facebook',
                   'pickup_method', 'payment_method', 'status']
        widgets = {
            'equipment': forms.Select(attrs=WIDGET_ATTRS),
            'start_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'contact_facebook': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'facebook.com/yourprofile'}),
            'pickup_method': forms.Select(attrs=WIDGET_ATTRS),
            'payment_method': forms.RadioSelect,
            'status': forms.Select(attrs=WIDGET_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        accessories = Equipment.objects.filter(categories__name__iexact='Accessories', is_available=True).distinct()
        self.fields['addons'].queryset = accessories
        if self.instance and self.instance.pk:
            self.fields['addons'].initial = self.instance.addons.all()
        # Equipment picked as the main item shouldn't also be pickable as its own add-on.
        self.fields['equipment'].queryset = Equipment.objects.filter(is_available=True)

    def clean(self):
        cleaned = super().clean()
        equipment = cleaned.get('equipment')
        start_date = cleaned.get('start_date')
        end_date = cleaned.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "End date can't be before the start date.")
            return cleaned

        if equipment and start_date and end_date:
            overlapping = Booking.objects.filter(
                equipment=equipment,
                status__in=ACTIVE_BOOKING_STATUSES,
                start_date__lte=end_date,
                end_date__gte=start_date,
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise forms.ValidationError(
                    f"{equipment.name} is already booked for part of that date range. "
                    "Please pick different dates or a different item."
                )

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        days = (instance.end_date - instance.start_date).days + 1
        days = max(days, 1)
        addons = self.cleaned_data.get('addons') or []
        addon_daily_total = sum((item.daily_rate for item in addons), Decimal('0'))
        instance.total_cost = (instance.equipment.daily_rate + addon_daily_total) * days
        instance.down_payment_amount = (instance.total_cost / 2).quantize(Decimal('0.01'))
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class BookingStatusForm(forms.ModelForm):
    """Lightweight form for updating just status / return_date (customer-facing flows)."""
    class Meta:
        model = Booking
        fields = ['status', 'return_date']
        widgets = {
            'status': forms.Select(attrs=WIDGET_ATTRS),
            'return_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
        }


class BookingSelectWidget(forms.Select):
    """Tags each <option> with the booking's total_cost so the template JS
    can auto-fill the amount field when a booking is picked."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # Django 5+/6 passes a ModelChoiceIteratorValue wrapper, not a raw pk
        raw_pk = getattr(value, 'value', value)
        if raw_pk:
            try:
                booking = Booking.objects.get(pk=raw_pk)
                option['attrs']['data-cost'] = str(booking.total_cost)
            except (Booking.DoesNotExist, ValueError, TypeError):
                pass
        return option


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['booking', 'amount', 'payment_method', 'payment_status', 'payment_date', 'reference_no']
        widgets = {
            'booking': BookingSelectWidget(attrs=WIDGET_ATTRS),
            'amount': forms.NumberInput(attrs=WIDGET_ATTRS),
            'payment_method': forms.Select(attrs=WIDGET_ATTRS),
            'payment_status': forms.Select(attrs=WIDGET_ATTRS),
            'payment_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'reference_no': forms.TextInput(attrs=WIDGET_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer bookings that don't already have a payment record,
        # but keep the current booking visible when editing an existing payment.
        qs = Booking.objects.filter(payment__isnull=True)
        if self.instance and self.instance.pk and self.instance.booking_id:
            qs = Booking.objects.filter(Q(payment__isnull=True) | Q(pk=self.instance.booking_id))
        self.fields['booking'].queryset = qs.select_related('equipment', 'customer').order_by('-created_at')
