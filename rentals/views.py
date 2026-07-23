import json

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone

from .models import Category, Equipment, EquipmentImage, Booking, Payment, BookingStatusLog, PaymentStatusLog
from .forms import (
    CategoryForm, EquipmentForm, EquipmentImageForm,
    BookingForm, PaymentForm
)


def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


# ---------- CATEGORY ----------

@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'rentals/category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added.')
            return redirect('rentals:category_list')
    else:
        form = CategoryForm()
    return render(request, 'rentals/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('rentals:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'rentals/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('rentals:category_list')
    return render(request, 'rentals/confirm_delete.html', {'object': category, 'back_url': 'rentals:category_list'})


# ---------- EQUIPMENT ----------

def equipment_list(request):
    equipment = Equipment.objects.prefetch_related('images', 'categories').all()
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    if query:
        equipment = equipment.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        equipment = equipment.filter(categories__id=category_id)
    equipment = equipment.distinct()
    categories = Category.objects.all()

    quickview_data = {}
    for item in equipment:
        quickview_data[item.pk] = {
            'name': item.name,
            'rate': str(item.daily_rate),
            'description': item.description or '',
            'condition': item.get_condition_display(),
            'category': item.categories.first().name if item.categories.first() else '',
            'available': item.is_available,
            'image': item.primary_image.image.url if item.primary_image else '',
            'detail_url': reverse('rentals:equipment_detail', args=[item.pk]),
            'book_url': f"{reverse('rentals:booking_create')}?equipment={item.pk}",
        }

    return render(request, 'rentals/equipment_list.html', {
        'equipment_list': equipment,
        'categories': categories,
        'selected_category': category_id,
        'query': query or '',
        'quickview_data': quickview_data,
    })


def equipment_detail(request, pk):
    item = get_object_or_404(Equipment.objects.prefetch_related('images', 'categories'), pk=pk)
    context = {'item': item}
    if is_admin(request.user):
        context['booking_history'] = item.bookings.select_related('customer').order_by('-created_at')[:20]
    return render(request, 'rentals/equipment_detail.html', context)


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def equipment_create(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save()
            for f in request.FILES.getlist('images'):
                EquipmentImage.objects.create(equipment=equipment, image=f)
            # make the first uploaded image primary if none flagged
            if not equipment.images.filter(is_primary=True).exists():
                first_img = equipment.images.first()
                if first_img:
                    first_img.is_primary = True
                    first_img.save()
            messages.success(request, 'Equipment added.')
            return redirect('rentals:equipment_detail', pk=equipment.pk)
    else:
        form = EquipmentForm()
    return render(request, 'rentals/equipment_form.html', {'form': form, 'title': 'Add Equipment'})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def equipment_update(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            for f in request.FILES.getlist('images'):
                EquipmentImage.objects.create(equipment=equipment, image=f)
            messages.success(request, 'Equipment updated.')
            return redirect('rentals:equipment_detail', pk=equipment.pk)
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'rentals/equipment_form.html',
                  {'form': form, 'title': 'Edit Equipment', 'equipment': equipment})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def equipment_delete(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, 'Equipment deleted.')
        return redirect('rentals:equipment_list')
    return render(request, 'rentals/confirm_delete.html', {'object': equipment, 'back_url': 'rentals:equipment_list'})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def equipment_image_set_primary(request, pk, image_id):
    image = get_object_or_404(EquipmentImage, pk=image_id, equipment_id=pk)
    image.is_primary = True
    image.save()
    messages.success(request, 'Primary image updated.')
    return redirect('rentals:equipment_detail', pk=pk)


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def equipment_image_delete(request, pk, image_id):
    image = get_object_or_404(EquipmentImage, pk=image_id, equipment_id=pk)
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image removed.')
    return redirect('rentals:equipment_detail', pk=pk)


# ---------- BOOKING ----------

def maybe_auto_confirm_booking(payment, changed_by):
    """If a payment is marked as Paid, automatically advance its booking one
    step forward (Pending -> Confirmed) and log it as a system-triggered change.
    Guarded by booking.status == 'pending', so this only fires once — later
    saves where the payment stays Paid won't re-trigger it."""
    booking = payment.booking
    if payment.payment_status == 'paid' and booking.status == 'pending':
        old_status = booking.status
        booking.status = 'confirmed'
        booking.save(update_fields=['status'])
        BookingStatusLog.objects.create(
            booking=booking,
            old_status=old_status,
            new_status='confirmed',
            note='Automatically confirmed after the payment was marked as Paid.',
            is_automatic=True,
            changed_by=changed_by,
        )


def maybe_auto_record_payment(booking, changed_by):
    """Mirror of maybe_auto_confirm_booking, in the other direction: if a
    booking is marked Confirmed, automatically record its payment as Paid
    (creating the payment record on the spot if one doesn't exist yet) with
    today's date, and log it as a system-triggered change.

    Guarded by payment.payment_status != 'paid', so this only fires once —
    later saves where the booking stays Confirmed won't re-trigger it. This
    calls Payment.save() directly rather than going through the payment_*
    views, so it can't loop back into maybe_auto_confirm_booking above."""
    if booking.status != 'confirmed':
        return
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'amount': booking.down_payment_amount,
            'payment_method': booking.payment_method,
            'payment_status': 'pending',
        }
    )
    if payment.payment_status != 'paid':
        old_status = payment.payment_status
        payment.payment_status = 'paid'
        payment.payment_date = timezone.localdate()
        payment.save(update_fields=['payment_status', 'payment_date'])
        PaymentStatusLog.objects.create(
            payment=payment,
            old_status=old_status,
            new_status='paid',
            note='Automatically marked Paid after the booking was confirmed.',
            is_automatic=True,
            changed_by=changed_by,
        )


