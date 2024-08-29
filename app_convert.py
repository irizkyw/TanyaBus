import os
import re
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import googlemaps
from gtts import gTTS
import google.generativeai as genai

app = Flask(__name__)

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

# Initialize the GenerativeModel with custom system instruction
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=(
        "Anda adalah panduan transportasi berbasis AI yang terintegrasi dengan peta Google Maps. "
        "Anda dapat memberikan estimasi waktu perjalanan, kondisi real-time kendaraan umum, "
        "informasi kepadatan lalu lintas, serta menjadi pemandu wisata virtual multibahasa."
    ),
)

# Initialize chat session
chat_session = model.start_chat(
    history=[
        {
            "role": "model",
            "parts": [
                "Selamat datang! 👋 Saya adalah panduan transportasi dan wisata Anda di Jawa Barat. 😊"
            ],
        }
    ]
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('prompt')
    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    chat_session.history.append({"role": "user", "parts": [user_input]})

    try:
        # Generate response from the AI model
        response = chat_session.send_message(user_input)
        chat_session.history.append({"role": "model", "parts": [response.text]})

        places = extract_location(user_input)
        response_data = {"message": response.text}

        if "lokasi saya" in user_input.lower():
            latitude, longitude = get_current_location()
            if latitude and longitude:
                response_data.update({
                    "latitude": latitude,
                    "longitude": longitude,
                    "show_map": True,
                })
        elif places:
            latitude, longitude = get_coordinates_from_location(places[0])
            if latitude and longitude:
                response_data.update({
                    "latitude": latitude,
                    "longitude": longitude,
                    "show_map": True,
                })

        return jsonify(response_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

def extract_location(prompt):
    response = model.generate_content(
        f"Temukan semua konteks tempat dari kalimat berikut dan format dalam list Python yang dipisahkan oleh koma. "
        f"Hindari nama negara atau nama daerah, fokus ke nama tempat saja. Misalnya: tempat = ['Telkom University', 'Alun-Alun Bandung']. "
        f"Kalimat: '{prompt}'"
    )

    pattern = r"\['(.*?)'\]"
    places = re.findall(pattern, response.text)
    return [place.strip() for place in places[0].split("', '")] if places else []

def get_coordinates_from_location(location_name):
    try:
        geocode_result = gmaps.geocode(location_name)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            print(f"Geocoding failed for location: {location_name}")
            return None, None
    except Exception as e:
        print(f"Error during geocoding: {e}")
        return None, None

def get_current_location():
    try:
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        return data['latitude'], data['longitude']
    except Exception as e:
        print(f"Error retrieving location: {e}")
        return None, None

@app.route('/init-message', methods=['GET'])
def init_message():
    try:
        response = chat_session.send_message("hi bot")
        chat_session.history.append({"role": "model", "parts": [response.text]})
        return jsonify({"message": response.text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
