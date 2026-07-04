import os
import fitz
import json
import re
import time
from google import genai
from PIL import Image
from dotenv import load_dotenv
import io

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL_ID = 'gemini-2.0-flash'

PDF_DIR = "PDFs"
OUTPUT_DIR = "data/json_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROMPT = """
You are an expert Physics professor and Web Developer. I am providing an image of a scanned physics examination paper.
Your task is to perfectly extract the ENGLISH questions from this page.
Ignore any Hindi text entirely.

For EACH English question found on the page, provide a JSON object in an array. 
Even if there is only one question, return it inside a JSON array [ { ... } ].

Schema for each object:
{
    "id": "A unique ID string (e.g. PDFName_Q1)",
    "question_number": "The question number (e.g. '1', '2(a)', 'Q3')",
    "topic": "Determine the specific physics topic (1-3 words, e.g. Thermodynamics, Quantum Mechanics). Use your vast physics knowledge (and search if necessary) to determine this based on the question context.",
    "question_text": "The full English text of the question. Format all math equations, symbols, and variables using standard LaTeX enclosed in \\( \\) for inline or $$ $$ for block.",
    "options": ["(a) option 1", "(b) option 2"], // Array of strings if it is multiple choice, otherwise empty array.
    "has_diagram": true/false, // true ONLY if there is a physics diagram, circuit, or graph associated with this specific question on this page.
    "diagram_image": null, // We will store the SVG code here. If has_diagram is true, write highly accurate, clean, and scalable SVG code that perfectly replicates the diagram in the image. Use standard physics symbols. If false, set to null.
    "marks": 10 // If points/marks are visible (e.g. [10], (5)), put the integer here. Otherwise null.
}

Return ONLY the valid JSON array. Do not include markdown formatting, backticks, or any other text.
"""

def extract_json(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception as e:
            pass
    # Fallback to direct load
    try:
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        print("Failed to parse direct JSON:", e)
        return []

def process():
    pdf_files = ["10_PHYSICS2_0.pdf"] # Just process PDF 1
    
    all_results = []
    global_q_counter = 1
    
    for pdf_name in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        print(f"\nProcessing {pdf_name} via Gemini 1.5 Flash...")
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                
                print(f"  Sending page {page_num+1}/{len(doc)} to Gemini...")
                
                retries = 3
                while retries > 0:
                    try:
                        response = client.models.generate_content(
                            model=MODEL_ID,
                            contents=[PROMPT, img]
                        )
                        
                        data = extract_json(response.text)
                        
                        if data and isinstance(data, list):
                            print(f"  Found {len(data)} questions on page {page_num+1}.")
                            for q in data:
                                q["source_pdf"] = pdf_name
                                q["id"] = f"{pdf_name.split('_')[0]}_Q{global_q_counter}"
                                global_q_counter += 1
                                all_results.append(q)
                        else:
                            print(f"  No questions found or invalid format on page {page_num+1}.")
                        break
                    except Exception as e:
                        print(f"  Error on page {page_num+1}: {e}")
                        if "429" in str(e) or "Quota" in str(e) or "quota" in str(e).lower():
                            print("  Rate limited! Sleeping for 65 seconds...")
                            time.sleep(65)
                            retries -= 1
                        else:
                            break
                            
                # Strict delay to respect 20 RPM limit (which is 1 request every 3 seconds, 15 is extremely safe)
                time.sleep(15)
                
        except Exception as e:
            print(f"Error opening {pdf_name}: {e}")
            
    # Save to JSON
    out_path = os.path.join(OUTPUT_DIR, "pdf_1_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)
    print(f"Done! Extracted {len(all_results)} total questions to {out_path}")

if __name__ == "__main__":
    process()
