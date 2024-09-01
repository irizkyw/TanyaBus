import streamlit as st
import dashscope
import os
import requests
import re
from gtts import gTTS
from dotenv import load_dotenv
import math
from http import HTTPStatus
import time

# Load environment variables
load_dotenv()

# Configure Dashscope
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
api_key = os.getenv("ALIBABA_API_KEY")  # Ensure this is set in your .env file
api_key_map = os.getenv("GOOGLE_MAPS_API_KEY")

# Initialize the GenerativeModel with custom system instruction
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

# Function to call Alibaba API
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
            api_key=api_key
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

# Initialize chat session
def start_chat():
    # Replace with your prompt
    initial_prompt = "Selamat datang! 👋 Saya adalah panduan transportasi dan wisata Anda di Jawa Barat. 😊 Apakah Anda ingin mengetahui estimasi waktu perjalanan, kondisi kendaraan umum, atau informasi tentang tempat wisata di sekitar Anda? Saya siap membantu! 🌍🚌"
    return [{"role": "model", "parts": [initial_prompt]}]

st.title("AIBUS 🚌")

def get_route(start_location, end_location, api_key_map):
    api_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start_location,
        "destination": end_location,
        "key": api_key_map,
    }
    response = requests.get(api_url, params=params)
    return response.json()

def extract_location(prompt):
    try:
        response_text = call_alibaba_model(
            f"Find all location contexts from the following sentence and format them into a Python list separated by commas. Avoid country names or region names, focus on place names only. Example: places = ['Telkom University', 'Alun-Alun Bandung']. Sentence: '{prompt}'"
        )
        # Pattern to extract the list of places
        pattern = r"\['(.*?)'\]"
        places = re.findall(pattern, response_text)
        places = [place.strip() for place in places[0].split("', '")] if places else []
        print(places)
        return places
    except Exception as e:
        print(f'An error occurred: {e}')
        return []

def get_random_duck_image():
    api_url = "https://random-d.uk/api/v2/random"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get("url")
    return None

# Display chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_map" not in st.session_state:
    st.session_state.show_map = False

if "duck_image_url" not in st.session_state:
    st.session_state.duck_image_url = None

if prompt := st.chat_input("Say something"):
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    
    

    # tts = gTTS(response_text)
    # tts.save('response.mp3')
    # st.audio('response.mp3')

    places = extract_location(prompt)
    time.sleep(2)

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

    vehicles_data = fetch_vehicle_data()

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

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = (math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    def find_nearest_vehicle(lat1, lon1, vehicles_data):
        nearest_vehicle = None
        min_distance = float('inf')
        for vehicle in vehicles_data:
            lat2 = vehicle.get("GPS_Latitude")
            lon2 = vehicle.get("GPS_Longitude")
            if lat2 is not None and lon2 is not None:
                distance = haversine(lat1, lon1, lat2, lon2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_vehicle = vehicle
        return nearest_vehicle

    # Example function to convert vehicle data to string
    def vehicles_data_to_string(vehicles_data):
        if not vehicles_data:
            return "No vehicle data available."
        vehicle_info_list = []
        for vehicle in vehicles_data:
            vehicle_info = (f"ID: {vehicle.get('ID', 'N/A')}, "
                            f"Nomor Kendaraan: {vehicle.get('Vehicle_No', 'N/A')}, "
                            f"Kode Kendaraan: {vehicle.get('Vehicle_Code', 'N/A')}, "
                            f"Latitude GPS: {vehicle.get('GPS_Latitude', 'N/A')}, "
                            f"Longitude GPS: {vehicle.get('GPS_Longitude', 'N/A')}")
            vehicle_info_list.append(vehicle_info)
        return "\n".join(vehicle_info_list)

    # Example function to convert nearest vehicle data to string
    def nearest_vehicle_to_string(nearest_vehicle):
        if not nearest_vehicle:
            return "No nearest vehicle data available."
        return (f"ID: {nearest_vehicle.get('ID', 'N/A')}, "
                f"Nomor Kendaraan: {nearest_vehicle.get('Vehicle_No', 'N/A')}, "
                f"Kode Kendaraan: {nearest_vehicle.get('Vehicle_Code', 'N/A')}, "
                f"Latitude GPS: {nearest_vehicle.get('GPS_Latitude', 'N/A')}, "
                f"Longitude GPS: {nearest_vehicle.get('GPS_Longitude', 'N/A')}")

    # Example data (replace with actual values)
    vehicles_data = fetch_vehicle_data()
    latitude, longitude = get_coordinates_from_location(api_key_map, places[0])
    nearest_vehicle = find_nearest_vehicle(latitude, longitude, vehicles_data)
    
    final_prompt = (
        #f"Data Kendaraan Umum Real Time:\n{vehicles_data_to_string(vehicles_data)}\n\n"
        f"Kondisi Sekitar kita: {get_traffic_condition(api_key, latitude, longitude, latitude + 0.0001, longitude + 0.0001)}\n\n"
        f"Kendaraan Terdekat:\n{nearest_vehicle_to_string(nearest_vehicle)}\n\n"
        f"Berdasarkan semua informasi diatas jawab pertanyaan berikut menggunakan transportasi umum: {prompt}"
    )
    response_text = call_alibaba_model(final_prompt)

    st.session_state.messages.append({"role": "model", "parts": [response_text]})
    if len(places) == 2:
        start_location = places[0]
        end_location = places[1]
        st.session_state.show_map = True
        st.session_state.duck_image_url = None
    elif len(places) == 1:
        st.session_state.show_map = False
        st.session_state.duck_image_url = get_random_duck_image()
    else:
        st.session_state.show_map = False
        st.error("Could not extract valid locations.")

for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message['parts'][0])
    else:
        st.chat_message("assistant", avatar="☕").write(message['parts'][0])

def generate_map_url_route(start_location, end_location, api_key):
    return f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={start_location}&destination={end_location}&mode=transit"

def generate_map_url(location, api_key):
    return f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={location}"

if st.session_state.show_map:
    map_url = generate_map_url_route(start_location, end_location, api_key_map)
    st.subheader("Rute Perjalanan di Google Maps")
    st.markdown(f'<iframe src="{map_url}" width="100%" height="500"></iframe>', unsafe_allow_html=True)

elif st.session_state.duck_image_url:
    map_url = generate_map_url(places[0], api_key)
    st.markdown(f'<iframe src="{map_url}" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)


# if nearest_vehicle:
#     st.subheader("Kendaraan Terdekat")
#     st.write(f"ID: {nearest_vehicle.get('ID')}")
#     st.write(f"Nomor Kendaraan: {nearest_vehicle.get('Vehicle_No')}")
#     st.write(f"Kode Kendaraan: {nearest_vehicle.get('Vehicle_Code')}")
#     st.write(f"Latitude GPS: {nearest_vehicle.get('GPS_Latitude')}")
#     st.write(f"Longitude GPS: {nearest_vehicle.get('GPS_Longitude')}")
