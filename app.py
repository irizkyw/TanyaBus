from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    print("Raw request data:", request.data)

    user_input = request.json.get("prompt", "").strip()

    print("User input:", user_input)

    if not user_input:
        return jsonify({
            "message": "No input provided.",
            "show_map": False
        })

    lat, lng = None, None

    if user_input.lower() == "hi bot":
        bot_response = {
            "message": "Hi!, How can I help you?",
            "show_map": False
        }
    elif user_input.lower() == "hallo bot":
        bot_response = {
            "message": "Hello!",
            "show_map": False
        }
    elif "map" in user_input.lower():
        bot_response = {
            "message": "Here is the map:",
            "show_map": True,
            "latitude": -6.917464,
            "longitude": 107.619123
        }
    elif "lat:" in user_input and "long:" in user_input:
        try:
            lat = float(user_input.split("lat:")[1].split(",")[0].strip())
            lng = float(user_input.split("long:")[1].strip())
            bot_response = {
                "message": "Here is your current location:",
                "show_map": True,
                "latitude": lat,
                "longitude": lng
            }
        except (ValueError, IndexError):
            bot_response = {
                "message": "Sorry, I couldn't parse the location data.",
                "show_map": False
            }
    else:
        bot_response = {
            "message": "I'm sorry, I don't understand that.",
            "show_map": False
        }

    return jsonify(bot_response)


if __name__ == '__main__':
    app.run(debug=True)
