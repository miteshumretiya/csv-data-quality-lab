"""Qt presentation layer; data analysis takes place in analyser.py."""
from __future__ import annotations

import sys
from pathlib import Path
from PyQt6.QtCore import QThread, Qt, QUrl
from PyQt6.QtGui import QAction, QColor, QDragEnterEvent, QDropEvent, QFont
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView,
)

from .analyser import FileReport, export_cleaned, export_summary
from .worker import BatchAnalysisWorker


THEME = """
QMainWindow { background:#0d1420; }
QWidget { color:#e2e9f2; font-family:'Segoe UI'; font-size:10pt; }
QFrame#Sidebar { background:#151f2e; border:1px solid #2a3b50; border-radius:12px; }
QFrame#Card { background:#192638; border:1px solid #2e4054; border-radius:10px; }
QLabel#Title { font-size:23pt; font-weight:800; color:#e7f5ff; }
QLabel#Tag { color:#63e6cb; font-size:10pt; font-weight:600; }
QLabel#Metric { color:#ffffff; font-size:19pt; font-weight:700; }
QLabel#Muted { color:#9baec2; }
QPushButton { background:#22364c; border:1px solid #3a5368; border-radius:7px; padding:9px 12px; }
QPushButton:hover { background:#2c4c62; }
QPushButton:disabled { color:#647487; background:#1c2939; }
QPushButton#Primary { background:#0ca78c; border-color:#0ca78c; color:#061b22; font-weight:700; }
QPushButton#Primary:hover { background:#23c8a9; }
QListWidget, QTableWidget, QTextEdit, QLineEdit { background:#111c2b; border:1px solid #30445b;
    border-radius:6px; color:#e0ebf7; selection-background-color:#087b81; }
QListWidget { padding:6px; }
QListWidget::item { padding:8px; }
QHeaderView::section { background:#1f3449; color:#bbdbe9; padding:8px; border:0; border-bottom:1px solid #345065; }
QTabWidget::pane { border:1px solid #2b3d50; background:#121f2e; border-radius:7px; }
QTabBar::tab { background:#1c3043; padding:10px 17px; margin-right:3px; border-top-left-radius:7px; border-top-right-radius:7px; }
QTabBar::tab:selected { background:#0b897f; color:#ffffff; }
QProgressBar { border:1px solid #3b5167; border-radius:6px; height:13px; text-align:center; color:white; background:#111c2a; }
QProgressBar::chunk { background:#15bda6; border-radius:5px; }
QMenuBar { background:#122033; }
QMenuBar::item:selected, QMenu::item:selected { background:#23646c; }
QMenu { background:#18283a; border:1px solid #334b60; }
QStatusBar { background:#152334; color:#a4c9dc; }
"""


def _metric(label: str):
    card = QFrame(objectName="Card")
    layout = QVBoxLayout(card)
    name = QLabel(label, objectName="Muted")
    value = QLabel("-", objectName="Metric")
    layout.addWidget(name)
    layout.addWidget(value)
    return card, value


class DataLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Data Quality Lab")
        self.resize(1280, 830)
        self.setMinimumSize(950, 610)
        self.setAcceptDrops(True)
        self.setStyleSheet(THEME)
        self.files: list[str] = []
        self.reports: dict[str, FileReport] = {}
        self._thread: QThread | None = None
        self._worker: BatchAnalysisWorker | None = None
        self._cancelled = False
        self._issues = 0
        self._create_interface()
        self._init_audio()
        self.statusBar().showMessage("Ready - import your CSV datasets to begin.")

    def _create_interface(self):
        file_menu = self.menuBar().addMenu("&File")
        help_menu = self.menuBar().addMenu("&Help")
        for title, handler in [("Add CSV datasets...", self.add_files),
                               ("Export cleaned dataset...", self.save_cleaned),
                               ("Export quality summary...", self.save_summary)]:
            action = QAction(title, self)
            action.triggered.connect(handler)
            file_menu.addAction(action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        about = QAction("About", self)
        about.triggered.connect(lambda: QMessageBox.information(
            self, "About CSV Data Quality Lab",
            "CSV Data Quality Lab\nA PyQt6 learning project for CSV profiling, quality checks and safe exports."))
        help_menu.addAction(about)

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 18, 22, 16)
        outer.setSpacing(16)
        title = QLabel("CSV Data Quality Lab", objectName="Title")
        subtitle = QLabel("Inspect your datasets  /  Identify data issues  /  Export a cleaner copy", objectName="Tag")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter, 1)
        sidebar = QFrame(objectName="Sidebar")
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 18, 16, 16)
        side.setSpacing(12)
        heading = QLabel("DATASETS", objectName="Tag")
        side.addWidget(heading)
        side.addWidget(QLabel("Add one or more UTF-8 CSV files", objectName="Muted"))
        self.dataset_list = QListWidget()
        self.dataset_list.currentRowChanged.connect(self.show_current)
        side.addWidget(self.dataset_list, 1)
        self.add_button = QPushButton("+  Add CSV Files")
        self.add_button.setObjectName("Primary")
        self.add_button.clicked.connect(self.add_files)
        side.addWidget(self.add_button)
        self.analyse_button = QPushButton("Analyze All Datasets")
        self.analyse_button.clicked.connect(self.start_analysis)
        side.addWidget(self.analyse_button)
        self.stop_button = QPushButton("Cancel Running Analysis")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_analysis)
        side.addWidget(self.stop_button)
        side.addWidget(QLabel("EXPORT RESULTS", objectName="Tag"))
        self.clean_button = QPushButton("Save Cleaned CSV")
        self.clean_button.clicked.connect(self.save_cleaned)
        side.addWidget(self.clean_button)
        self.summary_button = QPushButton("Save Quality Summary")
        self.summary_button.clicked.connect(self.save_summary)
        side.addWidget(self.summary_button)
        self.sidebar_note = QLabel("No datasets imported yet.", objectName="Muted")
        self.sidebar_note.setWordWrap(True)
        side.addWidget(self.sidebar_note)
        splitter.addWidget(sidebar)

        content = QWidget()
        right = QVBoxLayout(content)
        right.setContentsMargins(10, 0, 0, 0)
        right.setSpacing(12)
        metric_row = QGridLayout()
        metric_row.setSpacing(10)
        self.metrics = {}
        for index, name in enumerate(["DATA ROWS", "MISSING CELLS", "DUPLICATE ROWS", "QUALITY SCORE"]):
            card, value = _metric(name)
            metric_row.addWidget(card, 0, index)
            self.metrics[name] = value
        right.addLayout(metric_row)
        self.tabs = QTabWidget()
        right.addWidget(self.tabs, 1)

        overview = QWidget()
        ov = QVBoxLayout(overview)
        self.dataset_heading = QLabel("Choose a dataset to view its profile", objectName="Title")
        self.dataset_heading.setWordWrap(True)
        ov.addWidget(self.dataset_heading)
        self.overview = QTextEdit()
        self.overview.setReadOnly(True)
        self.overview.setPlainText("Import your files, then select Analyze All Datasets.\n\n"
                                   "Results will include missing cells, duplicate records, numeric columns and a quality score.\n\n"
                                   "Original CSV files are never modified.")
        ov.addWidget(self.overview)
        self.tabs.addTab(overview, "Overview")

        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        searchbar = QHBoxLayout()
        searchbar.addWidget(QLabel("Find in sample:"))
        self.preview_search = QLineEdit()
        self.preview_search.setPlaceholderText("Filter the displayed sample rows...")
        self.preview_search.textChanged.connect(self.fill_preview)
        searchbar.addWidget(self.preview_search)
        preview_layout.addLayout(searchbar)
        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        preview_layout.addWidget(self.preview_table)
        preview_layout.addWidget(QLabel("Preview is limited to the first 150 data records.", objectName="Muted"))
        self.tabs.addTab(preview_tab, "Sample rows")

        profile_tab = QWidget()
        prof_layout = QVBoxLayout(profile_tab)
        self.profile_table = QTableWidget(0, 6)
        self.profile_table.setHorizontalHeaderLabels(["Column", "Detected", "Filled", "Missing", "Min", "Mean"])
        self.profile_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.profile_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        prof_layout.addWidget(self.profile_table)
        self.tabs.addTab(profile_tab, "Column profile")

        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.activity = QTextEdit()
        self.activity.setReadOnly(True)
        log_layout.addWidget(self.activity)
        self.tabs.addTab(log_tab, "Activity log")
        splitter.addWidget(content)
        splitter.setSizes([300, 850])

        bottom = QHBoxLayout()
        self.progress_text = QLabel("0 / 0 datasets processed", objectName="Muted")
        bottom.addWidget(self.progress_text)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        bottom.addWidget(self.progress, 1)
        outer.addLayout(bottom)

    def _init_audio(self):
        self.sound = QSoundEffect(self)
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        path = base / "assets" / "complete.wav"
        if path.is_file():
            self.sound.setSource(QUrl.fromLocalFile(str(path)))
            self.sound.setVolume(0.35)

    def log(self, message: str):
        self.activity.append(message)

    def add_files(self):
        chosen, _ = QFileDialog.getOpenFileNames(self, "Choose CSV datasets", "", "CSV files (*.csv)")
        self.register_files(chosen)

    def register_files(self, paths):
        added = 0
        for path in paths:
            p = Path(path).resolve()
            if p.suffix.lower() != ".csv" or not p.is_file():
                continue
            if str(p) not in self.files:
                self.files.append(str(p))
                self.dataset_list.addItem(p.name)
                added += 1
        if added:
            self.dataset_list.setCurrentRow(len(self.files) - 1)
            self.sidebar_note.setText(f"{len(self.files)} dataset(s) available")
            self.log(f"Added {added} dataset(s).")
            self.statusBar().showMessage(f"Imported {len(self.files)} CSV file path(s).")

    def _selected_file(self) -> str | None:
        index = self.dataset_list.currentRow()
        return self.files[index] if 0 <= index < len(self.files) else None

    def start_analysis(self):
        if self._thread is not None:
            return
        if not self.files:
            QMessageBox.warning(self, "No datasets", "Add at least one CSV file before analyzing.")
            return
        self.reports.clear()
        self._issues = 0
        self._cancelled = False
        self.progress.setRange(0, len(self.files))
        self.progress.setValue(0)
        self.progress_text.setText(f"0 / {len(self.files)} datasets processed")
        self.add_button.setEnabled(False)
        self.analyse_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log(f"Started background analysis of {len(self.files)} CSV file(s).")
        self.statusBar().showMessage("Analyzing datasets in background; window remains interactive.")
        self._thread = QThread(self)
        self._worker = BatchAnalysisWorker(self.files)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.report_ready.connect(self.on_report)
        self._worker.issue.connect(self.on_issue)
        self._worker.progress.connect(self.on_progress)
        self._worker.completed.connect(self.on_complete)
        self._worker.completed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self.on_thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def stop_analysis(self):
        if self._worker:
            self._worker.request_stop()
            self.log("Cancellation requested; worker will stop safely.")
            self.stop_button.setEnabled(False)

    def on_report(self, report: FileReport):
        self.reports[report.source] = report
        self.log(f"Analyzed {Path(report.source).name}: {report.row_count} rows, {report.duplicate_count} duplicates.")
        if self._selected_file() == report.source:
            self.show_current()

    def on_issue(self, filename: str, message: str):
        self._issues += 1
        self.log(f"ERROR: {Path(filename).name}: {message}")

    def on_progress(self, number: int, total: int):
        self.progress.setValue(number)
        self.progress_text.setText(f"{number} / {total} datasets processed")

    def on_complete(self, cancelled: bool):
        self._cancelled = cancelled
        self.log("Processing cancelled." if cancelled else "Background processing completed.")

    def on_thread_finished(self):
        self._worker = None
        self._thread = None
        self.add_button.setEnabled(True)
        self.analyse_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if self._cancelled:
            msg = "Analysis cancelled; completed results are still available."
        elif self._issues:
            msg = f"Finished with {self._issues} error(s). Open Activity log for details."
        else:
            msg = f"Finished successfully: {len(self.reports)} dataset(s) analyzed."
        self.statusBar().showMessage(msg)
        if not self._cancelled and not self._issues:
            self.sound.play()

    def show_current(self, *_args):
        chosen = self._selected_file()
        if not chosen:
            return
        report = self.reports.get(chosen)
        self.dataset_heading.setText(Path(chosen).name)
        if report is None:
            self.overview.setPlainText("This dataset has not been analyzed yet. Select Analyze All Datasets.")
            for label in self.metrics.values():
                label.setText("-")
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            self.profile_table.setRowCount(0)
            return
        self.metrics["DATA ROWS"].setText(f"{report.row_count:,}")
        self.metrics["MISSING CELLS"].setText(f"{report.missing_cells:,}")
        self.metrics["DUPLICATE ROWS"].setText(f"{report.duplicate_count:,}")
        self.metrics["QUALITY SCORE"].setText(f"{report.quality_score:.1f}%")
        self.overview.setPlainText(
            f"Source: {report.source}\n"
            f"File size: {report.bytes_on_disk:,} bytes\n"
            f"Columns: {len(report.headers)}\nRows: {report.row_count:,}\n"
            f"Missing values: {report.missing_cells:,}\nDuplicate rows: {report.duplicate_count:,}\n"
            f"Quality score: {report.quality_score:.1f}%\n\n"
            "Quality score is a simple teaching metric. It penalizes empty cells and exact duplicate records; "
            "it is not a guarantee that a dataset is accurate or free of bias.\n\n"
            "The original input is read-only. Use Save Cleaned CSV to create a separate copy."
        )
        self.profile_table.setRowCount(len(report.columns))
        for r, column in enumerate(report.columns):
            values = [column.name, column.kind, str(column.non_empty), str(column.missing),
                      self._float_str(column.minimum), self._float_str(column.mean)]
            for c, value in enumerate(values):
                self.profile_table.setItem(r, c, QTableWidgetItem(value))
        self.fill_preview()

    @staticmethod
    def _float_str(value):
        return "-" if value is None else f"{value:,.3f}"

    def fill_preview(self, *_args):
        report = self.reports.get(self._selected_file())
        if report is None:
            return
        query = self.preview_search.text().casefold().strip()
        rows = [row for row in report.sample if not query or query in " ".join(row).casefold()]
        self.preview_table.setUpdatesEnabled(False)
        try:
            self.preview_table.setColumnCount(len(report.headers))
            self.preview_table.setHorizontalHeaderLabels(list(report.headers))
            self.preview_table.setRowCount(len(rows))
            for index, row in enumerate(rows):
                for col, cell in enumerate(row):
                    self.preview_table.setItem(index, col, QTableWidgetItem(cell))
            self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        finally:
            self.preview_table.setUpdatesEnabled(True)

    def save_cleaned(self):
        selected = self._selected_file()
        if not selected:
            QMessageBox.information(self, "No dataset selected", "Select a CSV dataset from the list.")
            return
        suggestion = str(Path(selected).with_name(Path(selected).stem + "_clean.csv"))
        dest, _ = QFileDialog.getSaveFileName(self, "Save cleaned dataset", suggestion, "CSV files (*.csv)")
        if not dest:
            return
        try:
            count = export_cleaned(selected, dest)
        except Exception as error:
            QMessageBox.critical(self, "Export failed", str(error))
        else:
            self.log(f"Saved cleaned CSV with {count:,} unique records: {dest}")
            QMessageBox.information(self, "Export successful", f"Saved {count:,} rows to a separate CSV file.")

    def save_summary(self):
        report = self.reports.get(self._selected_file())
        if report is None:
            QMessageBox.information(self, "Analyze first", "Analyze and select a dataset before exporting its quality summary.")
            return
        dest, _ = QFileDialog.getSaveFileName(self, "Save quality summary", "quality_summary.csv", "CSV files (*.csv)")
        if not dest:
            return
        try:
            export_summary(report, dest)
        except Exception as error:
            QMessageBox.critical(self, "Export failed", str(error))
        else:
            self.log(f"Saved quality report: {dest}")
            QMessageBox.information(self, "Export successful", "Column quality summary saved.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() and any(u.toLocalFile().lower().endswith('.csv') for u in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        self.register_files([u.toLocalFile() for u in event.mimeData().urls()])
        event.acceptProposedAction()

    def closeEvent(self, event):
        if self._thread is not None and self._thread.isRunning():
            answer = QMessageBox.question(self, "Processing is running",
                "Cancel the current analysis and close the application?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._worker.request_stop()
            if not self._thread.wait(5000):
                QMessageBox.warning(self, "Still running", "Please wait until the current file operation stops.")
                event.ignore()
                return
        event.accept()


def launch():
    app = QApplication(sys.argv)
    app.setApplicationName("CSV Data Quality Lab")
    win = DataLabWindow()
    win.show()
    sys.exit(app.exec())
