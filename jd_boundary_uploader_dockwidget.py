# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JDOperationsCenterUploaderDockWidget
                                 A QGIS plugin
 JD Boundary Uploader is a QGIS plugin designed to streamline the process of importing 
 and preparing boundary shapefiles for upload to the John Deere Operations Center. 
 The plugin automatically extracts and reprojects shapefiles from ZIP archives provided 
 from FADQ and provides an interactive editing interface where users can update attributes 
 such as Client Name, Farm Name, and Field Name. It supports grouping and merging of fields.
 Finally, JD Boundary Uploader generates a fully packaged ZIP archive—including the shapefile 
 and a metadata JSON file—that meets the required format for John Deere Operations Center uploads.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-02-15
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Frederic Landry
        email                : frlandry@gmail.com
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

# Charge l'interface depuis le fichier .ui
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'jd_boundary_uploader_dockwidget_base.ui'))

class JDOperationsCenterUploaderDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(JDOperationsCenterUploaderDockWidget, self).__init__(parent)
        self.setupUi(self)
        # Créez un conteneur pour y ajouter votre widget d'édition
        from .feature_table_dialog import FeatureTableDialog
        self.featureDialog = FeatureTableDialog()
        # Créer un widget conteneur et un layout
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.featureDialog)
        # Définir ce widget conteneur comme le widget central du dock
        self.setWidget(container)

    def closeEvent(self, event):
        """Emit the closingPlugin signal and accept the event."""
        self.closingPlugin.emit()
        event.accept()
