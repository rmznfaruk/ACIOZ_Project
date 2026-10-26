"""Compact PySide6 holographic overlay and chat interface."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ArcReactor(QWidget):
    """Paint a lightweight animated cyan circular visualizer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the animation phase and repaint timer."""
        super().__init__(parent)
        self._phase = 0.0
        self.setMinimumSize(180, 180)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(40)

    def _advance(self) -> None:
        """Advance the animation and request a repaint."""
        self._phase = (self._phase + 2.0) % 360
        self.update()

    def paintEvent(self, _event: object) -> None:
        """Draw concentric rings and rotating indicator marks."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = min(self.width(), self.height()) * 0.39
        glow = QColor(30, 220, 255, 210)
        painter.setPen(QPen(glow, 2))
        painter.drawEllipse(center, int(radius), int(radius))
        painter.setPen(QPen(QColor(30, 220, 255, 90), 1))
        painter.drawEllipse(center, int(radius * 0.74), int(radius * 0.74))
        painter.drawEllipse(center, int(radius * 0.48), int(radius * 0.48))

        painter.save()
        painter.translate(center)
        painter.rotate(self._phase)
        painter.setPen(QPen(glow, 4))
        painter.drawLine(0, -int(radius * 1.1), 0, -int(radius * 0.88))
        painter.drawLine(0, int(radius * 0.88), 0, int(radius * 1.1))
        painter.restore()

        painter.setPen(QPen(QColor(130, 245, 255, 170), 1))
        for index in range(48):
            angle = math.radians(index * 7.5)
            inner = radius * (0.82 if index % 4 == 0 else 0.88)
            outer = radius * 0.96
            painter.drawLine(
                int(center.x() + math.cos(angle) * inner),
                int(center.y() + math.sin(angle) * inner),
                int(center.x() + math.cos(angle) * outer),
                int(center.y() + math.sin(angle) * outer),
            )


class AssistantWindow(QMainWindow):
    """Display assistant state, conversation output, and typed input."""

    def __init__(self) -> None:
        """Build a frameless, translucent, always-on-top desktop window."""
        super().__init__()
        self.setWindowTitle("ACIÖZ")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 430)

        panel = QWidget()
        panel.setStyleSheet(
            "QWidget { background: rgba(4, 18, 32, 232); color: #a9f6ff; "
            "border: 1px solid #1caac4; border-radius: 16px; }"
            "QLineEdit { background: rgba(8, 34, 48, 220); padding: 8px; }"
            "QPushButton { background: #07576b; padding: 8px; }"
        )
        layout = QVBoxLayout(panel)
        header = QHBoxLayout()
        title = QLabel("ACIÖZ  /  LOCAL")
        title.setStyleSheet("font-weight: bold; border: none;")
        close_button = QPushButton("×")
        close_button.setFixedWidth(34)
        close_button.clicked.connect(self.close)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_button)

        self.status_label = QLabel("Başlatılıyor…")
        self.status_label.setStyleSheet("border: none;")
        self.status_label.setWordWrap(True)
        self.visualizer = ArcReactor()
        self.response_label = QLabel("Sistem yalnızca yerel servisleri kullanır.")
        self.response_label.setWordWrap(True)
        self.response_label.setMinimumHeight(56)
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setStyleSheet("border: none; padding: 6px;")

        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Bir komut yaz…")
        self.send_button = QPushButton("Gönder")
        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_button)

        layout.addLayout(header)
        layout.addWidget(self.status_label)
        layout.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.response_label)
        layout.addLayout(input_row)
        self.setCentralWidget(panel)

    def set_status(self, text: str) -> None:
        """Update the visible listening or processing state."""
        self.status_label.setText(text)

    def set_response(self, text: str) -> None:
        """Display the latest assistant response."""
        self.response_label.setText(text)

    def take_input(self) -> str:
        """Return and clear the typed user request."""
        text = self.input_field.text().strip()
        self.input_field.clear()
        return text
