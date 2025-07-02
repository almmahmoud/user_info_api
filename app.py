from flask import Flask, request, jsonify
import requests
import os
import mimetypes

app = Flask(__name__)

# إعداد البروكسي
url_pr = "customer-madmod_5b9rp-cc-it:psYWQ_rkEn5LwNb@pr.oxylabs.io:7777"
url_proxy = f'socks5://{url_pr}'
proxy_data = {
    'http': url_proxy,
    'https': url_proxy,
}

# مسارات الملفات حسب الكود
DOCUMENT_PATHS = {
    100: "static/passport.jpg",
    187: "static/nulla_osta.jpg",
    188: "static/phone.jpg"
}

# استعلام بيانات المستخدم
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

        url = "https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm/protocol/openid-connect/userinfo"
        response = requests.get(url, headers=headers, proxies=proxy_data)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch user info", "details": response.text}), response.status_code

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


# رفع الملفات تلقائيًا عند الطلب
@app.route('/upload_document', methods=['POST'])
def upload_document():
    try:
        data = request.get_json()
        token = data.get("token")
        code = int(data.get("code"))

        if not token or code not in DOCUMENT_PATHS:
            return jsonify({"error": "Missing token or invalid code"}), 400

        path = DOCUMENT_PATHS[code]
        if not os.path.exists(path):
            return jsonify({"error": "File not found on server"}), 404

        filename = os.path.basename(path)
        mime_type, _ = mimetypes.guess_type(path)
        file_size = os.path.getsize(path)

        # خطوة 1: الحصول على presigned URL
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        json_data = {
            "fileSize": file_size,
            "fileName": filename,
            "mimeType": mime_type
        }

        presign_response = requests.post(
            "https://egyapi.almaviva-visa.it/reservation-manager/api/documents/v1/upload-presigned-url",
            json=json_data, headers=headers, proxies=proxy_data
        )

        if presign_response.status_code != 200:
            return jsonify({"error": "Failed to get presigned URL", "details": presign_response.text}), 500

        presign_data = presign_response.json()
        presigned_url = presign_data['presignedUrl']
        temporary_key = presign_data['temporaryKey']

        # خطوة 2: رفع الملف
        with open(path, 'rb') as f:
            upload_headers = {"Content-Type": mime_type}
            upload_response = requests.put(presigned_url, headers=upload_headers, data=f, proxies=proxy_data)

        if upload_response.status_code != 200:
            return jsonify({"error": "Upload failed", "details": upload_response.text}), 500

        return jsonify({
            "documentTypeId": code,
            "temporaryKey": temporary_key,
            "fileName": filename,
            "fileSize": file_size,
            "mimeType": mime_type
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# تشغيل على Render (0.0.0.0 + PORT env)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
