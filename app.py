from flask import Flask, request, jsonify
import requests
import os
import mimetypes

app = Flask(__name__)

proxy = {
    'http': 'socks5://customer-xxx@pr.oxylabs.io:7777',
    'https': 'socks5://customer-xxx@pr.oxylabs.io:7777',
}

DOCUMENT_PATHS = {
    100: "static/passport.jpg",
    187: "static/nulla_osta.jpg",
    188: "static/phone.jpg"
}

@app.route('/user_info', methods=['POST'])
def user_info():
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Missing token"}), 400

    # Step 1: Get user info
    headers = {"Authorization": f"Bearer {token}"}
    user_response = requests.get(
        "https://egyiam.almaviva-visa.it/realms/oauth2-visaSystem-realm/protocol/openid-connect/userinfo",
        headers=headers,
        proxies=proxy
    )

    if user_response.status_code != 200:
        return jsonify({"error": "Failed to get user info", "details": user_response.text}), 500

    user_info = user_response.json()

    # Step 2: Upload documents
    upload_results = []

    for code, path in DOCUMENT_PATHS.items():
        if not os.path.exists(path):
            upload_results.append({"code": code, "error": "File not found on server"})
            continue

        filename = os.path.basename(path)
        mime_type, _ = mimetypes.guess_type(path)
        file_size = os.path.getsize(path)

        # Get presigned URL
        presign_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        presign_data = {
            "fileSize": file_size,
            "fileName": filename,
            "mimeType": mime_type
        }
        presign_response = requests.post(
            "https://egyapi.almaviva-visa.it/reservation-manager/api/documents/v1/upload-presigned-url",
            json=presign_data, headers=presign_headers, proxies=proxy
        )

        if presign_response.status_code != 200:
            upload_results.append({
                "code": code,
                "error": "Failed to get presigned URL",
                "details": presign_response.text
            })
            continue

        presign_json = presign_response.json()
        presigned_url = presign_json["presignedUrl"]
        temporary_key = presign_json["temporaryKey"]

        # Upload file
        with open(path, 'rb') as f:
            upload_headers = {"Content-Type": mime_type}
            upload_response = requests.put(presigned_url, headers=upload_headers, data=f, proxies=proxy)

        if upload_response.status_code != 200:
            upload_results.append({
                "code": code,
                "error": "Upload failed",
                "details": upload_response.text
            })
            continue

        # Success
        upload_results.append({
            "documentTypeId": code,
            "temporaryKey": temporary_key,
            "fileName": filename,
            "fileSize": file_size,
            "mimeType": mime_type
        })

    return jsonify({
        "user_info": user_info,
        "uploaded_documents": upload_results
    })
