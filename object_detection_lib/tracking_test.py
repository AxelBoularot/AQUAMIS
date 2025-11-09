import cv2
from ultralytics import YOLO
import torch
print("CUDA available:", torch.cuda.is_available())

#------------------------------------------------------------------------------- CODE MADE BY JACQUES DOVE NOËL -------------------------------------------------------------------------------------------

# Load the YOLO11 model
model = YOLO("yolo11n.pt").to("cuda")

# Open the video file
#D:/Videos/WIN_20241015_08_21_58_Pro.mp4

video_path = "http://10.46.67.60:8080/video"
cap = cv2.VideoCapture(0)
frame_count = 0

# Loop through the video frames
while cap.isOpened():
    # Read a frame from the video
    success, frame = cap.read()
    frame = cv2.resize(frame, (640, 360))
    frame_count += 1
    if frame_count % 2 != 0:  # Skip every other frame
        continue

    if success:
        # Run YOLO11 tracking on the frame, persisting tracks between frames
        results = model.track(frame, persist=True)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # Display the annotated frame
        cv2.imshow("YOLO11 Tracking", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()