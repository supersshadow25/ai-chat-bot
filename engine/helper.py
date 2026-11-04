import os
import re
import time
import markdown2
from bs4 import BeautifulSoup


# ---------------- YOUTUBE SEARCH ----------------
def extract_yt_term(command: str):
    if not command:
        return None

    pattern = r'play\s+(.*?)\s+on\s+youtube'
    match = re.search(pattern, command, re.IGNORECASE)
    return match.group(1) if match else None


# ---------------- TEXT CLEANING ----------------
def remove_words(input_string, words_to_remove):
    if not input_string:
        return ""

    words = input_string.split()
    filtered_words = [
        word for word in words
        if word.lower() not in words_to_remove
    ]
    return " ".join(filtered_words)


# ---------------- ADB HELPERS ----------------
def _run_adb(command: str):
    """
    Safely run adb commands.
    Won't crash if adb is missing.
    """
    try:
        os.system(command)
        time.sleep(1)
    except Exception as e:
        print("ADB Error:", e)


# key events like back, home, call end
def keyEvent(key_code):
    _run_adb(f'adb shell input keyevent {key_code}')


# Tap event (screen touch)
def tapEvents(x, y):
    _run_adb(f'adb shell input tap {x} {y}')


# Input text into mobile
def adbInput(message):
    if not message:
        return
    _run_adb(f'adb shell input text "{message}"')


# Go back multiple times
def goback(key_code):
    for _ in range(6):
        keyEvent(key_code)


# Replace spaces for URL encoding
def replace_spaces_with_percent_s(input_string):
    if not input_string:
        return ""
    return input_string.replace(" ", "%s")


# ---------------- MARKDOWN CLEAN ----------------
def markdown_to_text(md):
    """
    Converts Gemini / LLM markdown safely into plain text.
    """
    if not md:
        return ""

    try:
        html = markdown2.markdown(str(md))
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text().strip()
    except Exception as e:
        print("Markdown parse error:", e)
        return str(md)
