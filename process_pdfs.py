import os
import fitz
import re
import time
from PIL import Image
from dotenv import load_dotenv
import io
import numpy as np
import easyocr
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

PDF_DIR = "PDFs"
OUTPUT_DIR = "data/output_topics"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize OCR reader once
print("Loading EasyOCR models (this will take a few seconds)...")
ocr_reader = easyocr.Reader(['en'])
print("EasyOCR loaded successfully!")

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

def get_topic_from_groq(text: str) -> str:
    prompt = f"""
    Given the following text from an exam question, identify its core topic in 1 to 3 words (e.g., 'Thermodynamics', 'Quantum Mechanics', 'Electromagnetism').
    Ignore any Hindi or fragmented text.
    Return ONLY the topic name, nothing else. No markdown, no quotes.

    Question Text:
    {text}
    """
    
    retries = 3
    while retries > 0:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
            )
            topic = chat_completion.choices[0].message.content.strip()
            # Clean up topic
            topic = re.sub(r'[^a-zA-Z0-9\s-]', '', topic).strip()
            if not topic:
                topic = "Uncategorized"
            return topic
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                time.sleep(5)
                retries -= 1
            else:
                return "Uncategorized"
    return "Uncategorized"

def process():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    pdf_files = pdf_files[:5] # Limit to 5 PDFs as requested
    
    print(f"Found {len(pdf_files)} PDFs to process.")
    
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
                
                print(f"  Scanning page {page_num+1}/{len(doc)} with EasyOCR...")
                result = ocr_reader.readtext(np.array(img))
                
                # Identify questions and their Y coordinates
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
                            "end_y": img.size[1] # Default to bottom of page
                        }
                    else:
                        if current_q:
                            current_q["text"] += text + " "
                            
                if current_q:
                    questions_data.append(current_q)
                
                print(f"  Found {len(questions_data)} questions on page.")
                
                # Crop and get topics
                for i, q in enumerate(questions_data):
                    print(f"    Processing Q{i+1}...")
                    topic = get_topic_from_groq(q["text"])
                    
                    # Add padding to crop
                    top = max(0, q["start_y"] - 15)
                    bottom = min(img.size[1], q["end_y"] - 5)
                    left = 0
                    right = img.size[0]
                    
                    if bottom <= top:
                        continue # Invalid crop
                        
                    cropped = img.crop((left, top, right, bottom))
                    
                    topic_dir = os.path.join(OUTPUT_DIR, topic)
                    os.makedirs(topic_dir, exist_ok=True)
                    
                    safe_pdf_name = pdf_name.replace(".pdf", "")
                    out_path = os.path.join(topic_dir, f"{safe_pdf_name}_p{page_num+1}_q{i+1}.png")
                    cropped.save(out_path)
                    
        except Exception as e:
            print(f"Error opening {pdf_name}: {e}")

if __name__ == "__main__":
    process()
