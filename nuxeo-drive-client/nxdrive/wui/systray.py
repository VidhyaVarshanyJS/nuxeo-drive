'''
Created on 27 janv. 2015

@author: Remi Cattiau
'''
from PyQt4 import QtGui, QtCore
from nxdrive.logging_config import get_logger
from nxdrive.wui.dialog import WebDialog, WebDriveApi
from nxdrive.engine.activity import FileAction
import sys
log = get_logger(__name__)


class WebSystrayApi(WebDriveApi):

    @QtCore.pyqtSlot()
    def show_settings(self):
        super(WebSystrayApi, self).show_settings()
        self._dialog.hide()

    @QtCore.pyqtSlot(str, result=str)
    def open_remote(self, uid):
        res = super(WebSystrayApi, self).open_remote(uid)
        self._dialog.hide()
        return res

    @QtCore.pyqtSlot(str, str, result=str)
    def open_local(self, uid, path):
        res = super(WebSystrayApi, self).open_local(uid, path)
        self._dialog.hide()
        return res

    @QtCore.pyqtSlot()
    def open_help(self):
        self._manager.open_local_file("http://doc.nuxeo.com/display/USERDOC/Nuxeo+Drive")
        self._dialog.hide()

    @QtCore.pyqtSlot()
    def open_about(self):
        self._application.show_settings(section="About")
        self._dialog.hide()

    @QtCore.pyqtSlot()
    def suspend(self):
        self._manager.suspend()

    @QtCore.pyqtSlot(str, result=int)
    def get_syncing_items(self, uid):
        engine = self._get_engine(uid)
        return engine.get_dao().get_syncing_count()

    @QtCore.pyqtSlot()
    def resume(self):
        self._manager.resume()

    @QtCore.pyqtSlot()
    def advanced_systray(self):
        menu = QtGui.QMenu()
        menu.setFocusProxy(self._dialog)
        if self._manager.is_paused():
            menu.addAction("Resume", self.resume)
        else:
            menu.addAction("Suspend", self.suspend)
        menu.addSeparator()
        menu.addAction("About", self.open_about)
        menu.addAction("Help", self.open_help)
        menu.addSeparator()
        menu.addAction("Settings", self._application.show_settings)
        menu.addSeparator()
        menu.addAction("Quit", self._application.quit)
        menu.exec_(QtGui.QCursor.pos())

class WebSystrayView(WebDialog):
    '''
    classdocs
    '''
    def __init__(self, application, icon):
        '''
        Constructor
        '''
        super(WebSystrayView, self).__init__(application, "systray.html", api=WebSystrayApi(self, application))
        self._icon = icon
        self._view.setFocusProxy(self)
        self.resize(300, 370)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint);

    def replace(self):
        rect = self._icon.geometry()
        if rect.x() < 100:
            x = rect.x() + rect.width()
            y = rect.y() - self.height() + rect.height()
        elif rect.y() < 100:
            x = rect.x() + rect.width() - self.width()
            y = rect.y() + rect.height()
        else:
            x = rect.x() + rect.width() - self.width()
            y = rect.y() - self.height()
        self.move(x, y)

    def show(self):
        self.replace()
        super(WebSystrayView, self).show()
        if self.isVisible():
            self._view.reload()
            self.raise_()
            self.activateWindow()
            self.setFocus(QtCore.Qt.ActiveWindowFocusReason)

    def underMouse(self):
        # The original result was different from this simple
        return self.geometry().contains(QtGui.QCursor.pos())

    def shouldHide(self):
        if not (self.underMouse() or self._icon.geometry().contains(QtGui.QCursor.pos())):
            self.close()

    def focusOutEvent(self, event):
        if self._icon is None:
            return
        if not (self.underMouse() or self._icon.geometry().contains(QtGui.QCursor.pos())):
            self.close()
        super(WebSystrayView, self).focusOutEvent(event)

    def resizeEvent(self, event):
        super(WebSystrayView, self).resizeEvent(event)
        self.replace()

    @QtCore.pyqtSlot()
    def close(self):
        self._icon = None
        super(WebSystrayView, self).close()

class WebSystray(QtGui.QMenu):
    '''
    classdocs
    '''
    def __init__(self, application, systray_icon):
        '''
        Constructor
        '''
        super(WebSystray, self).__init__()
        self.aboutToShow.connect(self.onShow)
        self.aboutToHide.connect(self.onHide)
        self._application = application
        self._systray_icon = systray_icon
        self.dlg = None

    @QtCore.pyqtSlot()
    def dialogDeleted(self):
        self.dlg = None

    @QtCore.pyqtSlot()
    def onHide(self):
        if self.dlg:
            self.dlg.shouldHide()

    @QtCore.pyqtSlot()
    def onShow(self):
        if self.dlg is None:
            self.dlg = WebSystrayView(self._application, self._systray_icon)
            # Close systray when app is quitting
            self._application.aboutToQuit.connect(self.dlg.close)
            self.dlg.destroyed.connect(self.dialogDeleted)
        self.dlg.show()
