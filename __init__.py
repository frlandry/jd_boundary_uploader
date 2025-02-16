# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JDOperationsCenterUploader
                                 A QGIS plugin
 JD Boundary Uploader is a QGIS plugin designed to streamline the process of importing and preparing boundary shapefiles for upload to the John Deere Operations Center. The plugin automatically extracts and reprojects shapefiles from ZIP archives provided from FADQ and provides an interactive editing interface where users can update attributes such as Client Name, Farm Name, and Field Name. It supports grouping and merging of fields. Finally, JD Boundary Uploader generates a fully packaged ZIP archive—including the shapefile and a metadata JSON file—that meets the required format for John Deere Operations Center uploads.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-02-15
        copyright            : (C) 2025 by Frederic Landry
        email                : frlandry@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load JDOperationsCenterUploader class from file JDOperationsCenterUploader.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .jd_boundary_uploader import JDOperationsCenterUploader
    return JDOperationsCenterUploader(iface)
