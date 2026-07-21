from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QRectF

class Renderer:
    def __init__(self, pet):
        self.pet = pet
        self.speech_text = ""
        self.speech_timer = 0.0
        self.bubble_height = 45  # Height allocated for speech bubble above the pet

    def set_speech(self, text, duration=2.5):
        """Displays a speech bubble with the given text and timer."""
        self.speech_text = text
        self.speech_timer = duration

    def update(self, dt):
        """Updates text display timers."""
        if self.speech_timer > 0.0:
            self.speech_timer -= dt
            if self.speech_timer <= 0.0:
                self.speech_text = ""
                self.speech_timer = 0.0

    def draw(self, painter, scale):
        """
        Renders the pet and overlay assets onto the window QPainter.
        """
        scaled_bubble_offset = int(self.bubble_height * scale)
        scaled_pet_w = int(self.pet.physics.width * scale)
        scaled_pet_h = int(self.pet.physics.height * scale)

        # 1. Draw Pet Sprite
        pixmap = self.pet.sprite.get_current_pixmap()
        if pixmap:
            painter.drawPixmap(0, scaled_bubble_offset, scaled_pet_w, scaled_pet_h, pixmap)

        # 2. Draw Speech Bubble Overlay
        if self.speech_text:
            self._draw_speech_bubble(painter, scaled_pet_w, scaled_bubble_offset, scale)

    def _draw_speech_bubble(self, painter, width, bubble_h, scale):
        # Position margins
        padding = int(4 * scale)
        bubble_rect = QRectF(
            padding, 
            padding, 
            width - 2 * padding, 
            bubble_h - int(10 * scale)
        )

        # Paint styling (Modern semi-transparent glassmorphic look)
        painter.setPen(QPen(QColor(60, 130, 255, 220), max(1, int(1.5 * scale))))
        painter.setBrush(QBrush(QColor(20, 20, 25, 230)))
        
        # Rounded bubble rectangle
        painter.drawRoundedRect(bubble_rect, int(6 * scale), int(6 * scale))

        # Triangle arrow pointing down to the pet head
        from PySide6.QtGui import QPolygonF
        from PySide6.QtCore import QPointF
        arrow = QPolygonF()
        cx = width / 2.0
        by = bubble_h - int(10 * scale)
        arrow.append(QPointF(cx - int(5 * scale), by))
        arrow.append(QPointF(cx + int(5 * scale), by))
        arrow.append(QPointF(cx, by + int(5 * scale)))
        
        painter.drawPolygon(arrow)

        # Render Text
        font = QFont("Segoe UI", int(9 * scale))
        painter.setFont(font)
        painter.setPen(QColor(240, 240, 250))
        
        # Word-wrapped centered text
        painter.drawText(
            bubble_rect, 
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
            self.speech_text
        )
