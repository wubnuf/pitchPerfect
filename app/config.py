# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Backend ---
# Set to "lmstudio" to use a local LM Studio model, or "openai" for GPT-4
LLM_BACKEND = os.getenv("LLM_BACKEND", "lmstudio")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LM Studio settings (OpenAI-compatible local server)
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")

# --- Automation Backend ---
# Set to "openclaw" to use OpenClaw macOS native tools, or "pyautogui" for direct screen control
AUTOMATION_BACKEND = os.getenv("AUTOMATION_BACKEND", "openclaw")

# OpenClaw Gateway settings
OPENCLAW_GATEWAY_HOST = os.getenv("OPENCLAW_GATEWAY_HOST", "127.0.0.1")
OPENCLAW_GATEWAY_PORT = int(os.getenv("OPENCLAW_GATEWAY_PORT", "4840"))
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
OPENCLAW_SECRET = os.getenv("OPENCLAW_SECRET", "")
