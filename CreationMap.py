# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CreationMap
                                 A QGIS plugin
 Ce plugin réalise une carte de densité des communes à partir d’une région sélectionnée par l’utilisateur
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-12-30
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Université Paris 8
        email                : laurentwu123@gmail.com
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

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from .CreationMap_dialog import CreationMapDialog
from .resources import *
import os.path
import processing
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt5.QtCore import QVariant
from qgis.utils import iface
from PyQt5.QtWidgets import QProgressBar, QVBoxLayout, QApplication
import time
from PyQt5.QtWidgets import (
    QFileDialog,
    QAbstractItemView,
    QDialogButtonBox,
    QMessageBox,
)
from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsField,
    QgsDistanceArea,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange,
    QgsSymbol,
)


from PyQt5.QtWidgets import QDialog, QProgressBar, QVBoxLayout, QLabel


class CustomProgressDialog(QDialog):

    """
    Class permettant la création et la configuration
    de la progress bar pour les différents traitements
    """

    def __init__(self, title, message, max_value):
        super(CustomProgressDialog, self).__init__()

        self.setWindowTitle(title)

        self.layout = QVBoxLayout(self)

        self.label = QLabel(message)
        self.layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(max_value)
        self.layout.addWidget(self.progress_bar)

        self.setStyleSheet(
            """
            QDialog {
                background-color: rgb(72, 60, 50);
                color: white;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: rgb(72, 60, 50);
                color: white;
            }
            QProgressBar::chunk {
                background-color: #6fa053;
                margin: 0px;
            }
        """
        )

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        time.sleep(0.5)
        QApplication.processEvents()


