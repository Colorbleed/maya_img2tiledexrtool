from avalon.vendor.Qt import QtWidgets, QtCore

from . import img2tiledexrtool
from . import mayalib
reload(mayalib)
#import img2tiledexrtool
#import mayalib

class App(QtWidgets.QWidget):
    """Main application for alter settings per render job (layer)"""
    file_nodes = []

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.setObjectName("convertImg2TiledEXR")
        self.setWindowTitle("Image to tiled EXR converter")
        self.setWindowFlags(QtCore.Qt.Window)
        #self.setFixedSize(250, 500)
        self.resize(250,500)

        self.setup_ui()
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
        executable_button.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogOpenButton')))
        executable_hlayout.addWidget(executable_filename)
        executable_hlayout.addWidget(executable_button)

        executable_vlayout.addLayout(executable_hlayout)

        executable_grp.setLayout(executable_vlayout)

        # endregion executable
        # region options
        options_grp = QtWidgets.QGroupBox("Options")
        options_vlayout = QtWidgets.QVBoxLayout()



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
        overwrite_value = QtWidgets.QRadioButton()
        overwrite_value.setChecked(False)
        overwrite_hlayout.addWidget(overwrite_label)
        overwrite_hlayout.addWidget(overwrite_value)

        options_vlayout.addLayout(compression_hlayout)
        options_vlayout.addLayout(linear_hlayout)
        options_vlayout.addLayout(tilesize_hlayout)
        options_vlayout.addLayout(overwrite_hlayout)

        options_grp.setLayout(options_vlayout)
        # endregion options

        # Group box for type of machine list
        list_type_grp = QtWidgets.QGroupBox("Machine List Type")
        list_type_hlayout = QtWidgets.QHBoxLayout()

        black_list = QtWidgets.QRadioButton("Blacklist")
        black_list.setChecked(True)
        black_list.setToolTip("List machines which the job WILL NOT use")

        white_list = QtWidgets.QRadioButton("Whitelist")
        white_list.setToolTip("List machines which the job WILL use")

        list_type_hlayout.addWidget(black_list)
        list_type_hlayout.addWidget(white_list)
        list_type_grp.setLayout(list_type_hlayout)

        # region Machine selection
        file_node_hlayout = QtWidgets.QVBoxLayout()
        file_node_hlayout.setSpacing(2)
        file_node_list = QtWidgets.QListWidget()

        # Buttons
        button_vlayout = QtWidgets.QHBoxLayout()
        button_vlayout.setAlignment(QtCore.Qt.AlignCenter)
        button_vlayout.setSpacing(4)

        add_machine_btn = QtWidgets.QPushButton(">")
        add_machine_btn.setFixedWidth(25)

        remove_machine_btn = QtWidgets.QPushButton("<")
        remove_machine_btn.setFixedWidth(25)

        button_vlayout.addWidget(add_machine_btn)
        button_vlayout.addWidget(remove_machine_btn)

        file_node_hlayout.addWidget(file_node_list)
        file_node_hlayout.addLayout(button_vlayout)

        layout.addWidget(executable_grp)
        layout.addWidget(options_grp)
        layout.addWidget(list_type_grp)
        layout.addLayout(file_node_hlayout)

        # Enable access for all methods
        self.file_node_list = file_node_list
        self.black_list = black_list
        self.white_list = white_list

        self.compression_value = compression_value
        self.linear_value = linear_value
        self.tilesize_value = tilesize_value
        self.executable_filename = executable_filename

        self.setLayout(layout)

    def create_compression_options(self):
        compressions = ['none', 'rle', 'zip', 'zips', 'piz', 'pxr24', 'b44', 'b44a', 'dwaa', 'dwab']

        for compression in compressions:
            self.compression_value.addItem(compression)
        self.compression_value.setCurrentIndex(3)

    def create_linearcolor_options(self):
        choises = ['auto', 'on', 'off']
        for choise in choises:
            self.linear_value.addItem(choise)
        self.linear_value.setCurrentIndex(2)
        
    def populate_file_list(self):
        self.file_node_list.clear()
        self.file_nodes = mayalib.get_file_texture_nodes()
        for node in self.file_nodes:
            self.file_node_list.append(node)

    def refresh(self):

        self.compression_value.clear()
        self.linear_value.clear()

        self.create_compression_options()
        self.create_linearcolor_options()

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