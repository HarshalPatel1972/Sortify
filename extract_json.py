import os
import fitz
import re
import json
import time
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import io
import numpy as np
import cv2
import easyocr
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

PDF_DIR = "PDFs"
OUTPUT_DIR = "data/json_results"
DIAGRAMS_DIR = "data/diagrams"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

print("Loading OCR...")
ocr_reader = easyocr.Reader(['en'])

QUESTION_MARKER_REGEXES = [
    re.compile(r"^\s*\d{1,3}[\.\)]\s"),
    re.compile(r"^\s*Q\.?\s*\d{1,3}", re.IGNORECASE),
    re.compile(r"^\s*Question\s+\d{1,3}", re.IGNORECASE),
]

def is_question_start(text: str) -> bool:
    for regex in QUESTION_MARKER_REGEXES:
        if regex.search(text):
            return True
    return False

def format_question_via_groq(text: str):
    prompt = f"""
    Given the following raw text extracted from an exam paper using OCR, structure it into the following JSON format. Fix any minor OCR typos.
    Do NOT include backticks or markdown, ONLY output valid JSON.
    
    {{
        "topic": "1-3 word topic name (e.g. Thermodynamics, Optics, Quantum Mechanics)",
        "question_text": "The actual question text. You can use LaTeX like \\( E=mc^2 \\) for math.",
        "options": ["(a) option 1", "(b) option 2", "(c) option 3", "(d) option 4"], // Empty array if no options are present
        "marks": null // Integer if you see something like '[10 marks]' or '(5)', otherwise null
    }}
    
    Raw text:
    {text}
    """
    
    retries = 3
    while retries > 0:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
            )
            response = chat_completion.choices[0].message.content.strip()
            # Clean up response to ensure valid JSON
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
                
            return json.loads(response.strip())
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                time.sleep(5)
                retries -= 1
            else:
                print("Error parsing JSON:", e)
                return {
                    "topic": "Uncategorized",
                    "question_text": text,
                    "options": [],
                    "marks": None
                }
    return {
        "topic": "Uncategorized",
        "question_text": text,
        "options": [],
        "marks": None
    }

def detect_diagram(img, text_bboxes):
    # Convert image to grayscale numpy array
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    
    # Threshold to binary (invert so text/lines are white, background black)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Mask out all text boxes found by OCR
    for bbox in text_bboxes:
        pts = np.array(bbox, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.fillPoly(binary, [pts], 0) # fill with black
        
    # Check if there are significant non-text pixels left (lines, circles, etc.)
    kernel = np.ones((3,3), np.uint8)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    non_zero_count = cv2.countNonZero(opened)
    
    # If there are more than e.g. 1000 pixels of drawings, it's likely a diagram
    if non_zero_count > 1000:
        return True
    return False

def process():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    # Try the first PDF specifically
    pdf_files = ["10_PHYSICS2_0.pdf"] if "10_PHYSICS2_0.pdf" in pdf_files else pdf_files[:1]
    
    all_results = []
    global_q_counter = 1
    
    for pdf_name in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        print(f"\nProcessing {pdf_name}...")
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                
                print(f"  Scanning page {page_num+1}/{len(doc)}...")
                result = ocr_reader.readtext(np.array(img))
                
                questions_data = []
                current_q = None
                
                for item in result:
                    bbox_pts = item[0]
                    text = item[1]
                    
                    min_y = min([p[1] for p in bbox_pts])
                    max_y = max([p[1] for p in bbox_pts])
                    
                    if is_question_start(text):
                        if current_q:
                            current_q["end_y"] = min_y
                            questions_data.append(current_q)
                            
                        current_q = {
                            "start_y": min_y,
                            "text": text + " ",
                            "end_y": img.size[1],
                            "bboxes": [bbox_pts]
                        }
                    else:
                        if current_q:
                            current_q["text"] += text + " "
                            current_q["bboxes"].append(bbox_pts)
                            
                if current_q:
                    questions_data.append(current_q)
                
                print(f"  Found {len(questions_data)} questions.")
                
                for i, q in enumerate(questions_data):
                    print(f"    Formatting Q{i+1}...")
                    
                    json_data = format_question_via_groq(q["text"])
                    
                    top = max(0, int(q["start_y"]) - 15)
                    bottom = min(img.size[1], int(q["end_y"]) - 5)
                    left = 0
                    right = img.size[0]
                    
                    has_diagram = False
                    diagram_path = None
                    
                    if bottom > top:
                        cropped_img = img.crop((left, top, right, bottom))
                        
                        adjusted_bboxes = []
                        for b in q["bboxes"]:
                            adj_b = [[p[0]-left, p[1]-top] for p in b]
                            adjusted_bboxes.append(adj_b)
                            
                        has_diagram = detect_diagram(cropped_img, adjusted_bboxes)
                        
                        if has_diagram:
                            safe_name = pdf_name.replace(".pdf", "")
                            diagram_filename = f"{safe_name}_p{page_num+1}_q{i+1}.png"
                            diagram_path = f"data/diagrams/{diagram_filename}"
                            cropped_img.save(diagram_path)
                    
                    final_obj = {
                        "id": f"{pdf_name.split('_')[0]}_Q{global_q_counter}",
                        "source_pdf": pdf_name,
                        "question_number": str(global_q_counter),
                        "topic": json_data.get("topic", "Uncategorized"),
                        "question_text": json_data.get("question_text", ""),
                        "options": json_data.get("options", []),
                        "has_diagram": has_diagram,
                        "diagram_image": diagram_path,
                        "marks": json_data.get("marks", None)
                    }
                    
                    all_results.append(final_obj)
                    global_q_counter += 1
                    
        except Exception as e:
            print(f"Error on {pdf_name}: {e}")
            
    with open(os.path.join(OUTPUT_DIR, "pdf_1_results.json"), "w") as f:
        json.dump(all_results, f, indent=4)
    print("Done! JSON saved to pdf_1_results.json")

if __name__ == "__main__":
    process()
