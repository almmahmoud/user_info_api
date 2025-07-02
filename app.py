from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# إعداد البروكسي
url_pr = "customer-madmod_5b9rp-cc-it:psYWQ_rkEn5LwNb@pr.oxylabs.io:7777"
url_proxy = f'socks5://{url_pr}'
proxy_data = {
    'http': url_proxy,
    'https': url_proxy,
}

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

        url = "https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm-pkce/protocol/openid-connect/userinfo"

        response = requests.get(url, headers=headers, proxies=proxy_data)
        
        if response.status_code != 200:
            return jsonify({"error": f"Failed to get user info: {response.status_code}", "details": response.text}), response.status_code

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

# تشغيل السيرفر على 0.0.0.0 والبورت الجاي من البيئة (مناسب لـ Render)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
