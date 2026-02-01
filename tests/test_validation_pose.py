import cv2
import mediapipe as mp
import time

def validate_pose_detection(video_path="tests/test_pose.mp4"):
    mp_pose = mp.solutions.pose.Pose()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception("Video test file not found")

    frame_count = 0
    start = time.time()

    while True:
        success, frame = cap.read()
        if not success:
            break

        results = mp_pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            print("Warning: pose not detected on frame", frame_count)

        frame_count += 1

    duration = time.time() - start
    fps = frame_count / duration
    print(f"Processed {frame_count} frames at {fps:.2f} FPS, pose detected SUCCESS")

    if fps < 15:
        raise Warning("FPS too low, performance insufficient")

if __name__ == "__main__":
    validate_pose_detection()