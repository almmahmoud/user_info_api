from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Proxy configuration (تقدر تغيره حسب ما تحتاج)
url_pr = "customer-madmod_5b9rp-cc-it:psYWQ_rkEn5LwNb@pr.oxylabs.io:7777"
url_proxy = f'socks5://{url_pr}'
proxy_data = {
    'http': url_proxy,
    'https': url_proxy,
}

def fetch_user_info(token, proxy):
    url = 'https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm-pkce/protocol/openid-connect/userinfo'
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ar",
        "authorization": f"Bearer {token}",
        "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "referrer": "https://egy.almaviva-visa.it/",
        "referrerPolicy": "strict-origin-when-cross-origin",
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
    }

    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=15)
        response.raise_for_status()
        user_info = response.json()

        return {
            "email": user_info.get("email"),
            "family_name": user_info.get("family_name"),
            "given_name": user_info.get("given_name"),
            "phone_number": user_info.get("phone_number"),
            "date_of_birth": user_info.get("dateOfBirth"),
            "passport_number": user_info.get("passportNumber")
        }

    except requests.RequestException as e:
        return {"error": str(e)}
    except KeyError as e:
        return {"error": f"Missing key in response: {e}"}

@app.route("/user_info", methods=["POST"])
def get_user_info():
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token is required"}), 400

    result = fetch_user_info(token, proxy_data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
