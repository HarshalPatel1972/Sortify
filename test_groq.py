import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

try:
    print("Testing Groq API connection...")
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hello, are you available?"}],
        max_tokens=10
    )
    print("SUCCESS: Groq API is available and responding.")
except Exception as e:
    print(f"ERROR: Groq API check failed. Reason: {e}")
