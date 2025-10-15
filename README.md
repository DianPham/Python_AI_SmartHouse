# Smart Home Voice Assistant
**An intelligent home automation system integrating speech, computer vision, and contextual reasoning for daily assistance.**

---

## Overview
This project provides a **smart home automation system** designed to enhance convenience and accessibility for users through natural voice interaction and adaptive behavior learning.  
The assistant can handle **voice commands**, **respond with speech**, and **interact with physical devices**.  
It also learns user behavior patterns via object tracking to provide smarter and more personalized responses.

---

## Key Features
- 🎙️ **Voice Interaction:** Vietnamese speech recognition, wake word detection, and text-to-speech responses.  
- 🧠 **Intelligent Understanding:** Contextual command interpretation using Rasa NLU.  
- 🧩 **Behavior Learning:** Object tracking and activity detection via YOLO and DeepSORT.  
- ⚙️ **Home Control:** Manage lights, music, and other connected devices.  
- 🗺️ **Location Awareness:** Vietnamese geographic database for localized responses.  

---

## Technical Summary
### 🧱 Models and Frameworks
| Component | Model / Tool | Description |
|------------|---------------|-------------|
| **Speech-to-Text (STT)** | PhoWhisper | Fine-tuned for Vietnamese accents |
| **Text-to-Speech (TTS)** | Viettel TTS | Generates natural Vietnamese speech responses |
| **Wakeword Detection** | Porcupine | Activates system on wake phrase |
| **Language Understanding** | Rasa NLU | Extracts user intent and entities |
| **Object Tracking** | YOLOv8 + DeepSORT | Learns behavior from user activity |

### 🧩 Customizations
- Fine-tuned **PhoWhisper** model for niche Vietnamese accents using collected data.  
- Extended Rasa’s knowledge base for Vietnamese commands and multi-turn conversations.  
- Integrated YOLOv8 and DeepSORT pipelines for visual learning.

---

## System Architecture (Simplified)

```
WakeWord → PhoWhisper_Server (STT) → Rasa Agent → Action Server → Smart Device / Feedback
                                       ↗ 
            Object Tracking (YOLO + DeepSORT)
```

- **WakeWord:** Activates the system upon keyword detection.  
- **PhoWhisper Server:** Receives audio and returns transcription.  
- **Rasa Agent:** Interprets command intent and routes to proper action.  
- **Object Tracking:** Monitors user activity to send suitable responses.  
- **VoiceAssistant:** Executes commands and provides spoken feedback.

---

## Project Structure (Simplified)
```
.
├── main.py
├── requirements.txt
├── geo/                 # Vietnamese geographic dataset
├── Object Tracking/     # YOLO + DeepSORT modules
├── PhoWhisper_Server/   # Speech recognition API
├── VoiceAssistant/      # Core Rasa NLU assistant logic
├── WakeWord/            # Wakeword detection module
├── Process_Data_File/   # Tools for preparing training data
├── Test/                # Evaluation and experimental scripts
└── audio.wav            # Sample input
```

Each module works as an independent component communicating through internal triggers or APIs.

---

## Installation & Setup

### 🧰 Prerequisites
- Python 3.9+  
- `pip` and virtual environment recommended  
- GPU (optional) for YOLO-based tracking

### ⚙️ Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/DianPham/Python_AI_SmartHouse.git
cd Python_AI_SmartHouse

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start PhoWhisper server
cd PhoWhisper_Server
python init_server.py

# 4. Start Rasa agent
cd VoiceAssistant/Rasa
rasa run --enable-api --cors "*"

# 5. Run wakeword detection
cd WakeWord
python ww_interact.py
```

---

## How to Use

1. Ensure **PhoWhisper server**, **Rasa agent**, and **Wakeword** modules are running.  
2. Say the defined wakeword to activate the assistant.  
3. Give voice commands such as:  
   - “Turn on the lights.”  
   - “Play Rising.mp3.”  
   - “What’s on my calendar today?”  
4. The system will process, respond, and execute the corresponding action.  

---

## Example Workflow
```
[Wakeword detected] → Capture user audio
→ Send to PhoWhisper_Server → Get transcription
→ Rasa interprets command → Trigger action or response
→ Output speech via Viettel TTS
→ (Optional) Object tracking monitors environment
```

---

## Results and Performance
- Fine-tuned PhoWhisper improved WER by ~8% on Vietnamese speech.  
- Smooth wakeword detection and command processing with minimal latency.  
- Successful home device interactions (music, light control, calendar, email).  
- Integrated object tracking for adaptive behavior learning.

---

## Folder Highlights

- **VoiceAssistant/Rasa/** — Command interpretation and response logic.  
- **PhoWhisper_Server/** — STT model server with custom logging.  
- **WakeWord/** — Porcupine wakeword model and interaction scripts.  
- **Object Tracking/** — Behavior analysis using YOLOv8 + DeepSORT.  
- **Process_Data_File/** — Tools for cleaning and preparing voice datasets.  
- **Test/** — Component-specific evaluation scripts.

---

## Team & Credits
- **Dian Pham** — Project Lead, System Architect, AI Integration  
- **Van-Hai Ha** — Object Tracking, Data Preprocessing, Debugging  
- **Phuc-Dat Nguyen** — Object Tracking, Testing, Reporting

---

## License & Ethics
- For **educational and research use** only.  
- Respect licenses of third-party models and APIs.  
- Handle user data ethically and comply with privacy standards.

---

## Contact
**Dian Pham** — dianpham.ai@gmail.com  
GitHub: [DianPham](https://github.com/DianPham)
