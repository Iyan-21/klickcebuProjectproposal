import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from rentals.models import Equipment, Category, Booking


class LandingView(TemplateView):
    """Public marketing homepage. Signed-in users are bounced to their
    role-specific dashboard home instead of seeing the marketing page."""
    template_name = 'pages/landing.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_equipment'] = (
            Equipment.objects.filter(is_available=True)
            .prefetch_related('images', 'categories')
            .order_by('-created_at')[:6]
        )
        context['category_count'] = Category.objects.count()
        context['equipment_count'] = Equipment.objects.filter(is_available=True).count()
        return context


def availability_view(request):
    """Public calendar showing, for each day, whether equipment is fully
    available, partially booked, or fully booked — plus a per-date
    breakdown of exactly which items are free vs. taken."""
    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if not (1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        year, month = today.year, today.month

    first_of_month = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    month_start = first_of_month
    month_end = date(year, month, last_day_num)

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    equipment_qs = Equipment.objects.filter(is_available=True)
    total_equipment = equipment_qs.count()

    active_bookings = Booking.objects.filter(
        status__in=['pending', 'confirmed', 'ongoing'],
        start_date__lte=month_end,
        end_date__gte=month_start,
    ).select_related('equipment')

    booked_by_day = defaultdict(set)
    for b in active_bookings:
        cur = max(b.start_date, month_start)
        end = min(b.end_date, month_end)
        while cur <= end:
            booked_by_day[cur].add(b.equipment_id)
            cur += timedelta(days=1)

    # Build a lightweight {name, detail_url} list for every equipment item once,
    # then slice it per day using the equipment ids already grouped in booked_by_day.
    # This lets the calendar modal open instantly client-side instead of reloading
    # the page on every date click.
    equipment_lookup = {
        item.id: {'name': item.name, 'detail_url': reverse('rentals:equipment_detail', args=[item.pk])}
        for item in equipment_qs
    }
    all_equipment_ids = set(equipment_lookup.keys())

    cal = calendar.Calendar(firstweekday=6)  # Sunday-first, to match the calendar convention
    weeks, week = [], []
    day_details = {}
    for d in cal.itermonthdates(year, month):
        booked_ids = booked_by_day.get(d, set())
        if total_equipment == 0:
            status = 'none'
        else:
            booked_count = len(booked_ids)
            if booked_count == 0:
                status = 'available'
            elif booked_count >= total_equipment:
                status = 'full'
            else:
                status = 'partial'

        if d.month == month:
            available_ids = all_equipment_ids - booked_ids
            day_details[d.isoformat()] = {
                'label': d.strftime('%A, %B %-d, %Y'),
                'available': [equipment_lookup[i] for i in available_ids],
                'booked': [equipment_lookup[i] for i in booked_ids],
            }

        week.append({
            'date': d,
            'in_month': d.month == month,
            'status': status,
            'is_today': d == today,
        })
        if len(week) == 7:
            weeks.append(week)
            week = []

    # Supports deep links like ?date=2026-07-22 by telling the template which
    # date (if any) to auto-open the modal for on page load.
    selected_date = None
    sel = request.GET.get('date')
    if sel:
        try:
            candidate = date.fromisoformat(sel)
            if month_start <= candidate <= month_end:
                selected_date = candidate
        except ValueError:
            selected_date = None

    context = {
        'weeks': weeks,
        'month_label': first_of_month.strftime('%B %Y'),
        'prev_month': prev_month, 'prev_year': prev_year,
        'next_month': next_month, 'next_year': next_year,
        'current_month': month, 'current_year': year,
        'today': today,
        'selected_date': selected_date,
        'total_equipment': total_equipment,
        'weekday_labels': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'day_details_json': day_details,
    }
    return render(request, 'pages/availability.html', context)