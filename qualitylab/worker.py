"""Qt-safe batch worker: model processing stays outside the GUI thread."""
from __future__ import annotations
import threading
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from .analyser import AnalysisCancelled, profile_csv


class BatchAnalysisWorker(QObject):
    progress = pyqtSignal(int, int)
    report_ready = pyqtSignal(object)
    issue = pyqtSignal(str, str)
    completed = pyqtSignal(bool)

    def __init__(self, files: list[str]):
        super().__init__()
        # Private immutable work queue; the worker never edits GUI-owned models.
        self.files = tuple(files)
        self._cancel = threading.Event()

    def request_stop(self):
        # Event.set() is safe to call from the GUI thread.
        self._cancel.set()

    @pyqtSlot()
    def run(self):
        total = len(self.files)
        cancelled = False
        for index, path in enumerate(self.files, 1):
            if self._cancel.is_set():
                cancelled = True
                break
            try:
                report = profile_csv(path, cancelled=self._cancel.is_set)
            except AnalysisCancelled:
                cancelled = True
                break
            except Exception as error:
                self.issue.emit(path, str(error))
            else:
                self.report_ready.emit(report)
            self.progress.emit(index, total)
        self.completed.emit(cancelled)
