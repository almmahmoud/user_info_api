import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ User Info API is running!"

@app.route('/get_user_info', methods=['POST'])
def get_user_info():
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token is required"}), 400

    return jsonify(user_info(token))

def user_info(token):
    url = 'https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm-pkce/protocol/openid-connect/userinfo'
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": "Failed to fetch user info", "status_code": response.status_code}

    data = response.json()
    return {
        "email": data.get("email"),
        "family_name": data.get("family_name"),
        "given_name": data.get("given_name"),
        "phone_number": data.get("phone_number"),
        "dateOfBirth": data.get("dateOfBirth"),
        "passportNumber": data.get("passportNumber")
    }

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # For Render deployment
    app.run(debug=False, host='0.0.0.0', port=port)
