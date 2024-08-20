let map;
let busMarkers = {};
let recommendationMarkers = [];
let recommendationPath;
let socket;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    zoom: 12,
    center: { lat: -6.9175, lng: 107.6191 }, // Centered around Bandung initially
  });

  const trafficLayer = new google.maps.TrafficLayer();
  trafficLayer.setMap(map);

  socket = io(); // Initialize socket.io connection

  socket.on("busLocations", (buses) => {
    // Update bus markers
    buses.forEach((bus) => {
      if (!busMarkers[bus.id]) {
        busMarkers[bus.id] = new google.maps.Marker({
          position: { lat: bus.lat, lng: bus.lng },
          map: map,
          title: `Bus ${bus.id}`,
          icon: bus.icon || {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: "#00FF00",
            fillOpacity: 1,
            strokeWeight: 2,
            strokeColor: "#00FF00",
          },
        });
      } else {
        busMarkers[bus.id].setPosition({ lat: bus.lat, lng: bus.lng });
      }
    });
  });

  socket.on("recommendations", (locations) => {
    // Remove existing recommendation markers and path
    recommendationMarkers.forEach((marker) => marker.setMap(null));
    if (recommendationPath) {
      recommendationPath.setMap(null);
    }
    recommendationMarkers = [];

    // Add new recommendation markers
    if (locations.length > 0) {
      locations.forEach((location) => {
        const marker = new google.maps.Marker({
          position: { lat: location.lat, lng: location.lng },
          map: map,
          icon: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png",
          title: "Recommended Location",
        });
        recommendationMarkers.push(marker);
      });

      // Draw path if there are more than one recommendation
      if (locations.length > 1) {
        const path = new google.maps.Polyline({
          path: locations.map(
            (loc) => new google.maps.LatLng(loc.lat, loc.lng),
          ),
          geodesic: true,
          strokeColor: "#FF0000",
          strokeOpacity: 1.0,
          strokeWeight: 2,
        });
        path.setMap(map);
        recommendationPath = path;
      }

      // Center map on the first recommendation location
      const firstLocation = locations[0];
      map.setCenter({ lat: firstLocation.lat, lng: firstLocation.lng });
    }
  });

  // Handle chat functionality
  const chatForm = document.querySelector("#input-container");
  const messageInput = document.querySelector("#message-input");
  const sendButton = document.querySelector("#send-button");
  const messagesDiv = document.querySelector("#messages");

  function sendMessage() {
    const message = messageInput.value;
    if (message.trim() !== "") {
      const messageElement = document.createElement("div");
      messageElement.className = "p-2 rounded-lg max-w-xs";
      messageElement.textContent = message;
      messageElement.classList.add(
        "bg-blue-500",
        "text-white",
        "self-end",
        "text-right",
      );
      messagesDiv.appendChild(messageElement);
      messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to latest message

      socket.emit("chatMessage", message);
      messageInput.value = "";
    }
  }

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });

  sendButton.addEventListener("click", () => {
    sendMessage();
  });

  socket.on("botMessage", (message) => {
    const messageElement = document.createElement("div");
    messageElement.className = "p-2 rounded-lg max-w-xs";
    messageElement.textContent = `${message}`;
    messageElement.classList.add(
      "bg-gray-200",
      "text-black",
      "self-start",
      "text-left",
    );
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to latest message
  });

  socket.on("busLocationRequested", (data) => {
    const busId = data.id;
    const bus = busMarkers[busId];
    if (bus) {
      map.setCenter(bus.getPosition());
      map.setZoom(15);
    }
  });
}
