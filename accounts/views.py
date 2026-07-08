from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm

User = get_user_model()

MAX_FAILED_ATTEMPTS = 5

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        existing = User.objects.filter(email=email).first()
        if existing and existing.is_locked:
            messages.error(
                request,
                'This account has been locked due to too many failed login attempts. '
                'Please contact an administrator to unlock it.'
            )
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            user.failed_attempts = 0
            user.save(update_fields=['failed_attempts'])
            login(request, user)
            return redirect('dashboard:home')
        else:
            if existing:
                existing.failed_attempts += 1
                if existing.failed_attempts >= MAX_FAILED_ATTEMPTS:
                    existing.is_locked = True
                    messages.error(
                        request,
                        'Too many failed attempts. This account is now locked — '
                        'please contact an administrator.'
                    )
                else:
                    remaining = MAX_FAILED_ATTEMPTS - existing.failed_attempts
                    messages.error(
                        request,
                        f'Invalid email or password. {remaining} attempt(s) left before this account is locked.'
                    )
                existing.save(update_fields=['failed_attempts', 'is_locked'])
            else:
                messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')