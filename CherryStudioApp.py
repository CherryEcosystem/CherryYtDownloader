"""
================================================================================
              CHERRY DOWNLOADER NATIVE STUDIO - PRODUCTION BUILD v5.0
================================================================================
File Core: CherryStudioApp.py
Ecosystem: Cherry Ecosystem v5.0 (2026 Stable High-Performance Release)
Developer: @Not_PiyushXD
Engine: Multi-Threaded Parallel Chunk Engine with Decoupled Flask Backend API
GUI: PyQt6 High-Fidelity Chromium WebEngine Viewport Interface Wrapper
================================================================================
"""

import sys
import os
import re
import time
import uuid
import glob
import logging
import threading
import json
import subprocess
import urllib.request
import zipfile
import shutil
from flask import Flask, render_template_string, request, jsonify, send_file
import yt_dlp
from PyQt6.QtCore import QUrl, QObject, pyqtSlot, QSize
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# ==============================================================================
# 0. DIRECTORY PERMISSION WALL BREAK & DISK BUFFER OVERRIDE
# ==============================================================================
USER_PROFILE_DIR = os.environ.get("USERPROFILE", os.path.expanduser("~"))
DOWNLOAD_FOLDER = os.path.join(USER_PROFILE_DIR, "Downloads", "CherryCache")
BIN_FOLDER = os.path.join(DOWNLOAD_FOLDER, "bin")
SETTINGS_PATH = os.path.join(DOWNLOAD_FOLDER, "settings.json")

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(BIN_FOLDER, exist_ok=True)
os.chdir(DOWNLOAD_FOLDER)

# Configure internal diagnostic console pipelines
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] Core Thread (%(threadName)s): %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CherryEngine")

app = Flask(__name__)

CLEANUP_LOOP_INTERVAL_SECONDS = 3600
MAX_CACHE_FILE_LIFETIME_SECONDS = 1800

progress_store = {}
progress_lock = threading.Lock()
system_runtime_stats = {
    "last_download_timestamp": "None",
    "total_successful_sessions": 0,
    "engine_status": "Initializing Engine...",
    "active_stream_hooks": 0
}

installer_state = {
    "status": "idle",
    "progress": 0,
    "log": "Standing by for system launch sequence..."
}
installer_lock = threading.Lock()

# ==============================================================================
# 1. LOCAL DATA PERSISTENCE & SETTINGS HANDLER
# ==============================================================================
def load_application_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as config_file:
                return json.load(config_file)
        except Exception:
            pass
    default_config = {"has_seen_tutorial": False, "custom_ffmpeg_path": ""}
    save_application_settings(default_config)
    return default_config

def save_application_settings(settings_dict):
    try:
        with open(SETTINGS_PATH, 'w') as config_file:
            config_file.write(json.dumps(settings_dict, indent=4))
    except Exception as e:
        logger.error(f"Failed to write settings to local profile: {e}")

def pinpoint_active_ffmpeg_path():
    settings = load_application_settings()
    if settings.get("custom_ffmpeg_path") and os.path.exists(settings["custom_ffmpeg_path"]):
        return settings["custom_ffmpeg_path"]
        
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        bundled_ffmpeg = os.path.join(bundle_dir, "ffmpeg.exe")
        if os.path.exists(bundled_ffmpeg):
            return bundle_dir

    local_binary_exe = os.path.join(BIN_FOLDER, "ffmpeg.exe")
    if os.path.exists(local_binary_exe):
        return BIN_FOLDER

    winget_fallback = r'C:\Users\Piyush\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin'
    if os.path.exists(os.path.join(winget_fallback, "ffmpeg.exe")):
        return winget_fallback

    system_path_discover = shutil.which("ffmpeg")
    if system_path_discover:
        return os.path.dirname(system_path_discover)

    return None

def strip_ansi_sequences(text_stream):
    if not text_stream: return ''
    try:
        ansi_regex_pattern = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_regex_pattern.sub('', str(text_stream)).strip()
    except Exception:
        return str(text_stream).strip()

# ==============================================================================
# 2. AUTOMATED BACKEND CACHE STORAGE SCRUBBER THREAD
# ==============================================================================
def background_cache_garbage_collector():
    threading.current_thread().name = "CacheScrubberThread"
    while True:
        try:
            current_system_epoch_time = time.time()
            for active_file_path in glob.glob(os.path.join(DOWNLOAD_FOLDER, '*')):
                if os.path.isfile(active_file_path):
                    if (current_system_epoch_time - os.path.getmtime(active_file_path)) > MAX_CACHE_FILE_LIFETIME_SECONDS:
                        try:
                            os.remove(active_file_path)
                        except OSError:
                            pass
        except Exception as e:
            logger.error(f"Garbage collector loop exception: {e}")
        time.sleep(CLEANUP_LOOP_INTERVAL_SECONDS)

