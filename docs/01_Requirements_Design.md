# Task 1 - Requirements and design specification

## Application purpose

CSV Data Quality Lab helps a student, office worker or beginner analyst identify basic problems in CSV data without editing the original file. The user imports one or more data tables, runs a quality inspection, examines sample records and creates a cleaned copy. This project handles **structured CSV datasets**, not music, photos or general file browsing.

## Functional requirements

| ID | The application shall... | Acceptance evidence |
|---|---|---|
| FR01 | allow the user to add one or more valid CSV files | File selection and dataset list |
| FR02 | analyze selected CSV collections on a background thread | UI works during processing |
| FR03 | count records, missing values and exact duplicate rows | Overview test results |
| FR04 | detect numeric columns and summarize values | Column profile and unit tests |
| FR05 | display a bounded preview and search the preview text | Sample rows tab |
| FR06 | show progress, completion status, and any file errors | Progress bar and Activity log |
| FR07 | allow the user to request cancellation | Cancel button with large file |
| FR08 | export a distinct cleaned CSV without changing the input | Export unit tests |
| FR09 | export a structured quality summary | Summary test and saved CSV |
| FR10 | play a short confirmation sound when analysis succeeds | QtMultimedia test |

## Initial GUI wireframe

```text
+---------------------------------------------------------------------+
| FILE MENU          CSV DATA QUALITY LAB                              |
| Inspect your datasets / Identify issues / Export a cleaner copy     |
| +----------------------+--------------------------------------------+ |
| | DATASETS             | ROWS | MISSING | DUPLICATES | SCORE          | |
| | orders_north.csv     +--------------------------------------------+ |
| | orders_south.csv     | Overview | Sample rows | Column | Activity | |
| | feedback.csv         |                                            | |
| | [ + Add CSV Files ]  |      Selected dataset results              | |
| | [ Analyze All ]      |      Editable search for the preview       | |
| | [ Cancel ]           |                                            | |
| | [ Clean CSV ]        |                                            | |
| | [ Quality Summary ]  |                                            | |
| +----------------------+--------------------------------------------+ |
|     2 / 3 datasets processed    [##########             ]            |
+---------------------------------------------------------------------+
```

## Architecture

- **Model/data:** `qualitylab/analyser.py` processes CSV files and returns immutable `FileReport` / `ColumnProfile` values. It has no PyQt imports.
- **View/controller:** `qualitylab/gui.py` handles the QMainWindow interface, user events, presentation and worker coordination.
- **Background worker:** `qualitylab/worker.py` owns an immutable list of input filenames, checks a `threading.Event` for cancellation, and sends results to the GUI using Qt signals.
- **Assets:** `assets/complete.wav` supplies a short completion sound via QtMultimedia's `QSoundEffect`.

This design uses separation of concerns instead of a strictly separate controller class. The window coordinates the model and view and contains **no row-by-row CSV parsing logic**.
