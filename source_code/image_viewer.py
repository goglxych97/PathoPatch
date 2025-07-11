import os
import pandas as pd
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QButtonGroup,
    QApplication,
    QToolButton,
    QDialog,
    QComboBox,
)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal
from functions import resource_path, generate_magnification_dict


class ImageViewer(QWidget):
    image_changed = pyqtSignal(str)

    def __init__(self, df, images_path):
        super().__init__()
        self.image_files = df["file_name"].tolist() if "file_name" in df.columns else []
        del df

        with open(resource_path("style/image_viewer.qss"), "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

        self.magnifications = generate_magnification_dict()
        self.default_magnification = os.environ["DEFAULT_MAGNIFICATION"]
        self.current_magnification = self.default_magnification
        self.images_path = images_path
        self.image_index = 0
        self.pixmap = None
        self.set_ui()
        self.update_ui()
        self.select_default_magnification()
        QApplication.processEvents()
        self.update_image()

    def set_ui(self):
        self.image_label = QLabel()
        self.file_name_label = QLabel()
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems([f.split("_x_")[0] for f in self.image_files])
        self.image_dropdown.showPopup = self.show_popup_with_update
        self.image_dropdown.currentIndexChanged.connect(self.dropdown_image_change)
        self.info_button = QToolButton()
        self.info_button.setText("?")
        self.info_button.setFixedSize(20, 20)
        self.info_button.clicked.connect(self.show_info_popup)

        label_layout = QHBoxLayout()
        label_layout.addWidget(self.file_name_label)
        label_layout.addWidget(self.info_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_dropdown)
        main_layout.addLayout(label_layout)

        self.buttons = {mag: QPushButton(mag) for mag in self.magnifications.keys()}
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for button in self.buttons.values():
            button.setCheckable(True)
            button.clicked.connect(self.change_magnification)

            self.button_group.addButton(button)

        mag_button_layout = QHBoxLayout()
        mag_button_layout.setAlignment(Qt.AlignLeft)

        for button in self.buttons.values():
            mag_button_layout.addWidget(button)

        image_layout = QVBoxLayout()
        image_layout.addLayout(mag_button_layout)
        image_layout.addWidget(self.image_label)

        self.prev_button = QPushButton("<< Prev")
        self.next_button = QPushButton("Next >>")

        self.prev_button.clicked.connect(self.show_previous_image)
        self.next_button.clicked.connect(self.show_next_image)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)

        image_layout.addLayout(button_layout)
        main_layout.addLayout(image_layout)

        self.setLayout(main_layout)

    def show_popup_with_update(self):
        self.update_dropdown_colors()
        QComboBox.showPopup(self.image_dropdown)

    def update_dropdown_colors(self):
        csv_path = os.environ["DATABASE"]
        df = pd.read_csv(csv_path)

        for i, (file_name, classification) in enumerate(
            zip(df["file_name"], df["classification"])
        ):
            color = (
                "green"
                if pd.notna(classification) and str(classification).strip()
                else "red"
            )
            self.image_dropdown.setItemData(i, QColor(color), Qt.ForegroundRole)

    def dropdown_image_change(self, index):
        selected_text = self.image_dropdown.currentText()
        for i, path in enumerate(self.image_files):
            if path.split("_x_")[0] == selected_text:
                self.image_index = i
                self.update_image()
                self.change_magnification_to_default()
                self.image_changed.emit(self.image_files[self.image_index])
                break

    def show_info_popup(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Image Information")
        dialog.setFixedSize(300, 150)

        image_name = self.image_files[self.image_index]
        info_text = (
            f"<p align='left'>"
            f"<b>Slide :</b> {image_name[:8]}<br>"
            f"<b>X Position :</b> {image_name.split('_x_')[1].split('_y_')[0]}<br>"
            f"<b>Y Position :</b> {image_name.split('_y_')[1].split('_')[0]}<br>"
            f"<b>Predict Score :</b> {round(float(image_name.split('_')[-1].replace('.png', '')), 5)}"
            f"</p>"
        )

        info_label = QLabel(info_text, dialog)
        info_label.setTextFormat(Qt.RichText)
        info_label.setAlignment(Qt.AlignLeft)

        ok_button = QPushButton("OK", dialog)
        ok_button.clicked.connect(dialog.accept)

        layout = QVBoxLayout()
        layout.addWidget(info_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        dialog.exec_()

    def update_image(self):
        if 0 <= self.image_index < len(self.image_files):
            image_path = os.path.join(
                self.images_path,
                self.image_files[self.image_index].split("_top-")[0],
                os.environ["PATCH_MAGNIFICATION"],
                self.image_files[self.image_index],
            )
            self.file_name_label.setText(
                f"<b> Patch Name : {image_path.split('/')[-1].split('_x_')[0]}</b>"
            )
            self.pixmap = QPixmap(image_path)
            self.rendering_image()
            self.image_dropdown.setCurrentIndex(self.image_index)

    def update_ui(self):
        font_size = int(14 * self.width() / 435)
        for button in [self.prev_button, self.next_button, *self.buttons.values()]:
            font = button.font()
            font.setPointSize(font_size)
            button.setFont(font)

        self.prev_button.setFixedSize(
            int(180 / 435 * self.width()), int(50 / 585 * self.height())
        )
        self.next_button.setFixedSize(
            int(180 / 435 * self.width()), int(50 / 585 * self.height())
        )
        for button in self.buttons.values():
            button.setFixedSize(
                int(90 / 435 * self.width()), int(30 / 585 * self.height())
            )
        self.layout().setSpacing(int(18 * self.width() / 435))

    def show_previous_image(self):
        self.image_index = (self.image_index - 1) % len(self.image_files)
        self.change_magnification_to_default()
        self.update_image()
        self.image_changed.emit(self.image_files[self.image_index])

    def show_next_image(self):
        self.image_index = (self.image_index + 1) % len(self.image_files)
        self.change_magnification_to_default()
        self.update_image()
        self.image_changed.emit(self.image_files[self.image_index])

    def change_magnification_to_default(self):
        self.current_magnification = os.environ["DEFAULT_MAGNIFICATION"]
        for mag, button in self.buttons.items():
            button.setChecked(mag == self.current_magnification)

    def change_magnification(self):
        button = self.sender()
        magnification = button.text()
        self.current_magnification = magnification
        self.rendering_image()

        for mag, button in self.buttons.items():
            button.setChecked(mag == magnification)

    def rendering_image(self):
        if self.pixmap is None:
            return

        pixmap = self.pixmap
        original_width, original_height = pixmap.width(), pixmap.height()

        # 배율에 맞게 크기를 계산
        crop_width = int(
            original_width * self.magnifications[self.current_magnification]
        )
        crop_height = int(
            original_height * self.magnifications[self.current_magnification]
        )

        # crop 위치는 원본 크기에서 잘라내는 크기를 뺀 후, 그 절반만큼 이동해야
        crop_x = (original_width - crop_width) // 2  # 중앙을 기준으로 잘라냄
        crop_y = (original_height - crop_height) // 2  # 중앙을 기준으로 잘라냄

        # 이미지를 자르고 스케일링
        cropped_pixmap = pixmap.copy(crop_x, crop_y, crop_width, crop_height)

        # 이미지를 라벨 크기에 맞게 스케일링
        scaled_pixmap = cropped_pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            aspectRatioMode=Qt.KeepAspectRatio,
            transformMode=Qt.SmoothTransformation,
        )

        # 최종적으로 이미지 표시
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)

    def get_current_image_path(self):
        if 0 <= self.image_index < len(self.image_files):
            image_path = os.path.join(
                os.environ["PATCH_FOLDER"],
                self.image_files[self.image_index].split("_top-")[0],
                os.environ["PATCH_MAGNIFICATION"],
                self.image_files[self.image_index],
            )
            return image_path
        return None

    def select_default_magnification(self):
        self.buttons[self.default_magnification].setChecked(True)

    def resizeEvent(self, event):
        self.update_ui()
        self.update_image()

        super().resizeEvent(event)
