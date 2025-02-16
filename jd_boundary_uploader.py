#-*- coding: utf-8 -*-

#***************************************************************************
#                            JDOperationsCenterUploader
#                                 A QGIS plugin
#***************************************************************************/
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
import os.path
from . import resources
from .jd_boundary_uploader_dockwidget import JDOperationsCenterUploaderDockWidget

class JDOperationsCenterUploader:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        # Installer le traducteur en fonction de la locale de l'utilisateur
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'JDOperationsCenterUploader_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
            
        self.actions = []
        self.menu = self.tr(u'&JD Boundary Uploader')
        # Créer une toolbar dédiée dans la barre d'outils de QGIS
        self.toolbar = self.iface.addToolBar(u'JDOperationsCenterUploader')
        self.toolbar.setObjectName(u'JDOperationsCenterUploader')
        self.pluginIsActive = False
        self.dockwidget = None

    def tr(self, message):
        return QCoreApplication.translate('JDOperationsCenterUploader', message)

    def initGui(self):
        # Définir le chemin vers l'icône (assurez-vous que l'icône est présente dans vos ressources)
        icon_path = ':/plugins/jd_boundary_uploader/icon.png'
        self.add_action(icon_path,
                        text=self.tr(u'JD Boundary Uploader'),
                        callback=self.run,
                        parent=self.iface.mainWindow())

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True, parent=None):
        from qgis.PyQt.QtGui import QIcon
        action = QAction(QIcon(icon_path), text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def run(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True
            if self.dockwidget is None:
                self.dockwidget = JDOperationsCenterUploaderDockWidget(parent=self.iface.mainWindow())
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

    def onClosePlugin(self):
        self.pluginIsActive = False

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&JD Boundary Uploader'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar
