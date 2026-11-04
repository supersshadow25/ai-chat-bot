import os
import time

import cv2
import numpy as np
from PIL import Image

from engine.config import ADMIN_PASSWORD

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
TRAINER_PATH = os.path.join(BASE_DIR, "trainer", "trainer.yml")
CASCADE_PATH = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")


def get_registered_users():
    names = [""]
    if not os.path.isdir(SAMPLES_DIR):
        return names

    for folder in sorted(os.listdir(SAMPLES_DIR)):
        full_path = os.path.join(SAMPLES_DIR, folder)
        if os.path.isdir(full_path):
            names.append(folder)

    return names


def validate_admin_password(password):
    return str(password).strip() == str(ADMIN_PASSWORD).strip()


def train_face_model():
    if not hasattr(cv2, "face"):
        print("OpenCV face module not found (opencv-contrib-python missing)")
        return False

    if not os.path.isdir(SAMPLES_DIR):
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    if detector.empty():
        print("Haarcascade file not loaded")
        return False

    faces = []
    ids = []
    person_dirs = []

    for folder in sorted(os.listdir(SAMPLES_DIR)):
        full_path = os.path.join(SAMPLES_DIR, folder)
        if os.path.isdir(full_path):
            person_dirs.append(folder)

    if not person_dirs:
        return False

    for user_id, user_name in enumerate(person_dirs, start=1):
        user_dir = os.path.join(SAMPLES_DIR, user_name)
        for file_name in sorted(os.listdir(user_dir)):
            if not file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            img_path = os.path.join(user_dir, file_name)
            try:
                img = Image.open(img_path).convert("L")
                img_arr = np.array(img, "uint8")
                detected = detector.detectMultiScale(img_arr)

                for (x, y, w, h) in detected:
                    faces.append(img_arr[y:y + h, x:x + w])
                    ids.append(user_id)
            except Exception as exc:
                print(f"Skipping image {img_path}: {exc}")

    if not faces:
        return False

    recognizer.train(faces, np.array(ids))
    os.makedirs(os.path.dirname(TRAINER_PATH), exist_ok=True)
    recognizer.write(TRAINER_PATH)
    return True


def register_new_face(user_name):
    user_name = str(user_name).strip()
    if not user_name:
        return False

    safe_name = "".join(ch for ch in user_name if ch.isalnum() or ch in " _-")
    safe_name = safe_name.strip()
    if not safe_name:
        return False

    os.makedirs(os.path.join(SAMPLES_DIR, safe_name), exist_ok=True)

    face_detector = cv2.CascadeClassifier(CASCADE_PATH)
    if face_detector.empty():
        print("Haarcascade file not loaded")
        return False

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cam.isOpened():
        print("Camera not accessible")
        return False

    save_dir = os.path.join(SAMPLES_DIR, safe_name)
    count = 0
    print(f"Registering {safe_name}. Look at the camera. Press ESC to stop.")

    while True:
        ret, img = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            cv2.imwrite(os.path.join(save_dir, f"{count}.jpg"), gray[y:y + h, x:x + w])
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Register Face", img)

        if cv2.waitKey(1) & 0xFF == 27 or count >= 50:
            break

    cam.release()
    cv2.destroyAllWindows()

    if count == 0:
        return False

    return train_face_model()


def AuthenticateFace():
    """
    Returns:
        1 → face authenticated
        0 → authentication failed
    """

    flag = 0

    if not hasattr(cv2, "face"):
        print("OpenCV face module not found (opencv-contrib-python missing)")
        return 0

    if not os.path.isfile(TRAINER_PATH):
        if not train_face_model():
            print("Trainer file not found and no face samples available")
            return 0

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_PATH)

    faceCascade = cv2.CascadeClassifier(CASCADE_PATH)
    if faceCascade.empty():
        print("Haarcascade file not loaded")
        return 0

    font = cv2.FONT_HERSHEY_SIMPLEX
    names = get_registered_users()

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cam.isOpened():
        print("Camera not accessible")
        return 0

    cam.set(3, 640)
    cam.set(4, 480)

    minW = 0.1 * cam.get(3)
    minH = 0.1 * cam.get(4)

    start_time = time.time()
    TIMEOUT = 15

    while True:
        ret, img = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH)),
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            user_id, accuracy = recognizer.predict(gray[y:y + h, x:x + w])

            if accuracy < 80:
                name = names[user_id] if user_id < len(names) else "Unknown"
                flag = 1
                cv2.putText(img, name, (x + 5, y - 5), font, 1, (255, 255, 255), 2)
                break
            else:
                cv2.putText(img, "Unknown", (x + 5, y - 5), font, 1, (0, 0, 255), 2)

        cv2.imshow("Face Authentication", img)

        if cv2.waitKey(10) & 0xFF == 27:
            break

        if flag == 1:
            break

        if time.time() - start_time > TIMEOUT:
            break

    cam.release()
    cv2.destroyAllWindows()
    return flag
