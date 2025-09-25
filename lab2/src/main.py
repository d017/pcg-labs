import sys
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QTableWidget, QTableWidgetItem, QPushButton,
                             QFileDialog, QLabel, QProgressBar, QLineEdit,
                             QHeaderView, QMessageBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QFont, QPalette, QColor
import PIL.Image
from PIL.ExifTags import TAGS


class AsyncImageAnalyzer(QObject):
    progress_updated = pyqtSignal(int, int, str)
    analysis_finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=4)

    def stop_analysis(self):
        self.is_running = False

    async def analyze_images_async(self, folder_path, show_advanced=False):

        if not os.path.exists(folder_path):
            self.error_occurred.emit("Папка не існуе")
            return

        supported_formats = {'.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx'}
        image_files = []


        loop = asyncio.get_event_loop()

        def collect_files():
            files = []
            for root, dirs, walk_files in os.walk(folder_path):
                if not self.is_running:
                    break
                for file in walk_files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_formats:
                        files.append(os.path.join(root, file))
            return files

        image_files = await loop.run_in_executor(self.executor, collect_files)

        if not self.is_running:
            return

        total_files = len(image_files)
        self.progress_updated.emit(0, 0, "Пачатак аналізу...")

        results = []


        for i, file_path in enumerate(image_files):
            if not self.is_running:
                break

            try:

                result = await self.analyze_single_image(file_path, show_advanced)
                results.append(result)

                progress = int((i + 1) / total_files * 100) if total_files > 0 else 0
                self.progress_updated.emit(progress, i + 1, os.path.basename(file_path))


                await asyncio.sleep(0.001)

            except Exception as e:
                error_result = {
                    'filename': os.path.basename(file_path),
                    'size': 'Памылка',
                    'dpi': 'Памылка',
                    'color_depth': 'Памылка',
                    'compression': 'Памылка',
                    'format': 'Памылка',
                    'advanced': f'Памылка: {str(e)}',
                    'file_path': file_path
                }
                results.append(error_result)

        if self.is_running:
            self.analysis_finished.emit(results)

    async def analyze_single_image(self, file_path, show_advanced):

        loop = asyncio.get_event_loop()

        def analyze():
            try:
                with PIL.Image.open(file_path) as img:
                    filename = os.path.basename(file_path)
                    size = f"{img.width} × {img.height}"
                    format_type = img.format

                    dpi = img.info.get('dpi', (0, 0))
                    dpi_str = f"{dpi[0]} × {dpi[1]}" if dpi != (0, 0) else "-"

                    color_depth = self.get_color_depth(img)
                    compression = self.get_compression_info(img)
                    advanced_info = self.get_color_system_info(img) if show_advanced else ""

                    return {
                        'filename': filename,
                        'size': size,
                        'dpi': dpi_str,
                        'color_depth': color_depth,
                        'compression': compression,
                        'format': format_type,
                        'advanced': advanced_info,
                        'file_path': file_path
                    }
            except Exception as e:
                raise e

        return await loop.run_in_executor(self.executor, analyze)

    def get_color_depth(self, img):

        if img.mode in ['1']:
            return "1 біт (ч/б)"
        elif img.mode in ['L']:
            return "8 біт (адценні шэрага)"
        elif img.mode in ['P']:
            return "8 біт (палітра)"
        elif img.mode in ['RGB']:
            return "24 біты (True Color)"
        elif img.mode in ['RGBA']:
            return "32 біты (True Color + Alpha)"
        elif img.mode in ['CMYK']:
            return "32 біты (CMYK)"
        else:
            return f"{img.mode} (спецыяльны)"

    def get_compression_info(self, img):

        compression = img.info.get('compression', '-')

        if compression == 'jpeg':
            quality = img.info.get('quality', 'Не пазначана')
            return f"JPEG (якасць: {quality})" if quality != '-' else "JPEG"
        elif compression == 'tiff_lzw':
            return "LZW (TIFF)"
        elif compression == 'tiff_ccitt':
            return "CCITT (TIFF)"
        elif compression == 'zip':
            return "ZIP (PNG)"
        elif compression == 'packbits':
            return "PackBits (TIFF)"
        else:
            return str(compression)

    def get_color_system_info(self, img):
        try:
            if img.mode == 'RGB':
                color_info = "RGB"
            elif img.mode == 'RGBA':
                color_info = "RGBA"
            elif img.mode == 'CMYK':
                color_info = "CMYK"
            elif img.mode == 'L':
                color_info = "L (Адценні шэрага)"
            elif img.mode == 'P':
                color_info = "P (Палітра)"
            elif img.mode == '1':
                color_info = "1 (Чорна-белы)"
            else:
                color_info = f"{img.mode}"

            if hasattr(img, 'info') and 'icc_profile' in img.info:
                color_info += " ICC профіль"

            return color_info
        except Exception as e:
            return f"Памылка: {str(e)}"


