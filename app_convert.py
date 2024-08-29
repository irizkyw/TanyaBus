import os
import re
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import googlemaps
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
        "informasi kepadatan lalu lintas, serta menjadi pemandu wisata virtual multibahasa. "
        "Jika ditanya tentang lokasi saat ini, sebutkan ITB Bandung. "
        "Berikut adalah informasi tentang berbagai rute transportasi yang dapat Anda berikan: "
        "K1 - TRANS METRO BANDUNG KORIDOR 1: Cibiru - Cibeureum; "
        "K2 - TRANS METRO BANDUNG KORIDOR 2: Cicaheum - Cibeureum; "
        "K3 - TRANS METRO BANDUNG KORIDOR 3: Cicaheum - Sarijadi; "
        "K4 - TRANS METRO BANDUNG KORIDOR 4: Antapani - Leuwipanjang; "
        "K5 - TRANS METRO BANDUNG KORIDOR 5: Antapani - Stasiun Hall; "
        "F1 - TRANS METRO BANDUNG FEEDER 1: Stasiun Hall - Gunung Batu; "
        "F2 - TRANS METRO BANDUNG FEEDER 2: Summarecon Mall - Cibeureum; "
        "BS1 - BUS SEKOLAH KORIDOR 1: Antapani - Ledeng; "
        "BS2 - BUS SEKOLAH KORIDOR 2: Leuwipanjang - Dago; "
        "BS3 - BUS SEKOLAH KORIDOR 3: Cibiru - Alun Alun; "
        "BS4 - BUS SEKOLAH KORIDOR 4: Cibiru - Cibeureum; "
        "BDROS - Bandung Tour On The Bus."
    ),
)

# Initialize chat session
chat_session = model.start_chat(
    history=[
        {
            "role": "model",
            "parts": [
                "Selamat datang! 👋 Saya adalah panduan transportasi dan wisata Anda di Jawa Barat. 😊"
                "Apakah Anda ingin mengetahui estimasi waktu perjalanan, kondisi kendaraan umum, "
                "atau informasi tentang tempat wisata di sekitar Anda? Saya siap membantu! 🌍🚌"
            ],
        }
    ]
)

def generate_map_url_route(start_location, end_location, api_key):
    return f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={start_location}&destination={end_location}&mode=transit"

def generate_map_url(location, api_key):
    return f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={location}"

def get_lat_lng(location):
    api_key = "AIzaSyCMStVxIAgJETgmkls2wGVe_VU-YCscJIU"
    
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': location,
        'key': api_key
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an error for bad HTTP status codes
        result = response.json()
        
        if result['status'] == 'OK':
            location = result['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            raise ValueError(f"Error from Google Maps API: {result['status']}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed: {e}")
    
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
        print(f"Extracted places: {places}")
        # Determine map URL and duck image URL based on the number of places
        if len(places) == 2:
            start_location = places[0]+" Bandung"
            end_location = places[1]+" Bandung"
            response_data["x"] = {
                "lat" : get_lat_lng(start_location)[0],
                "lng" : get_lat_lng(start_location)[1]
            }
            response_data["y"] = {
                "lat" : get_lat_lng(end_location)[0],
                "lng" : get_lat_lng(end_location)[1]
            }

        elif len(places) == 1:
            place = places[0]+" Bandung"
            response_data['DuckImage'] = get_random_duck_image()
            response_data['x'] = {
                "lat" : get_lat_lng(place)[0],
                "lng" : get_lat_lng(place)[1]
            }
        else:
            response_data['MapEmbed'] = None
            response_data['DuckImage'] = None

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

def get_random_duck_image():
    api_url = "https://random-d.uk/api/v2/random"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get("url")
    return None

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
