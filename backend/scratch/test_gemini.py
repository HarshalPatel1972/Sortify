import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-1.5-pro')

img = Image.open('scratch/test_page.png')

prompt = """
Analyze this page from an exam. 
Identify all English questions (ignore Hindi versions of the questions).
For each English question, provide its bounding box in the format [ymin, xmin, ymax, xmax] scaled to 1000.
Also provide a 1-3 word topic name for each question based on its subject matter (e.g. 'Quantum Mechanics', 'Thermodynamics').
Output as JSON in this format:
[
  {
    "topic": "Topic Name",
    "box_2d": [ymin, xmin, ymax, xmax]
  }
]
Return ONLY the raw JSON array.
"""

response = model.generate_content([prompt, img])
print(response.text)
