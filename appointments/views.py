from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_service import interpret_message
from .holiday_service import get_holiday
from .models import Appointment
from .serializers import AppointmentSerializer
from .services import get_available_slots


class AvailableSlotsView(APIView):

    def get(self, request):
        date_string = request.query_params.get("date")

        if not date_string:
            return Response(
                {"error": "The 'date' parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            date = datetime.strptime(date_string, "%Y-%m-%d").date()

        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        holiday = get_holiday(date)

        if date.weekday() >= 5:
            return Response(
                {
                    "date": date_string,
                    "available": False,
                    "reason": "Weekend",
                    "slots": [],
                }
            )

        if holiday:
            return Response(
                {
                    "date": date_string,
                    "available": False,
                    "reason": "Holiday",
                    "holiday": holiday["localName"],
                    "slots": [],
                }
            )

        slots = get_available_slots(date)

        return Response(
            {
                "date": date_string,
                "available": True,
                "holiday": None,
                "slots": [slot.strftime("%H:%M") for slot in slots],
            }
        )


class AppointmentsView(APIView):

    def get(self, request):
        appointments = Appointment.objects.all().order_by("date", "time")

        serializer = AppointmentSerializer(appointments, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        date = serializer.validated_data["date"]
        appointment_time = serializer.validated_data["time"]

        # Verificar final de semana
        if date.weekday() >= 5:
            return Response(
                {
                    "error": (
                        "Appointments cannot be scheduled on weekends."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar feriado
        holiday = get_holiday(date)

        if holiday:
            return Response(
                {
                    "error": ("Appointments cannot be scheduled on holidays."),
                    "holiday": holiday["localName"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar horário comercial
        if appointment_time.hour < 8 or appointment_time.hour >= 18:
            return Response(
                {
                    "error": (
                        "Appointments must be scheduled between 08:00 and 17:00."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar horário ocupado
        appointment_exists = Appointment.objects.filter(
            date=date, time=appointment_time
        ).exists()

        if appointment_exists:
            return Response(
                {"error": ("This time slot is already occupied.")},
                status=status.HTTP_409_CONFLICT,
            )

        # Salvar consulta
        appointment = serializer.save()

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )


class AssistantView(APIView):

    def post(self, request):
        message = request.data.get("message")

        if not message:
            return Response(
                {"error": "The 'message' field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Enviar mensagem para o Gemini
            result = interpret_message(message)

            # ==========================================
            # CONSULTAR DISPONIBILIDADE
            # ==========================================
            if result.intent == "check_availability":
                if not result.date:
                    return Response(
                        {
                            "intent": result.intent,
                            "message": ("Informe a data que deseja consultar."),
                        }
                    )

                date = datetime.strptime(result.date, "%Y-%m-%d").date()

                holiday = get_holiday(date)

                # Verificar final de semana
                if date.weekday() >= 5:
                    return Response(
                        {
                            "intent": result.intent,
                            "date": result.date,
                            "available": False,
                            "reason": "Weekend",
                            "slots": [],
                        }
                    )

                # Verificar feriado
                if holiday:
                    return Response(
                        {
                            "intent": result.intent,
                            "date": result.date,
                            "available": False,
                            "reason": "Holiday",
                            "holiday": holiday["localName"],
                            "slots": [],
                        }
                    )

                # Buscar horários disponíveis
                slots = get_available_slots(date)

                formatted_slots = [
                    slot.strftime("%H:%M") for slot in slots
                ]

                return Response(
                    {
                        "intent": result.intent,
                        "date": result.date,
                        "available": len(formatted_slots) > 0,
                        "requested_time": result.time,
                        "slots": formatted_slots,
                    }
                )

            # ==========================================
            # AGENDAR CONSULTA
            # ==========================================
            if result.intent == "book_appointment":
                if not result.date:
                    return Response(
                        {
                            "intent": result.intent,
                            "message": ("Informe a data da consulta."),
                        }
                    )

                if not result.time:
                    return Response(
                        {
                            "intent": result.intent,
                            "message": ("Informe o horário da consulta."),
                        }
                    )

                date = datetime.strptime(result.date, "%Y-%m-%d").date()

                appointment_time = datetime.strptime(
                    result.time, "%H:%M"
                ).time()

                # Verificar final de semana
                if date.weekday() >= 5:
                    return Response(
                        {
                            "intent": result.intent,
                            "date": result.date,
                            "time": result.time,
                            "message": (
                                "Não é possível agendar consultas aos finais"
                                " de semana."
                            ),
                        }
                    )

                # Verificar feriado
                holiday = get_holiday(date)

                if holiday:
                    return Response(
                        {
                            "intent": result.intent,
                            "date": result.date,
                            "time": result.time,
                            "message": (
                                "Não é possível agendar consultas em feriados."
                            ),
                            "holiday": holiday["localName"],
                        }
                    )

                # Verificar horário comercial
                if (
                    appointment_time.hour < 8
                    or appointment_time.hour >= 18
                ):
                    return Response(
                        {
                            "intent": result.intent,
                            "date": result.date,
                            "time": result.time,
                            "message": (
                                "O horário deve estar entre 08:00 e 17:00."
                            ),
                        }
                    )

                # Verificar horário ocupado
                appointment_exists = Appointment.objects.filter(
                    date=date, time=appointment_time
                ).exists()

                if appointment_exists:
                    return Response(
                        {
                            "intent": result.intent,
                            "date": result.date,
                            "time": result.time,
                            "available": False,
                            "message": ("Esse horário já está ocupado."),
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                # Dados do paciente
                patient_name = request.data.get("patient_name")
                patient_phone = request.data.get("patient_phone")

                if not patient_name or not patient_phone:
                    return Response(
                        {
                            "intent": result.intent,
                            "date": result.date,
                            "time": result.time,
                            "message": (
                                "Para realizar o agendamento, informe nome e"
                                " telefone."
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Criar consulta no banco
                appointment = Appointment.objects.create(
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    date=date,
                    time=appointment_time,
                )

                # Retornar confirmação
                return Response(
                    {
                        "intent": result.intent,
                        "message": ("Consulta agendada com sucesso!"),
                        "appointment": AppointmentSerializer(
                            appointment
                        ).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

            # ==========================================
            # LISTAR AGENDAMENTOS
            # ==========================================
            if result.intent == "list_appointments":
                appointments = Appointment.objects.all().order_by(
                    "date", "time"
                )

                serializer = AppointmentSerializer(appointments, many=True)

                return Response(
                    {
                        "intent": result.intent,
                        "message": "Agendamentos encontrados.",
                        "appointments": serializer.data,
                    }
                )

            # ==========================================
            # OUTRAS INTENÇÕES
            # ==========================================
            return Response(
                {
                    "intent": result.intent,
                    "date": result.date,
                    "time": result.time,
                }
            )

        except ValueError:
            return Response(
                {
                    "error": (
                        "The date returned by the assistant is invalid."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as error:
            return Response(
                {
                    "error": "Could not process the message.",
                    "details": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )