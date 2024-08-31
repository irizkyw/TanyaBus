import { loader, typeText, generateUniqueId, chatStripe } from "./utilities.js";

const bot = window.botIcon;
const user = window.userIcon;

const form = document.querySelector("#chat-form");
const chatContainer = document.querySelector("#chat_container");

let loadInterval;
let activeIntervals = new Map();

async function fetchResponse(prompt) {
  const response = await fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    throw new Error("Network response was not ok");
  }

  return await response.json();
}

async function handleSubmit(e) {
  e.preventDefault();
  const prompt = document.querySelector("#prompt-textarea").value.trim();

  if (prompt === "") {
    console.warn("Empty input, ignoring submission");
    return;
  }

  await sendChat(prompt);
}

async function sendChat(prompt) {
  const uniqueId = generateUniqueId();

  chatContainer.innerHTML += chatStripe(
    false,
    prompt,
    generateUniqueId(),
    bot,
    user,
  );
  form.reset();

  chatContainer.innerHTML += chatStripe(true, " ", uniqueId, bot, user);
  chatContainer.scrollTop = chatContainer.scrollHeight;

  const messageDiv = document.getElementById(uniqueId);

  if (!messageDiv) {
    console.error("Message div not found after adding it to DOM:", uniqueId);
    return;
  }

  clearLoader(uniqueId);
  activeIntervals.set(uniqueId, loader(messageDiv));

  if (prompt.toLowerCase().includes("lokasi saya")) {
    handleLocationRequest(messageDiv, uniqueId);
    return;
  }

  await handleServerResponse(messageDiv, uniqueId, prompt);
}

function clearLoader(uniqueId) {
  if (activeIntervals.has(uniqueId)) {
    clearInterval(activeIntervals.get(uniqueId));
    activeIntervals.delete(uniqueId);
  }
}

async function handleLocationRequest(messageDiv, uniqueId) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        await fetchResponse(`lat:${latitude}, long:${longitude}`);
        await handleServerResponse(
          messageDiv,
          uniqueId,
          `lat:${latitude}, long:${longitude}`,
        );
      },
      (error) => {
        console.error("Error retrieving location:", error.message);
        messageDiv.innerHTML = "Error retrieving location: " + error.message;
        clearLoader(uniqueId);
      },
    );
  } else {
    console.error("Geolocation is not supported by this browser.");
    messageDiv.innerHTML = "Geolocation is not supported by this browser.";
    clearLoader(uniqueId);
  }
}

async function handleServerResponse(messageDiv, uniqueId, prompt) {
  try {
    const result = await fetchResponse(prompt);
    clearLoader(uniqueId);
    messageDiv.innerHTML = "";

    await typeText(messageDiv, result.message);

    if (result.show_map) {
      const mapContainerId = generateUniqueId();
      const mapContainer = `<div id="${mapContainerId}" class="map-container"></div>`;

      messageDiv.innerHTML += mapContainer;

      setTimeout(() => {
        createCustomMap(
          mapContainerId,
          result.x.lat,
          result.x.lng,
          result.y ? result.y.lat : null,
          result.y ? result.y.lng : null,
          null,
          10000,
          null,
          window.routeFiles,
        );
      }, 2000);
    }
  } catch (error) {
    console.error("Error:", error);
    clearLoader(uniqueId);
    messageDiv.innerHTML = "Error: " + error.message;
  }
}

async function initMessage() {
  const uniqueId = generateUniqueId();
  chatContainer.innerHTML += chatStripe(true, " ", uniqueId, bot, user);

  const messageDiv = document.getElementById(uniqueId);
  activeIntervals.set(uniqueId, loader(messageDiv));

  try {
    const result = await fetchResponse("hi bot");
    clearLoader(uniqueId);
    messageDiv.innerHTML = "";
    await typeText(messageDiv, result.message);
  } catch (error) {
    console.error("Error:", error);
    clearLoader(uniqueId);
    messageDiv.innerHTML = "Error: " + error.message;
  }
}

form.addEventListener("submit", handleSubmit);
form.addEventListener("keyup", (e) => {
  if (e.keyCode === 13 && !e.shiftKey) {
    e.preventDefault();
    handleSubmit(e);
  }
});

window.addEventListener("load", initMessage);
