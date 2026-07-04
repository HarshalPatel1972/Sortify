import fitz  # PyMuPDF
import re
import os
import json
from typing import List, Dict, Any
from ..models import Question
from PIL import Image
import io
import numpy as np
import easyocr

# Initialize OCR reader once
ocr_reader = None

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

def process_pdf(pdf_path: str, output_dir: str, source_pdf_id: int) -> List[Dict[str, Any]]:
    global ocr_reader
    doc = fitz.open(pdf_path)
    questions_data = []
    
    current_question = None
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Check if page has text
        text_content = page.get_text("text").strip()
        if not text_content:
            if ocr_reader is None:
                ocr_reader = easyocr.Reader(['en'])
                
            # OCR mode
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # easyocr takes numpy array
            result = ocr_reader.readtext(np.array(img))
            
            blocks = []
            scale = 72.0 / 200.0
            
            for item in result:
                bbox_pts = item[0]
                text = item[1]
                prob = item[2]
                
                min_x = min([p[0] for p in bbox_pts])
                min_y = min([p[1] for p in bbox_pts])
                max_x = max([p[0] for p in bbox_pts])
                max_y = max([p[1] for p in bbox_pts])
                
                scaled_bbox = [min_x * scale, min_y * scale, max_x * scale, max_y * scale]
                
                blocks.append({
                    "lines": [{"spans": [{"text": text}]}],
                    "bbox": scaled_bbox
                })
        else:
            blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" not in block:
                continue
                
            block_text = ""
            for line in block["lines"]:
                for span in line["spans"]:
                    block_text += span["text"] + " "
            block_text = block_text.strip()
            
            if not block_text:
                continue
                
            if is_question_start(block_text):
                # Save previous question if exists
                if current_question:
                    _finalize_question(current_question, doc, output_dir, source_pdf_id, len(questions_data))
                    questions_data.append(current_question)
                
                # Start new question
                current_question = {
                    "source_pdf_id": source_pdf_id,
                    "page_start": page_num,
                    "page_end": page_num,
                    "bbox_by_page": {page_num: list(block["bbox"])},
                    "extracted_text": block_text + "\n"
                }
            else:
                if current_question:
                    # Append to current question
                    current_question["page_end"] = page_num
                    if page_num not in current_question["bbox_by_page"]:
                        current_question["bbox_by_page"][page_num] = list(block["bbox"])
                    else:
                        # Union of bounding boxes
                        curr_bbox = current_question["bbox_by_page"][page_num]
                        new_bbox = block["bbox"]
                        current_question["bbox_by_page"][page_num] = [
                            min(curr_bbox[0], new_bbox[0]),
                            min(curr_bbox[1], new_bbox[1]),
                            max(curr_bbox[2], new_bbox[2]),
                            max(curr_bbox[3], new_bbox[3])
                        ]
                    current_question["extracted_text"] += block_text + "\n"
                    
    # Finalize the last question
    if current_question:
        _finalize_question(current_question, doc, output_dir, source_pdf_id, len(questions_data))
        questions_data.append(current_question)
        
    doc.close()
    return questions_data

def _finalize_question(q_data: Dict[str, Any], doc: fitz.Document, output_dir: str, source_pdf_id: int, q_index: int):
    # Render crop for the first page of the question
    page_start = q_data["page_start"]
    bbox = q_data["bbox_by_page"][page_start]
    page = doc[page_start]
    
    # Add a little padding to the bbox
    rect = fitz.Rect(max(0, bbox[0]-5), max(0, bbox[1]-5), min(page.rect.width, bbox[2]+5), min(page.rect.height, bbox[3]+5))
    
    pix = page.get_pixmap(clip=rect, dpi=200)
    image_filename = f"crop_{source_pdf_id}_{q_index}.png"
    image_path = os.path.join(output_dir, image_filename)
    pix.save(image_path)
    
    q_data["crop_image_path"] = image_path
    q_data["bbox_json"] = q_data["bbox_by_page"]
    del q_data["bbox_by_page"] # cleanup
