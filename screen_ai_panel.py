# -*- coding: utf-8 -*-
"""
Screen AI Panel - Standalone overlay app for selection-based OCR + AI Q&A.

Features:
- Draw a selection rectangle on screen, OCR the region, and use it as primary context.
- Minimal floating UI for asking questions and streaming AI answers.
- Defaults to DeepSeek R1 (free) via OpenRouter (OpenAI-compatible SDK).
- Uses provided API key by default; configurable via UI and environment variables.
- Privacy-first: Only selected text is sent by default. Optional broader screen OCR.
- Cross-platform (Windows/Mac primary). Requires Tesseract installed for OCR.
- Error handling and fallback to local OpenAI-compatible endpoint (e.g., Ollama) if available.

Run:
    python screen_ai_panel.py

Dependencies (install):
    pip install PyQt5 pyautogui pillow pytesseract openai requests

External dependency:
    Tesseract OCR
      - Windows: https://github.com/UB-Mannheim/tesseract/wiki (install and ensure tesseract.exe in PATH)
                 Common path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe
      - macOS: brew install tesseract (plus grant screen recording permission to Terminal)
      - Linux: sudo apt-get install tesseract-ocr

Hotkeys (when app is focused):
    - Ctrl+Shift+S: Start selection capture
    - Ctrl+Enter:   Ask the question
    - Esc:          Cancel selection overlay

Note:
- If you have Ollama running locally at http://localhost:11434, the app will automatically fallback
  to a local model if the remote API fails (privacy-friendly fallback).
"""

import os
import sys
import time
import traceback
from dataclasses import dataclass

from PyQt5.QtCore import (
    Qt,
    QRect,
    QPoint,
    QThread,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
    QFont,
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QGroupBox,
    QGridLayout,
    QSplitter,
    QMessageBox,
    QFileDialog,
)

# Third-party utilities
import pyautogui
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import requests

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


# -------------------------------
# Configuration & Defaults
# -------------------------------

