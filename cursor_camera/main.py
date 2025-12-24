import os
import sys
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
	QApplication,
	QCheckBox,
	QComboBox,
	QGridLayout,
	QGroupBox,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMainWindow,
	QPushButton,
	QSpinBox,
	QVBoxLayout,
	QWidget,
	QMessageBox,
)


ROLES: List[str] = ["Front", "Back", "Left", "Right", "Top", "Down", "Additional1", "Additional2"]
ROLE_SUFFIX: Dict[str, str] = {
	"Front": "F",
	"Back": "B",
	"Left": "L",
	"Right": "R",
	"Top": "T",
	"Down": "D",
	"Additional1": "A1",
	"Additional2": "A2",
}
DEFAULT_WIDTH = 640  # Default (now configurable via dropdown)
DEFAULT_HEIGHT = 480
SCAN_MAX_INDEX = 15  # scan 0..15 for available cameras
FRAME_INTERVAL_MS = 33  # ~30 FPS
PREVIEW_WIDTH = 640  # Lower resolution for preview performance
PREVIEW_HEIGHT = 360

# Reduce OpenCV log verbosity
try:
	cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except Exception:
	pass


def ensure_dirs():
	for role in ROLES:
		os.makedirs(os.path.join("images", role), exist_ok=True)


def zero_pad_id(id_text: str, width: int = 4) -> str:
	digits = "".join(ch for ch in id_text if ch.isdigit())
	if not digits:
		return "".zfill(width)
	return digits.zfill(width)


def quick_camera_test(index: int) -> bool:
	"""Quick test if camera index is available."""
	try:
		cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
		if cap and cap.isOpened():
			cap.release()
			return True
	except Exception:
		pass
	return False


def open_capture_with_fallback(index: int) -> Optional[cv2.VideoCapture]:
	"""Try MSMF -> DSHOW -> ANY backends to open camera by index."""
	backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
	for backend in backends:
		try:
			cap = cv2.VideoCapture(index, backend)
			if cap and cap.isOpened():
				return cap
		except Exception:
			pass
		try:
			if 'cap' in locals():
				cap.release()
		except Exception:
			pass
	return None


