import sys
import json
import urllib.request
import random # Added for random welcome messages
from pathlib import Path
from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QTextEdit, QLineEdit, QLabel,
    QGroupBox, QStatusBar, QMessageBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QPalette, QIcon, QShortcut, QKeySequence

# Constants
BIBLE_FILEPATH = 'kjv.json'

class DataLoader(QThread):
    """Background thread for loading Bible data."""
    data_loaded = Signal(dict)
    status_update = Signal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        """Load Bible data in background."""
        data = self.load_data()
        self.data_loaded.emit(data)

    def load_data(self) -> Dict[str, Any]:
        """Loads the Bible data from the JSON file or downloads it."""
        try:
            with open(BIBLE_FILEPATH, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if self.validate_data(data):
                self.status_update.emit("Bible data loaded successfully")
                return data
            else:
                return self.download_bible_data()

        except FileNotFoundError:
            return self.download_bible_data()
        except json.JSONDecodeError:
            self.status_update.emit("Error: Corrupted JSON file")
            return {}

    def validate_data(self, data: Dict) -> bool:
        """Validates the Bible data structure."""
        if not isinstance(data, dict) or len(data) == 0:
            return False

        first_book = next(iter(data.values()))
        if not isinstance(first_book, dict):
            return False

        first_chapter = next(iter(first_book.values()))
        return isinstance(first_chapter, dict)

    def download_bible_data(self) -> Dict[str, Any]:
        """Downloads KJV Bible data from online source."""
        try:
            self.status_update.emit("Downloading Bible data...")

            url = "https://github.com/thiagobodruk/bible/raw/master/json/kjv.json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

            with urllib.request.urlopen(req, timeout=30) as response:
                raw_data = json.load(response)

            self.status_update.emit("Converting data format...")
            converted = {}
            for book_obj in raw_data:
                book_name = book_obj["book"]
                chapters = book_obj["chapters"]
                converted[book_name] = chapters

            self.status_update.emit("Saving data locally...")
            with open(BIBLE_FILEPATH, "w", encoding="utf-8") as f:
                json.dump(converted, f, ensure_ascii=False, indent=2)

            self.status_update.emit("Bible data loaded successfully")
            return converted
        except Exception as e:
            self.status_update.emit(f"Download failed: {str(e)}")
            return {}


class BibleReaderApp(QMainWindow):
    """Modern Bible Reader with PySide6."""

    # List of encouraging messages for the welcome page
    WELCOME_MESSAGES = [
        "Today is a great day to open your heart to a new verse. Every word matters! 🙏",
        "The journey of faith is read, one chapter at a time. Keep going! 💡",
        "Let the ancient wisdom illuminate your modern path. You've got this! ✨",
        "Don't rush the stillness. Find comfort and challenge in today's reading. 📖",
        "Persistence in reading brings profound peace. Your time in the Word is an investment. 🕊️",
        "Welcome back! Remember, the Bible is not just a book, it's a living guide for life. 🧭",
        "Just one verse can change your perspective for the whole day. Read with intention. 💖",
        "Keep digging! There are treasures waiting for you in every chapter. 👑"
    ]

    def __init__(self):
        super().__init__()

        # Canonical book order
        self.canonical_books = [
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
            "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
            "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
            "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
            "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
            "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
            "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
            "Zephaniah", "Haggai", "Zechariah", "Malachi",
            "Matthew", "Mark", "Luke", "John", "Acts",
            "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
            "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
            "James", "1 Peter", "2 Peter", "1 John", "2 John",
            "3 John", "Jude", "Revelation"
        ]

        self.bible_data: Dict[str, Any] = {}
        self.search_results: List[Dict[str, str]] = []
        self.current_result_index = 0

        self.init_ui()
        self.apply_styles()
        self.load_data_async()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("📖 KJV Bible Reader")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        self.create_header(main_layout)

        # Control panel
        self.create_control_panel(main_layout)

        # Content area
        self.create_content_area(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Loading Bible data...")

        # Keyboard shortcuts
        self.setup_shortcuts()

    def create_header(self, layout):
        """Create the header section."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("📖 Holy Bible - King James Version")
        title.setObjectName("title")
        title_font = QFont("Segoe UI", 24, QFont.Bold)
        title.setFont(title_font)

        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

    def create_control_panel(self, layout):
        """Create the control panel with navigation and search."""
        control_group = QGroupBox("Navigation & Search")
        control_group.setObjectName("controlGroup")
        control_layout = QVBoxLayout()
        control_layout.setSpacing(15)

        # Navigation row
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)

        # Book selector
        book_label = QLabel("Book:")
        book_label.setFixedWidth(50)
        self.book_combo = QComboBox()
        self.book_combo.setMinimumWidth(200)
        self.book_combo.currentTextChanged.connect(self.on_book_changed)

        # Chapter selector
        chapter_label = QLabel("Chapter:")
        chapter_label.setFixedWidth(60)
        self.chapter_combo = QComboBox()
        self.chapter_combo.setFixedWidth(80)
        self.chapter_combo.currentTextChanged.connect(self.on_chapter_changed)

        # Navigation buttons
        self.prev_btn = QPushButton("◄ Previous")
        self.prev_btn.setObjectName("navButton")
        self.prev_btn.clicked.connect(self.previous_chapter)
        self.prev_btn.setFixedWidth(100)

        self.read_btn = QPushButton("Read Chapter")
        self.read_btn.setObjectName("primaryButton")
        self.read_btn.clicked.connect(self.read_chapter)
        self.read_btn.setFixedWidth(120)

        self.next_btn = QPushButton("Next ►")
        self.next_btn.setObjectName("navButton")
        self.next_btn.clicked.connect(self.next_chapter)
        self.next_btn.setFixedWidth(100)

        nav_layout.addWidget(book_label)
        nav_layout.addWidget(self.book_combo)
        nav_layout.addWidget(chapter_label)
        nav_layout.addWidget(self.chapter_combo)
        nav_layout.addSpacing(20)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.read_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()

        # Search row
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        search_label = QLabel("Search:")
        search_label.setFixedWidth(50)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter keywords to search the entire Bible...")
        self.search_input.returnPressed.connect(self.search_bible)

        self.search_btn = QPushButton("🔍 Search Bible")
        self.search_btn.setObjectName("searchButton")
        self.search_btn.clicked.connect(self.search_bible)
        self.search_btn.setFixedWidth(140)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.setFixedWidth(80)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.clear_btn)

        control_layout.addLayout(nav_layout)
        control_layout.addLayout(search_layout)
        control_group.setLayout(control_layout)

        layout.addWidget(control_group)

    def create_content_area(self, layout):
        """Create the main content area."""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 10, 20, 20)

        # Title bar with search navigation
        title_layout = QHBoxLayout()

        self.content_title = QLabel("Welcome")
        self.content_title.setObjectName("contentTitle")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        self.content_title.setFont(title_font)

        # Search result navigation
        self.search_nav_widget = QWidget()
        search_nav_layout = QHBoxLayout(self.search_nav_widget)
        search_nav_layout.setContentsMargins(0, 0, 0, 0)
        search_nav_layout.setSpacing(5)

        self.prev_result_btn = QPushButton("◄")
        self.prev_result_btn.setFixedSize(30, 30)
        self.prev_result_btn.clicked.connect(self.previous_result)

        self.result_label = QLabel("0/0")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFixedWidth(60)

        self.next_result_btn = QPushButton("►")
        self.next_result_btn.setFixedSize(30, 30)
        self.next_result_btn.clicked.connect(self.next_result)

        search_nav_layout.addWidget(self.prev_result_btn)
        search_nav_layout.addWidget(self.result_label)
        search_nav_layout.addWidget(self.next_result_btn)

        self.search_nav_widget.hide()

        title_layout.addWidget(self.content_title)
        title_layout.addStretch()
        title_layout.addWidget(self.search_nav_widget)

        content_layout.addLayout(title_layout)

        # Text display
        self.text_display = QTextEdit()
        self.text_display.setObjectName("textDisplay")
        self.text_display.setReadOnly(True)
        display_font = QFont("Georgia", 13)
        self.text_display.setFont(display_font)
        self.text_display.setPlainText("Loading Bible data, please wait...")

        content_layout.addWidget(self.text_display)

        layout.addWidget(content_widget)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        QShortcut(QKeySequence("Left"), self).activated.connect(self.previous_chapter)
        QShortcut(QKeySequence("Right"), self).activated.connect(self.next_chapter)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.search_input.setFocus())
        QShortcut(QKeySequence("Return"), self.search_input).activated.connect(self.search_bible)

    def apply_styles(self):
        """Apply custom stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }

            #header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3a8a, stop:1 #3b82f6);
                border-bottom: 3px solid #1e40af;
            }

            #title {
                color: white;
                padding: 10px;
            }

            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #1e40af;
            }

            #controlGroup {
                margin: 20px;
            }

            QLabel {
                color: #374151;
                font-size: 12px;
                font-weight: 600;
            }

            #contentTitle {
                color: #1e40af;
                font-size: 18px;
                font-weight: bold;
            }

            QComboBox {
                border: 2px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: white;
                font-size: 12px;
                min-height: 20px;
            }

            QComboBox:hover {
                border: 2px solid #3b82f6;
            }

            QComboBox:focus {
                border: 2px solid #1e40af;
            }

            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #6b7280;
                margin-right: 5px;
            }

            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 15px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
            }

            QLineEdit:hover {
                border: 2px solid #3b82f6;
            }

            QLineEdit:focus {
                border: 2px solid #1e40af;
                background-color: #f0f9ff;
            }

            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                min-height: 20px;
            }

            #primaryButton {
                background-color: #1e40af;
                color: white;
            }

            #primaryButton:hover {
                background-color: #1e3a8a;
            }

            #primaryButton:pressed {
                background-color: #1e3a8a;
            }

            #searchButton {
                background-color: #f59e0b;
                color: white;
            }

            #searchButton:hover {
                background-color: #d97706;
            }

            #searchButton:pressed {
                background-color: #b45309;
            }

            #navButton {
                background-color: #6b7280;
                color: white;
            }

            #navButton:hover {
                background-color: #4b5563;
            }

            #navButton:pressed {
                background-color: #374151;
            }

            #clearButton {
                background-color: #e5e7eb;
                color: #374151;
            }

            #clearButton:hover {
                background-color: #d1d5db;
            }

            #clearButton:pressed {
                background-color: #9ca3af;
            }

            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }

            #textDisplay {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                background-color: #fafafa;
                padding: 20px;
                line-height: 1.8;
            }

            QTextEdit {
                selection-background-color: #bfdbfe;
            }

            QStatusBar {
                background-color: #f3f4f6;
                color: #6b7280;
                border-top: 1px solid #d1d5db;
                font-size: 11px;
                padding: 5px;
            }

            QScrollBar:vertical {
                border: none;
                background: #f3f4f6;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def load_data_async(self):
        """Load Bible data in background thread."""
        self.loader = DataLoader()
        self.loader.data_loaded.connect(self.on_data_loaded)
        self.loader.status_update.connect(self.status_bar.showMessage)
        self.loader.start()

    def on_data_loaded(self, data: Dict[str, Any]):
        """Handle loaded Bible data."""
        self.bible_data = data

        if self.bible_data:
            # Get books in canonical order
            self.book_names = [book for book in self.canonical_books if book in self.bible_data]
            self.book_combo.addItems(self.book_names)

            if self.book_names:
                self.book_combo.setCurrentText(self.book_names[0])
                self.update_chapters()
                self.display_welcome()
                self.status_bar.showMessage("Ready - Select a book and chapter to read")
        else:
            self.content_title.setText("Error")
            self.text_display.setPlainText("Failed to load Bible data. Please check your internet connection.")
            self.status_bar.showMessage("Failed to load Bible data")
            QMessageBox.critical(self, "Error", "Could not load Bible data.\nPlease check your internet connection.")

    def display_welcome(self):
        """Display welcome message with a random encouraging quote."""
        self.content_title.setText("Welcome to KJV Bible Reader")

        # Select a random encouraging message
        encouraging_message = random.choice(self.WELCOME_MESSAGES)

        # The standard instruction text, using HTML for better formatting
        instruction_text = """
<div style="font-family: Georgia; font-size: 14px; line-height: 2.0; color: #1f2937; margin-top: 20px;">
    <h3 style="color: #1e40af; border-bottom: 1px solid #d1d5db; padding-bottom: 5px;">📖 Getting Started</h3>
    <ul style="list-style-type: none; padding-left: 0;">
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> Select a Book and Chapter from the dropdowns above.</li>
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> Click 'Read Chapter' or the chapter will load automatically.</li>
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> Use <b>◄ Previous</b> and <b>Next ►</b> buttons to navigate between chapters.</li>
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> Use the <b>Search</b> box to find verses containing specific words.</li>
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> Press <b>Ctrl+F</b> to quickly jump to search.</li>
    </ul>

    <h3 style="color: #1e40af; border-bottom: 1px solid #d1d5db; padding-bottom: 5px;">⌨️ Keyboard Shortcuts</h3>
    <ul style="list-style-type: none; padding-left: 0;">
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> <b>Left Arrow:</b> Previous Chapter</li>
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> <b>Right Arrow:</b> Next Chapter</li>
        <li><span style="color: #3b82f6; margin-right: 8px;">•</span> <b>Enter (in search):</b> Search Bible</li>
    </ul>
</div>
        """

        # Combine the encouragement and instructions in a nicely formatted HTML block
        html_content = f"""
<div style="font-family: 'Segoe UI', sans-serif; padding: 15px; background-color: #e0f2fe; border-radius: 8px; border: 1px solid #90cdf4; margin-bottom: 25px;">
    <p style="font-size: 16px; color: #1e40af; font-weight: bold; margin: 0;">
        {encouraging_message}
    </p>
</div>
{instruction_text}
<div style="font-family: Georgia; font-size: 14px; line-height: 1.5; color: #6b7280; margin-top: 25px; padding-top: 10px; border-top: 1px dashed #d1d5db;">
    The King James Version of the Bible is loaded and ready to read.
</div>
        """

        self.text_display.setHtml(html_content)


    def on_book_changed(self):
        """Handle book selection change."""
        self.update_chapters()
        if self.bible_data:
            self.read_chapter()

    def update_chapters(self):
        """Update chapter dropdown based on selected book."""
        book = self.book_combo.currentText()
        self.chapter_combo.clear()

        if book and book in self.bible_data:
            chapters = sorted([int(c) for c in self.bible_data[book].keys()])
            chapter_strs = [str(c) for c in chapters]
            self.chapter_combo.addItems(chapter_strs)

            if chapter_strs:
                self.chapter_combo.setCurrentText(chapter_strs[0])

    def on_chapter_changed(self):
        """Handle chapter selection change."""
        if self.bible_data and self.book_combo.currentText():
            self.read_chapter()

    def read_chapter(self):
        """Display the selected chapter. FIX: Verses are read in numerical order."""
        book = self.book_combo.currentText()
        chapter = self.chapter_combo.currentText()

        if not book or not chapter or not self.bible_data:
            return

        try:
            chapter_data = self.bible_data[book][chapter]
            # FIX: Get and sort verse numbers numerically
            verse_numbers = sorted([int(v) for v in chapter_data.keys()])

            # Build HTML content
            html = f"""
            <div style="font-family: Georgia; font-size: 14px; line-height: 2.0; color: #1f2937;">
                <h2 style="color: #1e40af; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                    {book} - Chapter {chapter}
                </h2>
                <div style="margin-top: 20px;">
            """

            for verse_num_int in verse_numbers:
                verse_num = str(verse_num_int)
                text = chapter_data[verse_num]

                html += f"""
                <p style="margin: 15px 0;">
                    <span style="color: #3b82f6; font-weight: bold; font-size: 11px; margin-right: 8px;">
                        {verse_num}
                    </span>
                    <span>{text}</span>
                </p>
                """

            html += "</div></div>"

            self.text_display.setHtml(html)
            self.content_title.setText(f"{book} - Chapter {chapter}")
            self.status_bar.showMessage(f"{book} {chapter} (KJV) — {len(chapter_data)} verses")
            self.search_nav_widget.hide()

        except KeyError:
            self.content_title.setText("Error")
            self.text_display.setPlainText(f"Chapter {book} {chapter} not found.")
            self.status_bar.showMessage("Chapter not available")

    def previous_chapter(self):
        """Navigate to previous chapter."""
        book = self.book_combo.currentText()
        chapter = self.chapter_combo.currentText()

        if not book or not chapter:
            return

        chapters = [self.chapter_combo.itemText(i) for i in range(self.chapter_combo.count())]
        current_idx = chapters.index(chapter)

        if current_idx > 0:
            self.chapter_combo.setCurrentText(chapters[current_idx - 1])
        else:
            # Go to previous book
            book_idx = self.book_names.index(book)
            if book_idx > 0:
                self.book_combo.setCurrentText(self.book_names[book_idx - 1])
                self.update_chapters()
                # Set to last chapter
                last_chapter = self.chapter_combo.itemText(self.chapter_combo.count() - 1)
                self.chapter_combo.setCurrentText(last_chapter)

    def next_chapter(self):
        """Navigate to next chapter."""
        book = self.book_combo.currentText()
        chapter = self.chapter_combo.currentText()

        if not book or not chapter:
            return

        chapters = [self.chapter_combo.itemText(i) for i in range(self.chapter_combo.count())]
        current_idx = chapters.index(chapter)

        if current_idx < len(chapters) - 1:
            self.chapter_combo.setCurrentText(chapters[current_idx + 1])
        else:
            # Go to next book
            book_idx = self.book_names.index(book)
            if book_idx < len(self.book_names) - 1:
                self.book_combo.setCurrentText(self.book_names[book_idx + 1])
                self.update_chapters()
                # Set to first chapter
                self.chapter_combo.setCurrentText(self.chapter_combo.itemText(0))

    def search_bible(self):
        """Search the entire Bible."""
        search_term = self.search_input.text().strip()

        if not search_term:
            QMessageBox.warning(self, "Search", "Please enter a search term.")
            return

        if not self.bible_data:
            return

        self.status_bar.showMessage("Searching Bible...")
        self.content_title.setText(f"Searching for: '{search_term}'...")
        self.text_display.setPlainText("Processing search, please wait...")

        QApplication.processEvents()

        normalized_term = search_term.lower()
        self.search_results = []

        # Search through all verses
        for book_name in self.book_names:
            book_data = self.bible_data[book_name]
            # Ensure chapters are processed in order for better search result grouping
            chapter_numbers = sorted([int(c) for c in book_data.keys()])
            for chapter_num_int in chapter_numbers:
                chapter_num = str(chapter_num_int)
                chapter_data = book_data[chapter_num]
                # Ensure verses are processed in order
                verse_numbers = sorted([int(v) for v in chapter_data.keys()])
                for verse_num_int in verse_numbers:
                    verse_num = str(verse_num_int)
                    verse_text = chapter_data[verse_num]
                    if normalized_term in verse_text.lower():
                        reference = f"{book_name} {chapter_num}:{verse_num}"
                        self.search_results.append({
                            'reference': reference,
                            'book': book_name,
                            'chapter': chapter_num,
                            'verse': verse_num,
                            'text': verse_text
                        })

        self.current_result_index = 0

        if self.search_results:
            self.display_search_results()
            self.search_nav_widget.show()
            self.status_bar.showMessage(f"Found {len(self.search_results)} verses containing '{search_term}'")
        else:
            self.content_title.setText("No Results")
            self.text_display.setPlainText(f"No verses found containing '{search_term}'.\n\nTry different keywords or check spelling.")
            self.status_bar.showMessage("No results found")
            self.search_nav_widget.hide()

    def display_search_results(self):
        """Display search results with highlighting."""
        if not self.search_results:
            return

        search_term = self.search_input.text().strip().lower()

        html = f"""
        <div style="font-family: Georgia; font-size: 13px; line-height: 1.9; color: #1f2937;">
            <h2 style="color: #1e40af; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                Search Results: '{self.search_input.text()}' ({len(self.search_results)} found)
            </h2>
            <div style="margin-top: 20px;">
        """

        for i, result in enumerate(self.search_results, 1):
            # Highlight search term
            text = result['text']
            text_lower = text.lower()
            highlighted_text = ""
            last_pos = 0

            pos = text_lower.find(search_term)
            while pos != -1:
                highlighted_text += text[last_pos:pos]
                highlighted_text += f'<span style="background-color: #fef3c7; padding: 2px 4px; border-radius: 3px; font-weight: 600;">{text[pos:pos+len(search_term)]}</span>'
                last_pos = pos + len(search_term)
                pos = text_lower.find(search_term, last_pos)

            highlighted_text += text[last_pos:]

            html += f"""
            <div style="margin-bottom: 25px; padding: 15px; background-color: white; border-left: 4px solid #3b82f6; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="color: #059669; font-weight: bold; font-size: 13px; margin-bottom: 8px;">
                    {i}. {result['reference']}
                </div>
                <div style="color: #374151; font-size: 14px;">
                    {highlighted_text}
                </div>
            </div>
            """

        html += "</div></div>"

        self.text_display.setHtml(html)
        self.content_title.setText(f"Search Results: '{self.search_input.text()}' ({len(self.search_results)} found)")
        self.update_result_navigation()

    def update_result_navigation(self):
        """Update search result navigation."""
        if self.search_results:
            self.result_label.setText(f"{self.current_result_index + 1}/{len(self.search_results)}")
            self.prev_result_btn.setEnabled(self.current_result_index > 0)
            self.next_result_btn.setEnabled(self.current_result_index < len(self.search_results) - 1)

    def previous_result(self):
        """Navigate to previous search result."""
        if self.current_result_index > 0:
            self.current_result_index -= 1
            self.jump_to_current_result()

    def next_result(self):
        """Navigate to next search result."""
        if self.current_result_index < len(self.search_results) - 1:
            self.current_result_index += 1
            self.jump_to_current_result()

    def jump_to_current_result(self):
        """Jump to the current search result."""
        if not self.search_results:
            return

        result = self.search_results[self.current_result_index]

        # Update navigation
        self.update_result_navigation()

        # Navigate to the book and chapter
        self.book_combo.blockSignals(True)
        self.chapter_combo.blockSignals(True)

        self.book_combo.setCurrentText(result['book'])
        self.update_chapters()
        self.chapter_combo.setCurrentText(result['chapter'])

        self.book_combo.blockSignals(False)
        self.chapter_combo.blockSignals(False)

        # Display the chapter with highlighting
        self.display_chapter_with_highlight(result['book'], result['chapter'], result['verse'])

    def display_chapter_with_highlight(self, book: str, chapter: str, highlight_verse: str):
        """Display a chapter with a specific verse highlighted. FIX: Verses are read in numerical order."""
        try:
            chapter_data = self.bible_data[book][chapter]
            search_term = self.search_input.text().strip().lower()
            # FIX: Get and sort verse numbers numerically
            verse_numbers = sorted([int(v) for v in chapter_data.keys()])

            html = f"""
            <div style="font-family: Georgia; font-size: 14px; line-height: 2.0; color: #1f2937;">
                <h2 style="color: #1e40af; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">
                    {book} - Chapter {chapter}
                </h2>
                <div style="margin-top: 20px;">
            """

            for verse_num_int in verse_numbers:
                verse_num = str(verse_num_int)
                text = chapter_data[verse_num]

                # Highlight the matching verse
                is_highlight = (verse_num == highlight_verse)

                # Add highlighting for search term
                display_text = text
                if search_term and search_term in text.lower():
                    text_lower = text.lower()
                    highlighted_text = ""
                    last_pos = 0

                    pos = text_lower.find(search_term)
                    while pos != -1:
                        highlighted_text += text[last_pos:pos]
                        highlighted_text += f'<span style="background-color: #fef3c7; padding: 2px 4px; border-radius: 3px; font-weight: 600;">{text[pos:pos+len(search_term)]}</span>'
                        last_pos = pos + len(search_term)
                        pos = text_lower.find(search_term, last_pos)

                    highlighted_text += text[last_pos:]
                    display_text = highlighted_text

                # Style for highlighted verse
                verse_style = ""
                if is_highlight:
                    verse_style = 'background-color: #dbeafe; padding: 10px; border-radius: 6px; border-left: 4px solid #3b82f6;'

                html += f"""
                <p style="margin: 15px 0; {verse_style}">
                    <span style="color: #3b82f6; font-weight: bold; font-size: 11px; margin-right: 8px;">
                        {verse_num}
                    </span>
                    <span>{display_text}</span>
                </p>
                """

            html += "</div></div>"

            self.text_display.setHtml(html)
            self.content_title.setText(f"{book} - Chapter {chapter}")
            self.status_bar.showMessage(f"Result {self.current_result_index + 1}/{len(self.search_results)}: {book} {chapter}:{highlight_verse}")

            # Scroll to highlighted verse
            cursor = self.text_display.textCursor()
            cursor.movePosition(cursor.Start)
            self.text_display.setTextCursor(cursor)

        except KeyError:
            self.content_title.setText("Error")
            self.text_display.setPlainText(f"Chapter {book} {chapter} not found.")

    def clear_search(self):
        """Clear search results and input."""
        self.search_input.clear()
        self.search_results = []
        self.current_result_index = 0
        self.search_nav_widget.hide()
        self.display_welcome()
        self.status_bar.showMessage("Search cleared")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("KJV Bible Reader")

    window = BibleReaderApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# def app():
#     return None