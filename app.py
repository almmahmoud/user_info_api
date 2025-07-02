from flask import Flask, request, jsonify
import requests
import os
import mimetypes

app = Flask(__name__)

url_pr = "customer-madmod_5b9rp-cc-it:psYWQ_rkEn5LwNb@pr.oxylabs.io:7777"
url_proxy = f'socks5://{url_pr}'
proxy_data = {
    'http': url_proxy,
    'https': url_proxy,
}

# Local file paths mapped by document type code
DOCUMENT_PATHS = {
    100: "static/passport.jpg",
    187: "static/nulla_osta.jpg",
    188: "static/phone.jpg"
}

@app.route('/user_info', methods=['POST'])
def get_user_info_and_upload(proxy=proxy_data):
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"error": "Token is required"}), 400

        # Get user info
        headers = {
            "Authorization": f"Bearer {token}"
        }
        user_info_response = requests.get(
            "https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm/protocol/openid-connect/userinfo",
            headers=headers,
            proxies=proxy
        )

        if user_info_response.status_code != 200:
            return jsonify({"error": "Failed to fetch user info", "details": user_info_response.text}), 500

        user_info = user_info_response.json()

        # Upload all documents
        uploaded_docs = []

        for code, path in DOCUMENT_PATHS.items():
            if not os.path.exists(path):
                uploaded_docs.append({"code": code, "error": f"{path} not found"})
                continue

            filename = os.path.basename(path)
            mime_type, _ = mimetypes.guess_type(path)
            file_size = os.path.getsize(path)

            # Step 1: Get presigned URL
            headers_presign = {
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
                json=json_data, headers=headers_presign, proxies=proxy
            )

            if presign_response.status_code != 200:
                uploaded_docs.append({"code": code, "error": "Presign failed", "details": presign_response.text})
                continue

            presign_data = presign_response.json()
            presigned_url = presign_data['presignedUrl']
            temporary_key = presign_data['temporaryKey']

            # Step 2: Upload to S3
            with open(path, 'rb') as f:
                upload_headers = {
                    "Content-Type": mime_type
                }
                upload_response = requests.put(presigned_url, headers=upload_headers, data=f, proxies=proxy)

            if upload_response.status_code != 200:
                uploaded_docs.append({"code": code, "error": "Upload failed", "details": upload_response.text})
                continue

            uploaded_docs.append({
                "documentTypeId": code,
                "temporaryKey": temporary_key,
                "fileName": filename,
                "fileSize": file_size,
                "mimeType": mime_type
            })

        return jsonify({
            "user_info": user_info,
            "uploaded_documents": uploaded_docs
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app on Render with dynamic port
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
