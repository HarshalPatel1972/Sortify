import os
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_topic_pdf(topic_name: str, questions: List[Dict[str, Any]], output_path: str):
    """
    Generates a PDF for a given topic containing images of the questions.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title Page
    title = Paragraph(f"<b>Topic: {topic_name}</b>", styles['Title'])
    subtitle = Paragraph(f"Total Questions: {len(questions)}", styles['Heading2'])
    story.append(title)
    story.append(Spacer(1, 20))
    story.append(subtitle)
    story.append(Spacer(1, 50))
    
    # Process each question
    for idx, q in enumerate(questions):
        story.append(Paragraph(f"<b>Question {idx + 1}</b> (Source: PDF ID {q['source_pdf_id']}, Page {q['page_start']})", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        # Load image and scale
        img_path = q["crop_image_path"]
        if os.path.exists(img_path):
            try:
                img = Image(img_path)
                
                # Scale image to fit width (max ~450)
                max_width = 450
                if img.drawWidth > max_width:
                    scale = max_width / float(img.drawWidth)
                    img.drawWidth = max_width
                    img.drawHeight = img.drawHeight * scale
                
                story.append(img)
            except Exception as e:
                story.append(Paragraph(f"<i>Error loading image: {e}</i>", styles['Normal']))
        else:
            story.append(Paragraph("<i>Image not found</i>", styles['Normal']))
            
        story.append(Spacer(1, 30))
        
    doc.build(story)