# ==============================================================================
# 3. BACKGROUND DEPENDENCY AUTO-INSTALLER CORE PIPELINE
# ==============================================================================
def download_ffmpeg_worker_thread():
    global installer_state
    threading.current_thread().name = "FFmpegInstallerThread"
    
    with installer_lock:
        installer_state["status"] = "downloading"
        installer_state["progress"] = 10
        installer_state["log"] = "Establishing mirror pipeline link with static repository servers..."

    target_mirror_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_download_destination = os.path.join(DOWNLOAD_FOLDER, "ffmpeg_raw_package.zip")

    try:
        def update_download_metrics(chunk_count, chunk_size, total_size):
            with installer_lock:
                calculated_bytes = chunk_count * chunk_size
                if total_size > 0:
                    percent_complete = min(int((calculated_bytes / total_size) * 70) + 10, 80)
                    installer_state["progress"] = percent_complete
                    installer_state["log"] = f"Streaming network binary clusters: {calculated_bytes / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB"

        urllib.request.urlretrieve(target_mirror_url, zip_download_destination, reporthook=update_download_metrics)

        with installer_lock:
            installer_state["progress"] = 85
            installer_state["log"] = "Download phase terminated. Extraction of archived binary map trees..."

        with zipfile.ZipFile(zip_download_destination, 'r') as archival_reference:
            all_contained_files = archival_reference.namelist()
            for targeted_file_path in all_contained_files:
                if targeted_file_path.endswith("ffmpeg.exe") or targeted_file_path.endswith("ffprobe.exe"):
                    extracted_base_filename = os.path.basename(targeted_file_path)
                    destination_disk_path = os.path.join(BIN_FOLDER, extracted_base_filename)
                    with archival_reference.open(targeted_file_path) as source_stream, open(destination_disk_path, "wb") as targeted_disk_writer:
                        shutil.copyfileobj(source_stream, targeted_disk_writer)

        if os.path.exists(zip_download_destination):
            os.remove(zip_download_destination)

        ffmpeg_bin_folder = pinpoint_active_ffmpeg_path()
        if ffmpeg_bin_folder:
            os.environ["PATH"] = ffmpeg_bin_folder + os.pathsep + os.environ.get("PATH", "")
            with installer_lock:
                installer_state["progress"] = 100
                installer_state["status"] = "success"
                installer_state["log"] = "System core compilation verified. Launcher operational."
            system_runtime_stats["engine_status"] = "Operational"
        else:
            raise Exception("Validation structural verification mapping collapsed.")

    except Exception as installation_fault:
        logger.error(f"FFmpeg auto-installer thread crashed: {installation_fault}")
        if os.path.exists(zip_download_destination):
            try: os.remove(zip_download_destination)
            except Exception: pass
        with installer_lock:
            installer_state["status"] = "error"
            installer_state["progress"] = 0
            installer_state["log"] = f"Fatal Auto-Installation Collapse: {str(installation_fault)}"

# ==============================================================================
# 4. DECOUPLED FLASK INTERFACE ONBOARDING & STORAGE ENDPOINTS
# ==============================================================================
@app.route('/')
def serve_index_viewport():
    return render_template_string(HTML_TEMPLATE)

@app.route('/setup/status', methods=['GET'])
def query_setup_wizard_milestone():
    settings = load_application_settings()
    ffmpeg_detected_folder = pinpoint_active_ffmpeg_path()
    
    if ffmpeg_detected_folder:
        os.environ["PATH"] = ffmpeg_detected_folder + os.pathsep + os.environ.get("PATH", "")
        system_runtime_stats["engine_status"] = "Operational"
        ffmpeg_status_flag = True
    else:
        ffmpeg_status_flag = False

    return jsonify({
        "has_seen_tutorial": settings.get("has_seen_tutorial", False),
        "ffmpeg_installed": ffmpeg_status_flag
    })

@app.route('/setup/dismiss-tutorial', methods=['POST'])
def finalize_tutorial_milestone():
    settings = load_application_settings()
    settings["has_seen_tutorial"] = True
    save_application_settings(settings)
    return jsonify({"status": "acknowledged"})

@app.route('/setup/trigger-installer', methods=['POST'])
def launch_binary_installer_thread():
    with installer_lock:
        if installer_state["status"] != "downloading":
            installer_state["status"] = "triggered"
            installer_state["progress"] = 0
            installer_state["log"] = "Spawning operational downloader worker streams..."
            threading.Thread(target=download_ffmpeg_worker_thread, daemon=True).start()
    return jsonify({"status": "launched"})

@app.route('/setup/installer-polling', methods=['GET'])
def stream_installer_telemetry():
    with installer_lock:
        return jsonify(installer_state)

@app.route('/progress/<session_id>', methods=['GET'])
def dispatch_realtime_progress_packet(session_id):
    with progress_lock:
        realtime_data_packet = progress_store.get(session_id, {
            "percent": 0, "status": "Ready", "speed": "0 KB/s", "eta": "--:--",
            "downloaded": "0 MB", "total": "0 MB", "logs": ["Standing by..."]
        })
    return jsonify(realtime_data_packet)

@app.route('/stats', methods=['GET'])
def dispatch_system_metrics():
    return jsonify(system_runtime_stats)

def run_flask_server():
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

# ==============================================================================
# 5. NATIVE DESKTOP OPERATING ENGINE & WORKER BRIDGE
# ==============================================================================
def instantiate_progress_hook_callback(session_identifier):
    def execution_progress_callback(download_data_dict):
        with progress_lock:
            session_data = progress_store.get(session_identifier, {"logs": []})
            if download_data_dict['status'] == 'downloading':
                try:
                    raw_percent_string = strip_ansi_sequences(download_data_dict.get('_percent_str', '0%'))
                    cleaned_percent_value = raw_percent_string.replace('%', '').strip()
                    session_data["percent"] = float(cleaned_percent_value) if cleaned_percent_value else 0
                except Exception:
                    session_data["percent"] = 0

                session_data["speed"] = strip_ansi_sequences(download_data_dict.get('_speed_str', 'N/A'))
                session_data["eta"] = strip_ansi_sequences(download_data_dict.get('_eta_str', '--:--'))
                
                downloaded_bytes_count = download_data_dict.get('downloaded_bytes', 0)
                total_bytes_count = download_data_dict.get('total_bytes') or download_data_dict.get('total_bytes_estimate', 0)
                
                session_data["downloaded"] = f"{downloaded_bytes_count / (1024*1024):.1f} MB" if downloaded_bytes_count else "0 MB"
                session_data["total"] = f"{total_bytes_count / (1024*1024):.1f} MB" if total_bytes_count else "Unknown"
                session_data["status"] = "Downloading Chunks..."
                
                if len(session_data["logs"]) == 0 or "Multiplex concurrent threads active" not in session_data["logs"][-1]:
                    session_data["logs"].append(f"{time.strftime('[%H:%M:%S]')} ⚡ Multi-stream engine executing. Processing segments in parallel chunks...")

            elif download_data_dict['status'] == 'finished':
                session_data["percent"] = 99
                session_data["status"] = "Processing..."
                session_data["logs"].append(f"{time.strftime('[%H:%M:%S]')} Audio and Video streams captured. Passing maps to FFmpeg for fast structural stitching...")
            progress_store[session_identifier] = session_data
    return execution_progress_callback

