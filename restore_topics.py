import json
import os
import time
from groq import Groq

GROQ_KEYS = [
    os.environ.get("GROQ_API_KEY", "your_groq_api_key_1"),
    os.environ.get("GROQ_API_KEY_2", "your_groq_api_key_2"),
    os.environ.get("GROQ_API_KEY_3", "your_groq_api_key_3")
]
groq_client = Groq(api_key=GROQ_KEYS[0])

TOPICS = [
    "Classical Mechanics", "Atomic Physics", "Quantum Mechanics", "Electromagnetic Theory", 
    "Solid State Physics", "Nuclear Physics", "Thermodynamics", "Statistical Mechanics", 
    "Wave and Oscillation", "Optics", "Mathematical Physics", "Electronics", 
    "Modern Physics", "Superconductivity", "Semiconductor Physics"
]

file_path = 'data/json_results/all_questions.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get all questions that are "Modern Physics" (as it was the fallback)
target_qs = [q for q in data if q.get('topic') == 'Modern Physics']
print(f"Found {len(target_qs)} questions to reclassify.")

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

batches = list(chunker(target_qs, 20))
print(f"Total batches: {len(batches)}")

key_idx = 0
for i, batch in enumerate(batches):
    print(f"Processing batch {i+1}/{len(batches)}...")
    
    prompt = f"""
    You are an expert Physics professor. I will give you a JSON array of {len(batch)} question objects. 
    Each object has an "id" and a "text".
    Your job is to determine the best matching topic for EACH question from this EXACT list of 15 topics:
    {', '.join(TOPICS)}
    
    Return ONLY a JSON array of objects with "id" and "topic". EXACTLY {len(batch)} objects. 
    Do NOT return markdown backticks (like ```json), just raw JSON.
    
    Input JSON:
    """
    
    input_json = [{"id": q["id"], "text": q["question_text"][:350]} for q in batch]
    prompt += json.dumps(input_json)
    
    retries = 3
    while retries > 0:
        try:
            resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            out_text = resp.choices[0].message.content.strip()
            if out_text.startswith("```json"): out_text = out_text[7:]
            if out_text.startswith("```"): out_text = out_text[3:]
            if out_text.endswith("```"): out_text = out_text[:-3]
            
            results = json.loads(out_text.strip())
            
            # Map back
            for res in results:
                for q in target_qs:
                    if q["id"] == res["id"]:
                        assigned = res.get("topic", "Modern Physics")
                        # Validate
                        if assigned in TOPICS:
                            q["topic"] = assigned
            break
        except Exception as e:
            print(f"Error on batch {i+1}: {e}")
            if "429" in str(e).lower() or "rate limit" in str(e).lower():
                key_idx = (key_idx + 1) % len(GROQ_KEYS)
                groq_client = Groq(api_key=GROQ_KEYS[key_idx])
                print(f"Switched to key {key_idx}.")
            time.sleep(2)
            retries -= 1

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
print("Done reclassifying!")
