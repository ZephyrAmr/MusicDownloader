# MusicDownloader 🎵

A powerful and user-friendly desktop application to download music and videos from **YouTube** and **Spotify**.

## ✨ Features
- **YouTube Support**: Download Videos (MP4) or Audio (MP3).
- **Spotify Support**: Download entire Playlists seamlessly (no API keys required!).
- **Queue System**: Process multiple downloads in the background.
- **History**: Keep track of your downloads.
- **Auto-meta**: Automatically adds metadata to downloaded files.

## 🛠️ Requirements

To run this application, an end-user needs:

1.  **Windows OS** (Recommended for the provided batch launcher).
2.  **Python 3.10+**: [Download Here](https://www.python.org/downloads/).
    *   *Make sure to check "Add Python to PATH" during installation.*
3.  **FFmpeg**: Required for MP3 conversion.
    *   Download `ffmpeg.exe` and `ffprobe.exe` (from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)) and place them in the project folder.
    *   *(Alternatively, install them system-wide and add to PATH).*

## 🚀 Installation & Setup

1.  **Clone the valid repo**:
    ```bash
    git clone https://github.com/ZephyrAmr/MusicDownloader.git
    cd MusicDownloader
    ```

2.  **Install Dependencies**:
    Open a terminal in the folder and run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **FFmpeg Check**:
    Ensure `ffmpeg.exe` and `ffprobe.exe` are in the same folder as `downloader.py`.

## ▶️ How to Run

Simply double-click **`start.bat`** to launch the application.

*Or run via command line:*
```bash
python downloader.py
```

## 📝 Usage
1.  Paste a **YouTube Video/Playlist** OR **Spotify Playlist** URL.
2.  Select Format (**MP3** or **MP4**).
3.  (Optional) Type a folder name to organize downloads.
4.  Click **Add to Queue**.

---
*Note: This tool is for educational purposes only. Please respect copyright laws in your jurisdiction.*
