import requests


HOLIDAYS_API_URL = "https://date.nager.at/api/v3/PublicHolidays/2026/BR"


def get_holidays():
    response = requests.get(HOLIDAYS_API_URL, timeout=10)

    response.raise_for_status()

    return response.json()


def get_holiday(date):
    holidays = get_holidays()

    for holiday in holidays:
        if holiday["date"] == date.isoformat():
            return holiday

    return None