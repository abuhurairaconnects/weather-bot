"""
Google Gemini AI Service
Provides conversational intelligence, answering any user question in Bengali/English
with multi-turn conversation memory and automatic model fallback.
"""
import logging
import httpx
from typing import Dict, List, Any
from config import GEMINI_API_KEY, GEMINI_API_BASE_URL, GEMINI_MODELS

logger = logging.getLogger(__name__)

# In-memory conversation history per user_id:
# Dict[user_id, List[{"role": "user"|"model", "parts": [{"text": "..."}]}]]
_USER_HISTORIES: Dict[int, List[Dict[str, Any]]] = {}
MAX_HISTORY_TURNS = 6  # Keep last 6 messages (3 user + 3 assistant)

SYSTEM_INSTRUCTION = (
    "You are a friendly, courteous, and highly intelligent AI assistant embedded in a Telegram bot named 'Weather Alltime' (ওয়েদার অলটাইম). "
    "You can answer any question the user asks on any topic: general knowledge, science, philosophy, history, coding, mathematics, "
    "everyday life advice, cooking recipes, jokes, poetry, or casual conversation. "
    "\nGuidelines:"
    "\n1. If the user asks in Bengali (বাংলা), respond in fluent, polished, natural, and polite Bengali."
    "\n2. If the user asks in English, respond in clear, professional English."
    "\n3. Keep your answers well-structured, using markdown bolding, clear bullet points, and easy-to-read spacing on mobile screens."
    "\n4. If the user asks for live weather data of a specific city, provide helpful insights and inform them that typing the city name directly (e.g. 'Dhaka' or 'চট্টগ্রাম') gives a real-time live weather card with graphical charts."
)

async def ask_gemini(user_id: int, user_query: str, lang: str = "bn") -> str:
    """
    Sends the user prompt along with recent conversation history to Google Gemini API.
    Returns the generated response text in Markdown format.
    """
    if not GEMINI_API_KEY:
        if lang == "bn":
            return "⚠️ Gemini AI সেবা সক্রিয় করার জন্য API Key কনফিগার করা হয়নি।"
        return "⚠️ Gemini AI API Key is not configured."

    # Retrieve or initialize user history
    history = _USER_HISTORIES.get(user_id, [])
    # Trim history if exceeding limit
    if len(history) > MAX_HISTORY_TURNS:
        history = history[-MAX_HISTORY_TURNS:]

    # Prepare payload with history + new user message
    contents = list(history)
    contents.append({
        "role": "user",
        "parts": [{"text": user_query.strip()}]
    })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        }
    }

    headers = {"Content-Type": "application/json"}

    # Try models with fallback
    for model_name in GEMINI_MODELS:
        url = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            reply_text = parts[0]["text"].strip()
                            
                            # Save to user history
                            history.append({"role": "user", "parts": [{"text": user_query.strip()}]})
                            history.append({"role": "model", "parts": [{"text": reply_text}]})
                            _USER_HISTORIES[user_id] = history[-MAX_HISTORY_TURNS:]
                            
                            return reply_text
                elif resp.status_code in (429, 503):
                    logger.warning(f"Gemini model {model_name} returned {resp.status_code}, trying fallback model...")
                    continue
                else:
                    logger.error(f"Gemini API error ({model_name}): HTTP {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Gemini connection error on {model_name}: {e}")
            continue

    # If all models failed or threw errors:
    if lang == "bn":
        return "🤖 দুঃখিত, এই মুহূর্তে এআই রেসপন্স দিতে সামান্য সমস্যা হচ্ছে। অনুগ্রহ করে একটু পর আবার চেষ্টা করুন।"
    return "🤖 Sorry, I am having trouble reaching the AI service right now. Please try again in a moment."

def clear_user_history(user_id: int):
    """Clears conversation history for a specific user."""
    if user_id in _USER_HISTORIES:
        del _USER_HISTORIES[user_id]
