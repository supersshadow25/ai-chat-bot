import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CASCADE_PATH = os.path.join(
    BASE_DIR, "..", "haarcascade_frontalface_default.xml"
)

face_detector = cv2.CascadeClassifier(CASCADE_PATH)
if face_detector.empty():
    raise IOError("Haarcascade not found")

USER_NAME = "Sumeet"
USER_ID = 1

SAVE_DIR = os.path.join(BASE_DIR, USER_NAME)
os.makedirs(SAVE_DIR, exist_ok=True)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

count = 0
print("Look at the camera. Press ESC to stop.")

while True:
    ret, img = cam.read()
    if not ret:
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        count += 1
        cv2.imwrite(
            os.path.join(SAVE_DIR, f"{USER_ID}.{count}.jpg"),
            gray[y:y+h, x:x+w]
        )
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow("Register Face", img)

    if cv2.waitKey(1) & 0xFF == 27 or count >= 50:
        break

cam.release()
cv2.destroyAllWindows()
print("Face samples saved")
