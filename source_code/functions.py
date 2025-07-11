import os
import sys
import glob
import pandas as pd


def resource_path(relative_path):
    base_path = (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(base_path, relative_path)


def get_sorted_files(folder_path):
    files = glob.glob(f'{folder_path}/*/{os.environ["PATCH_MAGNIFICATION"]}/*.png')

    files.sort(
        key=lambda f: (
            int(os.path.basename(f).split("_")[1]),
            int(os.path.basename(f).split("_")[2][3:]),
        )
    )
    return files


def create_classification_csv(image_files, results_path):
    file_names = [os.path.basename(file_path) for file_path in image_files]
    classifications = {file_name: [] for file_name in file_names}
    output_file_path = os.environ["DATABASE"]

    for root, _, files in os.walk(results_path):
        for file in files:
            if file in classifications:
                parent_folder = os.path.basename(root)
                prefix = parent_folder.split("_")[0]
                if prefix.isdigit() and prefix not in classifications[file]:
                    classifications[file].append(prefix)

    # ★ 쉼표로 구분된 문자열로 변환
    classification_strings = {
        file: ",".join(sorted(classifications[file])) for file in file_names
    }

    df = pd.DataFrame(
        {
            "file_name": file_names,
            "classification": [classification_strings[file] for file in file_names],
        }
    )
    df.to_csv(output_file_path, index=False, encoding="utf-8")

    return df


def generate_magnification_dict():
    magnification_dict = {"5X": 1, "10X": 0.5, "20X": 0.25, "40X": 0.125}
    return magnification_dict
