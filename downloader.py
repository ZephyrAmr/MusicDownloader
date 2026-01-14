import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import yt_dlp
import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

HISTORY_FILE = "history.json"
CONFIG_FILE = "config.json"
MAX_CONCURRENT_DOWNLOADS = 3

class ConfigManager:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def get(self, key, default=None):
        return self.config.get(key, default)
        
    def set(self, key, value):
        self.config[key] = value
        self.save_config()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.title("Spotify Settings")
        self.geometry("400x250")
        self.resizable(False, False)
        
        ttk.Label(self, text="Spotify API Credentials", font=("Segoe UI", 12, "bold")).pack(pady=10)
        ttk.Label(self, text="Required for reliable playlist fetching.", font=("Segoe UI", 9)).pack()
        ttk.Label(self, text="Get them at developer.spotify.com", font=("Segoe UI", 8, "italic"), foreground="blue", cursor="hand2").pack(pady=(0, 10))
        
        form_frame = ttk.Frame(self, padding=10)
        form_frame.pack(fill=tk.X)
        
        ttk.Label(form_frame, text="Client ID:").pack(anchor=tk.W)
        self.client_id = tk.StringVar(value=config.get("spotify_client_id", ""))
        ttk.Entry(form_frame, textvariable=self.client_id, width=40).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(form_frame, text="Client Secret:").pack(anchor=tk.W)
        self.client_secret = tk.StringVar(value=config.get("spotify_client_secret", ""))
        ttk.Entry(form_frame, textvariable=self.client_secret, show="*", width=40).pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def save(self):
        self.config.set("spotify_client_id", self.client_id.get().strip())
        self.config.set("spotify_client_secret", self.client_secret.get().strip())
        messagebox.showinfo("Saved", "Settings saved!")
        self.destroy()

