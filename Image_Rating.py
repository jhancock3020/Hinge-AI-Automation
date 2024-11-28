import dlib
import numpy as np
import cv2
import os

def rate_image():
    # Check if the predictor file exists
    predictor_path = "shape_predictor_68_face_landmarks.dat"
    if not os.path.isfile(predictor_path):
        raise FileNotFoundError(f"Predictor file '{predictor_path}' not found.")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    # Load and check the image
    image_path = "cropped_element.png"
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image file '{image_path}' not found.")

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces in the image
    faces = detector(gray)

    # Check if there are no faces or multiple faces
    if len(faces) != 1:
        #print("Symmetry score: -1")
        return -1
    else:
        LEFT_SIDE = [i for i in range(0, 9)]  # Left jawline
        RIGHT_SIDE = [16 - i for i in range(0, 9)]  # Right jawline (mirrored indices)

        # Process the single detected face
        for face in faces:
            landmarks = predictor(gray, face)
            landmark_points = np.array([[p.x, p.y] for p in landmarks.parts()])

            # Draw facial landmarks on the image
            for (x, y) in landmark_points:
                cv2.circle(image, (x, y), 2, (0, 255, 0), -1)

            # Compute symmetry as distances to vertical center
            center_x = (face.left() + face.right()) // 2
            left_distances = np.abs(landmark_points[LEFT_SIDE, 0] - center_x)
            right_distances = np.abs(landmark_points[RIGHT_SIDE, 0] - center_x)
            symmetry_score = np.mean(left_distances / (right_distances + 1e-5))
            
            # Limit and invert symmetry score if needed
            symmetry_score = round(min(2 - symmetry_score, symmetry_score), 1)
            #print("Symmetry score:", symmetry_score)

            # Scale the score to [1, 10]
            scaled_score = max(1, min(10, (symmetry_score - 0) * 9 + 1))
            #print("Scaled Score:", scaled_score)

        # Display the image with facial landmarks
        #cv2.imshow("Facial Landmarks", image)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
    return scaled_score
