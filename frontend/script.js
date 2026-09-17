const API_URL = "http://127.0.0.1:8001/api";
const chat = document.getElementById("chat");
const form = document.getElementById("message-form");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");

// ==========================================
// ADICIONAR MENSAGEM AO CHAT
// ==========================================
function addMessage(text, sender) {
  const message = document.createElement("div");
  message.className = `message ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "user" ? "👤" : "🤖";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = text;

  message.appendChild(avatar);
  message.appendChild(bubble);
  chat.appendChild(message);

  chat.scrollTop = chat.scrollHeight;
}

// ==========================================
// MOSTRAR CARREGAMENTO
// ==========================================
function showTyping() {
  const message = document.createElement("div");
  message.className = "message assistant";
  message.id = "typing-message";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "🤖";

  const bubble = document.createElement("div");
  bubble.className = "bubble typing";
  bubble.textContent = "Digitando...";

  message.appendChild(avatar);
  message.appendChild(bubble);
  chat.appendChild(message);

  chat.scrollTop = chat.scrollHeight;
}

// ==========================================
// REMOVER CARREGAMENTO
// ==========================================
function removeTyping() {
  const typing = document.getElementById("typing-message");

  if (typing) {
    typing.remove();
  }
}

// ==========================================
// FORMATAR RESPOSTA
// ==========================================
function formatResponse(data) {
  if (data.message) {
    let response = data.message;

    // Se for disponibilidade
    if (data.intent === "check_availability" && data.slots) {
      if (data.slots.length === 0) {
        response += "<br><br>Não há horários disponíveis.";
      } else {
        response += "<br><br><strong>Horários disponíveis:</strong><br>";
        response += data.slots.map((slot) => `🕐 ${slot}`).join("<br>");
      }
    }

    // Se for listagem
    if (data.intent === "list_appointments" && data.appointments) {
      if (data.appointments.length === 0) {
        response += "<br><br>Nenhum agendamento encontrado.";
      } else {
        response += "<br><br>";

        data.appointments.forEach((appointment) => {
          response += `
            📅 ${appointment.date}
            <br>
            🕐 ${appointment.time}
            <br>
            👤 ${appointment.patient_name}
            <br><br>
          `;
        });
      }
    }

    // Se for agendamento
    if (data.intent === "book_appointment" && data.appointment) {
      const appointment = data.appointment;

      response += `
        <br><br>
        📅 <strong>Data:</strong> ${appointment.date}
        <br>
        🕐 <strong>Horário:</strong> ${appointment.time}
        <br>
        👤 <strong>Paciente:</strong> ${appointment.patient_name}
      `;
    }

    return response;
  }

  // Erro retornado pelo backend
  if (data.error) {
    return `❌ ${data.error}`;
  }

  return "Não consegui entender a resposta.";
}

// ==========================================
// ENVIAR MENSAGEM
// ==========================================
async function sendMessage(message) {
  if (!message.trim()) {
    return;
  }

  addMessage(message, "user");

  input.value = "";
  input.disabled = true;
  sendButton.disabled = true;

  showTyping();

  try {
    const response = await fetch(`${API_URL}/assistant`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
      }),
    });

    const data = await response.json();

    removeTyping();

    if (!response.ok) {
      addMessage(`❌ ${data.error || "Ocorreu um erro."}`, "assistant");
      return;
    }

    const formattedResponse = formatResponse(data);

    addMessage(formattedResponse, "assistant");
  } catch (error) {
    removeTyping();
    console.error(error);

    addMessage("❌ Não foi possível conectar ao servidor.", "assistant");
  } finally {
    input.disabled = false;
    sendButton.disabled = false;
    input.focus();
  }
}

// ==========================================
// FORMULÁRIO
// ==========================================
form.addEventListener("submit", function (event) {
  event.preventDefault();

  const message = input.value.trim();

  sendMessage(message);
});

// ==========================================
// BOTÕES DE SUGESTÃO
// ==========================================
document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", function () {
    const message = button.dataset.message;

    sendMessage(message);
  });
});

// ==========================================
// FOCO INICIAL
// ==========================================
input.focus();