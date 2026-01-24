import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load environment variables
load_dotenv()

# 2. Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
IMAGE_PATH = Path("1.jpg")
PROMPT = """
Analyze the provided medical prescription image and extract all visible data. 
Return ONLY a valid JSON object containing the extracted information. 
No markdown, no triple backticks, no explanations.
"""

def test_extraction():
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    if not IMAGE_PATH.exists():
        print(f"❌ Error: Image file not found at {IMAGE_PATH}")
        return

    print(f"🚀 Initializing Gemini Client (Model: {MODEL_NAME})...")
    client = genai.Client(api_key=API_KEY)

    print(f"📷 Reading image: {IMAGE_PATH}...")
    with open(IMAGE_PATH, "rb") as f:
        file_bytes = f.read()

    print("🧠 Sending to Gemini for extraction...")
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=file_bytes, mime_type="image/jpeg"),
                        types.Part.from_text(text=PROMPT),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )

        # Output result
        print("\n✅ Extraction Successful!")
        print("-" * 30)
        json_data = json.loads(response.text)
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
        print("-" * 30)

        # Save to file
        output_file = "extraction_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to {output_file}")

    except Exception as e:
        print(f"❌ Extraction Failed: {str(e)}")

if __name__ == "__main__":
    test_extraction()