@login_required
def booking_list(request):
    if is_admin(request.user):
        bookings = Booking.objects.select_related('customer', 'equipment').prefetch_related('status_logs__changed_by').all()
    else:
        bookings = Booking.objects.select_related('equipment').prefetch_related('status_logs__changed_by').filter(customer=request.user)

    # Get filter from query parameter
    status_filter = request.GET.get('status', '')
    if status_filter in ['pending', 'confirmed', 'ongoing', 'completed', 'cancelled']:
        bookings = bookings.filter(status=status_filter)

    status_counts = {
        'total': Booking.objects.all().count() if is_admin(request.user) else Booking.objects.filter(
            customer=request.user).count(),
        'pending': Booking.objects.filter(status='pending').count() if is_admin(
            request.user) else Booking.objects.filter(customer=request.user, status='pending').count(),
        'confirmed': Booking.objects.filter(status='confirmed').count() if is_admin(
            request.user) else Booking.objects.filter(customer=request.user, status='confirmed').count(),
        'ongoing': Booking.objects.filter(status='ongoing').count() if is_admin(
            request.user) else Booking.objects.filter(customer=request.user, status='ongoing').count(),
        'completed': Booking.objects.filter(status='completed').count() if is_admin(
            request.user) else Booking.objects.filter(customer=request.user, status='completed').count(),
        'cancelled': Booking.objects.filter(status='cancelled').count() if is_admin(
            request.user) else Booking.objects.filter(customer=request.user, status='cancelled').count(),
    }

    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    paginator = Paginator(bookings, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Preload each visible booking's status history for the "History" modal —
    # same instant-open-no-reload pattern as the availability calendar.
    logs_by_booking = {}
    for b in page_obj.object_list:
        logs_by_booking[b.pk] = [
            {
                'old_status': log.get_old_status_display() or '—',
                'new_status': log.get_new_status_display(),
                'note': log.note,
                'is_automatic': log.is_automatic,
                'changed_by': ((log.changed_by.get_full_name() or log.changed_by.email) if log.changed_by else 'System'),
                'created_at': log.created_at.strftime('%b %d, %Y %I:%M %p'),
            }
            for log in b.status_logs.all()
        ]

    return render(request, 'rentals/booking_list.html', {
        'bookings': page_obj,
        'page_obj': page_obj,
        'base_query': base_query,
        'status_counts': status_counts,
        'current_filter': status_filter,
        'logs_by_booking_json': logs_by_booking,
    })


@login_required
def booking_create(request):
    admin = is_admin(request.user)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if not admin:
            form.fields.pop('status')
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            if not admin:
                booking.status = 'pending'
            booking.save()
            form.save_m2m()
            if admin:
                maybe_auto_record_payment(booking, request.user)
            messages.success(request, 'Booking created.')
            return redirect('rentals:booking_list')
    else:
        initial = {}
        preselect_id = request.GET.get('equipment')
        if preselect_id and preselect_id.isdigit():
            initial['equipment'] = preselect_id
        form = BookingForm(initial=initial)
        if not admin:
            form.fields.pop('status')

    if admin:
        return render(request, 'rentals/booking_form.html', {'form': form, 'title': 'New Booking'})

    equipment_rates = {str(e.pk): str(e.daily_rate) for e in form.fields['equipment'].queryset}
    addon_rates = {str(e.pk): str(e.daily_rate) for e in form.fields['addons'].queryset}
    context = {
        'form': form,
        'title': 'Book a Camera',
        'equipment_rates_json': json.dumps(equipment_rates),
        'addon_rates_json': json.dumps(addon_rates),
        'security_deposit_default': Booking._meta.get_field('security_deposit').default,
    }
    return render(request, 'rentals/book_now.html', context)


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def booking_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    old_status = booking.status
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            saved = form.save()
            if saved.status != old_status:
                BookingStatusLog.objects.create(
                    booking=saved,
                    old_status=old_status,
                    new_status=saved.status,
                    note=form.cleaned_data.get('reason', '').strip(),
                    is_automatic=False,
                    changed_by=request.user,
                )
            maybe_auto_record_payment(saved, request.user)
            messages.success(request, 'Booking updated.')
            return redirect('rentals:booking_list')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'rentals/booking_form.html', {
        'form': form,
        'title': 'Edit Booking',
        'status_logs': booking.status_logs.select_related('changed_by').all(),
    })


