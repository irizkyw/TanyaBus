document.addEventListener("DOMContentLoaded", function () {
  function autoResize(element) {
    element.style.height = "auto";
    element.style.height = element.scrollHeight + "px";
  }

  const speechButton = document.getElementById("speechButton");
  const languageSelect = document.getElementById("languageSelect");
  const promptTextarea = document.getElementById("prompt-textarea");

  const recognition = new (window.SpeechRecognition ||
    window.webkitSpeechRecognition ||
    window.mozSpeechRecognition ||
    window.msSpeechRecognition)();
  recognition.continuous = true; // Keep listening until manually stopped

  let isListening = false;

  function updateLanguage() {
    recognition.lang = languageSelect.value;
  }

  recognition.onstart = () => {
    isListening = true;
    speechButton.querySelector("img").src = window.microphoneOffIcon;
  };

  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    promptTextarea.value += transcript; // Append to the existing content
    autoResize(promptTextarea); // Auto resize the textarea as content is added
  };

  recognition.onend = () => {
    isListening = false;
    speechButton.querySelector("img").src = window.microphoneOnIcon;
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    isListening = false;
    speechButton.querySelector("img").src = window.microphoneOnIcon;
  };

  speechButton.addEventListener("click", () => {
    if (isListening) {
      recognition.stop();
    } else {
      updateLanguage(); // Set the selected language
      recognition.start();
    }
  });
});
