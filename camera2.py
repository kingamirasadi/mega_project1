import cv2
import time

class LiveCam:
    def __init__(self, url):
        print("Initializing CameraFeed...")
        # Initialize the camera
        self.camera = cv2.VideoCapture(url)
        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera.")
        print("Camera initialized successfully.")

    def LiveCamFeed(self, fps=30):
        frame_delay = 1 / fps
        try:
            while True:
                start_time = time.time()
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to capture frame.")
                    break

                try:
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                except Exception as e:
                    print(f"Error encoding frame: {e}")
                    break

                # Control frame rate
                elapsed_time = time.time() - start_time
                if elapsed_time < frame_delay:
                    time.sleep(frame_delay - elapsed_time)
        finally:
            self.release_camera()

    def release_camera(self):
        """Release the camera."""
        self.camera.release()
        print("Camera released.")