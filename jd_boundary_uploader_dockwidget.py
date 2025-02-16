# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JDOperationsCenterUploaderDockWidget
                              A QGIS Plugin Component
                              -------------------------
 Description:
    JD Boundary Uploader is a QGIS plugin designed to streamline the process of 
    importing and preparing boundary shapefiles for upload to the John Deere Operations Center.
    It automatically extracts and reprojects shapefiles from ZIP archives provided by FADQ,
    and provides an interactive editing interface for updating attributes such as Client Name,
    Farm Name, and Field Name. It supports grouping and merging of fields.
    Finally, it generates a packaged ZIP archive containing the shapefile and a metadata JSON file,
    compliant with the required format for John Deere Operations Center uploads.
    
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
"""

import os
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal

# -----------------------------------------------------------------------------
# Load UI from the .ui file
# -----------------------------------------------------------------------------
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'jd_boundary_uploader_dockwidget_base.ui'))

# -----------------------------------------------------------------------------
# CLASS: JDOperationsCenterUploaderDockWidget
# -----------------------------------------------------------------------------
# Description:
#   Implements the dockable widget for the JD Boundary Uploader plugin.
#   This widget loads its interface from a Qt Designer .ui file and embeds the
#   FeatureTableDialog for interactive editing.
class JDOperationsCenterUploaderDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    # Signal emitted when the dock widget is closing
    closingPlugin = pyqtSignal()

    # -----------------------------------------------------------------------------
    # METHOD: __init__
    # -----------------------------------------------------------------------------
    # Description:
    #   Constructor. Initializes the dock widget, loads the UI, creates an instance
    #   of the FeatureTableDialog, and embeds it within a container widget.
    def __init__(self, parent=None):
        super(JDOperationsCenterUploaderDockWidget, self).__init__(parent)
        self.setupUi(self)
        # Import and create the editing widget
        from .feature_table_dialog import FeatureTableDialog
        self.featureDialog = FeatureTableDialog()
        # Create a container widget with a vertical layout to hold the editing widget
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.featureDialog)
        # Set the container as the central widget of the dock
        self.setWidget(container)

    # -----------------------------------------------------------------------------
    # METHOD: closeEvent
    # -----------------------------------------------------------------------------
    # Description:
    #   Overrides the close event to emit a closing signal and accept the event,
    #   allowing the plugin to perform any necessary cleanup.
    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
