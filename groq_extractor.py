import os
import fitz
import re
import json
import time
import cv2
import numpy as np
import pytesseract
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# We now use a list of 3 API keys to rotate automatically on rate limits
GROQ_KEYS = [
    os.environ.get("GROQ_API_KEY", "your_groq_api_key_1"),
    os.environ.get("GROQ_API_KEY_2", "your_groq_api_key_2"),
    os.environ.get("GROQ_API_KEY_3", "your_groq_api_key_3")
]
current_key_idx = 0
groq_client = Groq(api_key=GROQ_KEYS[current_key_idx])

os.environ["TESSDATA_PREFIX"] = r"C:\Users\Harshal Patel\scoop\apps\tesseract-languages\current"
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Harshal Patel\scoop\apps\tesseract\current\tesseract.exe'

PDF_DIR = "PDFs"
OUTPUT_DIR = "data/json_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROMPT = """
You are an expert Physics professor and Web Developer. I am providing you with the RAW OCR text extracted from a single page of a scanned physics examination paper.
The OCR might have errors and might contain random Hindi text, headers, footers, exam names, dates, or time limits.

Your task is to perfectly extract the ENGLISH questions from this raw text.
Ignore ANY Hindi text, headers, footers, exam dates, or irrelevant noise. Only focus on the actual questions.

For EACH English question found on the page, provide a JSON object in an array. 
Even if there is only one question, return it inside a JSON array [ { ... } ].

Schema for each object:
{
    "id": "A unique ID string (e.g. PDFName_Q1)",
    "question_number": "The question number (e.g. '1', '2(a)', 'Q3'). Try to parse this from the OCR.",
    "topic": "Determine the specific physics topic. MUST BE EXACTLY ONE OF THESE: Classical Mechanics, Atomic Physics, Quantum Mechanics, Electromagnetic Theory, Solid State Physics, Nuclear Physics, Thermodynamics, Statistical Mechanics, Wave and Oscillation, Optics, Mathematical Physics, Electronics, Modern Physics, Superconductivity, Semiconductor Physics.",
    "question_text": "The clean English text of the question. Fix any obvious OCR typos. Format all math equations, symbols, and variables using standard LaTeX enclosed in \\\\( \\\\) for inline or $$ $$ for block.",
    "options": ["(a) option 1", "(b) option 2"], 
    "marks": 10 
}

Return ONLY the valid JSON array. Do not include markdown formatting, backticks, or any other text. 
CRITICAL: ENSURE YOUR OUTPUT IS STRICTLY VALID JSON! ESCAPE BACKSLASHES IN LATEX PROPERLY (e.g. \\\\frac).
"""

def extract_json(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception as e:
            pass
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
    global current_key_idx
    global groq_client
    
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    
    out_path = os.path.join(OUTPUT_DIR, "all_questions.json")
    all_results = []
    processed_pdfs = set()
    global_q_counter = 1
    
    if os.path.exists(out_path):
        try:
            with open(out_path, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
                for q in all_results:
                    processed_pdfs.add(q.get("source_pdf"))
            global_q_counter = len(all_results) + 1
            print(f"Loaded {len(all_results)} existing questions. Skipping {len(processed_pdfs)} already processed PDFs.")
        except Exception as e:
            print("Could not load existing data, starting fresh.", e)

    for pdf_name in pdf_files:
        if pdf_name in processed_pdfs:
            print(f"Skipping {pdf_name} (already processed)...")
            continue
            
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        print(f"\n======================================")
        print(f"Processing {pdf_name} via Tesseract + Groq...")
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=300)
                img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 4:
                    img_np = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                else:
                    img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                
                print(f"  [{pdf_name}] OCR extracting page {page_num+1}/{len(doc)}...")
                try:
                    ocr_text = pytesseract.image_to_string(img_np, lang='eng+hin')
                except Exception as e:
                    print("  Falling back to eng only...")
                    ocr_text = pytesseract.image_to_string(img_np, lang='eng')
                    
                if not ocr_text.strip():
                    continue
                    
                print(f"  [{pdf_name}] Sending OCR text to Groq for JSON structuring...")
                
                # Retry loop for API keys
                max_retries = len(GROQ_KEYS)
                retries = 0
                success = False
                
                while retries < max_retries and not success:
                    try:
                        response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": PROMPT},
                                {"role": "user", "content": f"RAW OCR TEXT:\n{ocr_text}"}
                            ],
                            temperature=0.1,
                        )
                        output_text = response.choices[0].message.content
                        data = extract_json(output_text)
                        
                        if data and isinstance(data, list):
                            print(f"  [{pdf_name}] Found {len(data)} questions on page {page_num+1}.")
                            for q in data:
                                q["source_pdf"] = pdf_name
                                q["id"] = f"{pdf_name.split('_')[0]}_Q{global_q_counter}"
                                global_q_counter += 1
                                all_results.append(q)
                        else:
                            print(f"  [{pdf_name}] No questions found or invalid format on page {page_num+1}.")
                        
                        success = True # Broke out of retry loop successfully
                        time.sleep(0.5) 
                        
                    except Exception as api_e:
                        error_msg = str(api_e).lower()
                        if "429" in error_msg or "rate limit" in error_msg:
                            print(f"  [WARNING] Rate limit hit on Key {current_key_idx + 1}. Switching to next key...")
                            current_key_idx = (current_key_idx + 1) % len(GROQ_KEYS)
                            groq_client = Groq(api_key=GROQ_KEYS[current_key_idx])
                            retries += 1
                            if retries >= max_retries:
                                print(f"  [ERROR] All {len(GROQ_KEYS)} keys have hit their rate limits. Cannot proceed further today.")
                                raise Exception("ALL_KEYS_EXHAUSTED")
                            time.sleep(2) # Brief pause before retry
                        else:
                            # Not a rate limit error
                            print(f"  [ERROR] Groq API error: {api_e}")
                            break # Skip this page, don't keep retrying if it's a structural error
                
            # Progressive Save after every PDF
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=4, ensure_ascii=False)
            print(f"  [{pdf_name}] Progressively saved {len(all_results)} total questions to DB.")
                
        except Exception as e:
            print(f"Error processing {pdf_name}: {e}")
            if str(e) == "ALL_KEYS_EXHAUSTED":
                print("Stopping entire process due to exhaustion of all API keys.")
                break # Stop the outer PDF loop entirely
            
    print(f"\n======================================")
    print(f"DONE! Extracted {len(all_results)} TOTAL questions to {out_path}")

if __name__ == "__main__":
    process()
