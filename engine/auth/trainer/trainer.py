import os
import cv2
import numpy as np
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "..", "samples")
TRAINER_PATH = os.path.join(BASE_DIR, "trainer.yml")

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
ids = []
label_map = {}
current_id = 1

print("Scanning samples folder...")

for person_name in os.listdir(SAMPLES_DIR):
    person_path = os.path.join(SAMPLES_DIR, person_name)

    if not os.path.isdir(person_path):
        continue

    print(f"Found person: {person_name}")

    label_map[current_id] = person_name

    for file in os.listdir(person_path):
        if not file.lower().endswith(".jpg"):
            continue

        img_path = os.path.join(person_path, file)

        try:
            img = Image.open(img_path).convert("L")
            img_np = np.array(img, "uint8")
            img_np = cv2.resize(img_np, (200, 200))

            faces.append(img_np)
            ids.append(current_id)
        except Exception as e:
            print("Skipping image:", img_path, e)

    current_id += 1

if len(faces) == 0:
    raise Exception("No images loaded. Training failed.")

recognizer.train(faces, np.array(ids))
recognizer.write(TRAINER_PATH)

print("✅ Training completed successfully")
print("Total faces trained:", len(faces))
print("Trainer saved at:", TRAINER_PATH)
print("Label map:", label_map)
