from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from rentals.models import Camera, Booking

User = get_user_model()


@login_required
def home(request):
    context = {
        'total_users': User.objects.count(),
        'total_cameras': Camera.objects.count(),
        'total_bookings': Booking.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'dashboard/home.html', context)