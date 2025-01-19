import cv2
from deepface import DeepFace
import numpy as np
import os
import tempfile


class CameraFeed:
    def __init__(self,url):
        print("Initializing CameraFeed...")
        # Initialize the camera
        self.camera = cv2.VideoCapture(url)
        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera.")
        print("Camera initialized successfully.")

        # Path to the database of known faces
        self.db_path = '/home/amir-asadi/PycharmProjects/mega_project/known_image'
        if not os.path.exists(self.db_path):
            raise ValueError(f"Database path {self.db_path} does not exist.")

        print("CameraFeed initialized successfully.")

    def generate_frames(self):
        while True:
            # Read a frame from the camera
            ret, frame = self.camera.read()
            if not ret:
                break

            try:
                # Use DeepFace to extract faces from the frame
                extracted_faces = DeepFace.extract_faces(frame, detector_backend="opencv", enforce_detection=False)

                # Debugging: Check the type of extracted_faces
                print(f"Extracted faces: {extracted_faces}")

                # Iterate over detected faces
                for face in extracted_faces:
                    # Get the face region and confidence
                    facial_area = face["facial_area"]
                    x, y, w, h = facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]

                    # Draw a rectangle around the face
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    # Crop the face from the frame
                    cropped_face = frame[y:y + h, x:x + w]

                    # Debugging: Check the type of cropped_face
                    print(f"Type of cropped_face: {type(cropped_face)}")

                    if cropped_face.size > 0:
                        # Ensure it's a NumPy array (image matrix)
                        if isinstance(cropped_face, np.ndarray):
                            # Save the cropped face as a temporary image file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                                tmp_file_path = tmp_file.name
                                cv2.imwrite(tmp_file_path, cropped_face)
                                print(f"Temporary face image saved at: {tmp_file_path}")

                            # Perform face recognition using DeepFace
                            try:
                                results = DeepFace.find(img_path=tmp_file_path, db_path=self.db_path, enforce_detection=False)

                                # Debugging output to inspect results type and content
                                print(f"Results from DeepFace: {results} (Type: {type(results)})")

                                if isinstance(results, list) and len(results) > 0:
                                    # Assuming results is a list of DataFrames, take the first DataFrame
                                    df = results[0]
                                    if not df.empty:
                                        # Get the first row's 'identity' column value
                                        identity_path = df.iloc[0]['identity']
                                        name = os.path.basename(identity_path)
                                    else:
                                        name = "Unknown"
                                else:
                                    name = "Unknown"  # Label as unknown if no match is found

                            except Exception as e:
                                name = "Error"  # In case DeepFace throws an error
                                print(f"Error with DeepFace: {e}")

                        else:
                            name = "Invalid Face Data"  # Handle case if the cropped face is not a valid NumPy array
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
            frame = buffer.tobytes()

            # Yield the frame for Flask streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def release_camera(self):
        """Release the camera."""
        self.camera.release()
        print("Camera released.")