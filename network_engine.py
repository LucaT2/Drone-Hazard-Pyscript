import cv2
import requests
import threading

def send_to_java_async(frame, label, confidence, x, y, url):
    """Initializes a background thread to send data to the Spring server."""
    thread = threading.Thread(target=_send_request, args=(frame, label, confidence, x, y, url))
    thread.start()

def _send_request(frame, label, confidence, x:float, y:float, url):
    """The actual POST request logic."""
    _, img_encoded = cv2.imencode('.jpg', frame)
    files = {'image': ('detection.jpg', img_encoded.tobytes(), 'image/jpeg')}
    data = {
        'label': label,
        'confidence': f"{confidence:.2f}",
        'coord_x': x,
        'coord_y': y
    }
    try:
        # Timeout ensures the script doesn't hang if the Java server is down
        response = requests.post(url, files=files, data=data, timeout=1.0)
        if response.status_code == 200:
            print(f"✅ Transmitted: {label}")
    except Exception as e:
        print(f"⚠️ Network Error: {e}")