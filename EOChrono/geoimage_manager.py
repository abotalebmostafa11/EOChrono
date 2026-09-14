from qgis.PyQt.QtWidgets import QAction
from pathlib import Path
class GeoImageManager:
    def __init__(self,iface):
        self.iface=iface; self.action=None; self.plugin_dir=Path(__file__).parent; self.dlg=None
    def initGui(self):
        self.action=QAction('EOChrono 7.0.0',self.iface.mainWindow()); self.action.triggered.connect(self.run); self.iface.addToolBarIcon(self.action); self.iface.addPluginToMenu('&EOChrono',self.action)
    def unload(self):
        if self.action:self.iface.removeToolBarIcon(self.action); self.iface.removePluginMenu('&EOChrono',self.action)
    def run(self):
        from .ui_dialog import GeoImageDialog
        self.dlg=GeoImageDialog(self.iface,self.plugin_dir); self.dlg.show(); self.dlg.raise_(); self.dlg.activateWindow()