class ImageAnalysisThread(QThread):
    progress_updated = pyqtSignal(int, int, str)
    analysis_finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, folder_path, show_advanced=False):
        super().__init__()
        self.folder_path = folder_path
        self.show_advanced = show_advanced
        self.is_running = True
        self.analyzer = AsyncImageAnalyzer()

    def stop_analysis(self):
        self.is_running = False
        self.analyzer.stop_analysis()

    def run(self):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            self.analyzer.is_running = True
            self.analyzer.progress_updated.connect(self.progress_updated.emit)
            self.analyzer.analysis_finished.connect(self.analysis_finished.emit)
            self.analyzer.error_occurred.connect(self.error_occurred.emit)


            loop.run_until_complete(
                self.analyzer.analyze_images_async(self.folder_path, self.show_advanced)
            )
        except Exception as e:
            self.error_occurred.emit(f"Памылка аналізу: {str(e)}")
        finally:
            loop.close()
            self.analyzer.is_running = False


class ImageAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()
        self.analysis_thread = None
        self.async_tasks = []

    def init_ui(self):
        self.setWindowTitle("Аналізатар выяў")
        self.setGeometry(100, 100, 1800, 1200)


        central_widget = QWidget()
        self.setCentralWidget(central_widget)


        layout = QVBoxLayout(central_widget)
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)


        title_label = QLabel("📷 Аналізатар графічных файлаў")
        title_label.setFont(QFont("Segoe UI", 40, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 30px;")
        layout.addWidget(title_label)


        control_group = QGroupBox("Кіраванне аналізам")
        control_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 32px; }")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(25)

        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText("Выберыце папку з выявамі...")
        self.folder_path_edit.setMinimumHeight(80)
        self.folder_path_edit.setFont(QFont("Segoe UI", 28))

        self.browse_btn = QPushButton("📁 Агляд...")
        self.browse_btn.setMinimumHeight(80)
        self.browse_btn.setFont(QFont("Segoe UI", 28))
        self.browse_btn.clicked.connect(self.browse_folder)

        self.analyze_btn = QPushButton("🔍 Аналізаваць")
        self.analyze_btn.setMinimumHeight(80)
        self.analyze_btn.setFont(QFont("Segoe UI", 28))
        self.analyze_btn.clicked.connect(self.start_analysis)

        self.stop_btn = QPushButton("⏹️ Спыніць")
        self.stop_btn.setMinimumHeight(80)
        self.stop_btn.setFont(QFont("Segoe UI", 28))
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)

        self.advanced_cb = QCheckBox("Паказваць інфармацыю пра колерную сістэму")
        self.advanced_cb.setFont(QFont("Segoe UI", 28))
        self.advanced_cb.setStyleSheet("QCheckBox { spacing: 20px; }")

        folder_label = QLabel("Папка:")
        folder_label.setFont(QFont("Segoe UI", 28))

        control_layout.addWidget(folder_label)
        control_layout.addWidget(self.folder_path_edit)
        control_layout.addWidget(self.browse_btn)
        control_layout.addWidget(self.analyze_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.advanced_cb)

        layout.addWidget(control_group)


        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(30)
        layout.addWidget(self.progress_bar)


        self.status_label = QLabel("Гатовы да аналізу")
        self.status_label.setFont(QFont("Segoe UI", 26))
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)


        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Імя файла", "Памер (px)", "Разр. (DPI)",
            "Глыбіня колеру", "Сцісканне", "Фармат", "Колерная сістэма"
        ])


        self.results_table.setFont(QFont("Segoe UI", 24))
        header = self.results_table.horizontalHeader()
        header.setFont(QFont("Segoe UI", 26, QFont.Bold))
        header.setDefaultSectionSize(300)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)

        self.results_table.setSortingEnabled(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setMinimumHeight(500)
        layout.addWidget(self.results_table)


        self.stats_label = QLabel("Знойдзена файлаў: 0")
        self.stats_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.stats_label.setStyleSheet("color: #34495e;")
        layout.addWidget(self.stats_label)


        info_label = QLabel(
            "💡 <b>Асінхронны аналіз</b>: Файлы апрацоўваюцца паралельна, не блакуючы інтэрфейс. "
            "Вы можаце спыніць аналіз у любы момант."
        )
        info_label.setWordWrap(True)
        info_label.setFont(QFont("Segoe UI", 26))
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e8f4f8;
                border: 3px solid #bde0fe;
                border-radius: 15px;
                padding: 25px;
                color: #2c3e50;
            }
        """)
        layout.addWidget(info_label)

    def apply_styles(self):

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 28px;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                border-radius: 15px;
                color: white;
                padding: 20px 35px;
                font-weight: bold;
                min-width: 160px;
                font-size: 28px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QLineEdit {
                border: 4px solid #ddd;
                border-radius: 15px;
                padding: 20px 25px;
                font-size: 28px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QGroupBox {
                font-weight: bold;
                border: 3px solid #ddd;
                border-radius: 18px;
                margin-top: 20px;
                padding-top: 35px;
                background-color: white;
                font-size: 32px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px 0 15px;
                font-size: 32px;
            }
            QTableWidget {
                border: 3px solid #ddd;
                border-radius: 18px;
                background-color: white;
                gridline-color: #ddd;
                selection-background-color: #bdc3c7;
                font-size: 26px;
            }
            QHeaderView::section {
                background-color: #95a5a6;
                color: white;
                padding: 20px;
                border: none;
                font-weight: bold;
                font-size: 28px;
            }
            QProgressBar {
                border: 3px solid #ddd;
                border-radius: 12px;
                text-align: center;
                background-color: #ecf0f1;
                font-size: 26px;
                height: 35px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 10px;
            }
            QCheckBox {
                spacing: 20px;
                font-size: 28px;
            }
            QCheckBox::indicator {
                width: 40px;
                height: 40px;
                border-radius: 8px;
                border: 4px solid #bdc3c7;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
            }
            QLabel {
                font-size: 26(px;
            }
        """)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберыце папку з выявамі")
        if folder:
            self.folder_path_edit.setText(folder)
            supported_formats = {'.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx'}
            count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_formats:
                        count += 1
            self.stats_label.setText(f"Знойдзена падтрымоўваемых файлаў: {count}")

    def start_analysis(self):
        folder_path = self.folder_path_edit.text()

        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "Памылка", "Калі ласка, выберыце існуючую папку")
            return


        self.results_table.setRowCount(0)


        self.analyze_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)


        self.analysis_thread = ImageAnalysisThread(
            folder_path,
            self.advanced_cb.isChecked()
        )
        self.analysis_thread.progress_updated.connect(self.update_progress)
        self.analysis_thread.analysis_finished.connect(self.analysis_finished)
        self.analysis_thread.error_occurred.connect(self.handle_error)
        self.analysis_thread.start()

    def stop_analysis(self):
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.stop_analysis()
            self.analysis_thread.wait(5000)

        self.analyze_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Аналіз спынены")

    def update_progress(self, progress, current, filename):
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Апрацоўка: {filename} ({current} файлаў)")

    def handle_error(self, error_message):
        QMessageBox.warning(self, "Памылка", error_message)
        self.stop_analysis()

    def analysis_finished(self, results):

        self.results_table.setRowCount(len(results))

        for row, result in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(result['filename']))
            self.results_table.setItem(row, 1, QTableWidgetItem(result['size']))
            self.results_table.setItem(row, 2, QTableWidgetItem(result['dpi']))
            self.results_table.setItem(row, 3, QTableWidgetItem(result['color_depth']))
            self.results_table.setItem(row, 4, QTableWidgetItem(result['compression']))
            self.results_table.setItem(row, 5, QTableWidgetItem(result['format']))
            self.results_table.setItem(row, 6, QTableWidgetItem(result['advanced']))


        self.analyze_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Аналіз завершаны. Апрацавана файлаў: {len(results)}")

        QMessageBox.information(self, "Завершана",
                                f"Аналіз паспяхова завершаны!\nАпрацавана файлаў: {len(results)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 24))

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(248, 249, 250))
    palette.setColor(QPalette.WindowText, Qt.black)
    app.setPalette(palette)

    window = ImageAnalyzerApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()