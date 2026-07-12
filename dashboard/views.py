import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rentals.models import Equipment, Booking, Payment, Category

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


def _last_n_months(n):
    today = timezone.localdate()
    y, m = today.year, today.month
    months = []
    for _ in range(n):
        months.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return list(reversed(months))


@login_required
def home(request):
    if is_admin(request.user):
        return admin_home(request)
    return customer_home(request)


def admin_home(request):
    revenue = Payment.objects.filter(payment_status='paid').aggregate(total=Sum('amount'))['total'] or 0

    monthly_qs = (
        Payment.objects.filter(payment_status='paid', payment_date__isnull=False)
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(total=Sum('amount'))
    )
    monthly_map = {(r['month'].year, r['month'].month): float(r['total']) for r in monthly_qs}
    months = _last_n_months(6)
    revenue_chart = [
        {'label': calendar.month_abbr[m], 'value': monthly_map.get((y, m), 0)}
        for (y, m) in months
    ]
    max_val = max((d['value'] for d in revenue_chart), default=0) or 1
    for d in revenue_chart:
        d['pct'] = round((d['value'] / max_val) * 100) if max_val else 0

    context = {
        'total_users': User.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'total_bookings': Booking.objects.count(),
        'total_categories': Category.objects.count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'revenue': revenue,
        'revenue_chart': revenue_chart,
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_bookings': Booking.objects.select_related('customer', 'equipment').order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/admin_home.html', context)


def customer_home(request):
    bookings = Booking.objects.filter(customer=request.user).select_related('equipment')
    active_bookings = bookings.filter(status__in=['pending', 'confirmed', 'ongoing'])
    total_spent = Payment.objects.filter(
        booking__customer=request.user, payment_status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0
    context = {
        'active_count': active_bookings.count(),
        'total_bookings': bookings.count(),
        'total_spent': total_spent,
        'upcoming_bookings': active_bookings.order_by('start_date')[:5],
        'featured_equipment': Equipment.objects.filter(is_available=True)
            .prefetch_related('images', 'categories').order_by('-created_at')[:4],
        'today': timezone.localdate(),
    }
    return render(request, 'dashboard/customer_home.html', context)


# ---------- USER MANAGEMENT (entity: USER) ----------

@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def user_toggle_lock(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.is_locked = not user.is_locked
        if not user.is_locked:
            user.failed_attempts = 0
        user.save()
        messages.success(request, f"{user.email} is now {'locked' if user.is_locked else 'unlocked'}.")
    return redirect('dashboard:user_list')


@login_required
@user_passes_test(is_admin, login_url='dashboard:home')
def user_set_role(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in dict(User.ROLE_CHOICES):
            user.role = new_role
            user.save()
            messages.success(request, f"{user.email}'s role set to {new_role}.")
    return redirect('dashboard:user_list')
