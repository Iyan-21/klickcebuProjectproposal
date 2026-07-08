from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from rentals.models import Equipment, Booking, Payment, Category

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


@login_required
def home(request):
    context = {
        'total_users': User.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'total_bookings': Booking.objects.count(),
        'total_categories': Category.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'is_admin': is_admin(request.user),
    }
    return render(request, 'dashboard/home.html', context)


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
