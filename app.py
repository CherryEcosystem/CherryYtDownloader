import sys
import os
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

class CherryLocalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.setWindowTitle("Cherry Downloader Desktop Studio")
        self.setGeometry(100, 100, 1050, 700)
        
        # Initialize the web rendering viewport
        self.browser = QWebEngineView()
        
        # Set the exact path to your local index.html file
        local_ui_path = r"C:\Users\Piyush\Downloads\YTvidDownloader\app.html"
        
        if os.path.exists(local_ui_path):
            # Formats the Windows folder path into a browser-readable address
            self.browser.setUrl(QUrl.fromLocalFile(local_ui_path))
        else:
            # Error screen if the folder path is broken
            self.browser.setHtml(f"<h1>Error: UI File Missing!</h1><p>Could not find your file at: {local_ui_path}</p>")
            
        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CherryLocalApp()
    window.show()
    sys.exit(app.exec())