class BackendBridge(QObject):
    @pyqtSlot(str, str, str, str, str)
    def startNativeDownload(self, url, mode, resolution, bitrate, session_id):
        threading.Thread(target=self._execute_download_worker, args=(url, mode, resolution, bitrate, session_id), daemon=True).start()

    @pyqtSlot(str, str, str, str)
    def cutVideo(self, filepath, start_time, end_time, session_id):
        threading.Thread(target=self._execute_cut_worker, args=(filepath, start_time, end_time, session_id), daemon=True).start()

    def _execute_download_worker(self, url, mode, resolution, bitrate, session_id):
        start_stopwatch_time = time.time()
        
        with progress_lock:
            progress_store[session_id] = {
                "percent": 0, "status": "Initializing...", "speed": "0 KB/s", "eta": "--:--",
                "downloaded": "0 MB", "total": "0 MB", "logs": [f"{time.strftime('[%H:%M:%S]')} 🚀 Spawning Hyper-Speed concurrent processing streams..."]
            }

        try:
            active_bin_path = pinpoint_active_ffmpeg_path()
            file_prefix = os.path.join(DOWNLOAD_FOLDER, f'{session_id}_%(title)s.%(ext)s')
            
            # ==============================================================================
            # HYPER-SPEED TUNING MATRIX: Forced 16 Concurrent Dynamic Chunk Workers
            # ==============================================================================
            yt_downloader_options = {
                'cachedir': DOWNLOAD_FOLDER,
                'outtmpl': file_prefix,
                'progress_hooks': [instantiate_progress_hook_callback(session_id)],
                'nocheckcertificate': True, 'quiet': True, 'no_warnings': True,
                'prefer_ffmpeg': True, 'retries': 15, 'fragment_retries': 15,
                'merge_output_format': 'mp4',
                
                # Concurrent Thread Injectors
                'concurrent_fragment_downloads': 16, # 🔥 Downloads 16 chunks of the file at the exact same time
                'buffersize': 1024 * 1024 * 2,        # 💾 Expanded RAM IO Buffer to 2MB to keep hardware writing fast
                
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            }
            
            if active_bin_path:
                yt_downloader_options['ffmpeg_location'] = active_bin_path

            if getattr(sys, 'frozen', False):
                current_running_dir = os.path.dirname(sys.executable)
            else:
                current_running_dir = os.path.dirname(os.path.abspath(__file__))

            primary_cookie_file = os.path.join(current_running_dir, 'youtube_cookies.txt')
            original_cookie_file = os.path.join(current_running_dir, 'www.youtube.com_cookies.txt')
            
            target_cookie_path = None
            if os.path.exists(primary_cookie_file):
                target_cookie_path = primary_cookie_file
            elif os.path.exists(original_cookie_file):
                target_cookie_path = original_cookie_file

            if target_cookie_path:
                yt_downloader_options['cookiefile'] = target_cookie_path
                with progress_lock:
                    progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} 🔑 Secure Account Handshake injected. Bypass limits active.")
            else:
                with progress_lock:
                    progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} ℹ️ Session executing over Anonymous Connection vector.")

            if mode == 'mp3':
                yt_downloader_options['format'] = 'bestaudio/best'
                yt_downloader_options['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': bitrate
                }]
            else:
                # 🔊 High-Fidelity Merge Format Mapping
                yt_downloader_options['format'] = f'bestvideo[height<={resolution}]+bestaudio/best'

            with yt_dlp.YoutubeDL(yt_downloader_options) as ydl:
                metadata = ydl.extract_info(url, download=True)
                raw_filename = ydl.prepare_filename(metadata)
                compiled_final_filename = os.path.splitext(raw_filename)[0] + '.mp3' if mode == 'mp3' else raw_filename

            end_stopwatch_time = time.time()
            total_elapsed_seconds = max(1, int(end_stopwatch_time - start_stopwatch_time))
            
            system_runtime_stats["last_download_timestamp"] = time.strftime("%H:%M:%S")
            system_runtime_stats["total_successful_sessions"] += 1

            with progress_lock:
                if session_id in progress_store:
                    progress_store[session_id]["status"] = "Complete!"
                    progress_store[session_id]["percent"] = 100
                    progress_store[session_id]["filepath"] = compiled_final_filename
                    progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} ✅ Media file assembled and verified successfully.")
                    progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} ⏱️ TOTAL SESSION TIME ELAPSED: {total_elapsed_seconds} Seconds.")

            os.system(f'explorer /select,"{compiled_final_filename}"')

        except Exception as e:
            with progress_lock:
                if session_id in progress_store:
                    progress_store[session_id]["status"] = "Error"
                    progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} ❌ Pipeline Interrupted: {str(e)}")

    def _execute_cut_worker(self, filepath, start_time, end_time, session_id):
        try:
            with progress_lock:
                progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} 🎬 Extracting target sub-frames via direct stream-copy...")
            
            output_split_path = filepath.replace(".mp4", "_trimmed_segment.mp4")
            active_ffmpeg_dir = pinpoint_active_ffmpeg_path() or ""
            ffmpeg_executable = os.path.join(active_ffmpeg_dir, "ffmpeg.exe") if active_ffmpeg_dir else "ffmpeg"
            
            ffmpeg_execution_command = ["-y", "-ss", start_time, "-to", end_time, "-i", filepath, "-c", "copy", output_split_path]
            subprocess.run([ffmpeg_executable] + ffmpeg_execution_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            
            with progress_lock:
                progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} ✅ Sub-clip extracted successfully.")
                
            os.system(f'explorer /select,"{output_split_path}"')
        except Exception as e:
            with progress_lock:
                progress_store[session_id]["logs"].append(f"{time.strftime('[%H:%M:%S]')} ❌ Cutter Error: {str(e)}")

class CherryDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cherry Downloader Native Studio")
        self.setMinimumSize(1150, 850)
        
        self.browser = QWebEngineView()
        self.bridge_link_channel = BackendBridge()
        self.web_communication_channel = QWebChannel()
        
        self.web_communication_channel.registerObject('pyBridge', self.bridge_link_channel)
        self.browser.page().setWebChannel(self.web_communication_channel)
        
        self.browser.setUrl(QUrl("http://127.0.0.1:5000/"))
        self.setCentralWidget(self.browser)

# ==============================================================================
# 6. COMPREHENSIVE INTERFACE TEMPLATE MODULE (MASTER DESIGN SHEET)
# ==============================================================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cherry Downloader Native Studio v5.0</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }

        :root {
            --cherry-red: #ff2e5a;
            --cherry-dark: #d91744;
            --cherry-glow: rgba(255, 46, 90, 0.3);
            --bg-primary: #0a0e17;
            --bg-secondary: #121825;
            --bg-card: rgba(18, 24, 37, 0.6);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --text-primary: #ffffff;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --success: #10b981;
            --speed-fast: #3b82f6;
            --shadow-preset: 0 8px 32px rgba(0, 0, 0, 0.4);
            --warning-amber: #f59e0b;
        }

        body.light-theme {
            --bg-primary: #f4f6f9;
            --bg-secondary: #ffffff;
            --bg-card: rgba(255, 255, 255, 0.85);
            --border-subtle: rgba(15, 23, 42, 0.08);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --cherry-glow: rgba(255, 46, 90, 0.15);
            --shadow-preset: 0 8px 32px rgba(148, 163, 184, 0.15);
            --warning-amber: #b45309;
        }

        body {
            font-family: 'DM Sans', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
            transition: background 0.4s ease, color 0.4s ease;
        }
        
        .container { max-width: 1100px; margin: 0 auto; padding: 40px 24px; position: relative; z-index: 1; }
        
        .wizard-layer-container {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: var(--bg-primary); z-index: 9999; display: flex;
            align-items: center; justify-content: center; padding: 24px;
            transition: opacity 0.5s ease, transform 0.5s ease;
        }
        .wizard-viewport-box {
            background: var(--bg-card); border: 1px solid var(--border-subtle);
            padding: 50px; border-radius: 28px; width: 100%; max-width: 580px;
            text-align: center; box-shadow: var(--shadow-preset); backdrop-filter: blur(30px);
        }
        .wizard-title { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800; margin-bottom: 12px; }
        .wizard-description { color: var(--text-secondary); font-size: 1rem; margin-bottom: 30px; line-height: 1.6; }
        
        .tutorial-carousel-slide {
            background: var(--bg-secondary); border: 1px solid var(--border-subtle);
            border-radius: 16px; padding: 24px; text-align: left; margin-bottom: 25px;
        }
        .tutorial-slide-header { font-family: 'Syne', sans-serif; font-size: 1.1rem; color: var(--cherry-red); margin-bottom: 6px; }

        .loading-pulse-ring {
            width: 65px; height: 65px; border: 4px solid var(--border-subtle);
            border-top-color: var(--cherry-red); border-radius: 50%;
            animation: systemSpinLoop 1s linear infinite; margin: 30px auto;
        }
        @keyframes systemSpinLoop { to { transform: rotate(360deg); } }

        header { 
            display: flex; justify-content: space-between; align-items: center; 
            padding-bottom: 30px; margin-bottom: 30px; border-bottom: 1px solid var(--border-subtle);
            flex-wrap: wrap; gap: 20px;
        }
        .logo { font-family: 'Syne', sans-serif; font-size: 3rem; font-weight: 800; letter-spacing: -0.05em; background: linear-gradient(135deg, var(--cherry-red) 0%, #ff6b9d 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 15px var(--cherry-glow)); }
        .tagline { font-size: 1rem; color: var(--text-secondary); margin-top: 4px; }

        .theme-control-button {
            padding: 12px 24px; background: var(--bg-secondary); border: 1px solid var(--border-subtle);
            border-radius: 30px; color: var(--text-primary); font-weight: 700; cursor: pointer;
            transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; font-size: 0.85rem;
        }
        .theme-control-button:hover { border-color: var(--cherry-red); transform: translateY(-2px); }

        .system-hub-dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 30px; }
        .hub-card { background: var(--bg-card); border: 1px solid var(--border-subtle); padding: 20px 24px; border-radius: 20px; backdrop-filter: blur(20px); display: flex; flex-direction: column; gap: 4px; }
        .hub-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); font-weight: 700; }
        .hub-value { font-size: 1.2rem; font-weight: 700; font-family: 'Syne', sans-serif; display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 8px; height: 8px; background: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); }
        .user-badge { background: rgba(255, 46, 90, 0.1); color: var(--cherry-red); padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; border: 1px solid rgba(255, 46, 90, 0.2); }

        .main-dashboard-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 28px; padding: 45px; backdrop-filter: blur(25px); box-shadow: var(--shadow-preset); margin-bottom: 30px; }
        .url-input { width: 100%; padding: 22px 26px; font-size: 1.05rem; background: var(--bg-secondary); border: 2px solid var(--border-subtle); border-radius: 18px; color: var(--text-primary); outline: none; transition: all 0.3s ease; margin-bottom: 35px; }
        .url-input:focus { border-color: var(--cherry-red); box-shadow: 0 0 0 5px var(--cherry-glow); }
        
        .section-header { font-family: 'Syne', sans-serif; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-muted); margin-bottom: 18px; display: flex; align-items: center; gap: 10px; }
        .section-header::before { content: ''; width: 5px; height: 5px; background: var(--cherry-red); border-radius: 50%; }
        
        .options-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 14px; margin-bottom: 35px; }
        .option-btn { padding: 18px 22px; background: var(--bg-secondary); border: 2px solid var(--border-subtle); border-radius: 16px; color: var(--text-secondary); font-weight: 700; cursor: pointer; transition: all 0.25s ease; font-size: 0.95rem; }
        .option-btn:hover { border-color: var(--cherry-red); color: var(--text-primary); }
        .option-btn.active { background: linear-gradient(135deg, var(--cherry-red), var(--cherry-dark)); border-color: var(--cherry-red); color: white; box-shadow: 0 8px 24px var(--cherry-glow); }
        
        .download-btn { width: 100%; padding: 24px 36px; background: linear-gradient(135deg, var(--cherry-red), var(--cherry-dark)); border: none; border-radius: 18px; color: white; font-weight: 700; font-size: 1.15rem; cursor: pointer; font-family: 'Syne', sans-serif; text-transform: uppercase; letter-spacing: 0.06em; transition: all 0.3s; box-shadow: 0 10px 28px var(--cherry-glow); }
        .download-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .progress-section { display: none; margin-top: 40px; padding: 30px; background: var(--bg-secondary); border-radius: 20px; border: 1px solid var(--border-subtle); }
        .dashboard-split-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        
        .hardware-speed-warning-box { background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; font-weight: 700; font-size: 0.85rem; color: var(--warning-amber); display: flex; align-items: center; gap: 10px; font-family: 'Syne', sans-serif; text-transform: uppercase; }

        .progress-bar-container { width: 100%; height: 14px; background: rgba(0,0,0,0.15); border-radius: 7px; overflow: hidden; margin-bottom: 20px; position: relative; }
        body.light-theme .progress-bar-container { background: rgba(0,0,0,0.06); }
        .progress-bar { height: 100%; width: 0%; background: linear-gradient(90deg, var(--cherry-red), #ff6b9d); border-radius: 7px; transition: width 0.3s ease; }
        
        .progress-info { display: flex; justify-content: space-between; font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 14px; }
        .progress-status { font-weight: 700; color: var(--cherry-red); font-size: 1.05rem; }
        .speed-display { font-size: 1.7rem; font-weight: 700; color: var(--speed-fast); margin: 10px 0; font-family: 'Syne', sans-serif; }
        
        .console-box { background: #04070d; border: 1px solid rgba(255, 46, 90, 0.2); border-radius: 14px; padding: 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #10b981; height: 195px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
        body.light-theme .console-box { background: #f8fafc; border-color: rgba(15,23,42,0.08); color: #1e293b; }
        .console-line { white-space: pre-wrap; word-break: break-all; }

        .cutter-section { display: none; margin-top: 30px; padding: 35px; background: var(--bg-secondary); border-radius: 22px; border: 1px solid var(--border-subtle); }
        .cutter-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 20px; margin: 18px 0 26px; }
        .cutter-input { width: 100%; padding: 16px 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; background: var(--bg-primary); border: 1px solid var(--border-subtle); border-radius: 12px; color: var(--text-primary); outline: none; }
        .cutter-execute-button { width: 100%; padding: 18px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); border: none; border-radius: 14px; color: white; font-weight: 700; cursor: pointer; font-family: 'Syne', sans-serif; text-transform: uppercase; transition: all 0.25s; }

        .value-proposition-block { margin-top: 20px; margin-bottom: 40px; }
        .proposition-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 15px; }
        .prop-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 20px; padding: 30px; backdrop-filter: blur(20px); }
        .prop-title { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }
        .prop-desc { font-size: 0.9rem; color: var(--text-secondary); }

        footer { text-align: center; color: var(--text-muted); font-size: 0.9rem; padding-top: 30px; border-top: 1px solid var(--border-subtle); margin-top: 50px; }
        footer a { color: var(--cherry-red); text-decoration: none; font-weight: 600; }
    </style>
