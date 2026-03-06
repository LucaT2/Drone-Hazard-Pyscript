from ultralytics import YOLO

# 1. Load your existing model
model = YOLO("./weights/best_combined_datasets.pt")

# 2. Export to TensorRT (.engine) format
# device=0 uses your GTX 1650
# half=True enables FP16 (Double the speed on your card)
# imgsz=640 should match your training/SAHI slice size
success = model.export(format="engine", device=0, half=True, imgsz=640)

if success:
    print("✅ Export successful! Use 'best.engine' in your main script.")