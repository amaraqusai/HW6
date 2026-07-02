import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
print(f"Key format looks like: {api_key[:5] if api_key else 'None'}...")

try:
    client = genai.Client(vertexai=False, api_key=api_key)
    response = client.models.generate_content(
        model='gemini-flash-lite-latest',
        contents="Say 'API key is working!'"
    )
    print("SUCCESS:", response.text)
except Exception as e:
    print("FAILED:", str(e))
