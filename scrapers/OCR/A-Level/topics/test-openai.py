"""Quick test to see if OpenAI API is working"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

openai_key = os.getenv('OPENAI_API_KEY')

if openai_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        print("Testing OpenAI connection...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10,
            timeout=30
        )
        print(f"✅ SUCCESS: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("\nThis confirms OpenAI connectivity issues from your machine.")
else:
    print("No OpenAI key found")

