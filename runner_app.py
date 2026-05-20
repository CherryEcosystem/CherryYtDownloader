import sys
import threading
import time
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Import the Flask application instance from your web script code file
# Replace 'your_web_script_name' with the actual filename of your web version (without .py)
from your_web_script_name import app as flask_app 

def start_backend_server():
    """Launches your Flask application locally on port 5000 without debugging loops."""
    flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

class CherryDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configure Window Dimensions
        self.setWindowTitle("Cherry Downloader Studio")
        self.setGeometry(100, 100, 1100, 750)
        
        # Initialize the native web rendering view
        self.browser = QWebEngineView()
        
        # Route the view directly to your active local Flask server address
        self.browser.setUrl(QUrl("http://127.0.0.1:5000/"))
        
        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    # 1. Spin up your Flask app in a hidden background thread
    server_worker = threading.Thread(target=start_backend_server, daemon=True)
    server_worker.start()
    
    # 2. Give the local server a quick second to securely boot up and bind to the port
    time.sleep(1.2)
    
    # 3. Fire up the native desktop UI application window
    desktop_env = QApplication(sys.argv)
    main_window = CherryDesktopApp()
    main_window.show()
    
    # Cleanly exits everything when you close the app window
    sys.exit(desktop_env.exec())