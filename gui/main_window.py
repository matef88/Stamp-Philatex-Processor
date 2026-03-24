"""
Stamp Philatex Processor - Main GUI Window
Primary application window with processing controls.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFileDialog, QProgressBar, QTextEdit,
        QSplitter, QFrame, QGroupBox, QSpinBox, QCheckBox, QComboBox,
        QStatusBar, QToolBar, QMessageBox, QScrollArea, QGridLayout,
        QColorDialog, QTabWidget, QDoubleSpinBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
    from PyQt6.QtGui import QPixmap, QIcon, QAction, QFont, QColor
except ImportError as e:
    print("=================================================================")
    print("CRITICAL ERROR: Failed to load GUI framework (PyQt6).")
    print("This is usually caused by missing C++ redistributables or ")
    print("conflicting DLLs on your system.")
    print(f"Error details: {e}")
    print("=================================================================")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

try:
    from utils import load_config, get_project_root, setup_logging, get_image_files, get_resource_path, batch_convert_heic_to_jpg
    from process_stamps import StampProcessor, ProcessingResult
except ImportError as e:
    # Create simple app to show error if imports fail
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Startup Error", 
        f"Failed to import core modules.\n\nError: {e}\n\nPlease run 'install_dependencies.bat' to fix this.")
    sys.exit(1)


class ProcessingWorker(QThread):
    """Background worker thread for image processing."""

    progress = pyqtSignal(int, int, str)  # current, total, filename
    result = pyqtSignal(object)  # ProcessingResult
    finished = pyqtSignal(list)  # All results
    error = pyqtSignal(str)

    def __init__(self, processor: StampProcessor, input_path: Path, parent=None):
        super().__init__(parent)
        self.processor = processor
        self.input_path = input_path
        self._is_cancelled = False

    def run(self):
        """Run processing in background thread."""
        try:
            # Set dynamic output path
            self.processor.set_output_from_input(self.input_path)

            # HEIC Conversion (Always run)
            if self.input_path.is_dir(): # Only relevant for folders
                self.progress.emit(0, 0, "Checking for HEIC files...")
                batch_convert_heic_to_jpg(
                    directory=self.input_path,
                    delete_heic=True, # Always delete as requested
                    logger=self.processor.logger
                )

            # Get image files (Re-scan to get new JPGs)
            if self.input_path.is_file():
                image_files = [self.input_path]
            else:
                formats = self.processor.config.get('input', {}).get(
                    'supported_formats', ['.jpg', '.png']
                )
                image_files = get_image_files(self.input_path, recursive=False, formats=formats)

            total = len(image_files)
            results = []

            for i, img_path in enumerate(image_files):
                if self._is_cancelled:
                    break

                self.progress.emit(i + 1, total, img_path.name)

                result = self.processor.process_single_image(img_path)
                results.append(result)
                self.result.emit(result)

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        """Request cancellation."""
        self._is_cancelled = True


class ThumbnailWidget(QFrame):
    """Widget displaying a processed image thumbnail."""

    def __init__(self, result: ProcessingResult, parent=None):
        super().__init__(parent)
        self.result = result
        self._setup_ui()

    def _setup_ui(self):
        """Setup thumbnail UI."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setLineWidth(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Thumbnail image
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: transparent; border: none;")

        # Output path handling (dynamic)
        if self.result.output_path and self.result.output_path.exists():
            pixmap = QPixmap(str(self.result.output_path))
            scaled = pixmap.scaled(
                140, 140,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("No Preview")

        layout.addWidget(self.image_label)

        # Filename
        name_label = QLabel(self.result.input_path.name[:20])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(name_label)

        # Status indicator
        if self.result.success:
            if self.result.is_duplicate:
                status_text = "Duplicate"
                # Orange/Yellow for duplicate
                status_color = "#ffb86c"
                self.setStyleSheet("ThumbnailWidget { border: 2px solid #ffb86c; background-color: #44475a; border-radius: 8px; }")
            else:
                status_text = f"{self.result.confidence:.0%}"
                # Green for success
                status_color = "#50fa7b"
                self.setStyleSheet("ThumbnailWidget { border: 1px solid #6272a4; background-color: #44475a; border-radius: 8px; } ThumbnailWidget:hover { border: 1px solid #bd93f9; background-color: #55586c; }")
        else:
            status_text = "Failed"
            # Red for failure
            status_color = "#ff5555"
            self.setStyleSheet("ThumbnailWidget { border: 2px solid #ff5555; background-color: #44475a; border-radius: 8px; }")

        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(status_label)


class StampDetectionGUI(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.config = load_config()
        # Log to Desktop for easier debugging of frozen exe
        log_file = Path.home() / "Desktop" / "StampDetection_Log.txt"
        self.logger = setup_logging("GUI", log_file=str(log_file), level="DEBUG")
        self.processor = None
        self.worker = None
        self.results = []
        self.current_theme = 'dark'  # Track current theme

        self._setup_ui()
        self._apply_theme()
        
        # Enable Drag & Drop
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop event."""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if not files:
            return
            
        # If folder dropped, use it
        p = Path(files[0])
        if p.is_dir():
            self._set_input_folder(p)
        # If file dropped, use parent folder
        elif p.is_file():
            self._set_input_folder(p.parent)

    def _set_input_folder(self, folder_path: Path):
        """Helper to set input folder."""
        self.input_folder = folder_path
        self.folder_label.setText(str(self.input_folder))

        # Count images
        formats = self.config.get('input', {}).get('supported_formats', ['.jpg', '.png'])
        images = get_image_files(self.input_folder, recursive=False, formats=formats)
        self.image_count_label.setText(f"Images: {len(images)}")

        self.process_btn.setEnabled(len(images) > 0)
        self._log(f"Selected folder: {folder_path} ({len(images)} images)")

    def _setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("Stamp Philatex Processor")

        # Window size from config
        gui_config = self.config.get('gui', {})
        self.resize(
            gui_config.get('window_width', 1400),
            gui_config.get('window_height', 900)
        )

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        left_panel = self._create_control_panel()
        splitter.addWidget(left_panel)

        # Right panel - Results
        right_panel = self._create_results_panel()
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (30% / 70%)
        splitter.setSizes([400, 1000])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Menu bar
        self._create_menu_bar()

    def _create_control_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Input section
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setWordWrap(True)
        folder_layout.addWidget(self.folder_label, 1)

        self.browse_btn = QPushButton("Browse Folder...")
        self.browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(self.browse_btn)

        input_layout.addLayout(folder_layout)

        # Image count
        self.image_count_label = QLabel("Images: 0")
        input_layout.addWidget(self.image_count_label)

        layout.addWidget(input_group)

        layout.addWidget(input_group)

        # Settings Tabs
        settings_tabs = QTabWidget()
        settings_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #6272a4; }")

        # Tab 1: Basic Settings
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)

        # Confidence threshold
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Confidence:"))
        self.confidence_spin = QSpinBox()
        self.confidence_spin.setRange(10, 100)
        self.confidence_spin.setValue(int(self.config.get('detection', {}).get('confidence_threshold', 0.5) * 100))
        self.confidence_spin.setSuffix("%")
        self.confidence_spin.setToolTip("Minimum confidence to detect a stamp.")
        conf_layout.addWidget(self.confidence_spin)
        basic_layout.addLayout(conf_layout)

        # Checkboxes
        self.rotation_check = QCheckBox("Auto-rotate (deskew)")
        self.rotation_check.setChecked(self.config.get('processing', {}).get('rotation_correction', True))
        self.rotation_check.setToolTip("Automatically rotate stamps to be upright.")
        basic_layout.addWidget(self.rotation_check)

        self.normalize_check = QCheckBox("Normalize aspect ratio")
        self.normalize_check.setChecked(self.config.get('processing', {}).get('normalize_aspect_ratio', True))
        self.normalize_check.setToolTip("Prevent long thin strips by adding texture padding.")
        
        # Max aspect ratio spinner
        self.max_ratio_spin = QDoubleSpinBox()
        self.max_ratio_spin.setRange(1.0, 5.0)
        self.max_ratio_spin.setSingleStep(0.1)
        self.max_ratio_spin.setValue(self.config.get('processing', {}).get('max_aspect_ratio', 2.5))
        self.max_ratio_spin.setPrefix("Max: ")
        self.max_ratio_spin.setToolTip("Maximum allowed aspect ratio before padding is added.")
        self.max_ratio_spin.setFixedWidth(120)
        
        # Layout for normalization options
        norm_layout = QHBoxLayout()
        norm_layout.addWidget(self.normalize_check)
        norm_layout.addWidget(self.max_ratio_spin)
        norm_layout.addStretch()
        
        basic_layout.addLayout(norm_layout)

        self.duplicate_check = QCheckBox("Detect duplicates")
        self.duplicate_check.setChecked(self.config.get('duplicates', {}).get('enabled', True))
        self.duplicate_check.setToolTip("Check for previously processed stamps.")
        basic_layout.addWidget(self.duplicate_check)

        self.skip_processed_check = QCheckBox("Process New Only")
        self.skip_processed_check.setChecked(self.config.get('processing', {}).get('skip_processed', True))
        self.skip_processed_check.setToolTip("Skip images that already have a corresponding output file.")
        basic_layout.addWidget(self.skip_processed_check)

        basic_layout.addStretch()
        settings_tabs.addTab(basic_tab, "General")

        # Tab 2: Appearance & Margins
        appear_tab = QWidget()
        appear_layout = QVBoxLayout(appear_tab)

        # Expansion Margin
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Background Expansion:"))
        self.expand_spin = QDoubleSpinBox()
        self.expand_spin.setRange(0, 50)
        self.expand_spin.setSingleStep(1)
        self.expand_spin.setValue(self.config.get('processing', {}).get('expand_margin_percent', 0.05) * 100)
        self.expand_spin.setSuffix("%")
        self.expand_spin.setToolTip("How much original background to keep around the stamp.")
        margin_layout.addWidget(self.expand_spin)
        appear_layout.addLayout(margin_layout)

        # Texture Border
        border_layout = QHBoxLayout()
        border_layout.addWidget(QLabel("Green Texture Border:"))
        self.border_spin = QDoubleSpinBox()
        self.border_spin.setRange(0, 50)
        self.border_spin.setSingleStep(1)
        self.border_spin.setValue(self.config.get('processing', {}).get('texture_margin_percent', 0.10) * 100)
        self.border_spin.setSuffix("%")
        self.border_spin.setToolTip("Width of the textured border to add.")
        border_layout.addWidget(self.border_spin)
        appear_layout.addLayout(border_layout)

        # Colors Group
        color_group = QGroupBox("Colors")
        color_layout_main = QVBoxLayout(color_group)

        # Quick Colors
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Presets:"))
        
        for name, col in [("Green", [51, 112, 68]), ("Black", [0, 0, 0]), ("White", [255, 255, 255]), ("Gray", [128, 128, 128])]:
            btn = QPushButton(name)
            # col is BGR from config style, but we need RGB for QColor
            # If [51, 112, 68] is meant to be the green, and config says "color: [51, 112, 68]", 
            # and OpenCV reads it as BGR (Blue=51, Green=112, Red=68), then that matches a nice green.
            # So for QColor (RGB), we should flip strict BGR list if we assume config is BGR.
            # However, standard convention in this code seems to treat the list as [B, G, R].
            # So to get RGB: R=col[2], G=col[1], B=col[0].
            
            rgb_col = QColor(col[2], col[1], col[0])
            
            # Button styling
            if name == "White":
                btn.setStyleSheet(f"background-color: {rgb_col.name()}; color: black; border: 1px solid #ccc;")
            else:
                btn.setStyleSheet(f"background-color: {rgb_col.name()}; color: white;")
                
            # Create closure for the click handler
            # We must use default arg v=col to capture loop variable
            btn.clicked.connect(lambda checked, v=col: self._set_preset_color(
                QColor(v[2], v[1], v[0])
            ))
            quick_layout.addWidget(btn)
            
        color_layout_main.addLayout(quick_layout)
        
        color_layout_main.addSpacing(10)

        # Custom Border Color
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom Border:"))
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet("border: 1px solid #ccc;")
        current_color = self.config.get('background', {}).get('color', [51, 112, 68])
        self.current_bg_color = QColor(current_color[2], current_color[1], current_color[0])
        self._update_color_preview()
        custom_layout.addWidget(self.color_preview)

        self.color_btn = QPushButton("Pick Color...")
        self.color_btn.clicked.connect(self._pick_color)
        custom_layout.addWidget(self.color_btn)
        
        color_layout_main.addLayout(custom_layout)
        
        appear_layout.addWidget(color_group)

        # Show alignment line (debug feature - off by default)
        self.alignment_check = QCheckBox("Show alignment line")
        self.alignment_check.setChecked(self.config.get('processing', {}).get('show_alignment_line', False))
        appear_layout.addWidget(self.alignment_check)

        appear_layout.addStretch()
        settings_tabs.addTab(appear_tab, "Appearance")

        layout.addWidget(settings_tabs)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Ready to process")
        progress_layout.addWidget(self.progress_label)

        # Statistics
        # Statistics
        self.stats_label = QLabel("Processed: 0 | Success: 0 | Failed: 0 | Duplicates: 0")
        self.stats_label.setObjectName("stats_label")
        self.stats_label.setStyleSheet("font-size: 11px;")
        progress_layout.addWidget(self.stats_label)

        layout.addWidget(progress_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.process_btn = QPushButton("PROCESS BATCH")
        self.process_btn.setObjectName("process_btn")
        self.process_btn.setMinimumHeight(50)
        self.process_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_btn.clicked.connect(self._start_processing)
        self.process_btn.setEnabled(False)
        btn_layout.addWidget(self.process_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        # Open output folder button
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.clicked.connect(self._open_output_folder)
        layout.addWidget(self.open_output_btn)

        # Log output
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        # Log toolbar/actions
        log_tools = QHBoxLayout()
        
        self.open_log_btn = QPushButton("Open Log File")
        self.open_log_btn.clicked.connect(self._open_log_file)
        self.open_log_btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        log_tools.addWidget(self.open_log_btn)
        log_tools.addStretch()
        
        log_layout.addLayout(log_tools)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # Spacer
        layout.addStretch()

        return panel

    def _create_results_panel(self) -> QWidget:
        """Create the right results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Results"))

        # View options
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Grid View", "List View"])
        header_layout.addWidget(self.view_combo)

        header_layout.addStretch()

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_results)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Scrollable grid for thumbnails
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setSpacing(10)

        self.results_scroll.setWidget(self.results_container)
        layout.addWidget(self.results_scroll)

        return panel

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Folder...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._browse_folder)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        generate_texture = QAction("Generate Texture", self)
        generate_texture.triggered.connect(self._generate_texture)
        tools_menu.addAction(generate_texture)

        tools_menu.addSeparator()

        check_setup = QAction("Check Setup", self)
        check_setup.triggered.connect(self._check_setup)
        tools_menu.addAction(check_setup)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        # Theme Toggle in Menu bar (Right side)
        # We can't easily put a button on right side of QMenuBar in standard way, 
        # so adding a Toolbar action or just a menu item is easier.
        # Let's add a "View" menu for theme
        view_menu = menubar.addMenu("View")
        toggle_theme = QAction("Toggle Theme (Dark/Light)", self)
        toggle_theme.setShortcut("Ctrl+T")
        toggle_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme)

    def _apply_theme(self):
        """Apply dark theme styling."""
        theme = self.config.get('gui', {}).get('theme', 'dark')

        if theme == 'dark':
            # Get absolute path for resources
            check_path = str(get_resource_path("gui/resources/check_black.png")).replace('\\', '/')

            # Dracula Theme - Modern, High Contrast
            style = """
                QMainWindow, QWidget {
                    background-color: #282a36;
                    color: #f8f8f2;
                    font-family: "Segoe UI", "Roboto", sans-serif;
                    font-size: 14px;
                }
                QGroupBox {
                    border: 1px solid #6272a4;
                    border-radius: 8px;
                    margin-top: 24px;
                    padding-top: 16px;
                    font-weight: bold;
                    background-color: #2a2c3a;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 12px;
                    padding: 0 8px;
                    color: #50fa7b;
                    background-color: #282a36; /* Match window bg for clean cutout look */
                }
                QPushButton {
                    background-color: #44475a;
                    border: 1px solid #6272a4;
                    border-radius: 6px;
                    padding: 8px 16px;
                    color: #f8f8f2;
                    font-weight: bold;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #bd93f9;
                    color: #282a36;
                    border-color: #ff79c6;
                }
                QPushButton:pressed {
                    background-color: #ff79c6;
                    color: #282a36;
                }
                QPushButton:disabled {
                    background-color: #282a36;
                    border-color: #44475a;
                    color: #6272a4;
                }
                /* Primary Action Button Style */
                QPushButton[objectName="process_btn"] {
                    background-color: #50fa7b;
                    color: #282a36;
                    border: none;
                }
                QPushButton[objectName="process_btn"]:hover {
                    background-color: #69ff94;
                }
                
                QProgressBar {
                    border: 1px solid #6272a4;
                    border-radius: 6px;
                    text-align: center;
                    background-color: #21222c;
                    height: 24px;
                    color: #f8f8f2;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #bd93f9;
                    border-radius: 5px;
                }
                
                QTextEdit, QSpinBox, QComboBox, QLineEdit {
                    background-color: #21222c;
                    border: 1px solid #6272a4;
                    border-radius: 4px;
                    padding: 6px;
                    color: #f8f8f2;
                    selection-background-color: #bd93f9;
                    selection-color: #282a36;
                }
                QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
                    border: 1px solid #bd93f9;
                }
                
                QScrollArea {
                    border: none;
                    background-color: #282a36;
                }
                
                QCheckBox {
                    spacing: 12px;
                    color: #f8f8f2;
                    font-size: 14px;
                    padding: 4px;
                }
                QCheckBox::indicator {
                    width: 24px;
                    height: 24px;
                    border: 2px solid #6272a4;
                    border-radius: 6px;
                    background-color: #21222c;
                }
                QCheckBox::indicator:checked {
                    background-color: #50fa7b;
                    border-color: #50fa7b;
                    image: url("gui/resources/check_black.png"); /* Black check on green bg */
                }
                QCheckBox::indicator:hover {
                    border-color: #bd93f9;
                }
                
                QStatusBar {
                    background-color: #191a21;
                    color: #6272a4;
                    padding: 4px;
                }
                
                QSplitter::handle {
                    background-color: #44475a;
                    width: 2px;
                }
                
                QMenuBar {
                    background-color: #191a21;
                    border-bottom: 1px solid #44475a;
                    padding: 4px;
                }
                QMenuBar::item {
                    spacing: 8px;
                    padding: 6px 12px;
                    background: transparent;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #44475a;
                }
                QMenu {
                    background-color: #282a36;
                    border: 1px solid #6272a4;
                    border-radius: 4px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 8px 32px;
                }
                QMenu::item:selected {
                    background-color: #bd93f9;
                    color: #282a36;
                }
                
                /* Specific Widget Tweaks */
                QLabel {
                    color: #f8f8f2;
                    padding: 2px;
                }
                QLabel#stats_label {
                    color: #8be9fd; /* Cyan for stats */
                    font-weight: bold;
                    padding: 4px;
                }
            """
            self.setStyleSheet(style.replace('url("gui/resources/check_black.png")', f'url("{check_path}")'))

    def _toggle_theme(self):
        """Switch between dark and light themes."""
        if self.current_theme == 'dark':
            self.current_theme = 'light'
            self._apply_light_theme()
        else:
            self.current_theme = 'dark'
            self._apply_theme() # Default is dark
            
    def _apply_light_theme(self):
        """Apply light theme styling."""
        # Get absolute path for resources
        check_path = str(get_resource_path("gui/resources/check.png")).replace('\\', '/')
        style = """
            QMainWindow, QWidget {
                background-color: #f0f2f5;
                color: #1a1b1e;
                font-family: "Segoe UI", "Roboto", sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #ced4da;
                border-radius: 8px;
                margin-top: 24px;
                padding-top: 16px;
                font-weight: bold;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                color: #228be6;
                background-color: #f0f2f5; 
            }
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px 16px;
                color: #495057;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dee2e6;
                border-color: #adb5bd;
            }
            QPushButton[objectName="process_btn"] {
                background-color: #40c057; /* Green */
                color: #ffffff;
                border: none;
            }
            QPushButton[objectName="process_btn"]:hover {
                background-color: #51cf66;
            }
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 6px;
                text-align: center;
                background-color: #e9ecef;
                color: #1a1b1e;
            }
            QProgressBar::chunk {
                background-color: #228be6; /* Blue */
                border-radius: 5px;
            }
            QTextEdit, QSpinBox, QComboBox, QLineEdit, QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                color: #1a1b1e;
                selection-background-color: #228be6;
                selection-color: #ffffff;
            }
            QScrollArea {
                border: none;
                background-color: #f0f2f5;
            }
            QCheckBox {
                color: #1a1b1e;
                font-size: 14px;
                spacing: 12px;
                padding: 4px;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #228be6;
                border-color: #228be6;
                image: url("{check_path}"); /* White check on blue bg */
            }
            QStatusBar {
                background-color: #e9ecef;
                color: #495057;
                padding: 4px;
            }
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #ced4da;
                padding: 4px;
            }
            QMenuBar::item {
                spacing: 8px;
                padding: 6px 12px;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 32px;
            }
            QMenu::item:selected {
                background-color: #e9ecef;
                color: #1a1b1e;
            }
            QTabWidget::pane { border: 1px solid #ced4da; padding: 4px; }
            QLabel#stats_label {
                color: #1c7ed6;
                font-weight: bold;
            }
        """
        self.setStyleSheet(style.replace('{check_path}', check_path))

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Image Folder",
            str(get_project_root() / "raw_data")
        )

        if folder:
            self._set_input_folder(Path(folder))

    def _browse_file(self):
        """Open file browser dialog."""
        file_filter = "Images (*.jpg *.jpeg *.png *.heic *.bmp *.tiff *.webp);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image File",
            str(get_project_root() / "raw_data"),
            file_filter
        )

        if file_path:
            # Set input to the Parent Folder of the selected file
            self._set_input_folder(Path(file_path).parent)

    # _browse_folder replaced above to use shared helper
    
    def _start_processing(self):
        """Start the processing task."""
        if not hasattr(self, 'input_folder'):
            return

        # Update config with UI settings
        # Update config with UI settings
        self.config['detection']['confidence_threshold'] = self.confidence_spin.value() / 100
        self.config['processing']['rotation_correction'] = self.rotation_check.isChecked()
        self.config['processing']['normalize_aspect_ratio'] = self.normalize_check.isChecked()
        self.config['processing']['max_aspect_ratio'] = self.max_ratio_spin.value()
        self.config['processing']['show_alignment_line'] = self.alignment_check.isChecked()
        self.config['processing']['skip_processed'] = self.skip_processed_check.isChecked()
        self.config['duplicates']['enabled'] = self.duplicate_check.isChecked()
        
        # New Processing Params
        self.config['processing']['expand_margin_percent'] = self.expand_spin.value() / 100.0
        self.config['processing']['texture_margin_percent'] = self.border_spin.value() / 100.0
        
        # Update Color (Convert Qt RGB back to BGR for OpenCV)
        r, g, b, _ = self.current_bg_color.getRgb()
        self.config['background']['color'] = [b, g, r]

        # Create processor
        self.processor = StampProcessor(self.config)

        # Create worker thread
        self.worker = ProcessingWorker(self.processor, self.input_folder, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)

        # Update UI
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.results = []
        self._clear_results()

        self._log("Processing started...")
        self.worker.start()

    def _cancel_processing(self):
        """Cancel the current processing task."""
        if self.worker:
            self.worker.cancel()
            self._log("Cancelling...")

    def _on_progress(self, current: int, total: int, filename: str):
        """Handle progress update."""
        if total > 0:
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"Processing: {filename} ({current}/{total})")
            self.status_bar.showMessage(f"Processing {current} of {total}")
        else:
             self.progress_bar.setValue(0)
             self.progress_label.setText(f"Preparing: {filename}...")
             self.status_bar.showMessage(f"Preparing: {filename}...")

    def _on_result(self, result: ProcessingResult):
        """Handle single result."""
        # Handle skipped
        if result.skipped:
            self._log(f"  > Skipped (already exists): {result.input_path.name}")
            # Do not add to results list or grid to keep UI clean?
            # Or add to list so stats count it?
            # User wants to run on "new photos only", so counting skipped as "Processed" might be confusing vs "ignored".
            # Let's count them in stats but not show thumbnail
            self.results.append(result)
            
            # Update stats immediately
            success = sum(1 for r in self.results if r.success and not r.skipped)
            failed = len(self.results) - success - sum(1 for r in self.results if r.skipped)
            duplicates = sum(1 for r in self.results if r.is_duplicate)
            skipped = sum(1 for r in self.results if r.skipped)

            self.stats_label.setText(
                f"Processed: {len(self.results)} | Success: {success} | "
                f"Skipped: {skipped} | Duplicates: {duplicates}"
            )
            return

        self.results.append(result)

        # Add thumbnail to grid
        row = (len(self.results) - 1) // 5
        col = (len(self.results) - 1) % 5

        thumbnail = ThumbnailWidget(result)
        self.results_layout.addWidget(thumbnail, row, col)

        # Update stats
        success = sum(1 for r in self.results if r.success)
        failed = len(self.results) - success
        duplicates = sum(1 for r in self.results if r.is_duplicate)

        self.stats_label.setText(
            f"Processed: {len(self.results)} | Success: {success} | "
            f"Failed: {failed} | Duplicates: {duplicates}"
        )

        # Log
        if result.success:
            self._log(f"  + {result.input_path.name} (conf: {result.confidence:.0%})")
        else:
            self._log(f"  - {result.input_path.name}: {result.error_message}")

    def _on_finished(self, results: List[ProcessingResult]):
        """Handle processing completion."""
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Processing complete!")

        success = sum(1 for r in results if r.success)
        self._log(f"\nCompleted: {success}/{len(results)} successful")
        self.status_bar.showMessage(f"Done - {success}/{len(results)} successful")

        # Show completion message
        QMessageBox.information(
            self, "Processing Complete",
            f"Processed {len(results)} images.\n"
            f"Successful: {success}\n"
            f"Failed: {len(results) - success}"
        )

    def _on_error(self, error: str):
        """Handle processing error."""
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)

        self._log(f"ERROR: {error}")
        QMessageBox.critical(self, "Error", f"Processing failed:\n{error}")

    def _clear_results(self):
        """Clear all result thumbnails."""
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        if hasattr(self, 'input_folder'):
            # Dynamic path: InputDir/crops
            output_path = self.input_folder / 'crops'
        else:
            # Fallback
            output_path = get_project_root() / self.config.get('paths', {}).get('crops', 'output/crops')
            
        if output_path.exists():
            os.startfile(str(output_path))
        else:
            QMessageBox.warning(self, "Warning", f"Output folder does not exist yet:\n{output_path}")

    def _generate_texture(self):
        """Generate background texture."""
        from create_texture import create_texture

        output_path = get_project_root() / "assets" / "green_texture.jpg"
        create_texture(output_path=str(output_path))
        self._log(f"Texture generated: {output_path}")
        QMessageBox.information(self, "Success", f"Texture generated:\n{output_path}")

    def _check_setup(self):
        """Run setup check."""
        import subprocess
        script_path = get_project_root() / "scripts" / "test_setup.py"
        subprocess.Popen(['python', str(script_path)], creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Stamp Philatex Processor",
            "Stamp Philatex Processor v1.0\n\n"
            "AI-powered stamp detection, alignment, and cropping.\n\n"
            "Features:\n"
            "- YOLOv8 segmentation for precise detection\n"
            "- Auto-deskew for perfect alignment\n"
            "- Duplicate detection\n"
            "- AMD GPU acceleration support\n\n"
            "Built with PyQt6 + Ultralytics"
        )

    def _log(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _pick_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(self.current_bg_color, self, "Select Border Color")
        if color.isValid():
            self.current_bg_color = color
            self._update_color_preview()

    def _update_color_preview(self):
        """Update the small color preview box."""
        self.color_preview.setStyleSheet(
            f"background-color: {self.current_bg_color.name()}; border: 1px solid #6272a4; border-radius: 4px;"
        )

    def _set_preset_color(self, color: QColor):
        """Set background color from preset."""
        self.current_bg_color = color
        self._update_color_preview()

    def _open_log_file(self):
        """Open the current log file."""
        log_path = get_project_root() / self.config.get('logging', {}).get('log_file', 'output/processing.log')
        if log_path.exists():
            os.startfile(str(log_path))
        else:
            QMessageBox.information(self, "Log File", "Log file does not exist yet.")


def main():
    """Launch the GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Stamp Philatex Processor")

    window = StampDetectionGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
