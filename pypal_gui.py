#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import os
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QFileDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit,
    QRadioButton, QButtonGroup,
    QTextEdit, QProgressBar,
    QMessageBox
)

# =============================
# 🔁 BACKEND SELECTION
# =============================
from pypal import PyPal

# =============================
# Worker Thread
# =============================
class Worker(QThread):
    log = Signal(str)
    progress = Signal(str)
    finished = Signal(float)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, trace1, trace2, operation):
        super().__init__()
        self.trace1 = trace1
        self.trace2 = trace2
        self.operation = operation
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            p = PyPal()
            p.U = p.R = p.SR = p.S = p.C = p.M = False
            setattr(p, self.operation, True)

            p.trace1_name = Path(self.trace1).stem + ".txt"
            p.trace2_name = Path(self.trace2).stem + ".txt"

            self.log.emit(f"Trace 1: {self.trace1}")
            self.log.emit(f"Trace 2: {self.trace2}")
            self.log.emit(f"Operation: {self.operation}")

            start = time.time()

            # ---- Stage 1
            self.progress.emit("Loading & extracting unique frames…")
            if self._cancel:
                self.cancelled.emit()
                return
            p.UniqueFrames(self.trace1, self.trace2)

            elapsed = time.time() - start
            self.finished.emit(elapsed)

        except Exception as e:
            self.error.emit(str(e))


# =============================
# Drag-and-Drop LineEdit
# =============================
class FileDropEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        file_path = e.mimeData().urls()[0].toLocalFile()
        self.setText(file_path)


# =============================
# Main Window
# =============================
class PyPalWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyPal GUI")
        self.setFixedSize(850, 650)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ---- Trace 1
        layout.addWidget(QLabel("Trace 1 (to be synchronised)"))
        self.trace1_edit = FileDropEdit()
        layout.addLayout(self._browse_row(self.trace1_edit))

        # ---- Trace 2
        layout.addWidget(QLabel("Trace 2 (reference trace)"))
        self.trace2_edit = FileDropEdit()
        layout.addLayout(self._browse_row(self.trace2_edit))

        # ---- Operations
        layout.addWidget(QLabel("Operation"))
        self.op_group = QButtonGroup(self)

        ops = [
            ("Extract Unique Frames", "U"),
            ("Extract Reference Frames", "R"),
            ("Synchronise Reference Frames", "SR"),
            ("Synchronise Traces", "S"),
            ("Concatenate Traces", "C"),
            ("Merge Traces (Remove Duplicates)", "M"),
        ]

        for text, val in ops:
            rb = QRadioButton(text)
            rb.operation = val
            self.op_group.addButton(rb)
            layout.addWidget(rb)

        # ---- Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # ---- Progress label
        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)

        # ---- Buttons
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.cancel_btn = QPushButton("Cancel")
        self.exit_btn = QPushButton("Exit")

        self.cancel_btn.setEnabled(False)
        self.exit_btn.setEnabled(True)

        self.run_btn.clicked.connect(self.run)
        self.cancel_btn.clicked.connect(self.cancel)
        self.exit_btn.clicked.connect(self.close)

        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.exit_btn)
        layout.addLayout(btn_row)

        # ---- Log
        layout.addWidget(QLabel("Live Log"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.apply_dark_theme()

    # -----------------------------
    # Helpers
    # -----------------------------
    def _browse_row(self, edit):
        row = QHBoxLayout()
        btn = QPushButton("Browse")
        btn.clicked.connect(lambda: self.browse(edit))
        row.addWidget(edit)
        row.addWidget(btn)
        return row

    def browse(self, edit):
        f, _ = QFileDialog.getOpenFileName(self, "Select Trace", "", "Trace Files (*.txt *.tsv)")
        if f:
            edit.setText(f)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget { background:#1e1e1e; color:#e0e0e0; }
            QPushButton { background:#2e7d32; padding:6px; border-radius:4px; }
            QPushButton:hover { background:#388e3c; }
            QLineEdit, QTextEdit { background:#121212; border:1px solid #333; }
            QProgressBar::chunk { background:#3fa9f5; }
        """)

    # -----------------------------
    # Validation & warnings
    # -----------------------------
    def validate(self):
        # --------- Operation must be selected ---------
        btn = self.op_group.checkedButton()
        if not btn:
            QMessageBox.critical(self, "Error", "Select an operation")
            return False

        # --------- Both traces must exist ---------
        trace1_path = Path(self.trace1_edit.text())
        trace2_path = Path(self.trace2_edit.text())

        missing = []

        if not trace1_path.is_file():
            missing.append("Trace 1")

        if not trace2_path.is_file():
            missing.append("Trace 2")

        if missing:
            if len(missing) == 2:
                msg = "Both Trace 1 and Trace 2 must be selected"
            else:
                msg = f"{missing[0]} must be selected"

            QMessageBox.critical(self, "Error", msg)
            return False

        # --------- Overwrite warning mapping ---------
        overwrite_files = {
            "R": Path("ReferenceFrames/REFERENCE_FRAMES.txt"),
            "SR": Path("SynchronisedReferenceFrames/Synchronised_Reference_Frames.txt"),
            "C": Path("ConcatenatedTrace/ConcatenatedTrace.txt"),
            "M": Path("MergedTrace/Merged_Trace.txt")
        }

        op = btn.operation
        if op in overwrite_files and overwrite_files[op].exists():
            reply = QMessageBox.warning(
                self,
                "Overwrite Warning",
                f"The file for operation '{op}' already exists.\n"
                "It will be overwritten.\n\nContinue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return False

        return True



    # -----------------------------
    # Run / Cancel
    # -----------------------------
    def run(self):
        if not self.validate():
            return

        self.log.clear()
        self.progress.setVisible(True)
        self.progress_label.setText("Starting…")

        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.exit_btn.setEnabled(False)

        btn = self.op_group.checkedButton()

        self.worker = Worker(
            self.trace1_edit.text(),
            self.trace2_edit.text(),
            btn.operation
        )

        self.worker.log.connect(self.log.append)
        self.worker.progress.connect(self.progress_label.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.cancelled.connect(self.on_cancelled)
        self.worker.start()

    def cancel(self):
        if self.worker:
            self.worker.cancel()
            self.progress_label.setText("Cancelling…")

    def on_finished(self, elapsed):
        self.progress.setVisible(False)
        self.progress_label.setText("")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.exit_btn.setEnabled(True)
        self.log.append(f"Completed in {elapsed:.3f} seconds")
        print("*"*50)
        print(f"⏱  \033[1;32mTime Taken: {elapsed:.3f} seconds\033[0m")
        print("*"*50)

    def on_cancelled(self):
        self.progress.setVisible(False)
        self.progress_label.setText("Cancelled")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.exit_btn.setEnabled(True)
        self.log.append("Operation cancelled")

    def on_error(self, msg):
        self.progress.setVisible(False)
        self.progress_label.setText("")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.exit_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", msg)


# =============================
# Entry Point
# =============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PyPalWindow()
    window.show()
    sys.exit(app.exec())

