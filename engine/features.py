import json
import os
import sqlite3
import subprocess
import time
import webbrowser
from shlex import quote
from urllib.parse import quote_plus, urlsplit

import eel
import pyautogui

from engine.command import speak
from engine.config import ASSISTANT_NAME, GROQ_API_KEY
from engine.helper import extract_yt_term, remove_words

from groq import Groq


# ================= DATABASE =================
con = sqlite3.connect("jarvis.db", check_same_thread=False)
cursor = con.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS info (
    name TEXT,
    designation TEXT,
    mobileno TEXT,
    email TEXT,
    city TEXT
);

CREATE TABLE IF NOT EXISTS sys_command (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    path TEXT
);

CREATE TABLE IF NOT EXISTS web_command (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    url TEXT
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mobile_no TEXT,
    email TEXT,
    city TEXT
);
""")
con.commit()


# ================= SOUND =================
@eel.expose
def playAssistantSound():
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load("www/assets/audio/start_sound.mp3")
    pygame.mixer.music.play()


# ================= OPEN COMMAND =================
def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "").replace("open", "").strip().lower()

    try:
        cursor.execute("SELECT path FROM sys_command WHERE name = ?", (query,))
        result = cursor.fetchone()
        if result:
            speak(f"Opening {query}")
            os.startfile(result[0])
            return

        cursor.execute("SELECT url FROM web_command WHERE name = ?", (query,))
        result = cursor.fetchone()
        if result:
            speak(f"Opening {query}")
            webbrowser.open(result[0])
            return

        speak(f"Opening {query}")
        os.system(f"start {query}")

    except Exception as e:
        print("OpenCommand Error:", e)
        speak("Something went wrong")


# ================= YOUTUBE =================
def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if not search_term:
        return

    try:
        import pywhatkit as kit
        speak(f"Playing {search_term} on YouTube")
        kit.playonyt(search_term)
    except Exception:
        speak("Internet is not available")


def _open_website(url):
    url = str(url).strip()
    if not url or len(url) > 2048:
        return False
    if "://" not in url:
        url = f"https://{url}"

    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False

    return webbrowser.open(url, new=2)


def _search_web(query):
    query = str(query).strip()
    if not query:
        return False
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    return webbrowser.open(url, new=2)


def _open_registered_app(name):
    name = str(name).strip().lower()
    if not name:
        return False

    cursor.execute("SELECT path FROM sys_command WHERE name = ?", (name,))
    result = cursor.fetchone()
    if not result:
        return False

    os.startfile(result[0])
    return True


AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website the user requested in their default browser. Use for requests to visit, go to, or open a website.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "The website URL, including its domain."}},
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Open a browser search for a topic the user wants to find online.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "What to search for."}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_registered_app",
            "description": "Open an installed app that is already registered in Jarvis settings.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "The registered app name."}},
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
]


def _execute_ai_tool(tool_call):
    arguments = json.loads(tool_call.function.arguments or "{}")
    tool_name = tool_call.function.name

    if tool_name == "open_website":
        url = arguments.get("url", "")
        if _open_website(url):
            host = urlsplit(url if "://" in url else f"https://{url}").hostname
            speak(f"Opening {host}")
        else:
            speak("I couldn't open that website. Please check the address and try again.")
    elif tool_name == "search_web":
        query = arguments.get("query", "")
        if _search_web(query):
            speak(f"Searching the web for {query}")
        else:
            speak("Tell me what you would like me to search for.")
    elif tool_name == "open_registered_app":
        name = arguments.get("name", "")
        if _open_registered_app(name):
            speak(f"Opening {name}")
        else:
            speak(f"{name} isn't registered in Jarvis settings.")
    else:
        speak("I can't perform that action.")


# ================= HOTWORD (DISABLED) =================
def hotword():
    print("Hotword disabled (no access key)")
    while True:
        time.sleep(10)


# ================= CONTACT SEARCH =================
def findContact(query):
    words = [
        ASSISTANT_NAME, "make", "a", "to", "phone",
        "call", "send", "message", "whatsapp", "video"
    ]

    query = remove_words(query, words).strip().lower()

    try:
        cursor.execute(
            "SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ?",
            (f"%{query}%",)
        )
        number = cursor.fetchone()[0]

        if not number.startswith("+91"):
            number = "+91" + number

        return number, query

    except:
        speak("Contact not found")
        return 0, 0


# ================= WHATSAPP =================
def whatsApp(mobile_no, message, flag, name):
    encoded = quote(message)
    url = f"whatsapp://send?phone={mobile_no}&text={encoded}"

    subprocess.run(f'start "" "{url}"', shell=True)
    time.sleep(6)
    pyautogui.press("enter")

    speak(f"{flag} successful to {name}")


# ================= CALL =================
def makeCall(name, mobile):
    speak(f"Calling {name}")
    os.system(
        f'adb shell am start '
        f'-a android.intent.action.CALL -d tel:{mobile}'
    )


# ================= SMS =================
def sendMessage(message, mobile, name):
    speak(f"Sending message to {name}")

    os.system(
        f'adb shell am start -a android.intent.action.SENDTO '
        f'-d sms:{mobile} --es sms_body "{message}"'
    )
    os.system("adb shell input keyevent 22")
    os.system("adb shell input keyevent 66")


# ================= GROQ AI (FINAL – WORKING) =================
def ai_reply(query):
    if not GROQ_API_KEY:
        print("Groq Error: GROQ_API_KEY environment variable is not set")
        speak("AI is not configured. Set the Groq API key in PowerShell and restart Jarvis.")
        return

    try:
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are Jarvis, a smart, friendly voice assistant. When the user asks to open or visit a website, search online, or open an installed app, call the matching tool instead of replying with a link or instructions. Only open apps registered in Jarvis settings. Never claim an action succeeded unless its tool reports success."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            temperature=0.6,
            tools=AI_TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        if message.tool_calls:
            for tool_call in message.tool_calls[:3]:
                _execute_ai_tool(tool_call)
            return

        answer = (message.content or "").strip()
        if answer:
            speak(answer)
        else:
            speak("I couldn't complete that request.")

    except Exception as e:
        status_code = getattr(e, "status_code", None)
        print(f"Groq Error ({type(e).__name__}, status {status_code}):", e)

        if status_code == 401:
            speak("The Groq API key is invalid or revoked. Set a new key and restart Jarvis.")
        elif status_code == 429:
            speak("The Groq free quota or rate limit was reached. Please wait and try again.")
        elif status_code is None:
            speak("Could not connect to Groq. Check your internet connection and try again.")
        else:
            speak("Groq rejected the request. Check the terminal for details.")


# ================= UI HELPERS =================
@eel.expose
def assistantName():
    return ASSISTANT_NAME


@eel.expose
def personalInfo():
    cursor.execute("SELECT * FROM info")
    data = cursor.fetchone()
    if data:
        eel.getData(json.dumps(data))


@eel.expose
def displaySysCommand():
    cursor.execute("SELECT * FROM sys_command")
    eel.displaySysCommand(json.dumps(cursor.fetchall()))


@eel.expose
def displayWebCommand():
    cursor.execute("SELECT * FROM web_command")
    eel.displayWebCommand(json.dumps(cursor.fetchall()))


@eel.expose
def displayPhoneBookCommand():
    cursor.execute("SELECT * FROM contacts")
    eel.displayPhoneBookCommand(json.dumps(cursor.fetchall()))
