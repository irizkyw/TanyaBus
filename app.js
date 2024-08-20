require("dotenv").config();
const express = require("express");
const http = require("http");
const socketIo = require("socket.io");
const path = require("path");

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static("public"));

const busRoutes = {
  1: {
    route: "Route A",
    start: { lat: -6.9175, lng: 107.6191 },
    end: { lat: -6.93, lng: 107.63 },
  },
  2: {
    route: "Route B",
    start: { lat: -6.92, lng: 107.62 },
    end: { lat: -6.94, lng: 107.64 },
  },
};

app.get("/", (req, res) => {
  res.render("map", {
    googleMapsApiKey: process.env.GOOGLE_MAPS_API_KEY,
  });
});

io.on("connection", (socket) => {
  console.log("New client connected");

  setInterval(() => {
    const busLocations = [
      { id: 1, lat: -6.9175, lng: 107.6191 },
      { id: 2, lat: -6.92, lng: 107.62 },
    ];
    socket.emit("busLocations", busLocations);
  }, 5000);

  socket.on("chatMessage", (message) => {
    console.log("Received message:", message);

    let botResponse = "I didn't understand that.";
    const busId = extractBusIdFromMessage(message);

    if (message.toLowerCase().includes("hello")) {
      botResponse = "Hi there! How can I help you?";
    } else if (message.toLowerCase().includes("bye")) {
      botResponse = "Goodbye! Have a great day!";
    } else if (message.toLowerCase().includes("where is bus")) {
      if (busId && busRoutes[busId]) {
        const route = busRoutes[busId];
        botResponse = `Bus ${busId} is on ${route.route}. Starting from (${route.start.lat}, ${route.start.lng}) to (${route.end.lat}, ${route.end.lng}).`;
        socket.emit("busLocationRequested", { id: busId, route });
      } else {
        botResponse = "Bus ID not found.";
      }
    }

    socket.emit("botMessage", botResponse);
  });

  socket.on("disconnect", () => {
    console.log("Client disconnected");
  });
});

function extractBusIdFromMessage(message) {
  const match = message.match(/bus (\d+)/i);
  return match ? parseInt(match[1], 10) : null;
}

server.listen(3000, () => {
  console.log("Server is running on http://localhost:3000");
});
