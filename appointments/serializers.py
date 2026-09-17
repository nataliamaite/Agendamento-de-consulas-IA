from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient_name",
            "patient_phone",
            "date",
            "time",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]