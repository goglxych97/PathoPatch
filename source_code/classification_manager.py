import os
import sys
import datetime
import shutil
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QSizePolicy,
    QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from functions import resource_path


class ClassificationManager(QWidget):
    def __init__(self, result_folder, itermin_saved, get_current_image_path):
        super().__init__()

        with open(
            resource_path("style/classification_manager.qss"), "r", encoding="utf-8"
        ) as f:
            self.setStyleSheet(f.read())

        self.result_folder = result_folder
        self.itermin_saved = itermin_saved
        self.get_current_image_path = get_current_image_path
        self.text_inputs = []
        self.select_buttons = []
        self.input_containers = []
        self.default_text_width = 300
        self.default_text_height = 40
        self.default_spacing = 10
        self.setup_ui()

    def setup_ui(self):
        self.merge_duplicate_folders(self.result_folder)
        main_layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.container_widget = QWidget()
        self.container_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setSpacing(self.default_spacing)
        self.container_layout.setAlignment(Qt.AlignTop)

        existing_folders = sorted(
            [
                folder
                for folder in os.listdir(self.result_folder)
                if folder.split("_")[0].isdigit()
            ],
            key=lambda x: int(x.split("_")[0]),  # "_" 앞의 숫자를 기준으로 정렬
        )

        folder_count = max(4, len(existing_folders))
        for i in range(folder_count):
            folder_name = ""
            if i < len(existing_folders):
                folder_name = (
                    existing_folders[i].split("_", 1)[1]
                    if "_" in existing_folders[i]
                    else ""
                )
            self.add_text_input(i + 1, folder_name=folder_name)

        self.scroll_area.setWidget(self.container_widget)

        self.add_button = QPushButton("Add Classification Item")
        self.add_button.clicked.connect(
            lambda: self.add_text_input(len(self.text_inputs) + 1)
        )
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.add_button)
        self.initialize_button = QPushButton(
            "Initialize item to classification csv file"
        )
        self.initialize_button.clicked.connect(self.initialize_csv)
        main_layout.addWidget(self.initialize_button)

        self.save_button = QPushButton("Interim Save")
        self.save_button.clicked.connect(self.save_classification_state)
        main_layout.addWidget(self.save_button)

        self.setLayout(main_layout)

        self.update_text_input_states()
        self.update_delete_buttons()

    def add_text_input(self, index, folder_name=""):
        input_layout = QHBoxLayout()
        input_layout.setSpacing(0)
        input_layout.setAlignment(Qt.AlignLeft)

        select_button = QPushButton(f"Select{index}")
        select_button.setObjectName("selectButton")
        select_button.setFixedSize(
            int(self.default_text_height * 1.2), int(self.default_text_height * 1.2)
        )
        select_button.setProperty("is_active", False)
        select_button.clicked.connect(
            lambda: self.handle_select_button_click(index - 1, select_button)
        )
        self.select_buttons.append(select_button)

        text_input = CustomTextEdit(index - 1)

        text_input.setPlaceholderText(f"Category {index}")
        text_input.setFixedHeight(int(self.default_text_height * 1.2))
        text_input.setFixedWidth(self.width() - 135)

        text_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_input.text_finalized.connect(self.on_text_finalized)
        text_input.textChanged.connect(self.on_text_changed)

        if folder_name:
            text_input.setPlainText(folder_name)

        delete_button = QPushButton("X")
        delete_button.setObjectName("deleteButton")
        delete_button.setFixedSize(
            int(self.default_text_height * 0.6), int(self.default_text_height * 0.6)
        )
        delete_button.clicked.connect(lambda: self.remove_text_input(text_input))
        delete_button.setVisible(False)

        input_layout.addWidget(select_button)
        input_layout.addWidget(text_input)
        input_layout.addWidget(delete_button)

        container = QWidget()
        container.setLayout(input_layout)
        self.container_layout.addWidget(container)

        self.text_inputs.append(text_input)
        self.input_containers.append(container)

        self.update_text_input_states()
        self.update_delete_buttons()

    def handle_select_button_click(self, index, button):
        is_active = button.property("is_active")
        selected_folder = f"{index + 1}_{self.text_inputs[index].toPlainText().strip()}"
        selected_folder_path = os.path.join(self.result_folder, selected_folder)
        current_image_path = self.get_current_image_path()
        image_name = os.path.basename(current_image_path)
        target_image_path = os.path.join(selected_folder_path, image_name)

        csv_path = os.environ["DATABASE"]
        df = pd.read_csv(csv_path, dtype={"classification": str})

        if not is_active:
            button.setProperty("is_active", True)
            os.makedirs(selected_folder_path, exist_ok=True)
            shutil.copy(current_image_path, target_image_path)

            df["classification"] = df["classification"].fillna("").astype(str)
            current_classification = df.loc[
                df["file_name"] == image_name, "classification"
            ].values
            if len(current_classification) == 0 or pd.isna(current_classification[0]):
                updated_classification = str(index)  # NaN이나 비어 있으면 index로 설정
            else:
                # 쉼표로 분리된 값 리스트 생성
                existing_values = [
                    value.strip()
                    for value in str(current_classification[0]).split(",")
                    if value.strip()
                ]
                if str(index) not in existing_values:
                    existing_values.append(str(index))  # index 추가
                updated_classification = ",".join(existing_values)

            df.loc[df["file_name"] == image_name, "classification"] = (
                updated_classification
            )
            df.to_csv(csv_path, index=False)
            self.update_text_input_states()

        else:
            button.setProperty("is_active", False)
            if os.path.exists(target_image_path):
                try:
                    os.remove(target_image_path)
                    print(f"Deleted {target_image_path}")
                except Exception as e:
                    print(f"Error deleting file: {e}")

            df["classification"] = df["classification"].fillna("").astype(str)
            current_classification = df.loc[
                df["file_name"] == image_name, "classification"
            ].values
            if len(current_classification) > 0 and not pd.isna(
                current_classification[0]
            ):
                # 쉼표로 분리된 값 리스트 생성
                existing_values = [
                    value.strip()
                    for value in str(current_classification[0]).split(",")
                    if value.strip()
                ]
                updated_values = [
                    value for value in existing_values if value != str(index)
                ]  # index 제거
                updated_classification = (
                    ",".join(updated_values) if updated_values else np.nan
                )

                df.loc[df["file_name"] == image_name, "classification"] = (
                    updated_classification
                )

            df.to_csv(csv_path, index=False)

            self.update_text_input_states()
            pass

    def on_text_finalized(self, index, text):
        self.create_or_update_folder(index, text)

    def on_text_changed(self):
        enable_next = True

        for i, text_input in enumerate(self.text_inputs):
            select_button = self.select_buttons[i]

            if enable_next and (
                i == 0 or self.text_inputs[i - 1].toPlainText().strip()
            ):
                text_input.setEnabled(True)
                select_button.setEnabled(True)
            else:
                text_input.setEnabled(False)
                select_button.setEnabled(False)

            if not text_input.isEnabled():
                enable_next = False

    def create_or_update_folder(self, index, text):
        folder_name = text.strip()
        new_folder_name = f"{index}_{folder_name}"
        new_folder_path = os.path.join(self.result_folder, new_folder_name)

        existing_folders = os.listdir(self.result_folder)
        current_folder = next(
            (folder for folder in existing_folders if folder.startswith(f"{index}_")),
            None,
        )

        if current_folder and current_folder != new_folder_name:
            current_folder_path = os.path.join(self.result_folder, current_folder)
            shutil.move(current_folder_path, new_folder_path)
        elif not os.path.exists(new_folder_path) and folder_name:
            os.makedirs(new_folder_path)

    def update_text_input_states(self):
        enable_next = True
        current_image_path = self.get_current_image_path()
        current_image_name = os.path.basename(current_image_path)

        for i, text_input in enumerate(self.text_inputs):
            select_button = self.select_buttons[i]
            folder_name = text_input.toPlainText().strip()
            folder_path = os.path.join(self.result_folder, f"{i + 1}_{folder_name}")

            is_currently_green = (
                "background-color: lightgreen;" in text_input.styleSheet()
            )
            is_green = False

            if os.path.isdir(folder_path):
                for file_name in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.isfile(file_path) and current_image_name == file_name:
                        is_green = True
                        break

            if is_green:
                text_input.setStyleSheet("background-color: lightgreen;")
                select_button.setProperty("is_active", True)
            else:
                text_input.setStyleSheet("")
                select_button.setProperty("is_active", False)

            if enable_next and (
                i == 0 or self.text_inputs[i - 1].toPlainText().strip()
            ):
                text_input.setEnabled(True)
                select_button.setEnabled(True)
            else:
                text_input.setEnabled(False)
                select_button.setEnabled(False)

            if not text_input.isEnabled():
                enable_next = False

    def update_delete_buttons(self):
        if len(self.text_inputs) <= 4:
            for container in self.input_containers:
                delete_button = container.layout().itemAt(2).widget()
                delete_button.setVisible(False)
        else:
            for container in self.input_containers:
                delete_button = container.layout().itemAt(2).widget()
                delete_button.setVisible(False)
            last_container = self.input_containers[-1]
            last_delete_button = last_container.layout().itemAt(2).widget()
            last_delete_button.setVisible(True)

    def update_classification_status(self, image_path):
        self.update_text_input_states()

    def remove_text_input(self, text_input):
        if len(self.text_inputs) > 4:
            index = self.text_inputs.index(text_input)
            container = self.input_containers[index]

            current_folder = f"{index + 1}_{text_input.toPlainText().strip()}"
            current_folder_path = os.path.join(self.result_folder, current_folder)

            if os.path.exists(current_folder_path):
                shutil.rmtree(current_folder_path)

            self.text_inputs.remove(text_input)
            self.select_buttons.pop(index)
            self.input_containers.remove(container)

            self.container_layout.removeWidget(container)
            container.deleteLater()

            self.update_text_input_states()
            self.update_delete_buttons()

    def initialize_csv(self):
        # 파일 다이얼로그로 CSV 파일을 선택
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )

        if file_path:
            try:
                df = pd.read_csv(file_path, encoding="cp949")
                result_folder = os.environ["RESULT_FOLDER"]
                if not os.path.exists(result_folder):
                    os.makedirs(result_folder)

                # CSV 파일의 각 행을 읽어서 폴더명을 변경하거나 새로 생성
                for idx, row in df.iterrows():
                    print(idx, row)
                    folder_name = (
                        f"{idx + 1}_{row['class']}"  # CSV에서 새 폴더 이름 생성
                    )
                    folder_path = os.path.join(result_folder, folder_name)

                    # 해당하는 폴더가 있는지 확인
                    old_folder_name = f"{idx + 1}_"
                    existing_folders = [
                        folder
                        for folder in os.listdir(result_folder)
                        if folder.startswith(old_folder_name)
                    ]

                    if existing_folders:
                        # 이미 폴더가 존재하면 폴더명을 바꿈
                        old_folder_path = os.path.join(
                            result_folder, existing_folders[0]
                        )
                        new_folder_path = folder_path
                        os.rename(old_folder_path, new_folder_path)
                        print(f"Renamed folder: {existing_folders[0]} -> {folder_name}")
                    else:
                        # 해당하는 폴더가 없으면 새 폴더를 생성
                        os.makedirs(folder_path)
                        print(f"Created folder: {folder_name}")

                # 프로그램 재시작
                self.restart_program()

            except Exception as e:
                print(f"Error reading CSV file: {e}")

    def merge_duplicate_folders(self, result_folder):
        # 이미 존재하는 폴더 목록 가져오기
        existing_folders = [
            folder
            for folder in os.listdir(result_folder)
            if folder.split("_")[0].isdigit()
        ]

        # 접두사를 기준으로 그룹화
        prefix_map = {}
        for folder in existing_folders:
            prefix = folder.split("_", 1)[0]  # 접두사 추출 (예: "1")
            if prefix not in prefix_map:
                prefix_map[prefix] = []
            prefix_map[prefix].append(folder)

        # 중복 처리: 각 접두사별로 하나의 폴더로 통합
        for prefix, folders in prefix_map.items():
            if len(folders) > 1:
                # 정렬된 순서로 유지할 폴더를 선택
                folders.sort()  # 이름 기준 정렬
                main_folder = folders[0]  # 첫 번째 폴더를 유지
                main_folder_path = os.path.join(result_folder, main_folder)
                os.makedirs(main_folder_path, exist_ok=True)

                print(f"Merging folders for prefix '{prefix}' into: {main_folder}")

                # 나머지 폴더에서 파일 이동
                for folder in folders[1:]:
                    folder_path = os.path.join(result_folder, folder)
                    for file_name in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, file_name)
                        target_path = os.path.join(main_folder_path, file_name)

                        # 파일 이동 (덮어씌우기)
                        shutil.move(file_path, target_path)  # 동일한 이름이면 덮어씌움
                        print(f"Moved file: {file_path} -> {target_path}")

                    # 이동이 끝난 폴더 삭제
                    shutil.rmtree(folder_path)
                    print(f"Removed folder: {folder_path}")

    def restart_program(self):
        self.merge_duplicate_folders(self.result_folder)
        for container in self.input_containers:
            self.container_layout.removeWidget(container)
            container.deleteLater()

        self.text_inputs.clear()
        self.select_buttons.clear()
        self.input_containers.clear()

        # UI 재구성
        existing_folders = sorted(
            [
                folder
                for folder in os.listdir(self.result_folder)
                if folder.split("_")[0].isdigit()
            ],
            key=lambda x: int(x.split("_")[0]),  # "_" 앞의 숫자를 기준으로 정렬
        )

        folder_count = max(4, len(existing_folders))
        for i in range(folder_count):
            folder_name = ""
            if i < len(existing_folders):
                folder_name = (
                    existing_folders[i].split("_", 1)[1]
                    if "_" in existing_folders[i]
                    else ""
                )
            self.add_text_input(i + 1, folder_name=folder_name)

        self.update_text_input_states()
        self.update_delete_buttons()

    def save_classification_state(self):
        # Classification_Results 폴더 훑기
        classification_data = {}
        folders = [
            folder
            for folder in os.listdir(self.result_folder)
            if folder.split("_")[0].isdigit()
        ]
        folders.sort(key=lambda x: int(x.split("_")[0]))  # 숫자 순서로 정렬

        for folder in folders:
            folder_path = os.path.join(self.result_folder, folder)
            if os.path.isdir(folder_path):
                for file_name in os.listdir(folder_path):
                    if file_name not in classification_data:
                        classification_data[file_name] = []
                    classification_data[file_name].append(
                        folder.split("_")[0]
                    )  # 폴더 번호 추가

        # 데이터프레임 생성
        unique_classifications = sorted({f.split("_")[0] for f in folders}, key=int)
        df = pd.DataFrame(
            index=classification_data.keys(), columns=unique_classifications
        )
        df = df.fillna("")

        for file_name, classifications in classification_data.items():
            for classification in classifications:
                df.loc[file_name, classification] = "O"  # 해당 클래스에 체크 표시

        # 현재 시간 기준으로 파일 저장
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(self.itermin_saved, f"saved_{timestamp}.csv")
        df.to_csv(save_path, encoding="utf-8-sig")
        print(f"Classification state saved to: {save_path}")

    def resizeEvent(self, event):
        for text_input in self.text_inputs:
            text_input.setFixedWidth(self.width() - 135)

        super().resizeEvent(event)


class CustomTextEdit(QTextEdit):
    text_finalized = pyqtSignal(int, str)

    def __init__(self, index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index

    def focusOutEvent(self, event):
        self.text_finalized.emit(self.index + 1, self.toPlainText())
        super().focusOutEvent(event)
