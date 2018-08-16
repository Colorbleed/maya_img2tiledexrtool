"""
This module contains the UI parts for the mg2tiledexr toolset

In Maya running this script without a selection will show all file nodes in
scene. If a selection is made, it will filter and show all file nodes in your
selection.
"""
from avalon.vendor.Qt import QtWidgets, QtCore, QtGui
import os

# Workaround to PyCharm not autocompleting, without mucking in Qt.py source.
# if False: from PyQt5 import QtWidgets, QtCore, QtGui

from . import mayalib

# reload(mayalib)


class CustomListModel(QtCore.QAbstractListModel):
    """
    Custom model for our listview that shows an icon and node name
    """
    def __init__(self, data, parent=None):
        super(CustomListModel, self).__init__(parent)
        self.items = data
        index = QtCore.QModelIndex()
        self.beginInsertRows(index, 0, len(data))
        for item in data:
            self.beginInsertRows(index, 0, 0)
            pass
        self.endInsertRows()

        self.icons = []
        app_path = os.path.dirname(os.path.realpath(__file__))
        self.icons.append(QtGui.QIcon(os.path.join(app_path, 'res/not_converted.png')))
        self.icons.append(QtGui.QIcon(os.path.join(app_path, 'res/source.png')))
        self.icons.append(QtGui.QIcon(os.path.join(app_path, 'res/exr.png')))
        # self.icons.append(QtGui.QIcon('res/not_converted.png'))
        # self.icons.append(QtGui.QIcon('res/source.png'))
        # self.icons.append(QtGui.QIcon('res/exr.png'))

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.items)

    def data(self, index, role=None):
        if not index.isValid() or not (
                0 <= index.row() < len(self.items)):  return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:
            return self.items[index.row()][1]
        elif role == QtCore.Qt.DecorationRole:
            return self.icons[self.items[index.row()][0]]
        elif role == QtCore.Qt.UserRole:
            return self.items[index.row()]

    # def addItems(self):
    #     for key in self.modelDict:
    #         index=QtCore.QModelIndex()
    #         self.beginInsertRows(index, 0, 0)
    #         self.items.append(key)
    #     self.endInsertRows()


# class CustomList(QtWidgets.QListView):
#     def __init__(self, parent=None):
#         super(CustomList, self).__init__(parent)


