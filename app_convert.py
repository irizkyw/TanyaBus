from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import requests
import re
from gtts import gTTS
import googlemaps
import math
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
api_key = "AIzaSyCMStVxIAgJETgmkls2wGVe_VU-YCscJIU"

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
                "Selamat datang! 👋 Saya adalah panduan transportasi dan wisata Anda di Jawa Barat. 😊\n"
                "Apakah Anda ingin mengetahui estimasi waktu perjalanan, kondisi kendaraan umum, "
                "atau informasi tentang tempat wisata di sekitar Anda? Saya siap membantu! 🌍🚌"
            ],
        }
    ]
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    chat_session.history.append({"role": "user", "parts": [user_input]})

    # Generate response from the AI model
    response = chat_session.send_message(user_input)
    chat_session.history.append({"role": "model", "parts": [response.text]})

    # Extract locations from the model's response
    places = extract_location(user_input)

    # Convert text-to-speech and save as an audio file
    tts = gTTS(response.text)
    tts.save('response.mp3')

    # Initialize Google Maps API for route and traffic data
    if len(places) > 0:
        location_name = places[0]
        latitude, longitude = get_coordinates_from_location(api_key, location_name)
        condition = get_traffic_condition(api_key, latitude, longitude, latitude+0.0001, longitude+0.0001)
        vehicles_data = fetch_vehicle_data()
        nearest_vehicle = find_nearest_vehicle(latitude, longitude, vehicles_data)
        route = None

        if len(places) == 2:
            start_location = places[0]
            end_location = places[1]
            route = get_route(start_location, end_location, api_key)
        
        response_data = {
            "response": response.text,
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "traffic_condition": condition,
            "nearest_vehicle": nearest_vehicle,
            "route": route,
        }
    else:
        response_data = {"response": response.text, "error": "Could not extract valid locations."}

    return jsonify(response_data)

# Utility functions
def extract_location(prompt):
    response = model.generate_content(
        "Temukan semua konteks tempat dari kalimat berikut dan format dalam list Python yang dipisahkan oleh koma. Hindari nama negara atau nama daerah, fokus ke nama tempat saja. Misalnya: tempat = ['Telkom University', 'Alun-Alun Bandung']. Kalimat: '" + prompt + "'"
    )

    pattern = r"\['(.*?)'\]"
    places = re.findall(pattern, response.text)
    places = [place.strip() for place in places[0].split("', '")] if places else []
    return places

def get_route(start_location, end_location, api_key):
    api_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start_location,
        "destination": end_location,
        "key": api_key
    }
    response = requests.get(api_url, params=params)
    return response.json()

def fetch_vehicle_data():
    url = "https://bemo.uptangkutan-bandung.id/map/live-maps"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            vehicles = data.get("data", {}).get("result", {}).get("data", [])
            vehicle_list = []
            for vehicle in vehicles:
                vehicle_info = {
                    "ID": vehicle.get("id"),
                    "Vehicle No": vehicle.get("vehicle_no"),
                    "Vehicle Code": vehicle.get("vehicle_code"),
                    "GPS Latitude": vehicle.get("gps_position", {}).get("lat"),
                    "GPS Longitude": vehicle.get("gps_position", {}).get("lng"),
                }
                vehicle_list.append(vehicle_info)
            return vehicle_list
        else:
            return {"error": "Failed to retrieve data: Success flag is False"}
    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}

def get_coordinates_from_location(api_key, location_name):
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?fields=geometry&input={location_name}&inputtype=textquery&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if data.get('status') == 'OK' and 'candidates' in data and len(data['candidates']) > 0:
        location = data['candidates'][0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']
        return lat, lng
    else:
        return None, None  # No coordinates found or an error occurred

def get_traffic_condition(api_key, start_lat, start_lng, end_lat, end_lng):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_lat},{start_lng}&destination={end_lat},{end_lng}&departure_time=now&traffic_model=best_guess&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if 'routes' in data and len(data['routes']) > 0:
        legs = data['routes'][0]['legs']
        if len(legs) > 0:
            duration_in_traffic = legs[0].get('duration_in_traffic', {})
            if 'text' in duration_in_traffic:
                normal_duration = legs[0]['duration']['text']
                traffic_duration = duration_in_traffic['text']
                if 'min' in normal_duration and 'min' in traffic_duration:
                    normal_duration_minutes = int(normal_duration.split()[0])
                    traffic_duration_minutes = int(traffic_duration.split()[0])
                    if traffic_duration_minutes > normal_duration_minutes + 5:
                        return "macet"
                    else:
                        return "lancar"
                return "lancar"
    return "Tidak ada data"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (math.sin(dlat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def find_nearest_vehicle(lat, lng, vehicles):
    nearest_vehicle = None
    min_distance = float('inf')
    for vehicle in vehicles:
        vehicle_lat = vehicle.get("GPS Latitude")
        vehicle_lng = vehicle.get("GPS Longitude")
        if vehicle_lat and vehicle_lng:
            distance = haversine(lat, lng, vehicle_lat, vehicle_lng)
            if distance < min_distance:
                min_distance = distance
                nearest_vehicle = vehicle
    return nearest_vehicle

if __name__ == '__main__':
    app.run(debug=True)

       
