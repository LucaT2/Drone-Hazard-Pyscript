import cv2
import queue
import threading
import os
import random
# --- APP SETTINGS ---
STREAM_URL = "rtmp://172.20.10.4/live/key" 
WEIGHTS_PATH = "weights/best.engine"
JAVA_SERVER_IP = "192.168.1.134" 
JAVA_SERVER_PORT = "8080"
SPRING_SERVER_URL = f"http://{JAVA_SERVER_IP }:{JAVA_SERVER_PORT }/api/hazards/detect"
ECHO_SERVER_URL = "http://localhost:8080/api/fod/detect"
## java url = f"http://{JAVA_SERVER_IP }:{JAVA_SERVER_PORT }/api/hazards/detect" 
##localhost = "http://localhost:8080/api/fod/detect"
# --- DETECTION SETTINGS ---
DETECTION_INTERVAL = 90 
DISTANCE_THRESHOLD = 50 
CONFIDENCE_THRESHOLD = 0.7

class LiveStreamCapture:

    def __init__(self, url):
        self.lat = random.uniform(-90.0, 90.0)
        self.lon = random.uniform(-180.0, 180.0)
        self.yaw = 0.0      # Facing North
        self.pitch = 90.0

        # Prefer UDP for lower latency over RTMP/RTSP
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        self.cap = cv2.VideoCapture(url)
        if not self.cap.isOpened():
            print(f"❌ ERROR: Could not open stream at {url}")
            print("Check: 1. Is MediaMTX running? 2. Is the IP correct?")
            exit(1)
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader, daemon=True)
        t.start()

    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            if not self.q.empty():
                try: self.q.get_nowait() 
                except queue.Empty: pass
            self.q.put(frame)

    def read(self):
        return self.q.get()