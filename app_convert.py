from flask import Flask, jsonify, request
import os
import requests
from dotenv import load_dotenv
import math

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Google API Key
API_KEY = os.getenv("GEMINI_API_KEY")

# Function to get route from Google Maps API
def get_route(start_location, end_location, api_key):
    api_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start_location,
        "destination": end_location,
        "key": api_key
    }
    response = requests.get(api_url, params=params)
    return response.json()

# Function to get coordinates from a location name
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

# Function to calculate the Haversine distance between two coordinates
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
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

# Function to fetch vehicle data
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

# Function to find the nearest vehicle to a given location
def find_nearest_vehicle(lat1, lon1, vehicles_data):
    nearest_vehicle = None
    min_distance = float('inf')
    
    for vehicle in vehicles_data:
        lat2 = vehicle.get("GPS Latitude")
        lon2 = vehicle.get("GPS Longitude")
        
        if lat2 is not None and lon2 is not None:
            distance = haversine(lat1, lon1, lat2, lon2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_vehicle = vehicle
    
    return nearest_vehicle

# Endpoint to get the route between two locations
@app.route('/api/route', methods=['POST'])
def route():
    data = request.json
    start_location = data.get('start_location')
    end_location = data.get('end_location')
    
    route_data = get_route(start_location, end_location, API_KEY)
    
    return jsonify(route_data)

# Endpoint to get traffic condition between two locations
@app.route('/api/traffic', methods=['POST'])
def traffic():
    data = request.json
    start_location = data.get('start_location')
    end_location = data.get('end_location')
    
    start_lat, start_lng = get_coordinates_from_location(API_KEY, start_location)
    end_lat, end_lng = get_coordinates_from_location(API_KEY, end_location)
    
    if start_lat and start_lng and end_lat and end_lng:
        traffic_data = get_traffic_condition(API_KEY, start_lat, start_lng, end_lat, end_lng)
        return jsonify({"condition": traffic_data})
    else:
        return jsonify({"error": "Failed to get coordinates"}), 400

# Endpoint to get nearest vehicle to a location
@app.route('/api/nearest_vehicle', methods=['POST'])
def nearest_vehicle():
    data = request.json
    location_name = data.get('location_name')
    
    latitude, longitude = get_coordinates_from_location(API_KEY, location_name)
    vehicles_data = fetch_vehicle_data()
    
    if vehicles_data and latitude is not None and longitude is not None:
        nearest_vehicle = find_nearest_vehicle(latitude, longitude, vehicles_data)
        return jsonify(nearest_vehicle)
    else:
        return jsonify({"error": "Failed to retrieve vehicle data or coordinates"}), 400

# Start Flask server
if __name__ == '__main__':
    app.run(debug=True)
