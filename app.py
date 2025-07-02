from flask import Flask, request, jsonify
import requests
app = Flask(__name__)

@app.route('/user_info', methods=['POST'])
def user_info():
    try:
        data = request.get_json()
        token = data.get("token")
        if not token:
            return jsonify({"error": "Token is required"}), 400

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        response = requests.get("https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm-pkce/protocol/openid-connect/userinfo", headers=headers)
        user = response.json()
        return jsonify({
            "email": user.get("email"),
            "family_name": user.get("family_name"),
            "given_name": user.get("given_name"),
            "phone_number": user.get("phone_number"),
            "dateOfBirth": user.get("dateOfBirth"),
            "passportNumber": user.get("passportNumber")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 👇 الجزء المهم
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
