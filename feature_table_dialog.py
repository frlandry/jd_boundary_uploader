import os
import zipfile
import tempfile
import json
import random
from collections import defaultdict
import copy

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QFileDialog, QMessageBox, QLineEdit, QInputDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QColor, QFont
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsVectorFileWriter, QgsFeature, QgsFields, QgsField,
    QgsWkbTypes, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer,
    QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling, QgsCoordinateTransform
)
from qgis.utils import iface

# Fonction pour forcer le zoom sur la couche de travail
def zoomToWorkingLayer(layer):
    crs_dest = iface.mapCanvas().mapSettings().destinationCrs()
    crs_src = layer.crs()
    if crs_src != crs_dest:
        transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        extent = transform.transformBoundingBox(layer.extent())
    else:
        extent = layer.extent()
    iface.mapCanvas().setExtent(extent)
    iface.mapCanvas().refresh()

# Fonction de clonage de QgsFeature
def clone_feature(feat):
    new_feat = QgsFeature(feat.fields())
    new_feat.setGeometry(feat.geometry())
    new_feat.setAttributes(feat.attributes())
    return new_feat

# Fenêtre simplifiée pour la saisie des métadonnées
class MetadataDialog(QDialog):
    def __init__(self, default_client="", default_farm="", parent=None):
        super(MetadataDialog, self).__init__(parent)
        self.setWindowTitle("Enter Metadata")
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Client:"))
        self.clientEdit = QLineEdit(self)
        self.clientEdit.setText(default_client)
        layout.addWidget(self.clientEdit)
        layout.addWidget(QLabel("Farm:"))
        self.farmEdit = QLineEdit(self)
        self.farmEdit.setText(default_farm)
        layout.addWidget(self.farmEdit)
        self.nextButton = QPushButton("Next", self)
        self.nextButton.clicked.connect(self.validateAndAccept)
        layout.addWidget(self.nextButton)
    def validateAndAccept(self):
        if not self.clientEdit.text().strip() or not self.farmEdit.text().strip():
            QMessageBox.critical(self, "Error", "Client and Farm cannot be empty.")
        else:
            self.accept()
    def getValues(self):
        return self.clientEdit.text(), self.farmEdit.text()

