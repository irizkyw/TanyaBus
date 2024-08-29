from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("prompt")

    if user_input.lower() == "hallo bot":
        bot_response = {
            "message": "Hello!",
            "show_map": False
        }
    elif "map" in user_input.lower():
        bot_response = {
            "message": "Here is the map:",
            "show_map": True
        }
    else:
        bot_response = {
            "message": "I'm sorry, I don't understand that.",
            "show_map": False
        }

    return jsonify(bot_response)

if __name__ == '__main__':
    app.run(debug=True)
