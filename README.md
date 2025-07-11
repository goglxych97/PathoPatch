## PathoPatch: A software tool designed to facilitate easy annotation of patches extracted from whole-slide images. 

### 1. Command output example
https://github.com/user-attachments/assets/d2db65e8-d5c9-46b0-b116-bc5154cf4ee0

### 2. Folder structure overview
```
├── Classification_Results  # Folder where classified patches are saved
├── DB_warning_overwrite_on_execution.csv  # CSV database file that gets overwritten on each execution
├── Intermin_Saved  # Folder for intermediate saves
├── [Sample]Classification_Initialize.csv  # Sample CSV file used to load classification list
├── image_path  # Folder containing images; directory structure must follow the format below
│   ├── Slide_001
│   │   └── 20X
│   │       └── ...
│   └── ...
└── source_code  # Folder containing source code
```

### 3. Dependencies
```bash
$ cd source_code
$ python main.py
```

### 4. Dependencies
```bash
$ pip install PyQt5-tools
$ pip install pandas
```

You can create an executable file using PyInstaller on Windows and run the program without installing Python separately.
