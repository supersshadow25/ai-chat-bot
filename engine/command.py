import pyttsx3
import speech_recognition as sr
import eel
import time
from contextlib import contextmanager


# ================= TEXT TO SPEECH =================
engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)
engine.setProperty("rate", 174)


def speak(text):
    text = str(text)
    print("Jarvis:", text)

    try:
        eel.DisplayMessage(text)
        eel.receiverText(text)
    except:
        pass

    engine.say(text)
    engine.runAndWait()


# ================= SPEECH TO TEXT =================
@contextmanager
def _microphone_source():
    source = sr.Microphone()
    source.__enter__()
    if source.stream is None:
        raise OSError("No microphone input device is available, or access is blocked.")

    try:
        yield source
    finally:
        source.__exit__(None, None, None)


def takecommand():
    recognizer = sr.Recognizer()

    try:
        with _microphone_source() as source:
            print("Listening...")
            try:
                eel.DisplayMessage("Listening...")
            except:
                pass

            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=10
            )

        print("Recognizing...")
        try:
            eel.DisplayMessage("Recognizing...")
        except:
            pass

        query = recognizer.recognize_google(audio, language="en-IN")
        print("User said:", query)
        return query.lower()

    except sr.WaitTimeoutError:
        return ""

    except sr.UnknownValueError:
        speak("Sorry, I didn't understand that.")
        return ""

    except sr.RequestError:
        speak("Speech service is unavailable.")
        return ""

    except Exception as e:
        print("Mic Error:", e)
        speak("Microphone error.")
        return ""


# ================= MAIN COMMAND ROUTER =================
@eel.expose
def allCommands(message=1):

    # -------- GET INPUT --------
    if message == 1:
        query = takecommand()
        if not query:
            try:
                eel.ShowHood()
            except:
                pass
            return
        eel.senderText(query)
    else:
        query = message
        eel.senderText(query)

    try:
        # -------- AI ACTIONS --------
        normalized_query = query.lower()
        if any(phrase in normalized_query for phrase in ("open ", "launch ", "visit ", "go to ", "search web", "search the web", "search for ")):
            from engine.features import ai_reply
            ai_reply(query)

        # -------- YOUTUBE --------
        elif "youtube" in normalized_query:
            from engine.features import PlayYoutube
            PlayYoutube(query)

        # -------- CALL / MESSAGE --------
        elif any(x in query for x in ["send message", "phone call", "video call"]):
            from engine.features import (
                findContact,
                whatsApp,
                makeCall,
                sendMessage
            )

            contact_no, name = findContact(query)
            if contact_no == 0:
                eel.ShowHood()
                return

            speak("Do you want to use mobile or WhatsApp?")
            preference = takecommand()

            if not preference:
                speak("No response received.")
                eel.ShowHood()
                return

            # ---- MOBILE ----
            if "mobile" in preference:
                if "send message" in query or "send sms" in query:
                    speak("What message should I send?")
                    msg = takecommand()
                    if msg:
                        sendMessage(msg, contact_no, name)

                elif "phone call" in query:
                    makeCall(name, contact_no)

            # ---- WHATSAPP ----
            elif "whatsapp" in preference:
                mode = "message"

                if "phone call" in query:
                    mode = "call"
                elif "video call" in query:
                    mode = "video call"
                else:
                    speak("What message should I send?")
                    query = takecommand()

                whatsApp(contact_no, query, mode, name)

        # -------- AI FALLBACK (OPENAI) --------
        else:
            from engine.features import ai_reply
            ai_reply(query)

    except Exception as e:
        print("Command Error:", e)
        speak("Something went wrong.")

    try:
        eel.ShowHood()
    except:
        pass
