import os
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from ui_manager import MainUI
from functions import resource_path

if __name__ == "__main__":

    # Environment variables
    os.environ["ICON_PATH"] = resource_path(os.path.join("style", "icon.png"))
    os.environ["PATCH_FOLDER"] = resource_path(os.path.join("..", "image_path"))
    os.environ["DATABASE"] = resource_path(
        os.path.join("..", "DB_warning_overwrite_on_execution.csv")
    )
    os.environ["RESULT_FOLDER"] = resource_path(
        os.path.join("..", "Classification_Results")
    )
    if not os.path.exists(os.environ["RESULT_FOLDER"]):
        os.makedirs(os.environ["RESULT_FOLDER"])

    os.environ["INTERMIN_SAVED"] = resource_path(os.path.join("..", "Intermin_Saved"))
    if not os.path.exists(os.environ["INTERMIN_SAVED"]):
        os.makedirs(os.environ["INTERMIN_SAVED"])

    os.environ["MAGNIFICATION_RATIO"] = "2"
    os.environ["PATCH_MAGNIFICATION"] = (
        "20X"  # The magnification level of the saved patch
    )
    os.environ["DEFAULT_MAGNIFICATION"] = (
        "20X"  # The magnification level of the default displayed patch
    )

    app = QApplication(sys.argv)

    icon_path = os.environ["ICON_PATH"]
    viewer = MainUI()
    viewer.setWindowTitle("PathoPatch Classification Helper")
    viewer.setWindowIcon(QIcon(icon_path))
    viewer.show()

    sys.exit(app.exec_())
