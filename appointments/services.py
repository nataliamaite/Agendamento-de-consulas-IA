from datetime import datetime, time

from .holiday_service import get_holiday
from .models import Appointment


WORKING_HOURS = [
    time(hour=hour)
    for hour in range(8, 18)
]


def is_weekend(date):
    return date.weekday() >= 5


def get_available_slots(date):
    if is_weekend(date):
        return []

    if get_holiday(date):
        return []

    occupied_times = set(
        Appointment.objects.filter(date=date)
        .values_list("time", flat=True)
    )

    available_slots = [
        slot
        for slot in WORKING_HOURS
        if slot not in occupied_times
    ]

    return available_slots