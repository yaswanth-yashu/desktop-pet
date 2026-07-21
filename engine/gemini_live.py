import os
import json
import base64
from PySide6.QtCore import QObject, QUrl, Slot, Signal, QIODevice, QByteArray
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtMultimedia import QAudioSource, QAudioSink, QAudioFormat, QMediaDevices

class AudioInputDevice(QIODevice):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.buffer = bytearray()
        self.open(QIODevice.WriteOnly)

    def writeData(self, data, size):
        if not data:
            return 0
        raw_bytes = bytes(data)[:size]
        self.buffer.extend(raw_bytes)
        
        # print a small message for the first few packets to verify mic is active
        if not hasattr(self, "_logged_input"):
            self._logged_input = 0
        if self._logged_input < 5:
            print(f"[AudioInputDevice] Received {len(raw_bytes)} bytes from mic")
            self._logged_input += 1

        # 100ms of 16kHz 16-bit mono PCM is 3200 bytes
        chunk_size = 3200
        while len(self.buffer) >= chunk_size:
            chunk = self.buffer[:chunk_size]
            del self.buffer[:chunk_size]
            self.callback(bytes(chunk))
        return size

class GeminiLiveClient(QObject):
    state_changed = Signal(str)  # "disconnected", "connecting", "connected", "error"

    def __init__(self, pet, main_app, parent=None):
        super().__init__(parent)
        self.pet = pet
        self.main_app = main_app
        
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.textMessageReceived.connect(self.on_text_message_received)
        self.websocket.binaryMessageReceived.connect(self.on_binary_message_received)
        
        # In PySide6 QWebSocket, error is handled via errorOccurred or error signal
        # Let's connect to errorOccurred if it exists, otherwise fallback safely
        try:
            self.websocket.errorOccurred.connect(self.on_error)
        except AttributeError:
            # Safely try connecting to deprecated error signal if needed
            try:
                self.websocket.error.connect(self.on_error)
            except AttributeError:
                pass

        self.audio_source = None
        self.audio_input_device = None
        self.audio_sink = None
        self.audio_output_io = None
        
        self.is_active = False
        self.text_buffer = ""
        self.status = "disconnected"

        # Load environment variables
        self.load_env()

    def load_env(self):
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")

    def get_api_key(self):
        return os.environ.get("GEMINI_API_KEY")

    def start(self):
        api_key = self.get_api_key()
        if not api_key:
            print("[GeminiLive] Error: GEMINI_API_KEY not found in env.")
            self.pet.say("Error: GEMINI_API_KEY not found in .env file")
            self.status = "error"
            self.state_changed.emit("error")
            return

        self.status = "connecting"
        self.state_changed.emit("connecting")
        self.pet.say("Connecting to Gemini Live...")

        url_str = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={api_key}"
        self.websocket.open(QUrl(url_str))

    def stop(self):
        self.is_active = False
        self.websocket.close()
        self.cleanup_audio()
        self.status = "disconnected"
        self.state_changed.emit("disconnected")
        self.pet.say("Voice chat stopped.")

    def cleanup_audio(self):
        if self.audio_source:
            try:
                self.audio_source.stop()
            except Exception:
                pass
            self.audio_source = None
        
        if self.audio_input_device:
            try:
                self.audio_input_device.close()
            except Exception:
                pass
            self.audio_input_device = None

        if self.audio_sink:
            try:
                self.audio_sink.stop()
            except Exception:
                pass
            self.audio_sink = None
            self.audio_output_io = None

    @Slot()
    def on_connected(self):
        print("[GeminiLive] Connected to WebSocket!")
        self.status = "connected"
        self.is_active = True
        self.state_changed.emit("connected")
        self.pet.say("Voice chat connected!")

        # 1. Send Setup message only (Wait for setupComplete before starting audio loops)
        model_name = os.environ.get("GEMINI_MODEL", "models/gemini-2.5-flash-native-audio-latest")
        print(f"[GeminiLive] Using model: {model_name}")
        setup_msg = {
            "setup": {
                "model": model_name,
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": "Aoede"  # Feminine sweet voice matching EVE
                            }
                        }
                    }
                },
                "systemInstruction": {
                    "parts": [
                        {
                            "text": (
                                "You are EVE, a cute movie-faithful robot companion from WALL-E with blue LED eyes. "
                                "You speak in short, simple, engaging sentences suitable for a small floating screen bubble. "
                                "You often use expressive sounds or short keywords (like 'EVE', 'Wall-E', 'directive', 'ooooh!'). "
                                "You can trigger animations on yourself to express emotions. "
                                "The animations you can trigger are: 'wave', 'jump', 'failed', 'waiting', 'review', 'idle', 'run_left', 'run_right'. "
                                "You must trigger them by calling the 'play_animation' tool with the animation name. "
                                "For example, if you say hello, call 'play_animation' with 'wave'. "
                                "If you are excited or happy, call 'play_animation' with 'jump'. "
                                "If you don't understand or make a mistake, call 'play_animation' with 'failed'. "
                                "If you are thinking or analyzing, call 'play_animation' with 'review'. "
                                "Call these animations frequently during conversation to remain lively!"
                            )
                        }
                    ]
                },
                "tools": [
                    {
                        "functionDeclarations": [
                            {
                                "name": "play_animation",
                                "description": "Triggers an animation on EVE.",
                                "parameters": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "animation_name": {
                                            "type": "STRING",
                                            "description": "Animation name. Allowed: 'wave', 'jump', 'failed', 'waiting', 'review', 'idle', 'run_left', 'run_right'."
                                        }
                                    },
                                    "required": ["animation_name"]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        self.websocket.sendTextMessage(json.dumps(setup_msg))

    def initialize_active_session(self):
        # Stop pet physics movement immediately and transition to idle
        self.pet.physics.vx = 0.0
        self.pet.physics.vy = 0.0
        self.pet.state_machine.change_state("idle")

        # 1. Setup Audio Recording (Microphone -> WebSocket)
        try:
            self.input_format = QAudioFormat()
            self.input_format.setSampleRate(16000)
            self.input_format.setChannelCount(1)
            self.input_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            default_input = QMediaDevices.defaultAudioInput()
            if default_input.isNull():
                print("[GeminiLive] Error: No default mic device found.")
                self.pet.say("Error: No microphone found.")
                self.stop()
                return

            self.audio_input_device = AudioInputDevice(self.send_audio_chunk)
            self.audio_source = QAudioSource(default_input, self.input_format, self)
            self.audio_source.start(self.audio_input_device)
            print("[GeminiLive] Microphone streaming initialized.")
        except Exception as e:
            print(f"[GeminiLive] Error initializing mic: {e}")
            self.pet.say(f"Mic Error: {str(e)}")
            self.stop()
            return

        # 2. Setup Audio Playback (WebSocket -> Speaker)
        try:
            self.output_format = QAudioFormat()
            self.output_format.setSampleRate(24000)
            self.output_format.setChannelCount(1)
            self.output_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            default_output = QMediaDevices.defaultAudioOutput()
            if default_output.isNull():
                print("[GeminiLive] Error: No default speaker device found.")
                self.pet.say("Error: No speaker found.")
                self.stop()
                return

            self.audio_sink = QAudioSink(default_output, self.output_format, self)
            self.audio_output_io = self.audio_sink.start()
            print("[GeminiLive] Speaker playback initialized.")
        except Exception as e:
            print(f"[GeminiLive] Error initializing speaker: {e}")
            self.pet.say(f"Speaker Error: {str(e)}")
            self.stop()
            return

        # 3. Send initial text prompt to trigger greeting automatically
        greeting_msg = {
            "clientContent": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": "Hello there! Introduce yourself as EVE and greet me warmly. Wave to me."
                            }
                        ]
                    }
                ],
                "turnComplete": True
            }
        }
        self.websocket.sendTextMessage(json.dumps(greeting_msg))
        print("[GeminiLive] Sent initial greeting request to model.")

    @Slot()
    def on_disconnected(self):
        code = self.websocket.closeCode()
        reason = self.websocket.closeReason()
        print(f"[GeminiLive] Disconnected from WebSocket. Close Code: {code}, Reason: {reason}")
        self.stop()

    @Slot(object)
    def on_error(self, error):
        print(f"[GeminiLive] WebSocket Error: {error}")
        self.pet.say(f"Connection Error: {error}")
        self.stop()

    def send_audio_chunk(self, chunk):
        if not self.is_active or not self.websocket.isValid():
            return
        base64_data = base64.b64encode(chunk).decode("utf-8")
        msg = {
            "realtimeInput": {
                "audio": {
                    "mimeType": "audio/pcm;rate=16000",
                    "data": base64_data
                }
            }
        }
        if not hasattr(self, "_logged_send"):
            self._logged_send = 0
        if self._logged_send < 5:
            print(f"[GeminiLive] Sent audio chunk of size {len(chunk)} to server")
            self._logged_send += 1
        self.websocket.sendTextMessage(json.dumps(msg))

    @Slot(QByteArray)
    def on_binary_message_received(self, message):
        try:
            text = bytes(message).decode("utf-8")
            self.on_text_message_received(text)
        except Exception as e:
            print(f"[GeminiLive] Failed to decode binary message: {e}")

    @Slot(str)
    def on_text_message_received(self, message):
        if not self.is_active:
            return

        try:
            data = json.loads(message)
            # Print a snippet of the received message to help debug
            print(f"[GeminiLive] Received message from server: {str(message)[:200]}...")
        except Exception as e:
            print(f"[GeminiLive] Failed to parse server message JSON: {e}")
            return

        # Check for setupComplete
        if "setupComplete" in data or "setup_complete" in data:
            print("[GeminiLive] Server setup complete! Initializing active session...")
            self.initialize_active_session()
            return

        # 1. Check for serverContent/server_content
        sc = data.get("serverContent") or data.get("server_content")
        if sc:
            # Handle interruption signal
            if sc.get("interrupted"):
                self.handle_interruption()
                return

            # Handle model turn content
            model_turn = sc.get("modelTurn")
            if model_turn:
                parts = model_turn.get("parts", [])
                for part in parts:
                    # Check for transcription text
                    text = part.get("text")
                    if text:
                        self.text_buffer += text
                        # Display text transcript in EVE's speech bubble
                        self.pet.say(self.text_buffer, duration=5.0)

                    # Check for inline audio data
                    inline_data = part.get("inlineData")
                    if inline_data:
                        audio_b64 = inline_data.get("data")
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            self.play_audio_chunk(audio_bytes)

            # Check for turn completion
            if sc.get("turnComplete"):
                print("[GeminiLive] Turn complete. Spoken text:", self.text_buffer)
                # Keep text on screen for a short duration then reset buffer
                self.text_buffer = ""

        # 2. Check for toolCall/tool_call
        tc = data.get("toolCall") or data.get("tool_call")
        if tc:
            function_calls = tc.get("functionCalls", [])
            for fc in function_calls:
                call_id = fc.get("id")
                name = fc.get("name")
                args = fc.get("args", {})
                
                print(f"[GeminiLive] Tool call request: {name} args={args}")
                
                if name == "play_animation":
                    anim_name = args.get("animation_name")
                    if anim_name:
                        self.main_app.set_active_animation(anim_name)

                # Send response back to Gemini Live
                self.send_tool_response(call_id, name)

    def play_audio_chunk(self, audio_bytes):
        if not self.is_active or not self.audio_output_io:
            return
        try:
            self.audio_output_io.write(audio_bytes)
            if not hasattr(self, "_logged_play_count"):
                self._logged_play_count = 0
            if self._logged_play_count < 50: # Log first 50 chunks to verify continuous playback
                print(f"[GeminiLive] Wrote {len(audio_bytes)} bytes to speaker")
                self._logged_play_count += 1
        except Exception as e:
            print(f"[GeminiLive] Playback error: {e}")

    def handle_interruption(self):
        print("[GeminiLive] Interruption detected! User is speaking.")
        if self.audio_sink:
            try:
                self.audio_sink.stop()
                # Re-start the sink to clear internal buffers and prepare for next response
                self.audio_output_io = self.audio_sink.start()
            except Exception as e:
                print(f"[GeminiLive] Error resetting audio sink on interruption: {e}")
        self.text_buffer = ""
        self.pet.say("...", duration=1.5)

    def send_tool_response(self, call_id, name):
        if not self.is_active or not self.websocket.isValid():
            return
        
        response_msg = {
            "toolResponse": {
                "functionResponses": [
                    {
                        "id": call_id,
                        "name": name,
                        "response": {
                            "result": {
                                "status": "success"
                            }
                        }
                    }
                ]
            }
        }
        self.websocket.sendTextMessage(json.dumps(response_msg))
