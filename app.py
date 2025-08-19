from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Flask crawl API is running!"})

@app.route("/crawl", methods=["GET"])
def crawl():
    url = "https://thptnguyenhuuhuan.hcm.edu.vn/tin-tuc-su-kien/c/14105"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)

    return jsonify({
        "status": resp.status_code,
        "html": resp.text[:2000]  # cắt 2000 ký tự đầu để tránh quá tải
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
