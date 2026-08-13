# 🤖 Meet Attendance Bot: Control Center

A premium, local Google Meet automation, recording, and real-time attendance monitor. Built with a modern, dark-themed CustomTkinter GUI dashboard, featuring loopback audio recording, local Whisper speech-to-text translation, keyword alarms, phone push notifications, and lecture bookmark snapshots.

---

## ✨ Features

- 🎛️ **Premium CustomTkinter GUI**: Dark-mode dashboard displaying bot engine states, active meeting details, live countdowns, scheduled timetables, setting controls, and a real-time monitor feed.
- 🔊 **Live VU Meter Visualizer**: Dynamic audio level progress bar with a custom decay filter, providing instant visual feedback that loopback audio is capturing properly.
- 🎙️ **Prerequisite-Free Audio Loopback**: Captures digital sound card output directly from Windows without needing a microphone or causing echo.
- 📝 **Faster-Whisper Transcription**: Uses lightweight local Whisper model inference to perform translation chunks with 0 loading delay between lectures (thanks to class-level model caching).
- 🚨 **Mute & Override Controls ("Attendance Marked")**: A one-click override button that instantly silences alarm sounds and blocks subsequent keyword alerts for the remainder of a class session.
- 📱 **Discord Phone Integration**: Connects to a Discord Webhook URL to send pings directly to your mobile phone with active lecture transcripts the moment your name or keywords are detected.
- 📅 **Day-to-Day Scheduler**: Automatically monitors your class schedule, opening Chrome profiles, joining meets early, disabling mics/cameras, and cleanly closing on session ends.
- 💾 **Lecture snapshots ("Bookmark Note")**: A single button on the monitor to capture the last 30 seconds of speech translation, saving it with timestamps inside a formatted local highlights file.

---

## 🛠️ Prerequisites & Installation

### 1. Requirements
Ensure you are running **Python 3.9+** on **Windows** (Windows is required for built-in `winsound` audio alarms, system loopback recording devices, and foreground focus dialogs).

### 2. Setup Repository
Clone or download the project files into your workspace directory.

### 3. Install Dependencies
Install the required packages using pip:
```powershell
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
Initialize Playwright’s browser binaries (Chromium):
```powershell
playwright install chromium
```

---

## ⚙️ Configuration Setup

1. Copy the example configuration template at the root directory:
   ```powershell
   copy config.example.json config.json
   ```
2. Open `config.json` in your favorite editor to edit your parameters:
   * **`user.name`**: Your name (used to greet you or log alerts).
   * **`attendance.keywords`**: List of speech patterns the bot should listen for (e.g., `"attendance"`, your name, your roll number, `"present"`).
   * **`classes`**: Set up your daily subject schedule, day of the week, join times (`HH:MM` in 24h format), and Google Meet links:
     ```json
     "classes": [
       {
         "subject": "Distributed Systems",
         "day": "Wednesday",
         "start": "10:25",
         "end": "11:20",
         "link": "https://meet.google.com/abc-defg-hij"
       }
     ]
     ```

---

## 🚀 Running the Bot

Run the master dashboard script:
```powershell
python main.py
```

### Dashboard Walkthrough:

#### 1. Home Dashboard
* **Start Bot / Stop Bot**: Runs or terminates the scheduler background thread.
* **Join Now / Leave Meeting**: Bypasses the scheduler countdown to immediately force-join the active class link, or gracefully exit the call.
* **Attendance Marked**: Silences any active alarm audio and blocks keyword alerts for the current session. Turns into `"Attendance OK"` once clicked.
* **Audio Level VU**: Fluctuates dynamically based on the speaker's voice in the Google Meet call.

#### 2. Timetable Tab
* Displays your schedule parsed from `config.json` grouped dynamically by day.

#### 3. Settings Tab
* Update your profile parameters, Whisper models (e.g. `tiny`, `base`, `small`, `medium`), device acceleration (`cpu`/`cuda`), and directories directly from the GUI without editing JSON.
* **Discord Integration**: Paste your Discord Channel Webhook URL in the **Discord Webhook URL** field and save settings to receive mobile push pings!

#### 4. Live Monitor Tab
* Shows real-time speech translations, console activity logs, and keyword match alerts.
* **⭐ Bookmark Note**: Instantly snapshots the last few lines of class transcription to `notes/highlights_YYYY-MM-DD.txt`.

---

## 📁 Directory Structure

```text
notes_taker/
├── core/                  # Bot scheduler, listener, recorder, and manager modules
├── ui/                    # CustomTkinter widgets, stylesheet colors, and layouts
├── notes/                 # Saved lecture snapshot bookmarks (.txt)
├── transcripts/           # Full class transcript files saved on session exit
├── recordings/            # Temporary audio files used in processing (.wav)
├── logs/                  # System log files (.log)
├── browser_profile/       # Chrome user profile folder for persisting Google logins
├── config.json            # Local user config (gitignored for credentials safety)
├── config.example.json    # Public configuration template
└── main.py                # Main application entry point
```

---

## 🔐 Security & Privacy
* Your **`config.json`** file and **`browser_profile/`** folder are automatically ignored in `.gitignore`. 
* This prevents your Google cookies, credentials, and private Discord Webhook URLs from ever leaking to GitHub. **Never delete `.gitignore` or upload these folders.**
