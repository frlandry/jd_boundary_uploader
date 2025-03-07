# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JDOperationsCenterUploader
                              A QGIS Plugin
                              -----------------
 Description:
    JD Boundary Uploader is a QGIS plugin designed to streamline the process of 
    importing and preparing boundary shapefiles for upload to the John Deere Operations Center.
    It automatically extracts and reprojects shapefiles from ZIP archives provided by FADQ,
    and provides an interactive editing interface to update attributes such as Client Name,
    Farm Name, and Field Name. It supports grouping and merging of fields.
    Finally, it generates a packaged ZIP archive containing the shapefile and a metadata JSON file,
    meeting the required format for uploads to the John Deere Operations Center.

 Author: Frederic Landry (frlandry@gmail.com)
 Date: 2025-02-15
 License: GNU General Public License (GPL v2 or later)

 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

 This script initializes the plugin and makes it available to QGIS.
"""

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """
    Load the JDOperationsCenterUploader class from the jd_boundary_uploader module.

    Parameters:
        iface (QgsInterface): QGIS interface instance.

    Returns:
        JDOperationsCenterUploader: An instance of the plugin.
    """
    from .jd_boundary_uploader import JDOperationsCenterUploader
    return JDOperationsCenterUploader(iface)
