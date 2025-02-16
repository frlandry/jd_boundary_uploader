#-*- coding: utf-8 -*-
"""
/***************************************************************************
 JDOperationsCenterUploader
                              A QGIS Plugin
                              -------------------------
 Description:
    JD Boundary Uploader is a QGIS plugin that streamlines the process of importing
    and preparing boundary shapefiles for upload to the John Deere Operations Center.
    It extracts and reprojects shapefiles from ZIP archives provided by FADQ, and presents
    an interactive editing interface for updating attributes (Client Name, Farm Name, Field Name).
    It supports grouping and merging of fields, and finally generates a ZIP archive containing
    the shapefile and a metadata JSON file that complies with JD requirements.
    
 Author: Frederic Landry (frlandry@gmail.com)
 Date: 2025-02-15
 License: GNU General Public License (GPL v2 or later)
 ***************************************************************************/
 
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 
 This script initializes the plugin, making it available to QGIS.
"""

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
import os.path
from . import resources
from .jd_boundary_uploader_dockwidget import JDOperationsCenterUploaderDockWidget

# -----------------------------------------------------------------------------
# CLASS: JDOperationsCenterUploader
# -----------------------------------------------------------------------------
# Description:
#   This class implements the main functionality of the JD Boundary Uploader plugin.
#   It initializes the plugin, sets up the toolbar action and dock widget, and manages
#   the plugin's lifecycle (loading, showing, and unloading).
class JDOperationsCenterUploader:
    def __init__(self, iface):
        """
        Constructor.

        Parameters:
            iface (QgsInterface): An interface instance that will be passed to this class,
                                  which provides the hook by which you can manipulate the QGIS
                                  application at runtime.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        # Install translator based on user locale.
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'JDOperationsCenterUploader_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
            
        self.actions = []
        self.menu = self.tr(u'&JD Boundary Uploader')
        # Create a dedicated toolbar in QGIS toolbar area.
        self.toolbar = self.iface.addToolBar(u'JDOperationsCenterUploader')
        self.toolbar.setObjectName(u'JDOperationsCenterUploader')
        self.pluginIsActive = False
        self.dockwidget = None

    # -----------------------------------------------------------------------------
    # METHOD: tr
    # -----------------------------------------------------------------------------
    # Description:
    #   Returns the translated string using QGIS translation API.
    def tr(self, message):
        return QCoreApplication.translate('JDOperationsCenterUploader', message)

    # -----------------------------------------------------------------------------
    # METHOD: initGui
    # -----------------------------------------------------------------------------
    # Description:
    #   Initializes the GUI for the plugin by adding the action to the toolbar and menu.
    def initGui(self):
        # Set the icon path (ensure the icon exists in the resources)
        icon_path = ':/plugins/jd_boundary_uploader/icon.png'
        self.add_action(icon_path,
                        text=self.tr(u'JD Boundary Uploader'),
                        callback=self.run,
                        parent=self.iface.mainWindow())

    # -----------------------------------------------------------------------------
    # METHOD: add_action
    # -----------------------------------------------------------------------------
    # Description:
    #   Creates an action (with an icon) and adds it to the plugin's toolbar and menu.
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

    # -----------------------------------------------------------------------------
    # METHOD: run
    # -----------------------------------------------------------------------------
    # Description:
    #   Activates the plugin by creating (if needed) and displaying the dock widget.
    def run(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True
            if self.dockwidget is None:
                self.dockwidget = JDOperationsCenterUploaderDockWidget(parent=self.iface.mainWindow())
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

    # -----------------------------------------------------------------------------
    # METHOD: onClosePlugin
    # -----------------------------------------------------------------------------
    # Description:
    #   Callback function when the dock widget is closed. Resets plugin state.
    def onClosePlugin(self):
        self.pluginIsActive = False

    # -----------------------------------------------------------------------------
    # METHOD: unload
    # -----------------------------------------------------------------------------
    # Description:
    #   Unloads the plugin by removing its actions from the QGIS interface.
    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&JD Boundary Uploader'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar
