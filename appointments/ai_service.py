import os
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()


class AssistantIntent(BaseModel):
    intent: str
    date: str | None = None
    time: str | None = None


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY não encontrada.")

client = genai.Client(api_key=api_key)


def interpret_message(message):
    today = date.today().isoformat()

    prompt = f"""
Você é um assistente de uma clínica de saúde.

A data atual é {today}.

Analise a mensagem do usuário e identifique a intenção.

As intenções possíveis são:

- check_availability: quando o usuário quer saber quais horários estão disponíveis.
- book_appointment: quando o usuário quer marcar uma consulta.
- list_appointments: quando o usuário quer consultar agendamentos.
- unknown: quando a mensagem não está relacionada a agendamento.

Extraia também:

- date no formato YYYY-MM-DD, quando houver uma data.
- time no formato HH:MM, quando houver um horário.

Entenda expressões como:

- hoje
- amanhã
- depois de amanhã
- segunda-feira
- terça-feira
- próxima terça
- às 14h
- às 14:30
- 10 da manhã

Não invente uma data ou horário que não esteja presente
ou que não possa ser determinado claramente.

Mensagem do usuário:

{message}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AssistantIntent,
        ),
    )

    return AssistantIntent.model_validate_json(response.text)