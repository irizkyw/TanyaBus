import os
import re
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import googlemaps
from http import HTTPStatus
import dashscope
import time
app = Flask(__name__)

# Load environment variables
load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

# Set the base HTTP API URL
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
apikeyALI = os.getenv("ALIBABA_API_KEY")

def initialize_model():
    return {
        "model_name": "qwen-max",  # Specify the model you want to use
        "generation_config": {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        },
        "system_instruction": (
            "Anda adalah panduan transportasi berbasis AI yang terintegrasi dengan peta Google Maps. "
            "Anda dapat memberikan estimasi waktu perjalanan, kondisi real-time kendaraan umum, "
            "informasi kepadatan lalu lintas, serta menjadi pemandu wisata virtual multibahasa. "
            "Jangan Menggunakan Kendaraan Pribadi atau Transportasi Online" 
            "Pastikan menggunakan transportasi umum atau berjalan kaki. "
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
    }

def call_alibaba_model(prompt):
    try:
        model = initialize_model()
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        responses = dashscope.Generation.call(
            model["model_name"],
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True,
            api_key=apikeyALI
        )
        
        response_text = ""
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                response_text += response.output.choices[0]['message']['content']
            else:
                print(f'Request failed: {response.status_code} - {response.message}')
        return response_text
    except Exception as e:
        print(f'An error occurred: {e}')
        return ''

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
                    "Vehicle_No": vehicle.get("vehicle_no"),
                    "Vehicle_Code": vehicle.get("vehicle_code"),
                    "GPS_Latitude": vehicle.get("gps_position", {}).get("lat"),
                    "GPS_Longitude": vehicle.get("gps_position", {}).get("lng"),
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
        return None, None

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

def generate_map_url_route(start_location, end_location, api_key):
    return f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={start_location}&destination={end_location}&mode=transit"

def generate_map_url(location, api_key):
    return f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={location}"

def get_lat_lng(location):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': location,
        'key': os.getenv("GOOGLE_MAPS_API_KEY")
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        result = response.json()

        if result['status'] == 'OK':
            location = result['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            print(f"Error from Google Maps API: {result['status']}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def extract_location(prompt):
    response = call_alibaba_model(
        f"Temukan semua konteks tempat dari kalimat berikut dan format dalam list Python yang dipisahkan oleh koma. "
        f"Hindari nama negara atau nama daerah, fokus ke nama tempat saja. Misalnya: tempat = ['Telkom University', 'Alun-Alun Bandung']. "
        f"Kalimat: '{prompt}'"
    )

    pattern = r"\['(.*?)'\]"
    places = re.findall(pattern, response)
    return [place.strip() for place in places[0].split("', '")] if places else []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('prompt')
    if not user_input:
        return jsonify({"error": "No message provided."}), 400

    # Construct the prompt for Alibaba AI
    places = extract_location(user_input)
    time.sleep(2)
    
    
    vehicles_data = fetch_vehicle_data()  # Replace with actual vehicle data
    # nearest_vehicle = "Nearest vehicle info here"  # Replace with actual nearest vehicle info

    print(f"Extracted places: {places}")
    response_text = (
        f"Data Kendaraan Umum Real Time:\n{vehicles_data}\n\n"
        #f"Kondisi Sekitar kita: {get_traffic_condition(api_key, latitude, longitude, latitude + 0.0001, longitude + 0.0001)}\n\n"
        #f"Kendaraan Terdekat:\n{nearest_vehicle}\n\n"
        f"Prompt: {user_input}"
    )

    try:
        # Generate response from Alibaba AI model
        response = call_alibaba_model(response_text)
        
        if response is None:
            return jsonify({"error": "Failed to get response from AI model."}), 500
        
        response_data = {"message": response}
        print(response_data)

        # Determine map URL based on the number of places
        if len(places) == 2:
            start_location = places[0] + " Bandung"
            end_location = places[1] + " Bandung"
            response_data["x"] = {
                "lat": get_lat_lng(start_location)[0],
                "lng": get_lat_lng(start_location)[1]
            }
            response_data["y"] = {
                "lat": get_lat_lng(end_location)[0],
                "lng": get_lat_lng(end_location)[1]
            }
            response_data["show_map"] = True
        elif len(places) == 1:
            place = places[0] + " Bandung"
            response_data['x'] = {
                "lat": get_lat_lng(place)[0],
                "lng": get_lat_lng(place)[1]
            }
            response_data["show_map"] = True
        else:
            response_data['show_map'] = False

        response_data["message"] = re.sub(r'\*\*.*?\*\*', '', response)
        print(jsonify(response_data))
        return jsonify(response_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/init-message', methods=['GET'])
def init_message():
    try:
        response = "Selamat datang! 👋 Saya adalah panduan transportasi dan wisata Anda di Jawa Barat. 😊 Apakah Anda ingin mengetahui estimasi waktu perjalanan, kondisi kendaraan umum, atau informasi tentang tempat wisata di sekitar Anda? Saya siap membantu! 🌍🚌"
        return jsonify({"message": response})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
