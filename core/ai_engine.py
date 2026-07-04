import json
import logging
import re
from typing import Dict, List, Any

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.NVIDIA_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1"
)

SYSTEM_PROMPT = """
CRITICAL INSTRUCTIONS

You are connected to an application that parses your output as JSON.

You MUST respond with ONLY a valid JSON object.

Do NOT:
• Use markdown code fences (```).
• Add explanations before the JSON.
• Add explanations after the JSON.
• Return plain text.
• Return multiple JSON objects.

The response MUST always be exactly in this format:

{
  "intent": "general_query",
  "response": "Your response here."
}

------------------------------------------------------------

You are Kiko.

Kiko is a friendly, intelligent and professional AI assistant similar to ChatGPT.

Your goals are:

• Help the user accurately.
• Be conversational.
• Explain clearly.
• Keep answers easy to read.
• Never sound robotic.

------------------------------------------------------------

WRITING STYLE

• Write naturally like a human.
• Keep responses concise unless the user requests detail.
• Use short paragraphs.
• Separate paragraphs with a blank line.
• Use simple language whenever possible.
• Avoid repeating information.
• Never use filler words.
• Don't force follow-up questions.

------------------------------------------------------------

FORMATTING RULES

For normal answers:

Keep paragraphs between 1 and 3 sentences.

Example:

Python is a popular programming language.

It is widely used for web development, AI, automation, and data science.

For lists:

Every bullet MUST be on its own line.

Correct:

Languages:

• Python
• Java
• C#

Wrong:

Languages: • Python • Java • C#

For steps:

Use numbered lists.

Example:

1. Install Python.
2. Create a virtual environment.
3. Install dependencies.

For comparisons:

Use this format:

Python

• Easy to learn
• Large ecosystem

Java

• Excellent performance
• Strong typing

------------------------------------------------------------

CODE RESPONSES

If the user asks for code:

• Return complete working code whenever practical.
• Use best practices.
• Use meaningful variable names.
• Include comments only where useful.
• Do not explain every line.
• Keep explanations brief.

------------------------------------------------------------

ACCURACY

If you don't know something:

Say so honestly.

Do not invent facts.

Do not hallucinate.

------------------------------------------------------------

INTENT CLASSIFICATION

Choose ONE of these values only:

greeting
farewell
faq
general_query
complaint
human_agent_request
unknown

------------------------------------------------------------

FINAL RULE

Return ONLY valid JSON.

Example:

{
  "intent": "general_query",
  "response": "Python is a high-level programming language used for web development, automation, AI, and much more."
}
"""


def build_messages(user_message: str, chat_history: List[Any]) -> List[Dict]:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for msg in chat_history[-10:]:

        role = str(msg.role).lower()

        if role in ("assistant", "bot", "ai"):
            role = "assistant"
        else:
            role = "user"

        messages.append(
            {
                "role": role,
                "content": msg.content
            }
        )

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    return messages


def parse_json(content: str):
    # Normalize encoding and strip whitespace
    content = content.strip()
    content = content.encode("utf-8").decode("utf-8")

    # Stage 1: direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[PARSE] Stage 1 failed: {e}")

    # Stage 2: extract first {...} block
    match = re.search(r"\{[\s\S]*\}", content)
    extracted = match.group() if match else None

    if extracted:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError as e:
            print(f"[PARSE] Stage 2 failed: {e}")

    # Stage 3: escape literal newlines inside JSON string values
    if extracted:
        fixed = re.sub(r'\n', r'\\n', extracted)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            print(f"[PARSE] Stage 3 failed: {e}")

    # Stage 4: strip all control characters except \n \r \t
    if extracted:
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', extracted)
        try:
            return json.loads(sanitized)
        except json.JSONDecodeError as e:
            print(f"[PARSE] Stage 4 failed: {e}")

    # Stage 5: manually extract intent and response with regex
    print("[PARSE] All JSON stages failed. Attempting regex field extraction.")
    intent_match = re.search(r'"intent"\s*:\s*"([^"]+)"', content)
    response_match = re.search(r'"response"\s*:\s*"([\s\S]+?)"\s*\}', content)

    if response_match:
        return {
            "intent": intent_match.group(1) if intent_match else "general_query",
            "response": response_match.group(1).replace("\\n", "\n")
        }

    return None


def validate_response(data):

    if not isinstance(data, dict):
        return None

    intent = data.get("intent", "general_query")

    if intent not in {
        "greeting",
        "farewell",
        "faq",
        "general_query",
        "complaint",
        "human_agent_request",
        "unknown",
    }:
        intent = "general_query"

    response = str(data.get("response", "")).strip()

    if not response:
        response = "I'm sorry, but I couldn't generate a response."

    return {
        "intent": intent,
        "response": response
    }


async def generate_ai_response(
    user_message: str,
    chat_history: list
) -> dict:

    messages = build_messages(user_message, chat_history)

    try:

        print("=" * 70)
        print("[AI ENGINE] Calling NVIDIA NIM")
        print("[MODEL] meta/llama-3.1-70b-instruct")
        print("=" * 70)

        completion = await client.chat.completions.create(

            model="meta/llama-3.1-70b-instruct",

            messages=messages,

            temperature=0.5,

            top_p=0.9,

            max_tokens=800,

            frequency_penalty=0.2,

            presence_penalty=0.1,
        )

        content = completion.choices[0].message.content.strip()

        print()
        print("[RAW MODEL OUTPUT]")
        print(repr(content))
        print()

        parsed = parse_json(content)

        print("========== DEBUG ==========")
        print(repr(content))
        print(parsed)
        print(type(parsed))
        print("===========================")

        if parsed:

            validated = validate_response(parsed)

            if validated:
                print("[AI ENGINE] JSON parsed successfully")
                return validated

        print("[AI ENGINE] Model returned non-JSON output.")
        print("[AI ENGINE] Falling back to plain text.")

        return {
            "intent": "general_query",
            "response": content
        }

    except Exception as e:

        logger.exception("NVIDIA API Error")

        print()
        print("=" * 70)
        print("[AI ENGINE ERROR]")
        print(type(e).__name__)
        print(str(e))
        print("=" * 70)
        print()

        return {
            "intent": "general_query",
            "response": (
                "Sorry, I'm having trouble connecting to my AI service "
                "right now. Please try again in a moment."
            )
        }