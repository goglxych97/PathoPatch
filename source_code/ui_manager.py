import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QShortcut, QHBoxLayout, QWidget
from PyQt5.QtGui import QKeySequence
from image_viewer import ImageViewer
from classification_manager import ClassificationManager
from functions import get_sorted_files, create_classification_csv


class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()

        images_path = os.environ["PATCH_FOLDER"]
        results_path = os.environ["RESULT_FOLDER"]
        intermin_saved = os.environ["INTERMIN_SAVED"]

        image_files = get_sorted_files(images_path)
        df = create_classification_csv(image_files, results_path)  # Database Initialize

        # Setup UI
        self.base_width = 900
        self.base_height = 600
        self.base_margin = 15

        self.resize(self.base_width, self.base_height)
        self.setMinimumSize(self.base_width, self.base_height)

        self.image_viewer = ImageViewer(df, images_path)
        self.classification_manager = ClassificationManager(
            results_path,
            intermin_saved,
            self.image_viewer.get_current_image_path,
        )

        self.setup_ui()
        self.shortcuts()
        self.image_viewer.image_changed.connect(self.update_classification_view)

    def setup_ui(self):
        self.update_widget_sizes()

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.image_viewer)
        main_layout.addWidget(self.classification_manager)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def shortcuts(self):
        shortcut1 = QShortcut(QKeySequence("Ctrl+Left"), self)
        shortcut1.activated.connect(self.image_viewer.prev_button.animateClick)
        shortcut2 = QShortcut(QKeySequence("Ctrl+Right"), self)
        shortcut2.activated.connect(self.image_viewer.next_button.animateClick)

        shortcut3 = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut3.activated.connect(lambda: self.click_button(0))
        shortcut4 = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut4.activated.connect(lambda: self.click_button(1))
        shortcut5 = QShortcut(QKeySequence("Ctrl+3"), self)
        shortcut5.activated.connect(lambda: self.click_button(2))
        shortcut6 = QShortcut(QKeySequence("Ctrl+4"), self)
        shortcut6.activated.connect(lambda: self.click_button(3))

    def click_button(self, button_index):
        # Make the button at button_index click
        if button_index < len(self.image_viewer.buttons):
            button = list(self.image_viewer.buttons.values())[button_index]
            button.setChecked(True)  # Ensure the button is selected
            button.clicked.emit()  # Trigger the button's click event

    def update_widget_sizes(self):
        margin_ratio_width = self.base_margin / self.base_width
        margin_ratio_height = self.base_margin / self.base_height

        margin_w = int(self.width() * margin_ratio_width)
        margin_h = int(self.height() * margin_ratio_height)

        half_width = self.width() // 2 - margin_w
        full_height = self.height() - margin_h

        self.image_viewer.setFixedWidth(half_width)
        self.classification_manager.setFixedWidth(half_width)
        self.image_viewer.setFixedHeight(full_height)
        self.classification_manager.setFixedHeight(full_height)

    def update_classification_view(self, image_path):
        self.classification_manager.update_classification_status(image_path)

    def resizeEvent(self, event):
        self.update_widget_sizes()
        super().resizeEvent(event)
