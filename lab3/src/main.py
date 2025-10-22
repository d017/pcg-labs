import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QFileDialog, QLabel, QComboBox, QGroupBox, QMessageBox,
    QSpinBox, QDoubleSpinBox, QCheckBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PIL import Image


def rgb_to_hsv(rgb):
    rgb = rgb.astype(np.float32) / 255.0
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    mx = np.max(rgb, axis=2)
    mn = np.min(rgb, axis=2)
    df = mx - mn

    h = np.zeros_like(mx)
    mask = df != 0
    h[mask & (mx == r)] = (60 * ((g - b) / df) % 6)[mask & (mx == r)]
    h[mask & (mx == g)] = (60 * ((b - r) / df) + 120)[mask & (mx == g)]
    h[mask & (mx == b)] = (60 * ((r - g) / df) + 240)[mask & (mx == b)]
    h = np.clip(h, 0, 360)

    s = np.zeros_like(mx)
    s[mask] = df[mask] / mx[mask]
    s = np.clip(s, 0, 1)

    v = mx
    hsv = np.stack([h, s * 255, v * 255], axis=2)
    return hsv.astype(np.uint8)


def hsv_to_rgb(hsv):
    h, s, v = hsv[:, :, 0].astype(np.float32), hsv[:, :, 1].astype(np.float32) / 255.0, hsv[:, :, 2].astype(np.float32) / 255.0
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c

    rgb = np.zeros((h.shape[0], h.shape[1], 3), dtype=np.float32)
    mask = (h >= 0) & (h < 60)
    rgb[mask] = np.stack([c[mask], x[mask], np.zeros_like(c[mask])], axis=1)
    mask = (h >= 60) & (h < 120)
    rgb[mask] = np.stack([x[mask], c[mask], np.zeros_like(c[mask])], axis=1)
    mask = (h >= 120) & (h < 180)
    rgb[mask] = np.stack([np.zeros_like(c[mask]), c[mask], x[mask]], axis=1)
    mask = (h >= 180) & (h < 240)
    rgb[mask] = np.stack([np.zeros_like(c[mask]), x[mask], c[mask]], axis=1)
    mask = (h >= 240) & (h < 300)
    rgb[mask] = np.stack([x[mask], np.zeros_like(c[mask]), c[mask]], axis=1)
    mask = (h >= 300) & (h <= 360)
    rgb[mask] = np.stack([c[mask], np.zeros_like(c[mask]), x[mask]], axis=1)

    rgb = (rgb + m[:, :, np.newaxis]) * 255
    return np.clip(rgb, 0, 255).astype(np.uint8)


def linear_contrast(img):
    if img.ndim == 3:
        out = np.zeros_like(img)
        for c in range(3):
            channel = img[:, :, c].astype(np.float32)
            min_val, max_val = channel.min(), channel.max()
            if max_val == min_val:
                out[:, :, c] = channel
            else:
                out[:, :, c] = 255 * (channel - min_val) / (max_val - min_val)
        return np.clip(out, 0, 255).astype(np.uint8)
    else:
        img = img.astype(np.float32)
        min_val, max_val = img.min(), img.max()
        if max_val == min_val:
            return img.astype(np.uint8)
        stretched = 255 * (img - min_val) / (max_val - min_val)
        return np.clip(stretched, 0, 255).astype(np.uint8)


def hist_equalize_grayscale(gray):
    hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
    cdf = hist.cumsum()
    cdf_normalized = (cdf - cdf.min()) * 255 / (cdf.max() - cdf.min())
    cdf_normalized = np.ma.filled(np.ma.masked_less(cdf_normalized, 0), 0).astype(np.uint8)
    return cdf_normalized[gray]


def hist_equalize_rgb(img):
    out = np.zeros_like(img)
    for c in range(3):
        out[:, :, c] = hist_equalize_grayscale(img[:, :, c])
    return out


def hist_equalize_hsv(img):
    hsv = rgb_to_hsv(img)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    v_eq = hist_equalize_grayscale(v)
    hsv_eq = np.stack([h, s, v_eq], axis=2)
    return hsv_to_rgb(hsv_eq)


def grayscale(img):
    if img.ndim == 3:
        return (0.2989 * img[:, :, 0] + 0.5870 * img[:, :, 1] + 0.1140 * img[:, :, 2]).astype(np.uint8)
    return img


def sobel_edge(gray):
    Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    Ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])

    h, w = gray.shape
    pad = 1
    padded = np.pad(gray, pad, mode='constant')
    Gx = np.zeros_like(gray, dtype=np.float32)
    Gy = np.zeros_like(gray, dtype=np.float32)

    
    for i in range(1, h+1):
        for j in range(1, w+1):
            region = padded[i-1:i+2, j-1:j+2]
            Gx[i-1, j-1] = np.sum(Kx * region)
            Gy[i-1, j-1] = np.sum(Ky * region)

    mag = np.hypot(Gx, Gy)
    if mag.max() == 0:
        return np.zeros_like(mag, dtype=np.uint8)
    mag = mag / mag.max() * 255
    return mag.astype(np.uint8)


def detect_edges(img, low=50, high=150, use_hysteresis=True):
    gray = grayscale(img)
    edges = sobel_edge(gray)
    
    
    final = np.zeros_like(edges)
    
    
    strong = edges >= high
    final[strong] = 255
    
    if use_hysteresis and low < high:
        
        weak = (edges >= low) & (edges < high)
        
        h, w = edges.shape
        for i in range(1, h-1):
            for j in range(1, w-1):
                if weak[i, j] and np.any(strong[i-1:i+2, j-1:j+2]):
                    final[i, j] = 255
    else:
        final[edges >= low] = 255
        
    return final


def overlay_edges(img, edges):
    out = img.copy()
    out[edges == 255] = [0, 0, 255]
    return out


def hough_line_transform(edges, angle_step=1, threshold=100, min_line_length=50, max_line_gap=10):
    h, w = edges.shape
    diag = int(np.ceil(np.sqrt(h**2 + w**2)))
    thetas = np.deg2rad(np.arange(-90, 90, angle_step))
    rhos = np.linspace(-diag, diag, diag*2)

    cos_t = np.cos(thetas)
    sin_t = np.sin(thetas)
    num_thetas = len(thetas)

    accumulator = np.zeros((len(rhos), num_thetas), dtype=np.int32)

    y_idxs, x_idxs = np.nonzero(edges)
    for i in range(len(x_idxs)):
        x = x_idxs[i]
        y = y_idxs[i]
        for t_idx in range(num_thetas):
            rho = x * cos_t[t_idx] + y * sin_t[t_idx]
            rho_idx = int(round(rho)) + diag
            if 0 <= rho_idx < len(rhos):
                accumulator[rho_idx, t_idx] += 1

    lines = []
    for rho_idx in range(accumulator.shape[0]):
        for theta_idx in range(accumulator.shape[1]):
            if accumulator[rho_idx, theta_idx] >= threshold:
                rho = rhos[rho_idx]
                theta = thetas[theta_idx]
                lines.append((rho, theta))
                
    return lines


def draw_lines(img, lines, min_length=50):
    out = img.copy()
    h, w = img.shape[:2]
    for rho, theta in lines:
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        x1 = int(x0 + 1000 * (-b))
        y1 = int(y0 + 1000 * (a))
        x2 = int(x0 - 1000 * (-b))
        y2 = int(y0 - 1000 * (a))
        
        
        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        if length < min_length:
            continue
            
        rr, cc = [], []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        x, y = x1, y1
        while True:
            if 0 <= x < w and 0 <= y < h:
                rr.append(y)
                cc.append(x)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        if len(rr) > 0:
            out[rr, cc] = [0, 255, 0]
    return out


