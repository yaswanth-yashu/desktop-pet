import os
import json
import urllib.request

def load_env():
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def main():
    env = load_env()
    api_key = env.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file.")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    print(f"Querying models list from: https://generativelanguage.googleapis.com/v1beta/models")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        models = data.get("models", [])
        print("\nAll available models:")
        for m in models:
            name = m.get("name")
            display_name = m.get("displayName")
            methods = m.get("supportedGenerationMethods", [])
            print(f"- {name} ({display_name})")
            
        print("\nModels supporting Live API (bidiGenerateContent):")
        live_models = []
        for m in models:
            name = m.get("name")
            display_name = m.get("displayName")
            methods = m.get("supportedGenerationMethods", [])
            if "bidiGenerateContent" in methods:
                print(f"  * {name} ({display_name})")
                live_models.append(name)
                
        if not live_models:
            print("  (None found. Note: some preview models might not expose bidiGenerateContent in their methods list metadata, but still support it).")
            
    except Exception as e:
        print(f"Error querying API: {e}")

if __name__ == "__main__":
    main()
