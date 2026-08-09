import sys
from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.core.asset_manager import ensure_assets_exist

def main():
    # Ensure assets exist before starting QApplication
    ensure_assets_exist()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
