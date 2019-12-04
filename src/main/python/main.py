import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QSystemTrayIcon, QMainWindow, QMenu, QAction, QApplication, QStyle
from asyncqt import QEventLoop

import asyncio
import websockets
import ws
import device

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip("pUsb2Snes 0.1")

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu = QMenu()
        tray_menu.addAction(QAction("pUsb2Snes 0.1", self))
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

if __name__ == '__main__':
    # Create application instance
    appctxt = ApplicationContext()
    appctxt.app.setQuitOnLastWindowClosed(False)

    # Setup application loop
    loop = QEventLoop(appctxt.app)
    asyncio.set_event_loop(loop)
    
    # Create main window and systray menu
    window = MainWindow()

    # Initialize devices and providers
    device.setup_devices()
    device.setup_providers()

    # Start websocket server
    start_server = websockets.serve(ws.connect, "localhost", 8080)
    asyncio.get_event_loop().run_until_complete(start_server)

    # Loop until quit
    with loop:
        sys.exit(loop.run_forever())