class CameraPanel(QWidget):
	def __init__(self, role: str, main_window=None, parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		self.role = role
		self.device_index: Optional[int] = None
		self.cap: Optional[cv2.VideoCapture] = None
		self.last_frame: Optional[np.ndarray] = None  # Cache last frame
		self.main_window = main_window  # Reference to MainWindow

		self.preview_label = QLabel("No Signal")
		self.preview_label.setAlignment(Qt.AlignCenter)
		self.preview_label.setMinimumSize(320, 180)
		self.preview_label.setStyleSheet("background-color: #111; color: #aaa;")

		self.device_combo = QComboBox()
		self.device_combo.setEditable(False)

		self.open_btn = QPushButton("Open")

		self.status_label = QLabel("Idle")
		self.status_label.setStyleSheet("color: #888;")

		group = QGroupBox(self.role)
		v = QVBoxLayout()
		v.addWidget(self.preview_label)

		h = QHBoxLayout()
		h.addWidget(QLabel("Device:"))
		h.addWidget(self.device_combo, 1)
		v.addLayout(h)

		v.addWidget(self.open_btn)

		v.addWidget(self.status_label)
		group.setLayout(v)

		outer = QVBoxLayout()
		outer.addWidget(group)
		self.setLayout(outer)

	def set_devices(self, indices: List[int]) -> None:
		current = self.device_combo.currentText()
		self.device_combo.clear()
		self.device_combo.addItem("- Unassigned -")
		for idx in indices:
			self.device_combo.addItem(f"Camera {idx}")
		if current:
			# try restore previous selection if still available
			idx = self.device_combo.findText(current)
			if idx >= 0:
				self.device_combo.setCurrentIndex(idx)

	def get_selected_index(self) -> Optional[int]:
		text = self.device_combo.currentText()
		if text and text.startswith("Camera "):
			try:
				return int(text.split(" ")[1])
			except (IndexError, ValueError):
				pass
		return None

	def open(self) -> bool:
		self.close()
		self.device_index = self.get_selected_index()
		if self.device_index is None:
			self.status_label.setText("Unassigned")
			return False
		
		# Check if camera is already in use by another panel
		if self.main_window and self.device_index in self.main_window.opened_cameras:
			self.status_label.setText(f"Camera {self.device_index} in use")
			return False
		
		cap = open_capture_with_fallback(self.device_index)
		if not cap:
			self.status_label.setText(f"Failed to open {self.device_index}")
			return False
		
		# Get resolution from main window
		resolution = self._get_resolution()
		width, height = resolution
		
		# Set buffer size to 1 to minimize latency
		cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
		# Set resolution
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
		# Use MJPG for better performance
		cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
		# Enable auto-exposure for better image quality
		cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # 0.75 = auto
		
		self.cap = cap
		
		# Track opened camera
		if self.main_window:
			self.main_window.opened_cameras[self.device_index] = self.role
		
		self.status_label.setText(f"Opened #{self.device_index}")
		return True
	
	def _get_resolution(self) -> Tuple[int, int]:
		"""Get selected resolution from main window"""
		if not self.main_window:
			return (640, 480)
		
		resolution_text = self.main_window.resolution_combo.currentText()
		if "1920x1080" in resolution_text:
			return (1920, 1080)
		elif "1280x720" in resolution_text:
			return (1280, 720)
		else:  # Default to 640x480
			return (640, 480)

	def close(self) -> None:
		if self.cap is not None:
			# Release camera from tracking
			if self.main_window and self.device_index is not None:
				self.main_window.opened_cameras.pop(self.device_index, None)
			
			try:
				self.cap.release()
			except Exception:
				pass
		self.cap = None
		self.last_frame = None
		self.status_label.setText("Idle")
		self.preview_label.setText("No Signal")

	def update_preview(self) -> None:
		if self.cap is None:
			return
		# Try to read new frame
		ok, frame = self.cap.read()
		if ok and frame is not None:
			self.last_frame = frame.copy() if frame is not None else None
			self.status_label.setText("Live")
			self._show_frame(frame)
		elif self.last_frame is not None:
			# Use cached frame if read failed
			self._show_frame(self.last_frame)
		else:
			self.status_label.setText("Read failed")

	def _show_frame(self, frame: np.ndarray) -> None:
		# Resize frame for preview to improve performance
		display_width = min(PREVIEW_WIDTH, self.preview_label.width())
		display_height = min(PREVIEW_HEIGHT, self.preview_label.height())
		
		# Resize using OpenCV before color conversion (faster)
		frame_resized = cv2.resize(frame, (display_width, display_height))
		
		# Convert to RGB
		rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
		h, w, ch = rgb.shape
		bytes_per_line = ch * w
		qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
		pix = QPixmap.fromImage(qimg).scaled(
			self.preview_label.width(),
			self.preview_label.height(),
			Qt.KeepAspectRatio,
			Qt.FastTransformation,  # Use FastTransformation for better performance
		)
		self.preview_label.setPixmap(pix)

	def grab(self) -> bool:
		if self.cap is None:
			return False
		return self.cap.grab()

	def retrieve(self) -> Optional[np.ndarray]:
		if self.cap is None:
			return None
		ok, frame = self.cap.retrieve()
		if not ok:
			return None
		return frame

	def capture_single(self) -> bool:
		"""Capture a single image and save it"""
		if self.cap is None:
			return False
		
		ok, frame = self.cap.read()
		if not ok or frame is None:
			return False
		
		# Get capture ID from main window
		if not self.main_window:
			return False
		
		pad = max(2, int(self.main_window.pad_width.value()))
		capture_id = zero_pad_id(self.main_window.id_input.text(), width=pad)
		if not capture_id:
			capture_id = "0".zfill(pad)
		
		# Save image
		suffix = ROLE_SUFFIX[self.role]
		fname = f"{capture_id}_{suffix}.jpg"
		out_dir = os.path.join("images", self.role)
		os.makedirs(out_dir, exist_ok=True)
		out_path = os.path.join(out_dir, fname)
		
		try:
			cv2.imwrite(out_path, frame)
			return True
		except Exception:
			return False


class MainWindow(QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.setWindowTitle("Walnut 8-Camera Capture")
		ensure_dirs()

		self.opened_cameras: Dict[int, str] = {}  # Track which camera is used by which panel
		self.panels: Dict[str, CameraPanel] = {role: CameraPanel(role, main_window=self) for role in ROLES}

		# Controls
		self.rescan_btn = QPushButton("Quick Scan (0-7)")
		self.manual_btn = QPushButton("Manual Add Camera")
		self.capture_all_btn = QPushButton("Capture All")

		self.id_input = QLineEdit()
		self.id_input.setPlaceholderText("0001")
		self.id_input.setText("0001")
		self.auto_inc = QCheckBox("Auto Increment")
		self.pad_width = QSpinBox()
		self.pad_width.setRange(2, 8)
		self.pad_width.setValue(4)
		
		# Resolution dropdown
		self.resolution_combo = QComboBox()
		self.resolution_combo.addItems(["640x480 (Fast)", "1280x720 (HD)", "1920x1080 (Full HD)"])
		self.resolution_combo.setCurrentIndex(0)  # Default to 640x480

		# Layout grid 2 x 4
		grid = QGridLayout()
		positions: List[Tuple[int, int]] = [
			(0, 0), (0, 1), (0, 2), (0, 3),
			(1, 0), (1, 1), (1, 2), (1, 3),
		]
		for (row, col), role in zip(positions, ROLES):
			grid.addWidget(self.panels[role], row, col)

		controls = QHBoxLayout()
		controls.addWidget(self.rescan_btn)
		controls.addWidget(self.manual_btn)
		controls.addStretch(1)
		controls.addWidget(QLabel("Resolution:"))
		controls.addWidget(self.resolution_combo)
		controls.addWidget(QLabel("ID:"))
		controls.addWidget(self.id_input)
		controls.addWidget(QLabel("Pad"))
		controls.addWidget(self.pad_width)
		controls.addWidget(self.auto_inc)
		controls.addStretch(1)
		controls.addWidget(self.capture_all_btn)

		root = QVBoxLayout()
		root.addLayout(grid)
		root.addLayout(controls)

		container = QWidget()
		container.setLayout(root)
		self.setCentralWidget(container)

		# Timer for previews
		self.timer = QTimer(self)
		self.timer.setInterval(FRAME_INTERVAL_MS)
		self.timer.timeout.connect(self._update_all_previews)

		# Signals
		self.rescan_btn.clicked.connect(self.rescan_devices)
		self.manual_btn.clicked.connect(self.manual_add_camera)
		self.capture_all_btn.clicked.connect(self.capture_all)
		
		# Connect panel buttons
		for role, panel in self.panels.items():
			panel.open_btn.clicked.connect(lambda checked, p=panel: p.open())
			panel.open_btn.clicked.connect(self._start_preview_if_needed)

		# Initial scan
		self.rescan_devices()

	def rescan_devices(self) -> None:
		indices = self._scan_available_cameras()
		for panel in self.panels.values():
			panel.set_devices(indices)
		QMessageBox.information(self, "Scan Complete", f"Found {len(indices)} cameras: {indices}")

	def manual_add_camera(self) -> None:
		"""Add a camera manually by index."""
		text, ok = QMessageBox.getText(self, "Manual Add Camera", "Enter camera index (0-15):")
		if ok and text.isdigit():
			index = int(text)
			if 0 <= index <= 15:
				if quick_camera_test(index):
					# Add to all panels
					for panel in self.panels.values():
						current_items = [panel.device_combo.itemText(i) for i in range(panel.device_combo.count())]
						if f"Camera {index}" not in current_items:
							panel.device_combo.addItem(f"Camera {index}")
					QMessageBox.information(self, "Success", f"Camera {index} added successfully!")
				else:
					QMessageBox.warning(self, "Error", f"Camera {index} not available")
			else:
				QMessageBox.warning(self, "Error", "Index must be 0-15")
		elif ok:
			QMessageBox.warning(self, "Error", "Please enter a valid number")

	def _scan_available_cameras(self) -> List[int]:
		"""Fast camera enumeration - only test common indices."""
		found: List[int] = []
		# Test camera indices 0-7 for speed
		for i in range(8):
			if quick_camera_test(i):
				found.append(i)
		return found

	def _start_preview_if_needed(self) -> None:
		"""Start preview timer if any camera is opened"""
		if not self.timer.isActive():
			any_opened = any(panel.cap is not None for panel in self.panels.values())
			if any_opened:
				self.timer.start()

	def capture_all(self) -> None:
		"""Capture images from all opened cameras simultaneously"""
		pad = max(2, int(self.pad_width.value()))
		capture_id = zero_pad_id(self.id_input.text(), width=pad)
		if not capture_id:
			capture_id = "0".zfill(pad)

		# Get frames from all active cameras
		images_to_save: List[Tuple[str, np.ndarray]] = []
		for role, panel in self.panels.items():
			if panel.cap is None:
				continue
			ok, frame = panel.cap.read()
			if ok and frame is not None:
				images_to_save.append((role, frame))

		# Save frames in parallel (faster)
		for role, frame in images_to_save:
			suffix = ROLE_SUFFIX[role]
			fname = f"{capture_id}_{suffix}.jpg"
			out_dir = os.path.join("images", role)
			os.makedirs(out_dir, exist_ok=True)
			out_path = os.path.join(out_dir, fname)
			try:
				cv2.imwrite(out_path, frame)
			except Exception:
				# ignore single save errors
				pass

		# Auto increment
		if self.auto_inc.isChecked():
			try:
				next_val = int(capture_id) + 1
				self.id_input.setText(str(next_val).zfill(pad))
			except Exception:
				pass

	def _update_all_previews(self) -> None:
		"""Update preview for all panels"""
		for panel in self.panels.values():
			panel.update_preview()
		
		# Stop timer if no cameras are opened
		if self.timer.isActive():
			any_opened = any(panel.cap is not None for panel in self.panels.values())
			if not any_opened:
				self.timer.stop()


def main() -> None:
	app = QApplication(sys.argv)
	win = MainWindow()
	win.resize(1800, 800)
	win.show()
	sys.exit(app.exec_())


if __name__ == "__main__":
	main()