def harris_corner(img, k=0.04, threshold=0.01, min_distance=10):
    gray = grayscale(img).astype(np.float32)
    Ix = np.zeros_like(gray)
    Iy = np.zeros_like(gray)
    Ix[1:-1, :] = gray[2:, :] - gray[:-2, :]
    Iy[:, 1:-1] = gray[:, 2:] - gray[:, :-2]

    Ixx = Ix ** 2
    Iyy = Iy ** 2
    Ixy = Ix * Iy

    def gaussian_kernel(size=5, sigma=1.0):
        ax = np.arange(-size // 2 + 1., size // 2 + 1.)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
        return kernel / np.sum(kernel)

    kernel = gaussian_kernel()
    Sxx = convolve2d(Ixx, kernel)
    Syy = convolve2d(Iyy, kernel)
    Sxy = convolve2d(Ixy, kernel)

    det = Sxx * Syy - Sxy ** 2
    trace = Sxx + Syy
    R = det - k * (trace ** 2)

    
    corners = R > (threshold * R.max())
    
    
    if min_distance > 0:
        from scipy.ndimage import maximum_filter
        data_max = maximum_filter(R, size=min_distance)
        corners = (R == data_max) & corners
        
    return corners.astype(np.uint8)


def convolve2d(image, kernel):
    h, w = image.shape
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant')
    output = np.zeros_like(image)
    for i in range(h):
        for j in range(w):
            output[i, j] = np.sum(padded[i:i+kh, j:j+kw] * kernel)
    return output


def draw_points(img, points):
    out = img.copy()
    h, w = img.shape[:2]
    y_idxs, x_idxs = np.nonzero(points)
    for y, x in zip(y_idxs, x_idxs):
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if 0 <= y+dy < h and 0 <= x+dx < w:
                    if dx == 0 or dy == 0:
                        out[y+dy, x+dx] = [255, 0, 0]
    return out


class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Апрацоўка выяў")
        self.setGeometry(100, 100, 1400, 800)
        self.original_image = None
        self.current_image = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        
        control_layout = QVBoxLayout()
        
        
        self.load_btn = QPushButton("Загрузіць выяву")
        self.load_btn.clicked.connect(self.load_image)
        control_layout.addWidget(self.load_btn)
        
        
        contrast_group = QGroupBox("Пашырэнне кантрасту")
        contrast_layout = QVBoxLayout()
        self.contrast_combo = QComboBox()
        self.contrast_combo.addItems([
            "Арыгінал",
            "Лінейнае пашырэнне кантрасту",
            "Эквалізацыя гістаграмы (адценні шэрага)",
            "Эквалізацыя гістаграмы (RGB)",
            "Эквалізацыя гістаграмы (HSV)"
        ])
        contrast_layout.addWidget(self.contrast_combo)
        contrast_group.setLayout(contrast_layout)
        control_layout.addWidget(contrast_group)
        
        
        seg_group = QGroupBox("Сегментацыя")
        seg_layout = QVBoxLayout()
        self.segment_combo = QComboBox()
        self.segment_combo.addItems([
            "Няма",
            "Перапады яркасці",
            "Выяўленне ліній",
            "Выяўленне кропак"
        ])
        seg_layout.addWidget(self.segment_combo)
        
        
        self.param_widgets = {}
        
        
        edge_form = QFormLayout()
        self.edge_low_spin = QSpinBox()
        self.edge_low_spin.setRange(0, 255)
        self.edge_low_spin.setValue(50)
        self.edge_high_spin = QSpinBox()
        self.edge_high_spin.setRange(0, 255)
        self.edge_high_spin.setValue(150)
        self.edge_hyst_check = QCheckBox("Гістэрызіс")
        self.edge_hyst_check.setChecked(True)
        edge_form.addRow("Нізкі парог:", self.edge_low_spin)
        edge_form.addRow("Высокі парог:", self.edge_high_spin)
        edge_form.addRow("", self.edge_hyst_check)
        edge_widget = QWidget()
        edge_widget.setLayout(edge_form)
        edge_widget.hide()
        seg_layout.addWidget(edge_widget)
        self.edge_param_widget = edge_widget
        
        
        line_form = QFormLayout()
        self.line_thresh_spin = QSpinBox()
        self.line_thresh_spin.setRange(1, 500)
        self.line_thresh_spin.setValue(80)
        self.line_min_len_spin = QSpinBox()
        self.line_min_len_spin.setRange(10, 500)
        self.line_min_len_spin.setValue(50)
        self.line_angle_step_spin = QSpinBox()
        self.line_angle_step_spin.setRange(1, 10)
        self.line_angle_step_spin.setValue(1)
        line_form.addRow("Парог Хафа:", self.line_thresh_spin)
        line_form.addRow("Мін. даўжыня:", self.line_min_len_spin)
        line_form.addRow("Крок вугла (°):", self.line_angle_step_spin)
        line_widget = QWidget()
        line_widget.setLayout(line_form)
        line_widget.hide()
        seg_layout.addWidget(line_widget)
        self.line_param_widget = line_widget
        
        
        point_form = QFormLayout()
        self.point_thresh_spin = QDoubleSpinBox()
        self.point_thresh_spin.setRange(0.001, 0.1)
        self.point_thresh_spin.setValue(0.01)
        self.point_thresh_spin.setSingleStep(0.001)
        self.point_min_dist_spin = QSpinBox()
        self.point_min_dist_spin.setRange(1, 50)
        self.point_min_dist_spin.setValue(10)
        point_form.addRow("Парог Харыса:", self.point_thresh_spin)
        point_form.addRow("Мін. адлегласць:", self.point_min_dist_spin)
        point_widget = QWidget()
        point_widget.setLayout(point_form)
        point_widget.hide()
        seg_layout.addWidget(point_widget)
        self.point_param_widget = point_widget
        
        seg_group.setLayout(seg_layout)
        control_layout.addWidget(seg_group)
        
        self.apply_btn = QPushButton("Ок")
        self.apply_btn.clicked.connect(self.apply_processing)
        self.apply_btn.setEnabled(False)
        control_layout.addWidget(self.apply_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout, 1)
        
        
        self.image_label = QLabel("Загрузіце выяву")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: #eee; border: 1px solid #ccc;")
        main_layout.addWidget(self.image_label, 4)
        
        
        self.segment_combo.currentTextChanged.connect(self.update_param_visibility)

    def update_param_visibility(self, method):
        self.edge_param_widget.hide()
        self.line_param_widget.hide()
        self.point_param_widget.hide()
        
        if method == "Перапады яркасці":
            self.edge_param_widget.show()
        elif method == "Выяўленне ліній":
            self.line_param_widget.show()
        elif method == "Выяўленне кропак":
            self.point_param_widget.show()

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Адкрыць выяву", 
            "", 
            "Выявы (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
        try:
            pil_img = Image.open(path).convert('RGB')
            self.original_image = np.array(pil_img)
            self.current_image = self.original_image.copy()
            self.display_image(self.original_image)
            self.apply_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Памылка", f"Не ўдалося загрузіць выяву:\n{e}")

    def display_image(self, arr):
        if arr is None:
            return
        h, w = arr.shape[:2]
        if arr.ndim == 3:
            qimg = QImage(arr.data, w, h, 3*w, QImage.Format_RGB888).rgbSwapped()
        else:
            arr_rgb = np.stack([arr]*3, axis=2)
            qimg = QImage(arr_rgb.data, w, h, 3*w, QImage.Format_RGB888).rgbSwapped()
        
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)

    def apply_processing(self):
        if self.original_image is None:
            return
            
        img = self.original_image.copy()
        contrast = self.contrast_combo.currentText()
        segment = self.segment_combo.currentText()

        
        if contrast == "Лінейнае пашырэнне кантрасту":
            img = linear_contrast(img)
        elif contrast == "Эквалізацыя гістаграмы (адценні шэрага)":
            gray = grayscale(img)
            eq = hist_equalize_grayscale(gray)
            img = np.stack([eq, eq, eq], axis=2)
        elif contrast == "Эквалізацыя гістаграмы (RGB)":
            img = hist_equalize_rgb(img)
        elif contrast == "Эквалізацыя гістаграмы (HSV)":
            img = hist_equalize_hsv(img)

        
        if segment == "Перапады яркасці":
            low = self.edge_low_spin.value()
            high = self.edge_high_spin.value()
            hyst = self.edge_hyst_check.isChecked()
            edges = detect_edges(img, low=low, high=high, use_hysteresis=hyst)
            img = overlay_edges(img, edges)
        elif segment == "Выяўленне ліній":
            edges = detect_edges(img, low=50, high=150)
            threshold = self.line_thresh_spin.value()
            min_len = self.line_min_len_spin.value()
            angle_step = self.line_angle_step_spin.value()
            lines = hough_line_transform(
                edges, 
                threshold=threshold,
                min_line_length=min_len,
                angle_step=angle_step
            )
            img = draw_lines(img, lines, min_length=min_len)
        elif segment == "Выяўленне кропак":
            threshold = self.point_thresh_spin.value()
            min_dist = self.point_min_dist_spin.value()
            points = harris_corner(img, threshold=threshold, min_distance=min_dist)
            img = draw_points(img, points)

        self.current_image = img
        self.display_image(img)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorApp()
    window.show()
    sys.exit(app.exec_())