# Default OpenAI-compatible API configuration (OpenRouter)
DEFAULT_BASE_URL = os.environ.get("OPENAI_COMPAT_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = os.environ.get("OPENAI_COMPAT_MODEL", "deepseek/deepseek-r1:free")

# Default API key (OpenRouter). Overridable via OPENAI_API_KEY environment variable.
DEFAULT_API_KEY = os.environ.get(
    "OPENAI_API_KEY",
    "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",
)

# Optional Windows Tesseract path auto-detection
if os.name == "nt":
    possible_paths = [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

# Speed up PyAutoGUI a bit
pyautogui.PAUSE = 0


@dataclass
class AIConfig:
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str = DEFAULT_API_KEY


class SelectionOverlay(QWidget):
    """A full-screen transparent overlay to draw a selection rectangle."""

    selectionMade = pyqtSignal(QRect)
    canceled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False
        # Cover the primary screen (simple & cross-platform)
        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())

    def start(self):
        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dark overlay
        overlay_color = QColor(0, 0, 0, 120)
        painter.fillRect(self.rect(), overlay_color)

        if self._selecting:
            rect = QRect(self._origin, self._current).normalized()
            # Clear area inside selection
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Draw border
            pen = QPen(QColor(0, 180, 255, 230), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Size label
            painter.setFont(QFont("Arial", 10))
            size_text = f"{rect.width()}x{rect.height()}"
            label_bg = QColor(0, 0, 0, 180)
            painter.setBrush(QBrush(label_bg))
            painter.setPen(Qt.NoPen)
            label_rect = QRect(rect.x(), rect.y() - 22, 80, 20)
            painter.drawRect(label_rect)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(label_rect.adjusted(5, 0, -5, 0), Qt.AlignLeft | Qt.AlignVCenter, size_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._current = event.pos()
            self._selecting = False
            rect = QRect(self._origin, self._current).normalized()
            self.hide()
            if rect.width() > 3 and rect.height() > 3:
                self.selectionMade.emit(rect)
            else:
                self.canceled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.canceled.emit()


class OCRWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, pil_image, lang="eng"):
        super().__init__()
        self.image = pil_image
        self.lang = lang

    def preprocess(self, im: Image.Image) -> Image.Image:
        # Convert to grayscale, increase contrast, slight blur to reduce noise
        im = im.convert("L")
        im = ImageOps.autocontrast(im)
        im = im.filter(ImageFilter.MedianFilter(size=3))
        return im

    def run(self):
        try:
            if pytesseract is None:
                self.error.emit("pytesseract is not installed.")
                return
            im = self.preprocess(self.image)
            text = pytesseract.image_to_string(im, lang=self.lang, config="--psm 6 --oem 3")
            text = text.strip()
            self.finished.emit(text)
        except pytesseract.pytesseract.TesseractNotFoundError as e:
            self.error.emit("Tesseract not found. Install Tesseract OCR and set the correct path in settings. "
                            "Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                            f"Details: {e}")
        except Exception as e:
            self.error.emit(f"OCR error: {e}")


class AIWorker(QThread):
    token = pyqtSignal(str)
    completed = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config: AIConfig, system_prompt: str, user_prompt: str):
        super().__init__()
        self.config = config
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        # Try remote first (OpenRouter by default)
        if OpenAI is None:
            self.error.emit("openai SDK not installed. Run: pip install openai")
            return

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": self.user_prompt})

        # Attempt remote
        try:
            client = OpenAI(base_url=self.config.base_url, api_key=self.config.api_key)
            stream = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=0.4,
                max_tokens=1200,
                stream=True,
            )
            full = []
            for event in stream:
                if self._stop:
                    break
                try:
                    delta = event.choices[0].delta.content or ""
                except Exception:
                    delta = ""
                if delta:
                    full.append(delta)
                    self.token.emit(delta)
            self.completed.emit("".join(full))
            return
        except Exception as e_remote:
            # Remote failed; try local OpenAI-compatible (e.g., Ollama)
            try:
                # Quick health check for Ollama
                requests.get("http://localhost:11434/", timeout=1)
                local_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                local_model = os.environ.get("OLLAMA_MODEL", "llama3.1")
                stream = local_client.chat.completions.create(
                    model=local_model,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=1200,
                    stream=True,
                )
                full = []
                for event in stream:
                    if self._stop:
                        break
                    try:
                        delta = event.choices[0].delta.content or ""
                    except Exception:
                        delta = ""
                    if delta:
                        full.append(delta)
                        self.token.emit(delta)
                self.completed.emit("".join(full))
                return
            except Exception as e_local:
                self.error.emit(
                    "AI request failed. Remote error: %s | Local fallback error: %s"
                    % (str(e_remote), str(e_local))
                )


class ScreenAIPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen AI Panel")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(860, 620)

        self.config = AIConfig()
        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.selectionMade.connect(self.on_selection)
        self.selection_overlay.canceled.connect(self.on_selection_canceled)

        self.selected_text = ""
        self.last_region = None  # QRect

        self._apply_styles()
        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        header = QLabel("🧠 Screen AI Panel – Selection OCR + DeepSeek R1")
        header.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        layout.addWidget(header)

        # Controls row
        controls = QHBoxLayout()
        self.btn_select = QPushButton("Select (Ctrl+Shift+S)")
        self.btn_select.clicked.connect(self.start_selection)
        controls.addWidget(self.btn_select)

        self.cb_auto_ask = QCheckBox("Auto-ask on select")
        self.cb_auto_ask.setChecked(True)
        controls.addWidget(self.cb_auto_ask)

        self.cb_include_screen = QCheckBox("Include full-screen OCR (optional)")
        self.cb_include_screen.setChecked(False)
        controls.addWidget(self.cb_include_screen)

        self.cb_local_only = QCheckBox("Local-only (no API)")
        self.cb_local_only.setChecked(False)
        controls.addWidget(self.cb_local_only)

        controls.addStretch(1)
        layout.addLayout(controls)

        # Settings group
        settings = QGroupBox("AI Settings (OpenAI-compatible)")
        grid = QGridLayout(settings)
        grid.addWidget(QLabel("Base URL:"), 0, 0)
        self.le_base_url = QLineEdit(self.config.base_url)
        grid.addWidget(self.le_base_url, 0, 1)

        grid.addWidget(QLabel("Model:"), 1, 0)
        self.le_model = QLineEdit(self.config.model)
        grid.addWidget(self.le_model, 1, 1)

        grid.addWidget(QLabel("API Key:"), 2, 0)
        self.le_api_key = QLineEdit(self.config.api_key)
        self.le_api_key.setEchoMode(QLineEdit.Password)
        grid.addWidget(self.le_api_key, 2, 1)

        # Tesseract configuration
        grid.addWidget(QLabel("Tesseract Path:"), 3, 0)
        self.le_tesseract = QLineEdit(getattr(pytesseract.pytesseract, "tesseract_cmd", ""))
        grid.addWidget(self.le_tesseract, 3, 1)

        tess_btns = QHBoxLayout()
        self.btn_browse_tess = QPushButton("Browse")
        self.btn_test_tess = QPushButton("Test Tesseract")
        tess_btns.addWidget(self.btn_browse_tess)
        tess_btns.addWidget(self.btn_test_tess)
        grid.addLayout(tess_btns, 4, 1)

        self.btn_browse_tess.clicked.connect(self.browse_tesseract)
        self.btn_test_tess.clicked.connect(self.test_tesseract)

        layout.addWidget(settings)

        # Splitter: left – selected text; right – Q/A
        splitter = QSplitter()

        # Left panel: Selected text preview
        left_box = QGroupBox("Selected Text (OCR result)")
        left_layout = QVBoxLayout(left_box)
        self.te_selected = QTextEdit()
        self.te_selected.setReadOnly(True)
        left_layout.addWidget(self.te_selected)
        splitter.addWidget(left_box)

        # Right panel: Q/A
        right_box = QGroupBox("Ask & Answer")
        right_layout = QVBoxLayout(right_box)

        self.le_question = QLineEdit()
        self.le_question.setPlaceholderText("Type your question and press Ctrl+Enter…")
        right_layout.addWidget(self.le_question)

        btn_row = QHBoxLayout()
        self.btn_ask = QPushButton("Ask (Ctrl+Enter)")
        self.btn_ask.clicked.connect(self.ask)
        btn_row.addWidget(self.btn_ask)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_stream)
        self.btn_stop.setEnabled(False)
        btn_row.addWidget(self.btn_stop)

        self.btn_copy = QPushButton("Copy Answer")
        self.btn_copy.clicked.connect(self.copy_answer)
        btn_row.addWidget(self.btn_copy)

        btn_row.addStretch(1)
        right_layout.addLayout(btn_row)

        self.te_answer = QTextEdit()
        self.te_answer.setReadOnly(True)
        right_layout.addWidget(self.te_answer)

        splitter.addWidget(right_box)
        splitter.setSizes([350, 500])
        layout.addWidget(splitter)

        # Status
        self.lbl_status = QLabel("Ready. Use Ctrl+Shift+S to select an area.")
        layout.addWidget(self.lbl_status)

    def _bind_shortcuts(self):
        # Use Qt shortcuts within the app window (cross-platform, no elevated perms)
        self.btn_select.setShortcut("Ctrl+Shift+S")
        self.btn_ask.setShortcut("Ctrl+Return")

    # -------------------------------
    # Selection + OCR
    # -------------------------------
    def start_selection(self):
        self.lbl_status.setText("Select a region to OCR… (Esc to cancel)")
        self.selection_overlay.start()

    def on_selection_canceled(self):
        self.lbl_status.setText("Selection canceled.")

    def on_selection(self, rect: QRect):
        # Map QRect to screen coordinates for PyAutoGUI
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        self.last_region = (x, y, w, h)
        try:
            img = pyautogui.screenshot(region=(x, y, w, h))  # PIL Image
        except Exception as e:
            self._error_dialog(
                "Screenshot failed",
                f"Could not capture the screen region.\n\nError: {e}\n\nOn macOS, ensure Terminal/IDE has Screen Recording permission.",
            )
            self.lbl_status.setText("Screenshot failed.")
            return

        self.lbl_status.setText("Running OCR…")
        self.set_tesseract_path_from_ui()
        self.ocr_worker = OCRWorker(img)
        self.ocr_worker.finished.connect(self.on_ocr_done)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.start()

    def on_ocr_done(self, text: str):
        self.selected_text = text or ""
        self.te_selected.setPlainText(self.selected_text)
        if not self.selected_text:
            self.lbl_status.setText("No text recognized. Try again or adjust region.")
            return
        self.lbl_status.setText("OCR complete.")
        if self.cb_auto_ask.isChecked():
            if not self.le_question.text().strip():
                self.le_question.setText("Explain the selected text and answer my question if any.")
            self.ask()

    def on_ocr_error(self, err: str):
        self._error_dialog("OCR Error", err)
        self.lbl_status.setText("OCR error.")

    # -------------------------------
    # AI Interaction
    # -------------------------------
    def _build_prompt(self, selected_text: str, optional_screen_text: str, user_question: str) -> tuple[str, str]:
        system = (
            "You are an AI assistant that answers questions based primarily on text the user selected from their screen.\n"
            "Use the SELECTED_TEXT as the main context. If SCREEN_TEXT is provided, you may reference it for additional context,"
            " but prioritize the selected text. Be concise, accurate, and cite what comes from the screen."
        )
        context_parts = []
        if selected_text:
            context_parts.append(f"SELECTED_TEXT:\n{selected_text}\n")
        if optional_screen_text:
            context_parts.append("\n--- Optional broader screen OCR (may be noisy) ---\n")
            context_parts.append(optional_screen_text)
        user = ("\n".join(context_parts) +
                "\n\nUser question:\n" + (user_question or "Explain the selected content."))
        return system, user

    def ask(self):
        if self.cb_local_only.isChecked():
            self.te_answer.setPlainText(
                "Local-only mode is enabled. No API calls will be made. Disable Local-only to query the model."
            )
            return

        if not self.selected_text.strip():
            self._warn_dialog("No selection", "Select a region first (Ctrl+Shift+S).")
            return

        self.config.base_url = (self.le_base_url.text().strip() or DEFAULT_BASE_URL)
        self.config.model = (self.le_model.text().strip() or DEFAULT_MODEL)
        self.config.api_key = (self.le_api_key.text().strip() or DEFAULT_API_KEY)
        self.set_tesseract_path_from_ui()

        if not self.config.api_key and self.config.base_url.startswith("https://"):
            self._warn_dialog("Missing API key", "Enter a valid API key in settings.")
            return

        screen_text = ""
        if self.cb_include_screen.isChecked():
            try:
                full_img = pyautogui.screenshot()
                screen_text = pytesseract.image_to_string(full_img, lang="eng", config="--psm 6 --oem 3")[:6000]
            except pytesseract.pytesseract.TesseractNotFoundError as e:
                self._warn_dialog("Tesseract Not Found", "Full-screen OCR skipped because Tesseract was not found. "
                                   "Install Tesseract and set its path in settings.\n"
                                   "Windows: https://github.com/UB-Mannheim/tesseract/wiki")
                screen_text = ""
            except Exception as e:
                # Non-fatal; proceed with selected text only
                screen_text = ""
                self.lbl_status.setText(f"Full-screen OCR error: {e}")

        system, user = self._build_prompt(self.selected_text, screen_text, self.le_question.text().strip())

        self.te_answer.clear()
        self.btn_ask.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("Querying AI…")

        self.ai_worker = AIWorker(self.config, system, user)
        self.ai_worker.token.connect(self._on_ai_token)
        self.ai_worker.completed.connect(self._on_ai_complete)
        self.ai_worker.error.connect(self._on_ai_error)
        self.ai_worker.start()

    def stop_stream(self):
        if hasattr(self, "ai_worker") and self.ai_worker.isRunning():
            self.ai_worker.stop()
            self.lbl_status.setText("Stopped.")
            self.btn_ask.setEnabled(True)
            self.btn_stop.setEnabled(False)

    def _on_ai_token(self, delta: str):
        self.te_answer.moveCursor(self.te_answer.textCursor().End)
        self.te_answer.insertPlainText(delta)
        self.te_answer.moveCursor(self.te_answer.textCursor().End)

    def _on_ai_complete(self, full: str):
        self.btn_ask.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Done.")

    def _on_ai_error(self, err: str):
        self.btn_ask.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Error.")
        self._error_dialog("AI Error", err)

    # -------------------------------
    # Utilities
    # -------------------------------
    def _apply_styles(self):
        # Minimal dark style for readability
        self.setStyleSheet(
            """
            QWidget { background: #121212; color: #e8e8e8; }
            QLineEdit, QTextEdit { background: #1a1a1a; color: #e8e8e8; border: 1px solid #333; }
            QPushButton { background: #222; color: #e8e8e8; border: 1px solid #555; padding: 4px 8px; }
            QPushButton:hover { background: #2a2a2a; }
            QGroupBox { border: 1px solid #333; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0px 3px 0px 3px; }
            QToolTip { background: #333; color: #eee; border: 1px solid #555; }
            """
        )

    def show_and_raise(self):
        self.show()
        try:
            self.raise_()
            self.activateWindow()
        except Exception:
            pass

    def set_selected_text(self, text: str, auto_ask: bool = False, question: str | None = None):
        text = (text or "").strip()
        self.selected_text = text
        self.te_selected.setPlainText(text)
        if question is not None:
            self.le_question.setText(question)
        if auto_ask and text:
            if not self.le_question.text().strip():
                self.le_question.setText("Explain the selected text.")
            self.ask()

    def prefill_question(self, question: str):
        self.le_question.setText(question or "")

    def focus_question_input(self):
        self.le_question.setFocus()

    def set_tesseract_path_from_ui(self):
        path = self.le_tesseract.text().strip()
        if path:
            pytesseract.pytesseract.tesseract_cmd = path

    def browse_tesseract(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select tesseract executable", "", "Executables (*.exe);;All Files (*)")
        if path:
            self.le_tesseract.setText(path)
            self.set_tesseract_path_from_ui()

    def test_tesseract(self):
        self.set_tesseract_path_from_ui()
        try:
            ver = pytesseract.get_tesseract_version()
            QMessageBox.information(self, "Tesseract", f"Detected Tesseract version: {ver}")
        except Exception as e:
            QMessageBox.critical(self, "Tesseract Error", "Could not run Tesseract. Ensure it is installed and the path is correct.\n\nError: %s" % e)

    def copy_answer(self):
        text = self.te_answer.toPlainText().strip()
        if not text:
            return
        QApplication.clipboard().setText(text)
        self.lbl_status.setText("Answer copied to clipboard.")

    def _error_dialog(self, title: str, msg: str):
        QMessageBox.critical(self, title, msg)

    def _warn_dialog(self, title: str, msg: str):
        QMessageBox.warning(self, title, msg)


def main():
    # High DPI support for better coordinate consistency
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    win = ScreenAIPanel()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
