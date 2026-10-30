# CSV Data Quality Lab

**Independent Advanced Programming Assessment 2 project**

A PyQt6 desktop dashboard for examining the quality of CSV datasets. This is a **data-analysis application**, not a media catalogue or file manager. The source files remain unchanged. Users import CSV datasets, run an asynchronous quality inspection, view missing-value and duplicate-row statistics, explore up to 150 preview records, and export a separate cleaned CSV or quality summary.

## Requirements

- Windows 10/11 recommended; Python 3.11 or newer
- PyQt6 (installed using `requirements.txt`)
- Optional: PyInstaller to build a Windows executable
- No online accounts, databases, or API keys are required

## Running it

**Windows:** extract the ZIP and double-click `run_windows.bat`. It checks whether PyQt6 is installed and installs it if needed (internet connection required on first install). Or in VS Code's terminal:

```powershell
py -3 -m pip install -r requirements.txt
py -3 main.py
```

**Other operating systems:** install requirements using pip, then `python main.py`.

## First hands-on test

1. Click **Add CSV Files** and select the three files in `sample_data`.
2. Click **Analyze All Datasets**. The interface must remain usable while the worker processes data.
3. Select `orders_north.csv` and examine the overview and column profile. It contains missing values and an exact duplicate row.
4. Open **Sample rows** and search for a name or city; this search operates on the displayed preview, not all records.
5. Use **Save Cleaned CSV** to create a new file with trimmed cells and exact duplicates removed. The original is not changed.
6. Use **Save Quality Summary** to export column statistics.
7. Repeat with a larger CSV file, test **Cancel Running Analysis**, then analyze again.
8. Confirm the short completion sound on a successful run. Your computer must have audio enabled.

## Automated tests

```powershell
py -3 -m unittest discover -s tests -v
```

There are 35 tests. These test the CSV analysis rules, validation, export and a small benchmark agreement test. Tests should be rerun on the student's computer and screenshot evidence saved.

## Performance experiment

```powershell
py -3 benchmarks/compare_methods.py --demo --files 6 --rows 2500 --repeats 3 --workers 4
```

The script generates **synthetic** datasets in a temporary directory and compares sequential, thread-pool and process-pool analysis. Save your actual terminal output for the technical report. Threading or multiprocessing may not be faster for small datasets; document the measurements instead of assuming a speed-up.

## Build the Windows EXE

Double-click `build_windows.bat`. It installs build dependencies and generates `dist/CSVDataQualityLab.exe`. Run the executable yourself and screenshot its working interface. Executable building was **not verified** in the project-authoring environment.

## What the files do

| File/folder | Purpose |
|---|---|
| `main.py` | Application entry point |
| `qualitylab/gui.py` | PyQt main window and user interaction |
| `qualitylab/analyser.py` | CSV validation, profiles and export logic |
| `qualitylab/worker.py` | QThread worker, signals and cancellation |
| `assets/complete.wav` | Original brief completion notification sound |
| `tests/` | 35 automated test cases |
| `benchmarks/` | Sequential/thread/process experiment |
| `sample_data/` | Three small teaching CSV samples |
| `docs/` | Design, test plan, draft report and Git instructions |
| `presentation/` | Slide deck to personalize and present |
| `evidence/` | Folder reserved for real screenshots and outputs |

## Submission integrity and remaining work

The project is a **working source-code starter**: the pure Python automated tests and benchmark have been executed, but the GUI could not be run in this authoring environment because PyQt6 could not be installed. Your friend's Windows GUI tests, audio verification, performance measurements on their machine, executable build, debugging evidence, Git work and in-class presentation remain their responsibility.

The enclosed technical report is a draft explaining this implementation, not a claim that the friend performed tests or version-control work. The friend should understand and, where needed, extend the application, then update the document with authentic results before submitting under the lecturer's rules.
