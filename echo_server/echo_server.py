from flask import Flask, request
import json

app = Flask(__name__)
id = 0
@app.route('/api/fod/detect', methods=['POST'])
def receive_detection():
    global id
    # Print the text data
    print(f"\n🔔 Received: {request.form.get('label')} ({request.form.get('confidence')})")
    print(f"📍 Coordinates: {request.form.get('coord_x')}, {request.form.get('coord_y')}")
    
    # Save the image so you can see it
    if 'image' in request.files:
        file = request.files['image']
        file.save(f"received_{id}.jpg")
        print(f"📸 Image saved as: received_{id}.jpg")
        id += 1

    return "OK", 200

if __name__ == '__main__':
    # Listen on all interfaces so the drone script can find it
    app.run(host='0.0.0.0', port=8080)