@login_required
def booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not is_admin(request.user) and booking.customer_id != request.user.id:
        messages.error(request, "You can't cancel this booking.")
        return redirect('rentals:booking_list')
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Booking removed.')
        return redirect('rentals:booking_list')
    return render(request, 'rentals/confirm_delete.html', {'object': booking, 'back_url': 'rentals:booking_list'})


# ---------- PAYMENT ----------

@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def payment_list(request):
    all_payments = Payment.objects.select_related('booking', 'booking__customer', 'booking__equipment').all()
    today = timezone.localdate()
    totals = {
        'collected': all_payments.filter(payment_status='paid').aggregate(s=Sum('amount'))['s'] or 0,
        'pending': all_payments.filter(payment_status='pending').aggregate(s=Sum('amount'))['s'] or 0,
        'this_month': all_payments.filter(
            payment_status='paid', payment_date__year=today.year, payment_date__month=today.month
        ).aggregate(s=Sum('amount'))['s'] or 0,
        'count': all_payments.count(),
    }
    status_counts = {
        'total': all_payments.count(),
        'pending': all_payments.filter(payment_status='pending').count(),
        'paid': all_payments.filter(payment_status='paid').count(),
        'refunded': all_payments.filter(payment_status='refunded').count(),
        'failed': all_payments.filter(payment_status='failed').count(),
    }

    payments = all_payments
    status_filter = request.GET.get('status', '')
    if status_filter in ['pending', 'paid', 'refunded', 'failed']:
        payments = payments.filter(payment_status=status_filter)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        payments = payments.filter(
            Q(booking__customer__first_name__icontains=search_query) |
            Q(booking__customer__last_name__icontains=search_query) |
            Q(booking__customer__email__icontains=search_query) |
            Q(reference_no__icontains=search_query) |
            Q(booking__equipment__name__icontains=search_query)
        )

    # Sorting: ?sort=amount|date|customer|method&dir=asc|desc (defaults to newest first)
    sort_fields = {
        'amount': 'amount',
        'date': 'payment_date',
        'customer': 'booking__customer__first_name',
        'method': 'payment_method',
    }
    sort_key = request.GET.get('sort', '')
    sort_dir = request.GET.get('dir', 'desc')
    if sort_key in sort_fields:
        field = sort_fields[sort_key]
        payments = payments.order_by(field if sort_dir == 'asc' else f'-{field}')
    else:
        sort_key, sort_dir = 'date', 'desc'
        payments = payments.order_by('-created_at')

    # Pagination — preserve status/search/sort in a reusable querystring for page links.
    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    paginator = Paginator(payments, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    logs_by_payment = {}
    for p in page_obj.object_list:
        logs_by_payment[p.pk] = [
            {
                'old_status': log.get_old_status_display() or '—',
                'new_status': log.get_new_status_display(),
                'note': log.note,
                'is_automatic': log.is_automatic,
                'changed_by': ((log.changed_by.get_full_name() or log.changed_by.email) if log.changed_by else 'System'),
                'created_at': log.created_at.strftime('%b %d, %Y %I:%M %p'),
            }
            for log in p.status_logs.select_related('changed_by').all()
        ]

    return render(request, 'rentals/payment_list.html', {
        'payments': page_obj,
        'page_obj': page_obj,
        'base_query': base_query,
        'totals': totals,
        'status_counts': status_counts,
        'current_filter': status_filter,
        'search_query': search_query,
        'sort_key': sort_key,
        'sort_dir': sort_dir,
        'logs_by_payment_json': logs_by_payment,
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            saved = form.save()
            maybe_auto_confirm_booking(saved, request.user)
            messages.success(request, 'Payment recorded.')
            return redirect('rentals:payment_list')
    else:
        form = PaymentForm()
    return render(request, 'rentals/payment_form.html', {'form': form, 'title': 'Record Payment'})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    old_status = payment.payment_status
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            saved = form.save()
            if saved.payment_status != old_status:
                PaymentStatusLog.objects.create(
                    payment=saved,
                    old_status=old_status,
                    new_status=saved.payment_status,
                    note=form.cleaned_data.get('reason', '').strip(),
                    is_automatic=False,
                    changed_by=request.user,
                )
            maybe_auto_confirm_booking(saved, request.user)
            messages.success(request, 'Payment updated.')
            return redirect('rentals:payment_list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'rentals/payment_form.html', {
        'form': form,
        'title': 'Edit Payment',
        'status_logs': payment.status_logs.select_related('changed_by').all(),
    })


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()