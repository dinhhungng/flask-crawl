from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask server is running!"

@app.route('/api/tintuc', methods=['GET'])
def get_tintuc():
    data = {
        "html": "<h1>Tin tức sự kiện</h1><p>Đây là dữ liệu mẫu</p>"
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
