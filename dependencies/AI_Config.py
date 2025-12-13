import torch
from ultralytics import YOLO

def load_yolo_model(model_path="object_detection_lib/yolo11n.pt"):
    try:
        print("CUDA available:", torch.cuda.is_available())
    except Exception as e:
        print(f"Error checking CUDA availability: {e}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    try:
        model = YOLO(model_path).to(device)
        return model, device
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        return None, device
