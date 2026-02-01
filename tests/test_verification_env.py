import cv2
import mediapipe as mp
import socket
import sys

def test_python_version():
    print("Python version:", sys.version)

def test_imports():
    print("OpenCV version:", cv2.__version__)
    print("MediaPipe version:", mp.__version__)

def test_camera_access():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Camera not accessible")
    print("Camera OK")
    cap.release()

def test_port_available(port=5670):
    s = socket.socket()
    try:
        s.bind(("0.0.0.0", port))
        print(f"Port {port} available")
    except OSError:
        raise Exception(f"Port {port} is already in use")
    finally:
        s.close()

if __name__ == "__main__":
    test_python_version()
    test_imports()
    test_camera_access()
    test_port_available()