"""On-demand camera capture for local image analysis."""

from __future__ import annotations

import cv2


class VisionEngine:
    """Capture one JPEG frame without continuously recording the camera."""

    def __init__(self, camera_index: int = 0) -> None:
        """Store the camera device index."""
        self._camera_index = camera_index

    def capture_jpeg(self) -> bytes:
        """Capture one camera frame and return it encoded as JPEG bytes."""
        camera = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        try:
            if not camera.isOpened():
                raise RuntimeError("Kamera açılamadı; bağlantıyı ve izinleri kontrol et.")
            success, frame = camera.read()
            if not success:
                raise RuntimeError("Kameradan görüntü alınamadı.")
            encoded, buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            if not encoded:
                raise RuntimeError("Kamera görüntüsü JPEG'e dönüştürülemedi.")
            return buffer.tobytes()
        finally:
            camera.release()