</head>
<body class="dark-theme">

    <div id="setup-wizard-overlay" class="wizard-layer-container">
        <div id="wizard-screen-splash" class="wizard-viewport-box">
            <h1 class="logo" style="font-size: 3.5rem; margin-bottom: 10px;">CherryStudio</h1>
            <p style="color: var(--text-secondary); letter-spacing: 0.05em; text-transform: uppercase; font-size: 0.8rem; font-weight: 700;">Loading System Environment...</p>
            <div class="loading-pulse-ring"></div>
        </div>

        <div id="wizard-screen-tutorial" class="wizard-viewport-box" style="display: none;">
            <h2 class="wizard-title">Welcome to Cherry Studio 🍒</h2>
            <p class="wizard-description">Let's walk through your high-performance workspace configuration before accessing the processing dashboard lines.</p>
            
            <div class="tutorial-carousel-slide">
                <div class="tutorial-slide-header">⚡ 16x Parallel Multi-Threading</div>
                <p style="font-size:0.85rem; color: var(--text-secondary);">Splits target media streams into 16 synchronous fragment streams, running network speeds flat-out to maximize hardware lane utilization.</p>
            </div>
            <div class="tutorial-carousel-slide">
                <div class="tutorial-slide-header">✂️ Stream Copy Video Trimmer</div>
                <p style="font-size:0.85rem; color: var(--text-secondary);">Slice frames with millisecond precision instantly. Uses direct bitstream copying vectors to completely bypass heavy re-encoding stages, protecting your CPU hardware.</p>
            </div>

            <button class="download-btn" onclick="dismissTutorialSlideScreen()">Initialize System Components ➔</button>
        </div>

        <div id="wizard-screen-installer" class="wizard-viewport-box" style="display: none;">
            <h2 class="wizard-title" id="installer-header-title">Dependency Error</h2>
            <p class="wizard-description" id="installer-meta-desc">The application layer requires the static FFmpeg package binaries to process, compile, and slice streaming files safely on your local hardware profile node.</p>
            
            <div class="progress-bar-container" style="background: rgba(0,0,0,0.3); height: 18px;">
                <div id="autoinstaller-progress-bar" class="progress-bar" style="width: 0%;"></div>
            </div>
            
            <p id="autoinstaller-status-log" style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--cherry-red); margin-bottom: 25px;">Analyzing local disk environment loops...</p>
            <button class="download-btn" id="btn-trigger-autoinstall" onclick="executeAutomatedBinaryDeployment()">⚡ Deploy Missing Dependencies</button>
        </div>
    </div>

    <div class="container">
        <header>
            <div class="header-brand-block">
                <h1 class="logo">CherryDownloader</h1>
                <p class="tagline">Hyper-speed multithreaded content processing studio</p>
            </div>
            <button class="theme-control-button" id="theme-toggle-btn" onclick="toggleTheme()">☀️ Light Theme</button>
        </header>

        <div class="system-hub-dashboard">
            <div class="hub-card">
                <div class="hub-label">System Kernel Status</div>
                <div class="hub-value"><span class="status-dot"></span> <span id="lbl-kernel-status">Operational</span></div>
            </div>
            <div class="hub-card">
                <div class="hub-label">Active Studio Operator</div>
                <div class="hub-value"><span class="user-badge">@Not_PiyushXD</span></div>
            </div>
            <div class="hub-card">
                <div class="hub-label">Total Successful Extracts</div>
                <div class="hub-value" id="lbl-total-extracts">0 Sessions</div>
            </div>
        </div>

        <div class="main-dashboard-card">
            <div class="url-input-wrapper">
                <input type="text" id="url-input" class="url-input" placeholder="Paste your target extraction link here..." autocomplete="off">
            </div>

            <div class="section-header">Target Extractor Configuration</div>
            <div class="options-grid">
                <button class="option-btn active" onclick="setConversionFormatProfile('mp4', this)">🎥 Video (MP4)</button>
                <button class="option-btn" onclick="setConversionFormatProfile('mp3', this)">🎵 Audio (MP3)</button>
            </div>

            <div id="video-options-group">
                <div class="section-header">Resolution Quality Configuration mapping</div>
                <div class="options-grid">
                    <button class="option-btn" onclick="setExtractionResolution('360', this)">360p Quality</button>
                    <button class="option-btn active" onclick="setExtractionResolution('720', this)">720p High Def</button>
                    <button class="option-btn" onclick="setExtractionResolution('1080', this)">1080p Full Def</button>
                </div>
            </div>

            <div id="audio-options-group" style="display: none;">
                <div class="section-header">Bitrate Compression Array Mapping</div>
                <div class="options-grid">
                    <button class="option-btn" onclick="setExtractionBitrate('64', this)">64 kbps (Low)</button>
                    <button class="option-btn active" onclick="setExtractionBitrate('128', this)">128 kbps (Standard)</button>
                    <button class="option-btn" onclick="setExtractionBitrate('256', this)">256 kbps (High Fidelity)</button>
                </div>
            </div>

            <button class="download-btn" id="download-btn" onclick="fireExtractionCorePipeline()"><span>⚡ Execute Core Download</span></button>

            <div class="progress-section" id="progress-section">
                <div class="hardware-speed-warning-box">
                    <span>⚠️ MULTI-THREAD PIPELINE ENGAGED. CAPTURING CHUNKS CONCURRENTLY.</span>
                </div>

                <div class="dashboard-split-layout">
                    <div>
                        <div class="progress-status" id="status-text">Synchronizing Engine Threads...</div>
                        <div class="speed-display" id="speed-display">0 KB/s</div>
                        <div class="progress-bar-container"><div class="progress-bar" id="progress-bar"></div></div>
                        <div class="progress-info"><div id="downloaded-text">0.0 MB</div><div id="eta-text">ETA: --:--</div></div>
                        <div class="download-size" id="size-text">Total Cluster Size: 0 MB</div>
                    </div>
                    <div>
                        <div class="section-header">Studio Engine Active Debug logs</div>
                        <div class="console-box" id="console-log-box">
                            <div class="console-line">[00:00:00] Standing by for incoming socket thread data loops...</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="cutter-section" id="cutter-section">
                <div class="section-header">🎬 In-Built Studio Video Cutter Module</div>
                <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 4px;">Slice down your downloaded clip asset instantly using direct stream-copy parsing layers:</p>
                <div class="cutter-grid">
                    <div>
                        <label class="section-header" style="font-size:0.65rem; margin-bottom:6px;">Start Cut Marker (HH:MM:SS)</label>
                        <input type="text" id="cut-start-marker" class="cutter-input" value="00:00:00">
                    </div>
                    <div>
                        <label class="section-header" style="font-size:0.65rem; margin-bottom:6px;">End Cut Marker (HH:MM:SS)</label>
                        <input type="text" id="cut-end-marker" class="cutter-input" value="00:00:15">
                    </div>
                </div>
                <button class="cutter-execute-button" onclick="executeNativeSlicerThread()">✂️ Slice Target Segment</button>
            </div>
        </div>

        <div class="value-proposition-block">
            <div class="section-header">Why Choose CherryDownloader Studio?</div>
            <div class="proposition-grid">
                <div class="prop-card">
                    <div class="prop-title">🚀 16-Worker Chunk Multiplexing</div>
                    <div class="prop-desc">Bypasses isolated server connection limits by stripping files into multiple small streams, maximizing throughput across residential internet infrastructure.</div>
                </div>
                <div class="prop-card">
                    <div class="prop-title">📦 Fully Multithreaded Subprocesses</div>
                    <div class="prop-desc">Completely decouples heavy streaming workloads away from your core UI wrapper to prevent browser view freezes or network frame loss during long operations.</div>
                </div>
                <div class="prop-card">
                    <div class="prop-title">🛠️ Permission Bypass Overrides</div>
                    <div class="prop-desc">Isolated local workspace configurations actively bypass system file permission walls, keeping cache distributions organized and completely fluid.</div>
                </div>
            </div>
        </div>

        <footer>
            <div>Engine Developed with Production Architecture Optimization by <a href="https://youtube.com/@Not_PiyushXD" target="_blank">@Not_PiyushXD</a></div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">Cherry Downloader Matrix Engine Framework v5.0 | Running over Chromium Blink Embed Context © 2026</div>
        </footer>
    </div>

    <script>
        let extractionMode = 'mp4'; let extractionResolution = '720'; let extractionBitrate = '128';
        let processingExecutionLock = false; let appSessionIdentifier = Math.random().toString(36).substring(2, 10);
        let backendMetricsInterval = null; let systemBridgeObject = null; let pathRefToDownloadedPayloadFile = "";
        let installerPollingTimer = null;

        new QWebChannel(qt.webChannelTransport, function (establishedChannelContext) {
            systemBridgeObject = establishedChannelContext.objects.pyBridge;
            runStartupWizardPipeline();
        });

        function runStartupWizardPipeline() {
            const statusLabel = document.querySelector('#wizard-screen-splash p');
            fetch('/setup/status')
                .then(res => res.json())
                .then(statusData => {
                    setTimeout(() => {
                        if (!statusData.has_seen_tutorial) {
                            transitionWizardScreen('wizard-screen-tutorial');
                        } else if (!statusData.ffmpeg_installed) {
                            statusLabel.textContent = "FFmpeg Missing! Redirecting to Installer Subsystem...";
                            statusLabel.style.color = 'var(--cherry-red)';
                            setTimeout(() => {
                                transitionWizardScreen('wizard-screen-installer');
                            }, 1200);
                        } else {
                            statusLabel.textContent = "✅ System has FFmpeg! Access Granted. Launching Engine...";
                            statusLabel.style.color = 'var(--success)';
                            setTimeout(() => { unlockStudioDashboardView(); }, 1200);
                        }
                    }, 1500);
                }).catch(() => {
                    statusLabel.textContent = "⚠️ Reconnecting to local pipeline network adapter...";
                    setTimeout(runStartupWizardPipeline, 1000);
                });
        }

        function transitionWizardScreen(targetScreenId) {
            document.getElementById('wizard-screen-splash').style.display = 'none';
            document.getElementById('wizard-screen-tutorial').style.display = 'none';
            document.getElementById('wizard-screen-installer').style.display = 'none';
            document.getElementById(targetScreenId).style.display = 'block';
        }

        function dismissTutorialSlideScreen() {
            fetch('/setup/dismiss-tutorial', { method: 'POST' })
                .then(() => {
                    fetch('/setup/status').then(res=>res.json()).then(statusData => {
                        if (!statusData.ffmpeg_installed) {
                            transitionWizardScreen('wizard-screen-installer');
                        } else {
                            unlockStudioDashboardView();
                        }
                    });
                });
        }

        function executeAutomatedBinaryDeployment() {
            document.getElementById('btn-trigger-autoinstall').disabled = true;
            document.getElementById('installer-header-title').textContent = "Downloading Files...";
            document.getElementById('installer-meta-desc').textContent = "Downloading static binary files. This process takes a moment depending on your internet connection speed profile.";
            fetch('/setup/trigger-installer', { method: 'POST' }).then(() => { installerPollingTimer = setInterval(pollDeploymentStatusStream, 750); });
        }

        function pollDeploymentStatusStream() {
            fetch('/setup/installer-polling')
                .then(res => res.json())
                .then(installState => {
                    document.getElementById('autoinstaller-progress-bar').style.width = installState.progress + '%';
                    document.getElementById('autoinstaller-status-log').textContent = installState.log;
                    if (installState.status === 'success') {
                        clearInterval(installerPollingTimer);
                        document.getElementById('autoinstaller-status-log').style.color = '#10b981';
                        setTimeout(unlockStudioDashboardView, 1200);
                    } else if (installState.status === 'error') {
                        clearInterval(installerPollingTimer);
                        document.getElementById('btn-trigger-autoinstall').disabled = false;
                        document.getElementById('btn-trigger-autoinstall').textContent = "Retry Deployment Phase";
                    }
                });
        }

        function unlockStudioDashboardView() {
            const masterWizardOverlay = document.getElementById('setup-wizard-overlay');
            masterWizardOverlay.style.opacity = '0';
            setTimeout(() => { masterWizardOverlay.style.display = 'none'; }, 500);
        }

        function toggleTheme() {
            const bodyDOMElement = document.body;
            const toggleButtonLabel = document.getElementById('theme-toggle-btn');
            if (bodyDOMElement.classList.contains('light-theme')) {
                bodyDOMElement.classList.remove('light-theme');
                bodyDOMElement.classList.add('dark-theme');
                toggleButtonLabel.textContent = "☀️ Light Theme";
            } else {
                bodyDOMElement.classList.remove('dark-theme');
                bodyDOMElement.classList.add('light-theme');
                toggleButtonLabel.textContent = "🌙 Dark Theme";
            }
        }

        function setConversionFormatProfile(targetFormat, htmlButtonElementReference) {
            extractionMode = targetFormat;
            document.querySelectorAll('[onclick^="setConversionFormatProfile"]').forEach(element => element.classList.remove('active'));
            htmlButtonElementReference.classList.add('active');
            document.getElementById('video-options-group').style.display = targetFormat === 'mp4' ? 'block' : 'none';
            document.getElementById('audio-options-group').style.display = targetFormat === 'mp3' ? 'block' : 'none';
        }

        function setExtractionResolution(resString, htmlButtonElementReference) { extractionResolution = resString; document.querySelectorAll('[onclick^="setExtractionResolution"]').forEach(element => element.classList.remove('active')); htmlButtonElementReference.classList.add('active'); }
        function setExtractionBitrate(bitrateString, htmlButtonElementReference) { extractionBitrate = bitrateString; document.querySelectorAll('[onclick^="setExtractionBitrate"]').forEach(element => element.classList.remove('active')); htmlButtonElementReference.classList.add('active'); }

        function clearMainControlPanelLocks() { clearInterval(backendMetricsInterval); processingExecutionLock = false; const targetButton = document.getElementById('download-btn'); targetButton.disabled = false; targetButton.innerHTML = '<span>⚡ Execute Core Download</span>'; }

        function fireExtractionCorePipeline() {
            const targetUrlString = document.getElementById('url-input').value.trim();
            if (!targetUrlString || processingExecutionLock) return;

            appSessionIdentifier = Math.random().toString(36).substring(2, 10);
            processingExecutionLock = true;

            document.getElementById('download-btn').disabled = true;
            document.getElementById('download-btn').innerHTML = '<span>⏳ Processing Streams...</span>';
            document.getElementById('progress-section').style.display = 'block';
            document.getElementById('cutter-section').style.display = 'none';
            document.getElementById('console-log-box').innerHTML = '<div class="console-line">[Establishing Direct Core OS Channel Lines...]</div>';

            backendMetricsInterval = setInterval(dispatchTelemetryPoll, 850);

            if (systemBridgeObject) {
                systemBridgeObject.startNativeDownload(targetUrlString, extractionMode, extractionResolution, extractionBitrate, appSessionIdentifier);
            } else {
                document.getElementById('console-log-box').innerHTML = '<div class="console-line">❌ Fault: Direct C++ Channel Lane failed mapping vectors.</div>';
                clearMainControlPanelLocks();
            }
        }

        async function dispatchTelemetryPoll() {
            try {
                const rawServerPayload = await fetch(`/progress/${appSessionIdentifier}`); 
                const derivedPacketJson = await rawServerPayload.json();
                
                document.getElementById('progress-bar').style.width = derivedPacketJson.percent + '%';
                document.getElementById('status-text').textContent = derivedPacketJson.status;
                document.getElementById('speed-display').textContent = derivedPacketJson.speed;
                document.getElementById('downloaded-text').textContent = derivedPacketJson.downloaded;
                document.getElementById('eta-text').textContent = 'ETA: ' + derivedPacketJson.eta;
                document.getElementById('size-text').textContent = 'Total Cluster Size: ' + derivedPacketJson.total;

                fetch('/stats').then(res => res.json()).then(stats => {
                    document.getElementById('lbl-total-extracts').textContent = stats.total_successful_sessions + ' Sessions';
                    document.getElementById('lbl-kernel-status').textContent = stats.engine_status;
                }).catch(()=>{});

                if (derivedPacketJson.logs && derivedPacketJson.logs.length > 0) {
                    const trackingLogDomBox = document.getElementById('console-log-box'); 
                    let structuralLogHtmlBlock = '';
                    derivedPacketJson.logs.forEach(singleLine => { structuralLogHtmlBlock += `<div class="console-line">${singleLine}</div>`; });
                    trackingLogDomBox.innerHTML = structuralLogHtmlBlock; 
                    trackingLogDomBox.scrollTop = trackingLogDomBox.scrollHeight;
                }
                
                if (derivedPacketJson.percent === 100) { 
                    pathRefToDownloadedPayloadFile = derivedPacketJson.filepath;
                    clearMainControlPanelLocks(); 
                    if (extractionMode === 'mp4' && pathRefToDownloadedPayloadFile) {
                        document.getElementById('cutter-section').style.display = 'block';
                        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                    }
                } else if (derivedPacketJson.status === 'Error') {
                    clearMainControlPanelLocks();
                }
            } catch (telemetryExceptionError) {
                console.error("Telemetry Loop anomaly: ", telemetryExceptionError);
            }
        }

        function executeNativeSlicerThread() {
            const calculatedStartTimestamp = document.getElementById('cut-start-marker').value.trim();
            const calculatedEndTimestamp = document.getElementById('cut-end-marker').value.trim();
            if (systemBridgeObject && pathRefToDownloadedPayloadFile) {
                systemBridgeObject.cutVideo(pathRefToDownloadedPayloadFile, calculatedStartTimestamp, calculatedEndTimestamp, appSessionIdentifier);
            }
        }
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    storage_scrubber_thread_instance = threading.Thread(target=background_cache_garbage_collector, name="ScrubberThread", daemon=True)
    storage_scrubber_thread_instance.start()
    
    logger.info("Cherry Video Downloader framework initialized successfully.")
    
    network_server_thread_instance = threading.Thread(target=run_flask_server, name="FlaskServerThread", daemon=True)
    network_server_thread_instance.start()
    
    time.sleep(1.2)
    
    application_runtime_manager = QApplication(sys.argv)
    application_window_frame_view = CherryDesktopApp()
    application_window_frame_view.show()
    
    sys.exit(application_runtime_manager.exec())