class CreationMap:

    """
    Class permettant la création du plugin à
    partir de ses différents traitements
    """

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "CreationMap_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr("&CreationMap")

        self.first_start = None

        self.message_box_style = """
        QMessageBox {
                        background-color: rgb(72, 60, 50);
                        font-size: 14px;
                        font-family: Arial;
                    }
                    QMessageBox QLabel {
                        color: white;
                    }
                    QPushButton {
                        background-color: rgb(226, 220, 193);
                        border-style: solid;
                        border-width: 2px;
                        border-radius: 10px;
                        padding: 6px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: rgb(72, 60, 50);
                        color: rgb(226, 220, 193);
                    }
                    QPushButton:pressed {
                        background-color: #d3cdb4;
                        color:black
                    }
        """

        self.commune_layer = None
        self.population_layer = None
        self.distance_area = QgsDistanceArea()
        self.distance_area.setEllipsoid("WGS84")
        self.layer_provider = None

    def tr(self, message):
        return QCoreApplication.translate("CreationMap", message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def on_apply_clicked(self):
        if not self.check_region_selection():
            return
        self.attribute_join()

    def initGui(self):
        icon_path = ":/plugins/CreationMap/icon.png"
        self.add_action(
            icon_path,
            text=self.tr(""),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr("&CreationMap"), action)
            self.iface.removeToolBarIcon(action)

    def selectShapefileCommune(self):
        """
        Sélection de la couche commune dans l'input de mon form
        avec gestion d'erreur
        """

        filename, _ = QFileDialog.getOpenFileName(
            self.dlg,
            "Sélectionner un Shapefile pour les communes",
            "",
            "Shapefiles (*.shp)",
        )
        if filename:
            layer_name = "commune"
            layer = QgsVectorLayer(filename, layer_name, "ogr")
            if not layer.isValid():
                QMessageBox.critical(
                    self.dlg,
                    "Erreur de chargement",
                    "Échec du chargement du Shapefile pour les communes.",
                )
                return

            if "region" not in [field.name() for field in layer.fields()]:
                QMessageBox.warning(
                    self.dlg,
                    "Champ 'region' manquant",
                    "Le fichier sélectionné ne contient pas le champ 'region'. Veuillez choisir un fichier valide.",
                )
                return

            QgsProject.instance().addMapLayer(layer)
            self.commune_layer = layer
            self.dlg.input_commune.setText(filename)

            fields = layer.fields()
            field_names = [field.name() for field in fields]
            self.dlg.commune_join.clear()
            self.dlg.commune_join.addItems(field_names)
            self.updateRegionList(layer, "region")

    def selectShapefilePopulation(self):
        """
        Sélection de la couche population dans l'input de mon form
        avec gestion d'erreur
        """

        filename, _ = QFileDialog.getOpenFileName(
            self.dlg,
            "Sélectionner un Shapefile pour la population",
            "",
            "Shapefiles (*.shp)",
        )
        if filename:
            self.loadShapefile(filename, "population")

    def loadShapefile(self, filename, layer_type):
        """
        Charge les deux couches sur le projet QGIS actuel
        et met à jour les informations dans le plugin
        """

        layer_name = f"{layer_type}"
        layer = QgsVectorLayer(filename, layer_name, "ogr")
        if not layer.isValid():
            print(f"Échec du chargement du Shapefile pour {layer_type}.")
            return None

        QgsProject.instance().addMapLayer(layer)
        if layer_type == "commune":
            self.dlg.input_commune.setText(filename)
            self.commune_layer = layer
            fields = layer.fields()
            field_names = [field.name() for field in fields]
            self.dlg.commune_join.clear()
            self.dlg.commune_join.addItems(field_names)
            self.updateRegionList(layer, "region")
        elif layer_type == "population":
            self.dlg.input_population.setText(filename)
            self.population_layer = layer
            fields = layer.fields()
            field_names = [field.name() for field in fields]
            self.dlg.population_join.clear()
            self.dlg.population_join.addItems(field_names)

        return layer

    def updateRegionList(self, layer, region_field_name):
        """
        Affiche la liste des régions lorsque la couche
        commune est chargée
        """

        regions = set()
        for feature in layer.getFeatures():
            region = str(feature[region_field_name])
            if region != "NULL":
                regions.add(str(region))

        model = QStandardItemModel()

        for region in sorted(regions):
            item = QStandardItem(region)
            model.appendRow(item)

        self.dlg.list_region.setModel(model)
        self.dlg.list_region.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def check_region_selection(self):
        """
        Vérifie si une région à été sélectionnée dans le plugin en
        affichant une popup
        """

        index = self.dlg.list_region.currentIndex()
        if not index.isValid():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Sélection de région manquante")
            msg_box.setText(
                "Aucune région n'a été sélectionnée. \nVoulez-vous continuer sans sélectionner de région. \n(ATTENTION : Temps de traitement très long)"
            )
            msg_box.setStyleSheet(self.message_box_style)
            continue_button = msg_box.addButton("Continuer", QMessageBox.AcceptRole)
            msg_box.addButton("Retour", QMessageBox.RejectRole)

            msg_box.exec_()

            if msg_box.clickedButton() == continue_button:
                return True
            else:
                return False
        return True

    def create_custom_message_box(self, icon, title, text):
        """
        Création d'une popup personnalisée
        """
        msg_box = QMessageBox()
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)

        msg_box.setStyleSheet(self.message_box_style)
        return msg_box

    def create_custom_message_box_with_progress(self, title, text, max_value):
        """
        Création d'une popup personnalisée pour la barre de chargement
        """

        self.msg_box = QMessageBox()
        self.msg_box.setIcon(QMessageBox.Information)
        self.msg_box.setWindowTitle(title)
        self.msg_box.setText(text)

        self.progress_bar = QProgressBar(self.msg_box)
        self.progress_bar.setMaximum(max_value)

        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        self.msg_box.setLayout(layout)

        self.msg_box.show()
        return self.msg_box

    def attribute_join(self):
        """
        Effectue la jointure attributaire ainsi que les autres pipelines par dessus
        """

        steps = 7
        progress_dialog = CustomProgressDialog(
            "Processing", "Processus en cours...", steps
        )
        progress_dialog.show()
        progress_dialog.update_progress(1)
        if self.commune_layer is not None and self.population_layer is not None:
            field_commune = self.dlg.commune_join.currentText()
            field_population = self.dlg.population_join.currentText()
            params_jointure = {
                "DISCARD_NOMATCHING": False,
                "FIELD": field_commune,
                "FIELD_2": field_population,
                "INPUT": self.commune_layer,
                "INPUT_2": self.population_layer,
                "METHOD": 0,
                "PREFIX": "",
                "OUTPUT": "memory:",
            }

            resultat = processing.run("native:joinattributestable", params_jointure)
            progress_dialog.update_progress(2)
            if resultat and resultat["OUTPUT"]:
                attribute_layer = resultat["OUTPUT"]

                total_features = attribute_layer.featureCount()
                non_empty_cod_com = sum(
                    1 for feature in attribute_layer.getFeatures() if feature["cod_com"]
                )
                non_empty_ptot = sum(
                    1 for feature in attribute_layer.getFeatures() if feature["ptot"]
                )

                pourcentage_cod_com = (non_empty_cod_com / total_features) * 100
                pourcentage_ptot = (non_empty_ptot / total_features) * 100
                progress_dialog.update_progress(3)
                if pourcentage_cod_com >= 80 and pourcentage_ptot >= 80:
                    self.filter_region(attribute_layer)
                    progress_dialog.update_progress(4)
                    self.calculate_density(attribute_layer)
                    self.set_density_symbology(attribute_layer)
                    progress_dialog.update_progress(5)
                    QgsProject.instance().addMapLayer(attribute_layer)
                    self.create_centroids(attribute_layer)
                    QgsProject.instance().layerTreeRoot().findLayer(
                        self.commune_layer.id()
                    ).setItemVisibilityChecked(False)
                    progress_dialog.update_progress(7)
                    QgsProject.instance().layerTreeRoot().findLayer(
                        self.population_layer.id()
                    ).setItemVisibilityChecked(False)
                    progress_dialog.close()
                    msg_box = self.create_custom_message_box(
                        QMessageBox.Information,
                        "Succès",
                        "Jointure réussie avec suffisamment de données.",
                    )
                    self.dlg.close()
                else:
                    QgsProject.instance().removeMapLayer(attribute_layer)
                    msg_box = self.create_custom_message_box(
                        QMessageBox.Warning,
                        "Erreur",
                        "Champs de jointure invalide.",
                    )
                msg_box.exec_()
            else:
                msg_box = self.create_custom_message_box(
                    QMessageBox.Critical,
                    "Erreur",
                    "Échec de la jointure des couches",
                )
                msg_box.exec_()

        else:
            msg_box = self.create_custom_message_box(
                QMessageBox.Warning,
                "Erreur du processus",
                "L'une des couches est non valide.",
            )
            msg_box.exec_()

    def filter_region(self, attribute_layer):
        """
        Filtre les régions sélectionnées par l'utilisateur
        """

        if self.commune_layer is not None:
            index = self.dlg.list_region.currentIndex()
            if index.isValid():
                region = index.data()
                print("---")
                print(region)
                attribute_layer.setName(f"map_density_{region}")
                expression = "\"region\" = '{}'".format(region)
                attribute_layer.setSubsetString(expression)

    def calculate_density(self, attribute_layer):
        """
        Calcul la densité à partir de la population et l'aire
        """

        try:
            layer_provider = attribute_layer.dataProvider()
            fields_to_add = []
            if layer_provider.fieldNameIndex("area") == -1:
                fields_to_add.append(QgsField("area", QVariant.Double))
            if layer_provider.fieldNameIndex("density") == -1:
                fields_to_add.append(QgsField("density", QVariant.Double))

            if fields_to_add:
                layer_provider.addAttributes(fields_to_add)
                attribute_layer.updateFields()

            attribute_layer.startEditing()
            field_index_area = attribute_layer.fields().indexFromName("area")
            field_index_density = attribute_layer.fields().indexFromName("density")

            for feature in attribute_layer.getFeatures():
                try:
                    area = self.distance_area.measureArea(feature.geometry()) / 1e6
                    feature.setAttribute(field_index_area, area)

                    density = 0
                    pop = feature["ptot"]
                    if pop is not None and area > 0:
                        density = pop / area

                    feature.setAttribute(field_index_density, density)
                    attribute_layer.updateFeature(feature)
                except Exception as e:
                    pass

            attribute_layer.commitChanges()

        except Exception as e:
            print(f"Erreur lors du traitement des données : {e}")

    def set_density_symbology(self, attribute_layer):
        """
        Edit la symbologie des couleurs pour la carte de densité
        """

        symbol = QgsSymbol.defaultSymbol(attribute_layer.geometryType())

        yellow_symbol = symbol.clone()
        yellow_symbol.setColor(QColor("Yellow"))
        yellow_range = QgsRendererRange(0, 100, yellow_symbol, "Densité Faible")

        orange_symbol = symbol.clone()
        orange_symbol.setColor(QColor("Orange"))
        orange_range = QgsRendererRange(100, 200, orange_symbol, "Densité Moyenne")

        red_symbol = symbol.clone()
        red_symbol.setColor(QColor("Red"))
        red_range = QgsRendererRange(200, float("inf"), red_symbol, "Densité Forte")

        renderer = QgsGraduatedSymbolRenderer(
            "density", [yellow_range, orange_range, red_range]
        )

        attribute_layer.setRenderer(renderer)

        attribute_layer.triggerRepaint()
        iface.layerTreeView().refreshLayerSymbology(attribute_layer.id())

    def create_centroids(self, attribute_layer):
        """
        Créer les centroids au centre de mes objets
        """

        params_centroides = {
            "INPUT": attribute_layer,
            "OUTPUT": "memory:",
        }

        res = processing.run("native:centroids", params_centroides)

        if res and res["OUTPUT"]:
            layer_centroides = res["OUTPUT"]
            layer_centroides.setName("centroid_point")
            QgsProject.instance().addMapLayer(layer_centroides)
        else:
            msg_box = self.create_custom_message_box(
                QMessageBox.Warning,
                "Erreur du processus",
                "L'une des couches est non valide.",
            )
            msg_box.exec_()

    def run(self):
        if self.first_start is True:
            self.first_start = False
            self.dlg = CreationMapDialog()
            self.dlg.button_commune.clicked.connect(self.selectShapefileCommune)
            self.dlg.button_population.clicked.connect(self.selectShapefilePopulation)
            self.dlg.button_box.button(QDialogButtonBox.Apply).clicked.connect(
                self.on_apply_clicked
            )

        self.dlg.show()
