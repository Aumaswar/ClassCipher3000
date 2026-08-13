# Google Meet Attendance Bot Control Center

A professional, local Google Meet automation, recording, and real-time attendance monitoring application. Built with a modern dark-themed CustomTkinter GUI dashboard, this tool features loopback audio recording, local Whisper speech-to-text translation, keyword alarms, mobile push notifications, and lecture bookmark snapshots.

---

## Key Features

- **CustomTkinter GUI Dashboard**: A clean user interface displaying bot status, class details, join window countdowns, schedule timetables, settings controls, and a live transcription monitor feed.
- **Live VU Meter Visualizer**: A real-time audio level indicator utilizing a custom decay filter, providing instant visual feedback on loopback audio capture status.
- **Audio Loopback Capture**: Directly records digital system sound card output from Windows without requiring physical microphone hardware or permissions, eliminating microphone echo.
- **Cached Whisper Transcription**: Employs lightweight, local Whisper model inference to transcribe audio in real-time, utilizing class-level model caching to prevent loading latency between consecutive classes.
- **Mute & Override Controls ("Attendance Marked")**: A manual override feature that silences active alarms and suspends keyword scanning for the remainder of the active class session.
- **Discord Integration**: Pings a designated Discord Webhook URL to deliver real-time notifications directly to your mobile device when attendance keywords are detected.
- **Class Scheduler**: Automatically parses daily class schedules to launch Chrome profiles, disable microphone and camera settings, join meetings, and exit on session completion.
- **Lecture Snippet Snapshot**: A dedicated manual bookmark button to capture the last 30 seconds of transcription and save it with timestamps to local highlight text files.

---

## Prerequisites & Installation

### 1. System Requirements
- Operating System: Windows (required for loopback device drivers, winsound beeps, and foreground dialog popups).
- Python: Version 3.9 or higher.

### 2. Setup Repository & Virtual Environment
Setting up a Python virtual environment is recommended to prevent library conflicts with globally installed packages:
```powershell
# 1. Navigate to the project directory
cd notes_taker

# 2. Create the virtual environment (.venv)
python -m venv .venv

# 3. Activate the virtual environment
.venv\Scripts\activate
```

### 3. Install Dependencies
Ensure your virtual environment is active (indicated by `(.venv)` in your terminal prompt) and install the packages:
```powershell
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
Initialize Playwright’s browser binaries inside the virtual environment:
```powershell
playwright install chromium
```

---

## Configuration Setup

1. Copy the example configuration template at the root directory:
   ```powershell
   copy config.example.json config.json
   ```
2. Open `config.json` to edit your parameters:
   * **`user.name`**: Your name (used for logging and notifications).
   * **`attendance.keywords`**: List of phrases the bot monitors (e.g. your name, roll number, or keywords like `"attendance"`, `"present"`).
   * **`classes`**: Set up your daily schedule, days of the week, class times (24h format), and meeting links:
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

## Operating the Application

Launch the main controller script:
```powershell
python main.py
```

### Page Walkthroughs:

#### 1. Home Dashboard
- **Start Bot / Stop Bot**: Runs or terminates the background schedule worker.
- **Join Now / Leave Meeting**: Bypasses countdowns to force-join the active class link, or exit the current call.
- **Attendance Marked**: Silences audio alarms and mutes notifications for the active class session.
- **Audio Level**: Real-time VU meter displaying speaker audio capture.

#### 2. Timetable Tab
- Displays your configured classes grouped by the day of the week.

#### 3. Settings Tab
- Update paths, model configurations (e.g., `tiny`, `base`, `small`, `medium`), device parameters (`cpu`/`cuda`), and directories.
- **Discord Integration**: Input your channel webhook URL to enable phone push pings.

#### 4. Live Monitor Tab
- Displays the active speech transcript, activity logs, and keyword match alerts.
- **Bookmark Note**: Saves the last 5 lines of the transcript to `notes/highlights_YYYY-MM-DD.txt`.

---

## Directory Structure

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

## Security & Privacy
Your **`config.json`** file and **`browser_profile/`** directories are automatically registered in **`.gitignore`**. This prevents active session cookies and private Discord webhook tokens from being committed to public repositories. Always keep these directories gitignored.
