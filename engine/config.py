ASSISTANT_NAME = "jarvis"
ADMIN_PASSWORD = "admin123"

try:
	from .config_local import GROQ_API_KEY
except ModuleNotFoundError:
	GROQ_API_KEY = ""

