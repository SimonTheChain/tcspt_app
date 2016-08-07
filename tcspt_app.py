import hashlib
import os
import sys
import time
import lxml.etree as etree
from PyQt4 import QtCore, QtGui

import tcspt_app_ui as mainframe
import tcspt_app_settings as settings


def hashfile(afile, hasher, blocksize=65536):
    """
    Generates checksums
    :param afile: file to process
    :param hasher: checksum algorithm
    :param blocksize: size of the buffer
    :return: checksum
    """
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    afile.seek(0)
    return hasher.hexdigest()


class Md5(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        settings.file_md5 = hashfile(open(settings.fichier, 'rb'), hashlib.md5())


class TcsptApp(QtGui.QMainWindow, mainframe.Ui_TcsptWindow):
    def __init__(self, parent=None):
        super(TcsptApp, self).__init__(parent)

        self.md5_thread = Md5()

        self.setupUi(self)

        self.ingest_btn.clicked.connect(self.ingest_dlg)
        self.source_btn.clicked.connect(self.source_dlg)
        self.checksum_btn.clicked.connect(self.checksum)
        self.stop_btn.clicked.connect(self.stop)
        self.export_btn.clicked.connect(self.export)

        self.show()

    def ingest_dlg(self):
        settings.xml_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate source xml file",
                directory=settings.directory,
                filter="Xml files (*.xml)"))

        if settings.xml_path:
            settings.directory = os.path.dirname(settings.xml_path)
            self.ingest_lbl.setText(os.path.basename(settings.xml_path))

    def source_dlg(self):
        settings.fichier = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        if settings.fichier:
            settings.directory = os.path.dirname(settings.fichier)
            settings.file_name = os.path.basename(settings.fichier)
            settings.file_path = os.path.dirname(settings.fichier)
            settings.file_size = os.path.getsize(settings.fichier)
            self.file_name_lbl.setText(settings.file_name)
            self.file_path_lbl.setText(settings.file_path)
            self.file_size_lbl.setText(str(settings.file_size))

    def checksum(self):
        if settings.file_path == "":
            path_msg = QtGui.QMessageBox()

            path_msg.setIcon(QtGui.QMessageBox.Information)
            path_msg.setText("Please select a a file to process.")
            path_msg.setWindowTitle("Input needed")
            path_msg.setStandardButtons(QtGui.QMessageBox.Ok)
            path_msg.exec_()
            return

        else:
            self.checksum_lbl.setText("")
            self.stop_btn.setEnabled(True)
            self.checksum_btn.setEnabled(False)
            self.checksum_progress.setRange(0, 0)
            self.connect(self.md5_thread, QtCore.SIGNAL("finished()"), self.checksum_done)
            self.md5_thread.start()

    def stop(self):
        self.md5_thread.terminate()
        self.stop_btn.setEnabled(False)
        self.checksum_btn.setEnabled(True)
        self.checksum_progress.setRange(0, 1)
        self.checksum_progress.setValue(0)

    def checksum_done(self):
        self.stop_btn.setEnabled(False)
        self.checksum_btn.setEnabled(True)
        self.checksum_lbl.setText(settings.file_md5)
        self.checksum_progress.setRange(0, 1)
        self.checksum_progress.setValue(1)

    def export(self):
        xml_data = etree.parse(settings.xml_path)
        root = xml_data.getroot()

        xml_file_name = root.xpath("//django-objects/object/field[@name='file_name']")
        xml_file_path = root.xpath("//django-objects/object/field[@name='file_path']")
        xml_file_size = root.xpath("//django-objects/object/field[@name='file_size']")
        xml_file_md5 = root.xpath("//django-objects/object/field[@name='file_md5']")

        xml_file_name[0].text = settings.file_name
        xml_file_path[0].text = settings.file_path
        xml_file_size[0].text = str(settings.file_size)
        xml_file_md5[0].text = settings.file_md5

        f = open(settings.xml_path, "w")
        f.write(etree.tostring(root))
        f.close()

        self.export_lbl.setText("Xml modified at %s." % time.strftime("%X"))


def main():
    app = QtGui.QApplication(sys.argv)
    gui = TcsptApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