class HistoryManager:
    def __init__(self):
        self.history = []
        self.load_history()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def add_entry(self, entry):
        # Entry: {date, title, url, format, path}
        self.history.insert(0, entry)
        self.save_history()

    def save_history(self):
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=4)

    def clear(self):
        self.history = []
        self.save_history()

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced YouTube Downloader")
        self.root.geometry("900x600")
        
        # Data
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()
        self.download_queue = [] # List of active download objects/dicts
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS)
        self.task_counters = 0
        
        # Style
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", rowheight=25)

        # UI Layout
        self.create_widgets()
        
        # Periodic update for queue management if needed (mostly event driven though)

    def create_widgets(self):
        # Top Bar for Settings
        top_bar = ttk.Frame(self.root, padding=5)
        top_bar.pack(fill=tk.X)
        ttk.Button(top_bar, text="Spotify Settings", command=self.open_settings).pack(side=tk.RIGHT, padx=5)

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        # Tab 1: Downloads
        self.tab_downloads = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_downloads, text="  Downloads  ")
        self.setup_downloads_tab()

        # Tab 2: History
        self.tab_history = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_history, text="  History  ")
        self.setup_history_tab()
    
    def open_settings(self):
        SettingsDialog(self.root, self.config_manager)

    def setup_downloads_tab(self):
        # -- Top Input Section --
        input_frame = ttk.Frame(self.tab_downloads, padding="10")
        input_frame.pack(fill=tk.X)
        
        # Row 1: URL
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="URL:").pack(side=tk.LEFT)
        self.url_var = tk.StringVar()
        entry = ttk.Entry(row1, textvariable=self.url_var)
        entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Row 2: Options
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X)

        # Format Selector
        ttk.Label(row2, text="Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="mp4")
        ttk.Radiobutton(row2, text="Video (MP4)", variable=self.format_var, value="mp4").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row2, text="Audio (MP3)", variable=self.format_var, value="mp3").pack(side=tk.LEFT, padx=5)
        
        # Folder Name Input
        ttk.Separator(row2, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        ttk.Label(row2, text="Save to Folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(row2, textvariable=self.folder_var, width=15)
        folder_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="(Optional)", foreground="gray").pack(side=tk.LEFT)

        # Add Button
        btn_add = ttk.Button(row2, text="Add to Queue", command=self.add_to_queue)
        btn_add.pack(side=tk.RIGHT, padx=10)

        # -- Active Downloads List --
        list_frame = ttk.Labelframe(self.tab_downloads, text="Queue & Active Downloads", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        cols = ("ID", "Title", "Folder", "Progress", "Status", "Speed")
        self.tree_active = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        
        self.tree_active.heading("ID", text="ID")
        self.tree_active.column("ID", width=40, anchor="center")
        
        self.tree_active.heading("Title", text="Title/URL")
        self.tree_active.column("Title", width=250)
        
        self.tree_active.heading("Folder", text="Folder")
        self.tree_active.column("Folder", width=80, anchor="center")
        
        self.tree_active.heading("Progress", text="Progress")
        self.tree_active.column("Progress", width=80, anchor="center")
        
        self.tree_active.heading("Status", text="Status")
        self.tree_active.column("Status", width=120, anchor="center")
        
        self.tree_active.heading("Speed", text="Speed")
        self.tree_active.column("Speed", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree_active.yview)
        self.tree_active.configure(yscroll=scrollbar.set)
        
        self.tree_active.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_history_tab(self):
        # -- Toolkit Bar --
        tool_frame = ttk.Frame(self.tab_history, padding="10")
        tool_frame.pack(fill=tk.X)

        ttk.Button(tool_frame, text="Refresh", command=self.refresh_history_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(tool_frame, text="Open Downloads Folder", command=self.open_downloads_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(tool_frame, text="Clear History", command=self.clear_history).pack(side=tk.RIGHT, padx=5)

        # -- History List --
        hist_frame = ttk.Frame(self.tab_history, padding="10")
        hist_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Date", "Title", "Format", "Path")
        self.tree_history = ttk.Treeview(hist_frame, columns=cols, show="headings", selectmode="browse")

        self.tree_history.heading("Date", text="Date")
        self.tree_history.column("Date", width=150)
        
        self.tree_history.heading("Title", text="Title")
        self.tree_history.column("Title", width=400)
        
        self.tree_history.heading("Format", text="Format")
        self.tree_history.column("Format", width=80, anchor="center")

        self.tree_history.heading("Path", text="Location")
        self.tree_history.column("Path", width=200)

        scrollbar = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self.tree_history.yview)
        self.tree_history.configure(yscroll=scrollbar.set)

        self.tree_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_history_ui()

    def add_to_queue(self):
        url = self.url_var.get().strip()
        fmt = self.format_var.get()
        folder_name = self.folder_var.get().strip()
        
        # Basic sanitization for folder name
        if folder_name:
            folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
            
        # Check if Spotify
        if "spotify.com" in url:
            # Handle Spotify in a separate thread/task
            self.task_counters += 1
            task_id = str(self.task_counters)
            display_folder = folder_name if folder_name else "root"
            self.tree_active.insert("", "end", iid=task_id, values=(task_id, "Parsing Spotify Playlist...", display_folder, "0%", "Resolving", "-"))
            
            # Start resolution task
            threading.Thread(target=self.resolve_spotify_playlist, args=(task_id, url, fmt, folder_name), daemon=True).start()
            self.url_var.set("")
            return

        # Normal YouTube flow
        self.task_counters += 1
        task_id = str(self.task_counters)
        
        display_folder = folder_name if folder_name else "root"
        self.tree_active.insert("", "end", iid=task_id, values=(task_id, url, display_folder, "0%", "Queued", "-"))
        
        # Clear entry (Optional: keep folder name so user can add multiple to same folder easily?)
        # Let's keep the folder name, clear only URL
        self.url_var.set("")
        
        # Submit to thread pool
        self.executor.submit(self.download_task, task_id, url, fmt, folder_name)

    def resolve_spotify_playlist(self, task_id, url, fmt, folder_name):
        try:
            from spotapi import Public
            self.update_task(task_id, status="Connecting to SpotAPI...")
            
            # Extract ID
            obj_id = ""
            obj_type = ""
            if "playlist" in url:
                obj_id = url.split("playlist/")[1].split("?")[0]
                obj_type = "playlist"
            elif "album" in url:
                obj_id = url.split("album/")[1].split("?")[0]
                obj_type = "album"
            elif "track" in url:
                obj_id = url.split("track/")[1].split("?")[0]
                obj_type = "track"
            
            tracks = []
            
            if obj_type == "playlist":
                self.update_task(task_id, status="Fetching Playlist...")
                for chunk in Public.playlist_info(obj_id):
                    # Data is typically in 'items' for spotapi
                    # Structure: items -> [ { itemV2: { data: { name, artists: { items: [ { profile: { name } } ] } } } } ]
                    items_list = chunk.get('items')
                    
                    if items_list:
                        for item in items_list:
                             try:
                                 data = item.get('itemV2', {}).get('data', {})
                                 if not data: continue
                                 
                                 name = data.get('name')
                                 
                                 # Artist logic
                                 artist_str = "Unknown"
                                 artists_container = data.get('artists', {})
                                 if 'items' in artists_container:
                                     first_artist = artists_container['items'][0]
                                     # Sometimes it's under 'profile', sometimes direct?
                                     # Debug showed: items[0]['profile']['name']
                                     profile = first_artist.get('profile')
                                     if profile:
                                         artist_str = profile.get('name')
                                     else:
                                         # fallback if structure varies
                                         artist_str = first_artist.get('name', 'Unknown')
                                         
                                 if name:
                                     tracks.append(f"{artist_str} - {name}")
                             except:
                                 continue

                    self.update_task(task_id, status=f"Found {len(tracks)} songs...")
            
            elif obj_type == "album":
                 # Fallback/Pending
                 self.update_task(task_id, status="Error", speed="Album support pending")
                 raise Exception("SpotAPI: Albums not fully supported yet.")

            elif obj_type == "track":
                 self.update_task(task_id, status="Error", speed="Track support pending")
                 raise Exception("SpotAPI: Single tracks not fully supported yet.")
            
            if not tracks:
                raise Exception("No tracks found.")

            self.update_task(task_id, status=f"Queuing {len(tracks)} songs...", progress="100%")
            
            self.root.after(1000, lambda: self.tree_active.delete(task_id))

            for i, track in enumerate(tracks):
                if not track.strip(): continue
                search_query = f"ytsearch1:{track}"
                self.root.after(i*50, lambda q=search_query, f=folder_name, fm=fmt: self.queue_spotify_track(q, f, fm))

        except Exception as e:
            err_msg = str(e)
            print(f"SpotAPI Error: {err_msg}")
            self.update_task(task_id, status="Error", speed=err_msg[:25])

    def queue_spotify_track(self, query, folder_name, fmt):
        self.task_counters += 1
        tid = str(self.task_counters)
        
        display_name = query.replace("ytsearch1:", "")
        display_folder = folder_name if folder_name else "root"
        
        self.tree_active.insert("", "end", iid=tid, values=(tid, display_name, display_folder, "0%", "Queued", "-"))
        self.executor.submit(self.download_task, tid, query, fmt, folder_name)

    def download_task(self, task_id, url, fmt, folder_name):
        try:
            self.update_task(task_id, status="Initializing...")
            
            # Determine path
            base_dir = os.path.join(os.getcwd(), 'downloads')
            if folder_name:
                download_dir = os.path.join(base_dir, folder_name)
            else:
                download_dir = base_dir
                
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

            ydl_opts = {
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'ignoreerrors': True,
                'progress_hooks': [lambda d: self.progress_hook(task_id, d)],
                'noplaylist': False,
            }

            if fmt == 'mp3':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                ydl_opts.update({'format': 'bestvideo+bestaudio/best'})

            info = {}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            self.update_task(task_id, progress="100%", status="Completed", speed="-")
            
            # Add to history
            title = info.get('title', 'Unknown Title') if info else url
            entry = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "title": title,
                "url": url,
                "format": fmt,
                "path": download_dir
            }
            self.history_manager.add_entry(entry)
            self.root.after(0, self.refresh_history_ui)

        except Exception as e:
            err_msg = str(e)
            if "ffmpeg" in err_msg.lower():
                err_msg = "Extract Audio Error (FFmpeg missing?)"
            self.update_task(task_id, status="Error", speed=err_msg)

    def progress_hook(self, task_id, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '').replace('%','')
            speed = d.get('_speed_str', '')
            status = "Downloading"
            
            self.root.after(0, lambda: self.update_task(task_id, progress=p+"%", status=status, speed=speed))
            
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.update_task(task_id, status="Processing...", progress="100%"))

    def update_task(self, task_id, **kwargs):
        # Must run on main thread
        try:
            curr_values = self.tree_active.item(task_id)['values']
            if not curr_values: return 
            
            # curr_values is a tuple (ID, Title, Folder, Progress, Status, Speed)
            new_values = list(curr_values)
            
            if 'title' in kwargs: new_values[1] = kwargs['title']
            # Folder is index 2, we don't update it dynamically usually
            if 'progress' in kwargs: new_values[3] = kwargs['progress']
            if 'status' in kwargs: new_values[4] = kwargs['status']
            if 'speed' in kwargs: new_values[5] = kwargs['speed']
            
            self.tree_active.item(task_id, values=new_values)
        except:
            pass

    def refresh_history_ui(self):
        # Clear current list
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
            
        # Re-populate
        for item in self.history_manager.history:
            self.tree_history.insert("", "end", values=(
                item.get('date'), 
                item.get('title'), 
                item.get('format'), 
                item.get('path')
            ))

    def clear_history(self):
        if messagebox.askyesno("Confirm", "Clear download history?"):
            self.history_manager.clear()
            self.refresh_history_ui()

    def open_downloads_folder(self):
        download_dir = os.path.join(os.getcwd(), 'downloads')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        os.startfile(download_dir)

if __name__ == "__main__":
    root = tk.Tk()
    # High DPI aware
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = DownloaderApp(root)
    root.mainloop()