class FeatureTableDialog(QDialog):
    def __init__(self, parent=None):
        super(FeatureTableDialog, self).__init__(parent)
        self.setWindowTitle("JD Boundary Uploader - Editing Panel")
        self.setMinimumWidth(300)
        self.layout = QVBoxLayout(self)
        # Sauvegarde pour annuler la dernière fusion
        self.lastMergeBackup = None

        # --- Extraction du ZIP et création de la couche mémoire ---
        zip_input_path, _ = QFileDialog.getOpenFileName(self, "Select FADQ ZIP", "", "Zip Files (*.zip)")
        if not zip_input_path:
            QMessageBox.critical(self, "Error", "No ZIP file selected.")
            self.close()
            return
        temp_dir = tempfile.mkdtemp(prefix="FADQ_")
        with zipfile.ZipFile(zip_input_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        shp_file = None
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith('.shp'):
                    shp_file = os.path.join(root, file)
                    break
            if shp_file:
                break
        if not shp_file:
            QMessageBox.critical(self, "Error", "No .shp file found in ZIP.")
            self.close()
            return

        orig_layer = QgsVectorLayer(shp_file, "Input Layer", "ogr")
        if not orig_layer.isValid():
            QMessageBox.critical(self, "Error", "The extracted layer is not valid.")
            self.close()
            return

        # Création de la couche mémoire avec champs requis
        crs = "EPSG:4326"
        geom_type = QgsWkbTypes.displayString(orig_layer.wkbType())
        self.layer = QgsVectorLayer(f"{geom_type}?crs={crs}", "Working Layer", "memory")
        prov = self.layer.dataProvider()
        fields = QgsFields()
        fields.append(QgsField("CLIENT_NAME", QVariant.String))
        fields.append(QgsField("FARM_NAME", QVariant.String))
        fields.append(QgsField("FIELD_NAME", QVariant.String))
        # POLYGONTYP est conservé dans la couche, mais ne sera pas affiché dans le widget
        fields.append(QgsField("POLYGONTYP", QVariant.LongLong))
        fields.append(QgsField("GROUPE", QVariant.String))
        prov.addAttributes(fields)
        self.layer.updateFields()

        self.layer.startEditing()
        for feat in orig_layer.getFeatures():
            new_feat = QgsFeature()
            new_feat.setGeometry(feat.geometry())
            new_feat.setFields(self.layer.fields())
            new_feat["CLIENT_NAME"] = ""
            new_feat["FARM_NAME"] = ""
            new_feat["FIELD_NAME"] = feat["NOPAR"] if feat.fields().indexOf("NOPAR") != -1 else ""
            wkb = feat.geometry().wkbType()
            if QgsWkbTypes.geometryType(wkb) == QgsWkbTypes.PolygonGeometry:
                new_feat["POLYGONTYP"] = 2 if QgsWkbTypes.isMultiType(wkb) else 1
            else:
                new_feat["POLYGONTYP"] = 0
            new_feat["GROUPE"] = ""
            prov.addFeatures([new_feat])
        self.layer.commitChanges()
        QgsProject.instance().addMapLayer(self.layer)
        self.setupLabels()

        # Remplacer le zoom classique par le zoom transformé
        zoomToWorkingLayer(self.layer)

        # Debug : nombre d'entités chargées
        num_feats = len(list(self.layer.getFeatures()))
        print("Number of features loaded:", num_feats)
        if num_feats == 0:
            QMessageBox.warning(self, "Warning", "No features loaded from the ZIP.")

        # --- Interface d'édition ---
        global_layout = QHBoxLayout()
        global_layout.addWidget(QLabel("Global Client:"))
        self.globalClientEdit = QLineEdit()
        global_layout.addWidget(self.globalClientEdit)
        global_layout.addWidget(QLabel("Global Farm:"))
        self.globalFarmEdit = QLineEdit()
        global_layout.addWidget(self.globalFarmEdit)
        self.btnApplyGlobal = QPushButton("Apply Global Values")
        self.btnApplyGlobal.clicked.connect(self.applyGlobalValues)
        global_layout.addWidget(self.btnApplyGlobal)
        self.layout.addLayout(global_layout)

        self.btnUpdateSymb = QPushButton("Update Symbology")
        self.btnUpdateSymb.clicked.connect(self.updateSymbology)
        self.layout.addWidget(self.btnUpdateSymb)

        instructions = QLabel(
            "Edit CLIENT_NAME, FARM_NAME, FIELD_NAME and specify GROUP for merging.\n"
            "Click on column headers to sort. You can select multiple rows; selection is synchronized with the map.")
        self.layout.addWidget(instructions)

        self.table = QTableWidget()
        # Afficher 4 colonnes (sans POLYGONTYP)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["CLIENT_NAME", "FARM_NAME", "FIELD_NAME", "GROUPE"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Utiliser MultiSelection pour permettre la sélection multiple sans modificateurs
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.layout.addWidget(self.table)

        self.table.itemSelectionChanged.connect(self.highlightFeature)
        self.layer.selectionChanged.connect(self.onMapSelectionChanged)

        # Boutons d'action de base
        btn_layout = QHBoxLayout()
        self.btnSave = QPushButton("Save Edits")
        self.btnSave.clicked.connect(self.saveEdits)
        self.btnMerge = QPushButton("Merge by Group")
        self.btnMerge.clicked.connect(self.mergeGroups)
        self.btnTerminate = QPushButton("Terminate")
        self.btnTerminate.clicked.connect(self.terminateAndClearGroup)
        btn_layout.addWidget(self.btnSave)
        btn_layout.addWidget(self.btnMerge)
        btn_layout.addWidget(self.btnTerminate)
        self.layout.addLayout(btn_layout)

        # Boutons supplémentaires pour assigner un groupe et annuler la dernière fusion
        extra_btn_layout = QHBoxLayout()
        self.btnAssignGroup = QPushButton("Assign Group")
        self.btnAssignGroup.clicked.connect(self.assignGroup)
        self.btnUndoMerge = QPushButton("Undo Merge")
        self.btnUndoMerge.clicked.connect(self.undoMerge)
        extra_btn_layout.addWidget(self.btnAssignGroup)
        extra_btn_layout.addWidget(self.btnUndoMerge)
        self.layout.addLayout(extra_btn_layout)

        # Bouton pour lancer un nouveau processus (désactivé par défaut)
        self.btnNewProcess = QPushButton("New Process")
        self.btnNewProcess.setEnabled(False)
        self.btnNewProcess.clicked.connect(self.newProcess)
        self.layout.addWidget(self.btnNewProcess)

        self.loadTable()

    def setupLabels(self):
        from qgis.core import QgsVectorLayerSimpleLabeling, QgsPalLayerSettings, QgsTextFormat
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "concat('Client: ', CLIENT_NAME, '\nFarm: ', FARM_NAME, '\nField: ', FIELD_NAME)"
        label_settings.placement = QgsPalLayerSettings.OverPoint
        label_settings.enabled = True
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Segoe UI", 10))
        text_format.setColor(QColor("black"))
        buffer_settings = text_format.buffer()
        buffer_settings.setEnabled(False)
        label_settings.setFormat(text_format)
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        self.layer.setLabeling(labeling)
        self.layer.setLabelsEnabled(True)
        self.layer.triggerRepaint()
        iface.mapCanvas().refresh()

    def loadTable(self):
        feats = list(self.layer.getFeatures())
        self.table.setRowCount(len(feats))
        self.feat_ids = [feat.id() for feat in feats]
        for i, feat in enumerate(feats):
            self.table.setItem(i, 0, QTableWidgetItem(feat.attribute("CLIENT_NAME") or ""))
            self.table.setItem(i, 1, QTableWidgetItem(feat.attribute("FARM_NAME") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(feat.attribute("FIELD_NAME") or ""))
            self.table.setItem(i, 3, QTableWidgetItem(feat.attribute("GROUPE") or ""))

    def applyGlobalValues(self):
        global_client = self.globalClientEdit.text()
        global_farm = self.globalFarmEdit.text()
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            selected_indexes = [self.table.model().index(row, 0) for row in range(self.table.rowCount())]
        for index in selected_indexes:
            row = index.row()
            self.table.item(row, 0).setText(global_client)
            self.table.item(row, 1).setText(global_farm)
        self.saveEdits()
        self.setupLabels()

    def assignGroup(self):
        group_name, ok = QInputDialog.getText(self, "Assign Group", "Enter group name:")
        if not ok or not group_name:
            return
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Info", "No rows selected.")
            return
        for index in selected_indexes:
            row = index.row()
            self.table.item(row, 3).setText(group_name)
        self.saveEdits()

    def undoMerge(self):
        if self.lastMergeBackup:
            reply = QMessageBox.question(
                self,
                "Confirm Undo",
                "This will revert all changes made by the last merge. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.layer.startEditing()
                all_ids = [feat.id() for feat in self.layer.getFeatures()]
                self.layer.deleteFeatures(all_ids)
                self.layer.dataProvider().addFeatures(self.lastMergeBackup)
                self.layer.commitChanges()
                self.refreshTable()
                QMessageBox.information(self, "Info", "Last merge undone.")
                self.lastMergeBackup = None
        else:
            QMessageBox.information(self, "Info", "No merge to undo.")

    def updateSymbology(self):
        farms = set()
        for feat in self.layer.getFeatures():
            f = feat.attribute("FARM_NAME") or ""
            if f.strip():
                farms.add(f.strip())
        categories = []
        for farm in farms:
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            color = QColor(r, g, b)
            symbol = QgsSymbol.defaultSymbol(self.layer.geometryType())
            if symbol.symbolLayerCount() > 0:
                symbol.symbolLayer(0).setFillColor(QColor(0, 0, 0, 0))
                symbol.symbolLayer(0).setStrokeColor(color)
                symbol.symbolLayer(0).setStrokeWidth(1.0)
            category = QgsRendererCategory(farm, symbol, farm)
            categories.append(category)
        if categories:
            renderer = QgsCategorizedSymbolRenderer("FARM_NAME", categories)
            self.layer.setRenderer(renderer)
            self.layer.triggerRepaint()
            iface.mapCanvas().refresh()
        else:
            QMessageBox.information(self, "Symbology", "No FARM_NAME provided for symbology update.")

    def highlightFeature(self):
        self.table.blockSignals(True)
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.layer.removeSelection()
            self.table.blockSignals(False)
            return
        row = selected[0].row()
        fid = self.feat_ids[row]
        self.layer.removeSelection()
        self.layer.selectByIds([fid])
        iface.mapCanvas().zoomToSelected(self.layer)
        self.table.blockSignals(False)

    def onMapSelectionChanged(self, selected, deselected, clearAndSelect):
        self.table.blockSignals(True)
        self.table.clearSelection()
        for i, fid in enumerate(self.feat_ids):
            if fid in selected:
                self.table.selectRow(i)
        self.table.blockSignals(False)

    def saveEdits(self):
        self.layer.startEditing()
        feats = list(self.layer.getFeatures())
        for i, fid in enumerate(self.feat_ids):
            for feat in feats:
                if feat.id() == fid:
                    feat["CLIENT_NAME"] = self.table.item(i, 0).text()
                    feat["FARM_NAME"] = self.table.item(i, 1).text()
                    feat["FIELD_NAME"] = self.table.item(i, 2).text()
                    feat["GROUPE"] = self.table.item(i, 3).text()
                    self.layer.updateFeature(feat)
                    break
        self.layer.commitChanges()

    def clone_feature(feat):
        new_feat = QgsFeature(feat.fields())
        new_feat.setGeometry(feat.geometry())
        new_feat.setAttributes(feat.attributes())
        return new_feat

    def mergeGroups(self):
        self.saveEdits()
        self.lastMergeBackup = [clone_feature(feat) for feat in self.layer.getFeatures()]
        groups = defaultdict(list)
        for feat in self.layer.getFeatures():
            group_val = (feat.attribute("GROUPE") or "").strip()
            if group_val:
                groups[group_val].append(feat)
        for group, feats in groups.items():
            if len(feats) < 2:
                continue
            merged_geom = feats[0].geometry()
            field_names = [feat.attribute("FIELD_NAME") for feat in feats if feat.attribute("FIELD_NAME")]
            merged_field_names = "-".join(field_names)
            for feat in feats[1:]:
                merged_geom = merged_geom.combine(feat.geometry())
            new_poly_type = 0
            if QgsWkbTypes.geometryType(merged_geom.wkbType()) == QgsWkbTypes.PolygonGeometry:
                new_poly_type = 2 if QgsWkbTypes.isMultiType(merged_geom.wkbType()) else 1
            new_attrs = [
                feats[0].attribute("CLIENT_NAME"),
                feats[0].attribute("FARM_NAME"),
                merged_field_names,
                new_poly_type,
                group
            ]
            new_feat = QgsFeature(self.layer.fields())
            new_feat.setGeometry(merged_geom)
            new_feat.setAttributes(new_attrs)
            self.layer.startEditing()
            fids_to_delete = [f.id() for f in feats]
            self.layer.deleteFeatures(fids_to_delete)
            self.layer.addFeature(new_feat)
            self.layer.commitChanges()
        QMessageBox.information(self, "Info", "Groups merged.")
        self.refreshTable()

    def clearGroupBeforeTerminate(self):
        self.layer.startEditing()
        for feat in self.layer.getFeatures():
            feat["GROUPE"] = ""
            self.layer.updateFeature(feat)
        self.layer.commitChanges()

    def terminateAndClearGroup(self):
        self.clearGroupBeforeTerminate()
        self.exportData()
        if hasattr(self, "exported_shp_path"):
            new_name = os.path.splitext(os.path.basename(self.exported_shp_path))[0]
            self.layer.setName(new_name)
            self.setupLabels()
            QMessageBox.information(self, "Info", f"Working layer renamed to {new_name}.")
        self.btnNewProcess.setEnabled(True)

    def exportData(self):
        shp_output_path, _ = QFileDialog.getSaveFileName(self, "Save final shapefile", "", "Shapefile (*.shp)")
        if not shp_output_path:
            QMessageBox.critical(self, "Error", "No save path provided for shapefile.")
            return
        error = QgsVectorFileWriter.writeAsVectorFormat(self.layer, shp_output_path, "UTF-8", self.layer.crs(), "ESRI Shapefile")
        if error[0] != QgsVectorFileWriter.NoError:
            QMessageBox.critical(self, "Error", f"Export error: {error}")
            return
        else:
            QMessageBox.information(self, "Success", "Shapefile exported.")
            self.exported_shp_path = shp_output_path

        client_values = set()
        farm_values = set()
        for feat in self.layer.getFeatures():
            val_client = feat.attribute("CLIENT_NAME")
            val_farm = feat.attribute("FARM_NAME")
            if val_client:
                client_values.add(val_client)
            if val_farm:
                farm_values.add(val_farm)
        default_client = client_values.pop() if len(client_values) == 1 else ""
        default_farm = farm_values.pop() if len(farm_values) == 1 else ""

        metaDialog = MetadataDialog(default_client, default_farm, self)
        if metaDialog.exec_() == QDialog.Accepted:
            global_client, global_farm = metaDialog.getValues()
        else:
            global_client, global_farm = "--", "--"

        metadata = {
            "Version": "1.0",
            "ClientName": global_client,
            "FarmName": global_farm,
            "ShapeDataType": "Boundary"
        }
        base_name = os.path.splitext(os.path.basename(shp_output_path))[0]
        json_filename = os.path.join(os.path.dirname(shp_output_path), f"{base_name}-Deere-Metadata.json")
        with open(json_filename, "w") as json_file:
            json.dump(metadata, json_file, indent=4)
        QMessageBox.information(self, "Success", "Metadata JSON created.")

        zip_output_path, _ = QFileDialog.getSaveFileName(self, "Save ZIP archive", os.path.dirname(shp_output_path), "Zip Files (*.zip)")
        if not zip_output_path:
            QMessageBox.critical(self, "Error", "No save path provided for ZIP.")
            return
        import zipfile
        with zipfile.ZipFile(zip_output_path, 'w') as zipf:
            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                file_path = os.path.splitext(shp_output_path)[0] + ext
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=os.path.basename(file_path))
            if os.path.exists(json_filename):
                zipf.write(json_filename, arcname=os.path.basename(json_filename))
        QMessageBox.information(self, "Success", f"ZIP archive created at:\n{zip_output_path}")

    def resetInterface(self):
        self.globalClientEdit.clear()
        self.globalFarmEdit.clear()
        self.refreshTable()
        self.setupLabels()
        iface.mapCanvas().setExtent(self.layer.extent())
        iface.mapCanvas().refresh()

    def refreshTable(self):
        self.table.setRowCount(0)
        self.loadTable()

    def newProcess(self):
        reply = QMessageBox.question(
            self,
            "Confirm New Process",
            "This will remove the current working layer and start a new process. Proceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if self.layer and self.layer.isValid() and self.layer.id() in QgsProject.instance().mapLayerIds():
                    QgsProject.instance().removeMapLayer(self.layer.id())
            except Exception as e:
                print("Layer removal issue:", e)
            new_zip, _ = QFileDialog.getOpenFileName(self, "Select new FADQ ZIP", "", "Zip Files (*.zip)")
            if not new_zip:
                return
            temp_dir = tempfile.mkdtemp(prefix="FADQ_")
            with zipfile.ZipFile(new_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            shp_file = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith('.shp'):
                        shp_file = os.path.join(root, file)
                        break
                if shp_file:
                    break
            if not shp_file:
                QMessageBox.critical(self, "Error", "No .shp file found in ZIP.")
                return
            new_orig_layer = QgsVectorLayer(shp_file, "Input Layer", "ogr")
            if not new_orig_layer.isValid():
                QMessageBox.critical(self, "Error", "The extracted layer is not valid.")
                return
            crs = "EPSG:4326"
            geom_type = QgsWkbTypes.displayString(new_orig_layer.wkbType())
            new_layer = QgsVectorLayer(f"{geom_type}?crs={crs}", "Working Layer", "memory")
            prov = new_layer.dataProvider()
            fields = QgsFields()
            fields.append(QgsField("CLIENT_NAME", QVariant.String))
            fields.append(QgsField("FARM_NAME", QVariant.String))
            fields.append(QgsField("FIELD_NAME", QVariant.String))
            fields.append(QgsField("POLYGONTYP", QVariant.LongLong))
            fields.append(QgsField("GROUPE", QVariant.String))
            prov.addAttributes(fields)
            new_layer.updateFields()
            new_layer.startEditing()
            for feat in new_orig_layer.getFeatures():
                new_feat = QgsFeature()
                new_feat.setGeometry(feat.geometry())
                new_feat.setFields(new_layer.fields())
                new_feat["CLIENT_NAME"] = ""
                new_feat["FARM_NAME"] = ""
                new_feat["FIELD_NAME"] = feat["NOPAR"] if feat.fields().indexOf("NOPAR") != -1 else ""
                wkb = feat.geometry().wkbType()
                if QgsWkbTypes.geometryType(wkb) == QgsWkbTypes.PolygonGeometry:
                    new_feat["POLYGONTYP"] = 2 if QgsWkbTypes.isMultiType(wkb) else 1
                else:
                    new_feat["POLYGONTYP"] = 0
                new_feat["GROUPE"] = ""
                prov.addFeatures([new_feat])
            new_layer.commitChanges()
            QgsProject.instance().addMapLayer(new_layer)
            new_layer.selectionChanged.connect(self.onMapSelectionChanged)
            self.layer = new_layer
            self.setupLabels()
            zoomToWorkingLayer(self.layer)
            self.loadTable()
            self.btnNewProcess.setEnabled(False)
            QMessageBox.information(self, "Info", "New process loaded successfully.")

if __name__ == '__main__':
    dialog = FeatureTableDialog()
    result = dialog.exec_()  # Mode modal
    if result == QDialog.Accepted:
        print("Dialog closed with acceptance.")
