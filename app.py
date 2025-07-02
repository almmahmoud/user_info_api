from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/get_user_info', methods=['POST'])
def get_user_info():
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"error": "Token is required"}), 400

        url = 'https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm-pkce/protocol/openid-connect/userinfo'
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": "Invalid token", "status_code": response.status_code}), response.status_code

        info = response.json()
        return jsonify({
            "email": info.get("email"),
            "family_name": info.get("family_name"),
            "given_name": info.get("given_name"),
            "phone_number": info.get("phone_number"),
            "dateOfBirth": info.get("dateOfBirth"),
            "passportNumber": info.get("passportNumber")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
