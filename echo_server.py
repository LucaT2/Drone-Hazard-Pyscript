from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/api/fod/detect', methods=['POST'])
def receive_detection():
    # Print the text data
    print(f"\n🔔 Received: {request.form.get('label')} ({request.form.get('confidence')})")
    print(f"📍 Coordinates: {request.form.get('coord_x')}, {request.form.get('coord_y')}")
    
    # Save the image so you can see it
    if 'image' in request.files:
        file = request.files['image']
        file.save(f"received_{request.form.get('label')}.jpg")
        print(f"📸 Image saved as: received_{request.form.get('label')}.jpg")
        
    return "OK", 200

if __name__ == '__main__':
    # Listen on all interfaces so the drone script can find it
    app.run(host='0.0.0.0', port=8080)