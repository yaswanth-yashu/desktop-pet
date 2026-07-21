import os
import sys
import json
from PySide6.QtCore import QCoreApplication, QUrl, QTimer, Slot, QByteArray
from PySide6.QtWebSockets import QWebSocket

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

class DiagnosticClient(QWebSocket):
    def __init__(self, api_key, model_name):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self.connected.connect(self.on_connected)
        self.disconnected.connect(self.on_disconnected)
        self.textMessageReceived.connect(self.on_message)
        self.binaryMessageReceived.connect(self.on_binary_message)
        self.errorOccurred.connect(self.on_error)
        
        # Open connection
        url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={self.api_key}"
        print(f"Connecting to: {url[:100]}...")
        self.open(QUrl(url))

    @Slot()
    def on_connected(self):
        print("\n[SUCCESS] Connected to Gemini Live WebSocket!")
        print(f"Socket State: {self.state().name}")
        
        # 1. Send Minimal Setup message only
        setup_msg = {
            "setup": {
                "model": self.model_name,
                "generationConfig": {
                    "responseModalities": ["AUDIO"]
                }
            }
        }
        payload = json.dumps(setup_msg)
        print(f"Sending minimal setup payload for model: {self.model_name}...")
        sent_bytes = self.sendTextMessage(payload)
        print(f"Bytes written by sendTextMessage: {sent_bytes} (payload len: {len(payload)})")

    @Slot()
    def on_disconnected(self):
        print(f"\n[INFO] Disconnected from WebSocket. Close Code: {self.closeCode()}, Reason: {self.closeReason()}")
        QCoreApplication.quit()

    @Slot(QByteArray)
    def on_binary_message(self, message):
        print(f"\n[RECEIVED BINARY] Got binary message of size {len(message)}")
        try:
            text = bytes(message).decode("utf-8")
            print("Decoded binary to text:")
            self.on_message(text)
        except Exception as e:
            print(f"Failed to decode binary message: {e}")

    @Slot(str)
    def on_message(self, message):
        try:
            data = json.loads(message)
            keys = list(data.keys())
            print(f"\n[RECEIVED] Message keys: {keys}")
            
            # Check for setupComplete
            if "setupComplete" in data or "setup_complete" in data:
                print("\n--> [SUCCESS] Server setup complete! Sending greeting text now...")
                greeting_msg = {
                    "clientContent": {
                        "turns": [
                            {
                                "role": "user",
                                "parts": [
                                    {
                                        "text": "Hello there! Introduce yourself as EVE and say hello."
                                    }
                                ]
                            }
                        ],
                        "turnComplete": True
                    }
                }
                payload = json.dumps(greeting_msg)
                sent_bytes = self.sendTextMessage(payload)
                print(f"Sent greeting bytes: {sent_bytes}")
                return

            # Check for serverContent
            sc = data.get("serverContent") or data.get("server_content")
            if sc:
                print(f"  * serverContent keys: {list(sc.keys())}")
                if sc.get("interrupted"):
                    print("  * [Interrupted]")
                model_turn = sc.get("modelTurn")
                if model_turn:
                    parts = model_turn.get("parts", [])
                    for part in parts:
                        text = part.get("text")
                        if text:
                            print(f"  * Transcription: {text}")
                        inline_data = part.get("inlineData")
                        if inline_data:
                            audio_data_len = len(inline_data.get("data", ""))
                            print(f"  * Audio data chunk received: {audio_data_len} base64 chars")
                if sc.get("turnComplete"):
                    print("  * [Turn Complete]")
            
            # Check for toolCall
            tc = data.get("toolCall") or data.get("tool_call")
            if tc:
                print(f"  * toolCall payload: {tc}")

        except Exception as e:
            print(f"Failed to parse server message: {e}")

    @Slot(object)
    def on_error(self, error):
        print(f"\n[ERROR] WebSocket Error: {error}")
        QCoreApplication.quit()

def main():
    app = QCoreApplication(sys.argv)
    env = load_env()
    api_key = env.get("GEMINI_API_KEY")
    model_name = env.get("GEMINI_MODEL", "models/gemini-2.5-flash-native-audio-latest")
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return
        
    client = DiagnosticClient(api_key, model_name)
    
    # Timeout after 15 seconds
    QTimer.singleShot(15000, lambda: (print("\nDiagnostic finished (15s timeout). Exiting."), QCoreApplication.quit()))
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
