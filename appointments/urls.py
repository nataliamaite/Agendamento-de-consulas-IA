from django.urls import path

from .views import (
    AvailableSlotsView,
    AppointmentsView,
    AssistantView,
)


urlpatterns = [
    path("available", AvailableSlotsView.as_view()),
    path("appointments", AppointmentsView.as_view()),
    path("assistant", AssistantView.as_view()),
]