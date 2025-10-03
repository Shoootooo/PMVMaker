import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    """The main entry point for the application."""
    # It's good practice to set the application name and version
    app = QApplication(sys.argv)
    app.setApplicationName("AI PMV Generator")
    app.setApplicationVersion("2.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()