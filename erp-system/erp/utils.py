def log_activity(request, category, action, description, url='', related_id=None):
    from .models import ActivityLog
    user = request.user if request.user.is_authenticated else None
    ActivityLog.objects.create(
        user=user,
        category=category,
        action=action,
        description=description,
        url=url,
        related_id=related_id,
    )


def current_month_bounds():
    """(first_day, last_day) of the current calendar month, as ISO date strings."""
    import calendar
    from datetime import date
    today = date.today()
    first = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    last = today.replace(day=last_day)
    return first.isoformat(), last.isoformat()


def resolve_date_range(request, from_key='date_from', to_key='date_to'):
    """(date_from, date_to) strings for a list-page filter bar.

    Defaults to the current calendar month when the request has no date
    params at all (a fresh nav-link visit). Once the filter form has been
    submitted -- even with both fields left blank, e.g. an "All Time" link
    of `?date_from=&date_to=` -- whatever was submitted is respected as-is,
    so clearing the filter genuinely shows everything instead of silently
    re-applying the current-month default.
    """
    if from_key in request.GET or to_key in request.GET:
        return request.GET.get(from_key, '').strip(), request.GET.get(to_key, '').strip()
    return current_month_bounds()
