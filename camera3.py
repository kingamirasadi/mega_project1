import cv2
from deepface import DeepFace
import numpy as np
import os
import tempfile
import threading
import queue
from face_database_handler import FaceDatabaseHandler  # Import the database handler


class CameraFeed3:
    def __init__(self, url, db_handler):
        print("Initializing CameraFeed...")
        # Initialize the camera
        self.camera = cv2.VideoCapture(url)
        if not self.camera.isOpened():
            raise RuntimeError(f"Could not open camera at URL: {url}")
        print("Camera initialized successfully.")

        # Path to the database of known faces
        self.db_path = '/home/amir-asadi/PycharmProjects/mega_project/known_image'
        if not os.path.exists(self.db_path):
            raise ValueError(f"Database path {self.db_path} does not exist.")

        # Database handler for storing recognized faces
        self.db_handler = db_handler

        # Queue for inter-thread communication
        self.frame_queue = queue.Queue(maxsize=10)
        self.stop_event = threading.Event()

        # Thread for frame capture
        self.capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        self.capture_thread.start()

        print("CameraFeed initialized successfully.")

    def preprocess_frame(self, frame):
        """
        Preprocess the frame to improve performance.
        - Resize the frame to a smaller resolution.
        - Convert to grayscale for faster processing (optional).
        """
        frame = cv2.resize(frame, (640, 480))  # Resize to 640x480 for faster processing
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Optional: Convert to grayscale
        return frame

    def capture_frames(self):
        """
        Capture frames from the camera and add them to the queue.
        """
        frame_counter = 0
        skip_frames = 2  # Process every 2nd frame

        while not self.stop_event.is_set():
            ret, frame = self.camera.read()
            if not ret:
                print("Failed to capture frame. Exiting capture thread.")
                break

            # Skip frames to reduce processing load
            if frame_counter % skip_frames == 0:
                # Preprocess the frame
                frame = self.preprocess_frame(frame)
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
                else:
                    print("Frame queue is full. Dropping frame.")

            frame_counter += 1

    def process_frames(self):
        """
        Process frames from the queue for face detection and recognition.
        """
        while not self.stop_event.is_set():
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()

                try:
                    # Use DeepFace to extract faces from the frame
                    extracted_faces = DeepFace.extract_faces(frame, detector_backend="opencv", enforce_detection=False)

                    # Iterate over detected faces
                    for face in extracted_faces:
                        # Get the face region and confidence
                        facial_area = face["facial_area"]
                        x, y, w, h = facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]

                        # Draw a rectangle around the face
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                        # Crop the face from the frame
                        cropped_face = frame[y:y + h, x:x + w]

                        if cropped_face.size > 0:
                            # Save the cropped face as a temporary image file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                                tmp_file_path = tmp_file.name
                                cv2.imwrite(tmp_file_path, cropped_face)

                            # Perform face recognition using DeepFace
                            try:
                                results = DeepFace.find(img_path=tmp_file_path, db_path=self.db_path,
                                                        enforce_detection=False)

                                if isinstance(results, list) and len(results) > 0:
                                    # Assuming results is a list of DataFrames, take the first DataFrame
                                    df = results[0]
                                    if not df.empty:
                                        # Get the first row's 'identity' column value
                                        identity_path = df.iloc[0]['identity']
                                        name = os.path.basename(identity_path)

                                        # Store the recognized face in MongoDB
                                        self.db_handler.insert_face(name, tmp_file_path)

                                    else:
                                        name = "Unknown"
                                else:
                                    name = "Unknown"  # Label as unknown if no match is found

                            except Exception as e:
                                name = "Error"  # In case DeepFace throws an error
                                print(f"Error with DeepFace: {e}")

                            # Clean up the temporary file
                            os.unlink(tmp_file_path)

                        else:
                            name = "No Face Detected"

                        # Display the name on the frame
                        cv2.putText(frame, name, (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (255, 255, 255), 2)

                except Exception as e:
                    print(f"Error during face detection or recognition: {e}")

                # Encode frame as JPEG for streaming
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

                # Yield the frame for Flask streaming
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def generate_frames(self):
        """
        Generate frames for streaming.
        """
        # Process frames in the main thread
        for frame in self.process_frames():
            yield frame

    def release_camera(self):
        """Release the camera."""
        self.stop_event.set()  # Signal the capture thread to stop
        self.capture_thread.join()  # Wait for the capture thread to finish
        self.camera.release()
        print("Camera released.")