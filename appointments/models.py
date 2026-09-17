from django.db import models


class Appointment(models.Model):
    patient_name = models.CharField(max_length=150)
    patient_phone = models.CharField(max_length=20)
    date = models.DateField()
    time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "time"],
                name="unique_appointment_datetime",
            )
        ]

    def __str__(self):
        return f"{self.patient_name} - {self.date} {self.time}"