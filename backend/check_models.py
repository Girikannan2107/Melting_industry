import os
import requests

# Load from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("✅ YOUR KEY HAS ACCESS TO THESE MODELS:")
    for model in data.get('models', []):
        # We only care about models that support generating content
        if 'generateContent' in model.get('supportedGenerationMethods', []):
            print(f" - {model['name'].replace('models/', '')}")
else:
    print("❌ ERROR:", response.json())