from openai import OpenAI
from .config import GROQ_API_KEY

# Groq provides an OpenAI-compatible endpoint
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def llm_json(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    """
    Returns the model response as plain text (we'll parse JSON ourselves).
    """
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON. No extra text."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content