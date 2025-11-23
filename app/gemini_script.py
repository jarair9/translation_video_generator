import json
import os
from typing import List, Dict

import google.generativeai as genai


def _load_api_key_from_env_file() -> str | None:
    """Try to load GOOGLE_API_KEY from a .env file in the project root.

    Expected format (one per line):
        GOOGLE_API_KEY=your_key_here
    """

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    if not os.path.isfile(env_path):
        return None
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("GOOGLE_API_KEY="):
                    # Extract the value after the =
                    value = line.split("=", 1)[1].strip()
                    # Remove quotes if present
                    value = value.strip("'\"")
                    return value
    except Exception:
        return None
    return None


def _configure_gemini() -> None:
    api_key = os.environ.get("GOOGLE_API_KEY") or _load_api_key_from_env_file()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Define it in a .env file or as an environment variable.")
    genai.configure(api_key=api_key)


def generate_script_with_gemini(
    topic: str,
    level: str = "beginner",
    num_pairs: int = 5,
    script_type: str = "sentences",
) -> List[Dict[str, str]]:
    if num_pairs <= 0:
        raise ValueError("num_pairs must be > 0")

    _configure_gemini()

    model = genai.GenerativeModel("gemini-2.0-flash")

    # Different prompts for words vs sentences
    if script_type == "words":
        content_instruction = """Generate exactly {num_pairs} individual vocabulary words as a JSON array.
Each item must be an object with these keys only:
  - en: a single English word
  - ur: the equivalent Urdu word (using correct Urdu script)

Constraints:
- Choose useful, common vocabulary words related to the topic.
- Use single words only (no phrases or sentences).
- Match the difficulty level appropriately.
- Do NOT include transliteration.
- Return ONLY valid JSON, no explanations, no markdown, no comments.
- Make sure the output can be parsed directly as JSON.

Example format:
[
  {{"en": "hello", "ur": "ہیلو"}},
  {{"en": "water", "ur": "پانی"}}
]
"""
    else:  # sentences
        content_instruction = """Generate exactly {num_pairs} short, simple example sentences as a JSON array.
Each item must be an object with these keys only:
  - en: the English sentence
  - ur: the equivalent natural Urdu sentence (using correct Urdu script)

Constraints:
- Use everyday, clear language that matches the level.
- Create complete, meaningful sentences.
- Do NOT include transliteration.
- Return ONLY valid JSON, no explanations, no markdown, no comments.
- Make sure the output can be parsed directly as JSON.

Example format:
[
  {{"en": "I am learning Urdu", "ur": "میں اردو سیکھ رہا ہوں"}},
  {{"en": "This is beautiful", "ur": "یہ خوبصورت ہے"}}
]
"""

    prompt = f"""
You are helping to create a bilingual English-Urdu teaching video script.

Topic: {topic}
Level: {level} learner.
Script Type: {script_type}

{content_instruction.format(num_pairs=num_pairs)}
"""


    response = model.generate_content(prompt)
    text = response.text.strip()

    # Remove markdown code blocks if present
    if text.startswith("```"):
        # Remove opening ```json or ```
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini response was not valid JSON: {exc}\nRaw: {text[:400]}...") from exc

    if not isinstance(data, list):
        raise RuntimeError("Gemini response JSON is not a list.")

    cleaned: List[Dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        en = str(item.get("en", "")).strip()
        ur = str(item.get("ur", "")).strip()
        if en and ur:
            cleaned.append({"en": en, "ur": ur})

    if not cleaned:
        raise RuntimeError("Gemini returned no usable en/ur pairs.")

    if len(cleaned) > num_pairs:
        cleaned = cleaned[:num_pairs]

    return cleaned
