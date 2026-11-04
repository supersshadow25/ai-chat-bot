import shutil
import subprocess
import eel

from engine.features import playAssistantSound
from engine.command import speak
from engine.auth import recoganize


def start():

    # Initialize eel
    eel.init("www")

    # Play startup sound
    playAssistantSound()

    @eel.expose
    def init():
        try:
            if shutil.which("adb"):
                subprocess.call(["device.bat"], shell=True)
            else:
                print("ADB not installed; skipping device setup.")
        except Exception as e:
            print("Device init error:", e)

        eel.hideLoader()
        speak("Ready for Face Authentication")

    @eel.expose
    def handleFaceAuthChoice(choice, password="", name=""):
        try:
            choice = str(choice).strip().lower()
            password = str(password or "").strip()
            name = str(name or "").strip()

            if choice in ("2", "new", "new user"):
                if not recoganize.validate_admin_password(password):
                    speak("Invalid admin password. Access denied.")
                    return

                if not name:
                    speak("New user name is required.")
                    return

                if not recoganize.register_new_face(name):
                    speak("New user registration failed.")
                    return

                speak(f"New user {name} registered successfully.")
                eel.hideFaceAuth()
                speak("Face Authentication Successful")
                eel.hideFaceAuthSuccess()
                speak("Hello, Welcome Sir. How can I help you?")
                eel.hideStart()
                playAssistantSound()
                return

            if choice not in ("1", "existing", "existing user"):
                speak("Invalid face authentication choice.")
                return

            flag = recoganize.AuthenticateFace()
            if flag == 1:
                eel.hideFaceAuth()
                speak("Face Authentication Successful")
                eel.hideFaceAuthSuccess()
                speak("Hello, Welcome Sir. How can I help you?")
                eel.hideStart()
                playAssistantSound()
            else:
                speak("Face Authentication Failed")
        except Exception as e:
            print("Face auth error:", e)
            speak("Face authentication failed")

    # ✅ ONLY this opens the UI
    eel.start(
        "index.html",
        mode="edge",   # Edge app mode
        host="localhost",
        port=8000,
        block=True
    )
