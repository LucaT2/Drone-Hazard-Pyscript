import cv2
import numpy as np
import math
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
import time
import random
from ultralytics import YOLO
import config
from network_engine import send_to_java_async
from coordinates_calculator import calculate_coordinates

#def load_my_model(weights_path):
print("Initializing SAHI Model...")
yolo_model = YOLO(config.WEIGHTS_PATH, task="detect")
detection_model = AutoDetectionModel.from_pretrained(
    model_type='ultralytics',
    model = yolo_model,
    confidence_threshold=config.CONFIDENCE_THRESHOLD,
    device='cuda'
)

# --- Video Source Selection ---
# You can switch this to a local path like 'my_drone_video.mp4' 
# or keep it as config.STREAM_URL  # OR config.STREAM_URL

print(f"Initializing Source: {config.video_input}")

# Check if the input is a local file to handle FPS/metadata better
is_file = config.video_input.endswith(('.mp4', '.avi', '.mov', '.mkv'))

if is_file:
    # Use standard OpenCV for local files
    reader_cap = cv2.VideoCapture(config.video_input)
    # Define a helper class/wrapper if your code expects a .read() method 
    # similar to LiveStreamCapture
    class FileWrapper:
        def __init__(self, cap):
            self.cap = cap
            # Default values for file-based processing
            self.yaw = 0.0   
            self.pitch = -90.0 
        def read(self):
            ret, frame = self.cap.read()
            return frame if ret else None
    
    reader = FileWrapper(reader_cap)
else:
    # Use your existing live stream class
    reader = config.LiveStreamCapture(config.video_input)

# --- Metadata Setup ---
fps_claimed = reader.cap.get(cv2.CAP_PROP_FPS)
frame_width = int(reader.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(reader.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out_fps = fps_claimed if fps_claimed > 0 else 30.0 

print(f"📹 Stream Header FPS: {fps_claimed}")

# 2. Setup Tracking & Stream
lk_params = dict(winSize=(15, 15), maxLevel=4, 
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))


tracked_points = np.array([]) 
tracked_dimensions = [] 
tracked_classes = []
old_gray = None
frame_count = 0
prev_time = time.time()
fps_start_time = time.time()
received_frame_count = 0
print("📡 Processing Live Feed...")

frame_width = int(reader.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(reader.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# Use claimed FPS or default to 30 if metadata is missing
out_fps = fps_claimed if fps_claimed > 0 else 30.0 




try:
    while True:
        frame = reader.read()
        if frame is None: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # --- PHASE 1: SAHI KEYFRAME ---
        if frame_count % config.DETECTION_INTERVAL == 0:
            result = get_sliced_prediction(
                frame, detection_model,
                slice_height=640, slice_width=640,
                overlap_height_ratio=0.2, overlap_width_ratio=0.2, verbose=0
            )
            
            new_pts, new_dims, new_clss = [], [], []
            
            for obj in result.object_prediction_list:
                x, y = int(obj.bbox.minx), int(obj.bbox.miny)
                w, h = int(obj.bbox.maxx - x), int(obj.bbox.maxy - y)
                cx, cy = x + w/2.0, y + h/2.0
                
                is_new = True
                if len(tracked_points) > 0:
                    for pt in tracked_points:
                        if math.hypot(cx - pt[0][0], cy - pt[0][1]) < config.DISTANCE_THRESHOLD:
                            is_new = False
                            break
                
                if is_new:
                    server_frame = frame.copy()
                    
                    # Draw the bounding box and label on the copy
                    cv2.rectangle(server_frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    label_text = f"{obj.category.name} {obj.score.value:.2f}"
                    cv2.putText(server_frame, label_text, (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    generated_coordinate_lat = random.uniform(config.LAT_RANGE[0], config.LAT_RANGE[1])
                    generated_coordinate_lon = random.uniform(config.LON_RANGE[0], config.LON_RANGE[1])

                    coordonate_x, coordonate_y = calculate_coordinates(
                        cx, cy, generated_coordinate_lat, generated_coordinate_lon,
                          yaw_drone=reader.yaw, pitch_camera=reader.pitch)
                    
                    send_to_java_async(server_frame, obj.category.name, 
                                       obj.score.value, coordonate_x,
                                         coordonate_y, config.LOCAL_SPRING_SERVER_URL)

                new_pts.append([[cx, cy]])
                new_dims.append((w, h))
                new_clss.append(obj.category.name)

            tracked_points = np.array(new_pts, dtype=np.float32) if new_pts else np.array([])
            tracked_dimensions, tracked_classes = new_dims, new_clss
            old_gray = gray.copy()

        # --- PHASE 2: OPTICAL FLOW ---
        elif len(tracked_points) > 0 and old_gray is not None:
            new_points, status, _ = cv2.calcOpticalFlowPyrLK(old_gray, gray, tracked_points, None, **lk_params)
            
            good_new, new_dims, new_clss = [], [], []
            
            for i, (new_pt, stat) in enumerate(zip(new_points, status)):
                if stat[0] == 1:
                    good_new.append([[new_pt[0][0], new_pt[0][1]]])
                    new_dims.append(tracked_dimensions[i])
                    new_clss.append(tracked_classes[i])

            tracked_points = np.array(good_new, dtype=np.float32)
            tracked_dimensions, tracked_classes = new_dims, new_clss
            old_gray = gray.copy()


        frame_count += 1
        received_frame_count +=1
        elapsed = time.time() - fps_start_time
        if elapsed >= 5.0:  # Every 5 seconds
            current_received_fps = received_frame_count / elapsed
            print(f"📥 Incoming Stream Speed: {current_received_fps:.2f} FPS")
            
            # Reset for next check
            received_frame_count = 0
            fps_start_time = time.time()
        if (frame_count % 100 == 0):
            new_time = time.time()
            duration = new_time - prev_time
            fps = 100 / duration
            prev_time = new_time
            print(f"📊 Average FPS (last 100 frames): {fps:.2f}")
        #cv2.imshow("FOD Analysis Active", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

finally:
    cv2.destroyAllWindows()