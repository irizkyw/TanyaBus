//llms.js
const bot = window.botIcon;
const user = window.userIcon;

const form = document.querySelector("#chat-form");
const chatContainer = document.querySelector("#chat_container");

let loadInterval;

function loader(element) {
  element.textContent = "";

  loadInterval = setInterval(() => {
    element.textContent += ".";

    if (element.textContent === "....") {
      element.textContent = "";
    }
  }, 300);
}

function typeText(element, text) {
  let index = 0;

  let interval = setInterval(() => {
    if (index < text.length) {
      element.innerHTML += text.charAt(index);
      index++;
    } else {
      clearInterval(interval);
    }
  }, 20);
}

function generateUniqueId() {
  const timestamp = Date.now();
  const randomNumber = Math.random();
  const hexadecimalString = randomNumber.toString(16);

  return `id-${timestamp}-${hexadecimalString}`;
}

function chatStripe(isAi, value, uniqueId) {
  if (isAi) {
    return `
      <div class="wrapper ai">
          <div class="chat">
              <div class="profile">
                  <img src=${bot} alt="bot" />
              </div>
              <div class="message" id=${uniqueId}>${value}</div>
          </div>
      </div>
      `;
  } else {
    return `
      <div class="wrapper user">
          <div class="chat">
              <div class="message" id=${uniqueId}>${value}</div>
              <div class="profile">
                  <img src=${user} alt="user" />
              </div>
          </div>
      </div>
      `;
  }
}

const handleSubmit = async (e) => {
  e.preventDefault();

  const prompt = document.querySelector("#prompt-textarea").value.trim();
  if (prompt === "") {
    console.warn("Empty input, ignoring submission");
    return;
  }

  chatContainer.innerHTML += chatStripe(false, prompt);
  form.reset();

  const uniqueId = generateUniqueId();
  chatContainer.innerHTML += chatStripe(true, " ", uniqueId);

  chatContainer.scrollTop = chatContainer.scrollHeight;
  const messageDiv = document.getElementById(uniqueId);
  loader(messageDiv);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: prompt,
      }),
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const result = await response.json();

    clearInterval(loadInterval);
    messageDiv.innerHTML = "";

    typeText(messageDiv, result.message);

    if (result.show_map) {
      const mapContainerId = generateUniqueId();
      const mapContainer = `
        <div id="${mapContainerId}" class="map-container"></div>
      `;

      setTimeout(() => {
        messageDiv.innerHTML += mapContainer;
        createCustomMap(mapContainerId, -6.917464, 107.619123);
      }, 1000);
    }
  } catch (error) {
    console.error("Error:", error);
    clearInterval(loadInterval);
    messageDiv.innerHTML = "Error: " + error.message;
  }
};

form.addEventListener("submit", handleSubmit);
form.addEventListener("keyup", (e) => {
  if (e.keyCode === 13 && !e.shiftKey) {
    e.preventDefault();
    handleSubmit(e);
  }
});

form.addEventListener("submit", handleSubmit);
form.addEventListener("keyup", (e) => {
  if (e.keyCode === 13 && !e.shiftKey) {
    e.preventDefault(); // Prevent default behavior
    handleSubmit(e);
  }
});