class App(QtWidgets.QWidget):
    """Main application for tiled EXR conversion"""
    file_nodes = []

    def __init__(self, parent=None):
        #QtWidgets.QWidget.__init__(self, parent)
        super(App, self).__init__(parent)
        self.setObjectName("convertImg2TiledEXR")
        self.setWindowTitle("Image to tiled EXR converter")
        self.setWindowFlags(QtCore.Qt.Window)
        # self.setFixedSize(250, 500)
        self.resize(480, 800)

        self.setup_ui()
        self.setup_connections()

        self.postfix_value.setText("_tiled")
        self.create_compression_options()
        self.create_linearcolor_options()

        self.populate_file_list()
        self.executable_filename.setText(mayalib.get_tiled_exr_exe_dir())

    def setup_ui(self):
        """Build the initial UI"""
        layout = QtWidgets.QVBoxLayout(self)

        # region executable
        executable_grp = QtWidgets.QGroupBox("Executable")
        executable_vlayout = QtWidgets.QVBoxLayout()

        executable_hlayout = QtWidgets.QHBoxLayout()
        executable_filename = QtWidgets.QLineEdit()
        executable_button = QtWidgets.QPushButton()
        executable_button.setIcon(self.style().standardIcon(
            getattr(QtWidgets.QStyle, 'SP_DialogOpenButton')))
        executable_hlayout.addWidget(executable_filename)
        executable_hlayout.addWidget(executable_button)

        executable_vlayout.addLayout(executable_hlayout)
        executable_grp.setLayout(executable_vlayout)
        # endregion executable

        # region options
        options_grp = QtWidgets.QGroupBox("Options")
        options_vlayout = QtWidgets.QVBoxLayout()

        postfix_hlayout = QtWidgets.QHBoxLayout()
        postfix_label = QtWidgets.QLabel("Postfix")
        postfix_value = QtWidgets.QLineEdit()
        postfix_hlayout.addWidget(postfix_label)
        postfix_hlayout.addWidget(postfix_value)

        compression_hlayout = QtWidgets.QHBoxLayout()
        compression_label = QtWidgets.QLabel("Compression")
        compression_value = QtWidgets.QComboBox()
        compression_hlayout.addWidget(compression_label)
        compression_hlayout.addWidget(compression_value)

        linear_hlayout = QtWidgets.QHBoxLayout()
        linear_label = QtWidgets.QLabel("Linear Conversion")
        linear_value = QtWidgets.QComboBox()
        linear_hlayout.addWidget(linear_label)
        linear_hlayout.addWidget(linear_value)

        tilesize_hlayout = QtWidgets.QHBoxLayout()
        tilesize_label = QtWidgets.QLabel("Tile Size")
        tilesize_value = QtWidgets.QSpinBox()
        tilesize_value.setValue(64)
        tilesize_hlayout.addWidget(tilesize_label)
        tilesize_hlayout.addWidget(tilesize_value)

        overwrite_hlayout = QtWidgets.QHBoxLayout()
        overwrite_label = QtWidgets.QLabel("Overwrite")
        overwrite_value = QtWidgets.QCheckBox()
        overwrite_value.setChecked(False)
        overwrite_hlayout.addWidget(overwrite_label)
        overwrite_hlayout.addWidget(overwrite_value)

        preserve_hlayout = QtWidgets.QHBoxLayout()
        preserve_label = QtWidgets.QLabel("Preserve Color Space ")
        preserve_value = QtWidgets.QCheckBox()
        preserve_value.setChecked(True)
        preserve_hlayout.addWidget(preserve_label)
        preserve_hlayout.addWidget(preserve_value)

        options_vlayout.addLayout(postfix_hlayout)
        options_vlayout.addLayout(compression_hlayout)
        options_vlayout.addLayout(linear_hlayout)
        options_vlayout.addLayout(tilesize_hlayout)
        options_vlayout.addLayout(overwrite_hlayout)
        options_vlayout.addLayout(preserve_hlayout)

        options_grp.setLayout(options_vlayout)
        # endregion options

        # Group box for type of machine list
        list_type_grp = QtWidgets.QGroupBox("File Texture Nodes")
        list_type_hlayout = QtWidgets.QVBoxLayout()

        refresh_button = QtWidgets.QPushButton("Refresh")
        refresh_button.setToolTip("Refresh texture lists")
        refresh_button.setIcon(self.style().standardIcon(
            getattr(QtWidgets.QStyle, 'SP_BrowserReload')))

        # region file node list
        file_node_hlayout = QtWidgets.QVBoxLayout()
        file_node_hlayout.setSpacing(2)
        file_node_list = QtWidgets.QListView()
        file_node_list.setAlternatingRowColors(True)
        file_node_list.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        file_node_list.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection)
        # endregion

        # conversion buttons
        button_vlayout = QtWidgets.QHBoxLayout()
        button_vlayout.setAlignment(QtCore.Qt.AlignCenter)
        button_vlayout.setSpacing(4)

        convert_button = QtWidgets.QPushButton("Convert")
        exr_button = QtWidgets.QPushButton("Show EXR")
        source_button = QtWidgets.QPushButton("Show Source")
        set_source_button = QtWidgets.QPushButton("Set new source")
        set_source_button.setDisabled(True)

        button_vlayout.addWidget(convert_button)
        button_vlayout.addWidget(exr_button)
        button_vlayout.addWidget(source_button)
        button_vlayout.addWidget(set_source_button)

        file_node_hlayout.addWidget(file_node_list)
        file_node_hlayout.addLayout(button_vlayout)

        list_type_hlayout.addWidget(refresh_button)
        list_type_hlayout.addLayout(file_node_hlayout)
        list_type_grp.setLayout(list_type_hlayout)

        layout.addWidget(executable_grp)
        layout.addWidget(options_grp)
        layout.addWidget(list_type_grp)
        layout.addLayout(file_node_hlayout)

        # Enable access for all methods
        self.file_node_list = file_node_list
        self.postfix_value = postfix_value
        self.compression_value = compression_value
        self.linear_value = linear_value
        self.tilesize_value = tilesize_value
        self.executable_filename = executable_filename
        self.exr_button = exr_button
        self.source_button = source_button
        self.convert_button = convert_button
        self.refresh_button = refresh_button
        self.overwritevalue = overwrite_value
        self.preserve_value = preserve_value

        self.setLayout(layout)

    def setup_connections(self):
        self.refresh_button.clicked.connect(self.refresh)
        self.exr_button.clicked.connect(self.show_exr)
        self.source_button.clicked.connect(self.show_source)
        self.convert_button.clicked.connect(self.convert)

    def create_compression_options(self):
        compressions = ['none', 'rle', 'zip', 'zips', 'piz', 'pxr24', 'b44',
                        'b44a', 'dwaa', 'dwab']

        for compression in compressions:
            self.compression_value.addItem(compression)
        self.compression_value.setCurrentIndex(3)

    def create_linearcolor_options(self):
        choices = ['auto', 'on', 'off']
        for choise in choices:
            self.linear_value.addItem(choise)
        self.linear_value.setCurrentIndex(2)

    def populate_file_list(self):
        self.file_nodes = mayalib.get_file_texture_model_data()
        self.file_node_list.reset()
        table_model = CustomListModel(self.file_nodes)
        self.file_node_list.setModel(table_model)

    def refresh(self):
        # self.create_compression_options()
        # self.create_linearcolor_options()
        print('refreshing')
        self.populate_file_list()

    def show_exr(self):
        self.show_source(False)

    def show_source(self, source=True):
        indices = self.file_node_list.selectedIndexes()
        nodes = []
        indices = self.file_node_list.selectedIndexes()
        for id in indices:
            nodes.append(self.file_node_list.model().index(id.row()).data(role=QtCore.Qt.UserRole))
        mayalib.revert_nodes(nodes, self.postfix_value.text(), source, self.preserve_value.isChecked())
        self.refresh()
        # for index in indices:
        #     self.file_node_list.selectionModel().select(index,
        #                                                 QtCore.QItemSelectionModel.Select)

    def convert(self):
        nodes = []
        indices = self.file_node_list.selectedIndexes()
        for id in indices:
            nodes.append(self.file_node_list.model().index(id.row()).data(role=QtCore.Qt.UserRole))
        self.convert_button.setDisabled(True)
        self.source_button.setDisabled(True)
        self.exr_button.setDisabled(True)
        #self.set_source_button.setDisabled(True)
        try:
            mayalib.convert_files(self.executable_filename.text(), nodes,
                                  preserve = self.preserve_value.isChecked(),
                                  threads=8,
                                  overwrite=self.overwritevalue.isChecked(),
                                  compression=self.compression_value.currentText(),
                                  linear=self.linear_value.currentText(),
                                  postfix=self.postfix_value.text(),
                                  tile_size=self.tilesize_value.value())
        except Exception as e:
            raise e
        finally:
            self.convert_button.setDisabled(False)
            self.source_button.setDisabled(False)
            self.exr_button.setDisabled(False)
        self.refresh()


def launch():
    global application

    toplevel_widgets = QtWidgets.QApplication.topLevelWidgets()
    mainwindow = next(widget for widget in toplevel_widgets if
                      widget.objectName() == "MayaWindow")

    application = App(parent=mainwindow)
    application.show()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    test = App()
    test.show()
    app.exec_()
