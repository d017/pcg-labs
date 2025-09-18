#include "mainwindow.h"
#include "colorconverter.h"
#include <ctime>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    srand(time(NULL));
    currentColor = QColor(rand() % 256, rand() % 256, rand() % 256);
    setupUi();
    applyStyleSheet();
    updateAll();
}

MainWindow::~MainWindow()
{
}

void MainWindow::setupUi()
{
    setWindowTitle("Каляровыя мадэлі: RGB ↔ HSV ↔ LAB");
    resize(1400, 700);

    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);

    QHBoxLayout *topLayout = new QHBoxLayout();

    colorPickerButton = new QPushButton("🎨 Выбраць колер", this);
    connect(colorPickerButton, &QPushButton::clicked, this, &MainWindow::onColorPickerClicked);

    colorPreview = new QLabel(this);
    colorPreview->setFixedSize(100, 100);
    colorPreview->setFrameShape(QFrame::Box);
    colorPreview->setStyleSheet("background-color: red; border: 2px dashed #6c757d;");

    topLayout->addWidget(colorPickerButton);
    topLayout->addStretch();
    QLabel* colorLabel =  new QLabel("Колер:", this);
    colorLabel->setFont(QFont("Arial", 30));
    topLayout->addWidget(colorLabel);
    topLayout->addWidget(colorPreview);

    mainLayout->addLayout(topLayout);

    QHBoxLayout *modelsLayout = new QHBoxLayout();

    QGroupBox *rgbGroup = new QGroupBox("RGB (0-255)", this);
    QGridLayout *rgbLayout = new QGridLayout();

    rgbRSpin = new QSpinBox(this);
    rgbRSpin->setRange(0, 255);
    rgbRSpin->setSingleStep(1.);
    rgbGSpin = new QSpinBox(this);
    rgbGSpin->setRange(0, 255);
    rgbGSpin->setSingleStep(1.);
    rgbBSpin = new QSpinBox(this);
    rgbBSpin->setRange(0, 255);
    rgbBSpin->setSingleStep(1.);

    rgbRSlider = new QSlider(Qt::Horizontal, this);
    rgbRSlider->setRange(0, 255);
    rgbGSlider = new QSlider(Qt::Horizontal, this);
    rgbGSlider->setRange(0, 255);
    rgbBSlider = new QSlider(Qt::Horizontal, this);
    rgbBSlider->setRange(0, 255);

    connect(rgbRSpin, QOverload<int>::of(&QSpinBox::valueChanged), rgbRSlider, &QSlider::setValue);
    connect(rgbGSpin, QOverload<int>::of(&QSpinBox::valueChanged), rgbGSlider, &QSlider::setValue);
    connect(rgbBSpin, QOverload<int>::of(&QSpinBox::valueChanged), rgbBSlider, &QSlider::setValue);

    connect(rgbRSlider, &QSlider::valueChanged, rgbRSpin, qOverload<int>(&QSpinBox::setValue));
    connect(rgbGSlider, &QSlider::valueChanged, rgbGSpin, qOverload<int>(&QSpinBox::setValue));
    connect(rgbBSlider, &QSlider::valueChanged, rgbBSpin, qOverload<int>(&QSpinBox::setValue));

    connect(rgbRSpin, QOverload<int>::of(&QSpinBox::valueChanged), this, &MainWindow::updateFromRgb);
    connect(rgbGSpin, QOverload<int>::of(&QSpinBox::valueChanged), this, &MainWindow::updateFromRgb);
    connect(rgbBSpin, QOverload<int>::of(&QSpinBox::valueChanged), this, &MainWindow::updateFromRgb);

    rgbLayout->addWidget(new QLabel("R:", this), 0, 0);
    rgbLayout->addWidget(rgbRSpin, 0, 1);
    rgbLayout->addWidget(rgbRSlider, 0, 2);

    rgbLayout->addWidget(new QLabel("G:", this), 1, 0);
    rgbLayout->addWidget(rgbGSpin, 1, 1);
    rgbLayout->addWidget(rgbGSlider, 1, 2);

    rgbLayout->addWidget(new QLabel("B:", this), 2, 0);
    rgbLayout->addWidget(rgbBSpin, 2, 1);
    rgbLayout->addWidget(rgbBSlider, 2, 2);

    rgbGroup->setLayout(rgbLayout);

    QGroupBox *hsvGroup = new QGroupBox("HSV", this);
    QGridLayout *hsvLayout = new QGridLayout();

    hsvHSpin = new QDoubleSpinBox(this);
    hsvHSpin->setRange(0.0, 360.0);
    hsvHSpin->setSingleStep(1.0);
    hsvSSpin = new QDoubleSpinBox(this);
    hsvSSpin->setRange(0.0, 100.0);
    hsvSSpin->setSingleStep(1.0);
    hsvVSpin = new QDoubleSpinBox(this);
    hsvVSpin->setRange(0.0, 100.0);
    hsvVSpin->setSingleStep(1.0);

    hsvHSlider = new QSlider(Qt::Horizontal, this);
    hsvHSlider->setRange(0, 360);
    hsvSSlider = new QSlider(Qt::Horizontal, this);
    hsvSSlider->setRange(0, 100);
    hsvVSlider = new QSlider(Qt::Horizontal, this);
    hsvVSlider->setRange(0, 100);

    connect(hsvHSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), hsvHSlider, &QSlider::setValue);
    connect(hsvSSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), hsvSSlider, &QSlider::setValue);
    connect(hsvVSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), hsvVSlider, &QSlider::setValue);

    connect(hsvHSlider, &QSlider::valueChanged, hsvHSpin, qOverload<double>(&QDoubleSpinBox::setValue));
    connect(hsvSSlider, &QSlider::valueChanged, hsvSSpin, qOverload<double>(&QDoubleSpinBox::setValue));
    connect(hsvVSlider, &QSlider::valueChanged, hsvVSpin, qOverload<double>(&QDoubleSpinBox::setValue));

    connect(hsvHSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &MainWindow::updateFromHsv);
    connect(hsvSSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &MainWindow::updateFromHsv);
    connect(hsvVSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &MainWindow::updateFromHsv);

    hsvLayout->addWidget(new QLabel("H (0-360):", this), 0, 0);
    hsvLayout->addWidget(hsvHSpin, 0, 1);
    hsvLayout->addWidget(hsvHSlider, 0, 2);

    hsvLayout->addWidget(new QLabel("S (0-100%):", this), 1, 0);
    hsvLayout->addWidget(hsvSSpin, 1, 1);
    hsvLayout->addWidget(hsvSSlider, 1, 2);

    hsvLayout->addWidget(new QLabel("V (0-100%):", this), 2, 0);
    hsvLayout->addWidget(hsvVSpin, 2, 1);
    hsvLayout->addWidget(hsvVSlider, 2, 2);

    hsvGroup->setLayout(hsvLayout);

    QGroupBox *labGroup = new QGroupBox("LAB", this);
    QGridLayout *labLayout = new QGridLayout();

    labLSpin = new QDoubleSpinBox(this);
    labLSpin->setRange(0.0, 100.0);
    labLSpin->setSingleStep(1.0);
    labASpin = new QDoubleSpinBox(this);
    labASpin->setRange(-128.0, 127.0);
    labASpin->setSingleStep(1.0);
    labBSpin = new QDoubleSpinBox(this);
    labBSpin->setRange(-128.0, 127.0);
    labBSpin->setSingleStep(1.0);

    connect(labLSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &MainWindow::updateFromLab);
    connect(labASpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &MainWindow::updateFromLab);
    connect(labBSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, &MainWindow::updateFromLab);

    labLSlider = new QSlider(Qt::Horizontal, this);
    labLSlider->setRange(0, 100);

    labASlider = new QSlider(Qt::Horizontal, this);
    labASlider->setRange(0, 255);

    labBSlider = new QSlider(Qt::Horizontal, this);
    labBSlider->setRange(0, 255);

    connect(labLSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), labLSlider, &QSlider::setValue);

    connect(labASpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, [this](double val) {
        labASlider->setValue(static_cast<int>(val + 128));
    });
    connect(labBSpin, QOverload<double>::of(&QDoubleSpinBox::valueChanged), this, [this](double val) {
        labBSlider->setValue(static_cast<int>(val + 128));
    });

    connect(labLSlider, &QSlider::valueChanged, labLSpin, qOverload<double>(&QDoubleSpinBox::setValue));
    connect(labASlider, &QSlider::valueChanged, this, [this](int val) {
        labASpin->setValue(val - 128.0);
    });
    connect(labBSlider, &QSlider::valueChanged, this, [this](int val) {
        labBSpin->setValue(val - 128.0);
    });

    labLayout->addWidget(new QLabel("L (0-100):", this), 0, 0);
    labLayout->addWidget(labLSpin, 0, 1);
    labLayout->addWidget(labLSlider, 0, 2);

    labLayout->addWidget(new QLabel("a (-128-127):", this), 1, 0);
    labLayout->addWidget(labASpin, 1, 1);
    labLayout->addWidget(labASlider, 1, 2);

    labLayout->addWidget(new QLabel("b (-128-127):", this), 2, 0);
    labLayout->addWidget(labBSpin, 2, 1);
    labLayout->addWidget(labBSlider, 2, 2);

    labGroup->setLayout(labLayout);

    modelsLayout->addWidget(rgbGroup);
    modelsLayout->addWidget(hsvGroup);
    modelsLayout->addWidget(labGroup);

    mainLayout->addLayout(modelsLayout);
    mainLayout->addStretch();
}

void MainWindow::updateFromRgb() {
    if (updating) return;
    updating = true;

    int r = rgbRSpin->value();
    int g = rgbGSpin->value();
    int b = rgbBSpin->value();

    currentColor = QColor(r, g, b);

    syncHsv();
    syncLab();

    colorPreview->setStyleSheet(QString("background-color: rgb(%1, %2, %3);").arg(r).arg(g).arg(b));

    updating = false;
}

void MainWindow::updateFromHsv() {
    if (updating) return;
    updating = true;

    double h = hsvHSpin->value();
    double s = hsvSSpin->value();
    double v = hsvVSpin->value();

    ColorTriple rgb = hsvToRgb(h, s, v);
    int r = static_cast<int>(qRound(std::max(0.0, std::min(255.0, rgb.x))));
    int g = static_cast<int>(qRound(std::max(0.0, std::min(255.0, rgb.y))));
    int b = static_cast<int>(qRound(std::max(0.0, std::min(255.0, rgb.z))));

    if (rgb.x < 0 || rgb.x > 255 || rgb.y < 0 || rgb.y > 255 || rgb.z < 0 || rgb.z > 255) {
        showWarning("HSV → RGB: значэнне выйшла за межы [0,255]. Выканана карэкцыя.");
    }

    currentColor = QColor(r, g, b);
    syncRgb();
    syncLab();

    colorPreview->setStyleSheet(QString("background-color: rgb(%1, %2, %3);").arg(r).arg(g).arg(b));

    updating = false;
}

void MainWindow::updateFromLab() {
    if (updating) return;
    updating = true;

    double L = labLSpin->value();
    double a = labASpin->value();
    double b_val = labBSpin->value();

    ColorTriple rgb = labToRgb(L, a, b_val);
    int r = static_cast<int>(qRound(std::max(0.0, std::min(255.0, rgb.x))));
    int g = static_cast<int>(qRound(std::max(0.0, std::min(255.0, rgb.y))));
    int b = static_cast<int>(qRound(std::max(0.0, std::min(255.0, rgb.z))));

    if (rgb.x < 0 || rgb.x > 255 || rgb.y < 0 || rgb.y > 255 || rgb.z < 0 || rgb.z > 255) {
        showWarning("LAB → RGB: значэнне выйшла за межы [0,255]. Выканана карэкцыя.");
    }

    currentColor = QColor(r, g, b);
    syncRgb();
    syncHsv();

    colorPreview->setStyleSheet(QString("background-color: rgb(%1, %2, %3);").arg(r).arg(g).arg(b));

    updating = false;
}

void MainWindow::syncRgb() {
    bool oldState = rgbRSpin->blockSignals(true);
    rgbRSpin->setValue(currentColor.red());
    rgbRSpin->blockSignals(oldState);

    oldState = rgbGSpin->blockSignals(true);
    rgbGSpin->setValue(currentColor.green());
    rgbGSpin->blockSignals(oldState);

    oldState = rgbBSpin->blockSignals(true);
    rgbBSpin->setValue(currentColor.blue());
    rgbBSpin->blockSignals(oldState);

    oldState = rgbRSlider->blockSignals(true);
    rgbRSlider->setValue(currentColor.red());
    rgbRSlider->blockSignals(oldState);

    oldState = rgbGSlider->blockSignals(true);
    rgbGSlider->setValue(currentColor.green());
    rgbGSlider->blockSignals(oldState);

    oldState = rgbBSlider->blockSignals(true);
    rgbBSlider->setValue(currentColor.blue());
    rgbBSlider->blockSignals(oldState);
}

void MainWindow::syncHsv() {
    ColorTriple hsv = rgbToHsv(currentColor.red(), currentColor.green(), currentColor.blue());
    bool oldState;

    oldState = hsvHSpin->blockSignals(true);
    hsvHSpin->setValue(hsv.x);
    hsvHSpin->blockSignals(oldState);

    oldState = hsvHSlider->blockSignals(true);
    hsvHSlider->setValue(static_cast<int>(hsv.x));
    hsvHSlider->blockSignals(oldState);

    oldState = hsvSSpin->blockSignals(true);
    hsvSSpin->setValue(hsv.y);
    hsvSSpin->blockSignals(oldState);

    oldState = hsvSSlider->blockSignals(true);
    hsvSSlider->setValue(static_cast<int>(hsv.y));
    hsvSSlider->blockSignals(oldState);

    oldState = hsvVSpin->blockSignals(true);
    hsvVSpin->setValue(hsv.z);
    hsvVSpin->blockSignals(oldState);

    oldState = hsvVSlider->blockSignals(true);
    hsvVSlider->setValue(static_cast<int>(hsv.z));
    hsvVSlider->blockSignals(oldState);
}

void MainWindow::syncLab() {
    ColorTriple lab = rgbToLab(currentColor.red(), currentColor.green(), currentColor.blue());
    bool oldState;

    oldState = labLSpin->blockSignals(true);
    labLSpin->setValue(lab.x);
    labLSpin->blockSignals(oldState);

    oldState = labASpin->blockSignals(true);
    labASpin->setValue(lab.y);
    labASpin->blockSignals(oldState);

    oldState = labBSpin->blockSignals(true);
    labBSpin->setValue(lab.z);
    labBSpin->blockSignals(oldState);

    oldState = labLSlider->blockSignals(true);
    labLSlider->setValue(static_cast<int>(lab.x));
    labLSlider->blockSignals(oldState);

    oldState = labASlider->blockSignals(true);
    labASlider->setValue(static_cast<int>(lab.y + 128));
    labASlider->blockSignals(oldState);

    oldState = labBSlider->blockSignals(true);
    labBSlider->setValue(static_cast<int>(lab.z + 128));
    labBSlider->blockSignals(oldState);
}

void MainWindow::updatePreviewColor(const QColor& color)
{
    if (!color.isValid()) return;
    colorPreview->setStyleSheet(
        QString("background-color: %1; border: 4px dashed #6c757d;").arg(color.name())
        );
}

void MainWindow::updateAll()
{
    if (!currentColor.isValid()) {
        currentColor = Qt::red;
    }

    int r = qBound(0, currentColor.red(), 255);
    int g = qBound(0, currentColor.green(), 255);
    int b = qBound(0, currentColor.blue(), 255);

    currentColor = QColor(r, g, b);
    updatePreviewColor(currentColor);
    syncRgb();
    syncHsv();
    syncLab();
}

void MainWindow::onColorPickerClicked() {
    QColor color = QColorDialog::getColor(currentColor, this, "Выберыце колер");
    if (color.isValid()) {
        currentColor = color;
        updateAll();
    }
}

void MainWindow::showWarning(const QString &message) {
    QMessageBox::warning(this, "Папярэджанне", message, QMessageBox::Ok);
}

void MainWindow::applyStyleSheet()
{
    QString style = R"(
        QMainWindow {
            background: #f8f9fa;
            font-size: 24px;
        }

        QGroupBox {
            font-weight: bold;
            font-size: 18px;
            border: 3px solid #007bff;
            border-radius: 16px;
            margin-top: 20px;
            padding: 20px;
            background: #ffffff;
            color: #007bff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 10px;
            background: #007bff;
            color: white;
            border-radius: 10px;
            font-size: 18px;
        }

        QLabel {
            font-size: 30px;
            color: #333;
        }

        QSpinBox, QDoubleSpinBox {
            padding: 8px;
            border: 2px solid #ced4da;
            border-radius: 8px;
            background: #ffffff;
            font-size: 24px;
            min-width: 160px;
            min-height: 40px;
        }

        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 3px solid #007bff;
        }

        QPushButton {
            background: #007bff;
            color: white;
            border: none;
            padding: 16px 32px;
            font-weight: bold;
            font-size: 30px;
            border-radius: 12px;
            min-width: 240px;
            min-height: 50px;
        }

        QPushButton:hover {
            background: #0056b3;
        }

        QPushButton:pressed {
            background: #004085;
        }

        QLabel#colorPreview {
            font-weight: bold;
            font-size: 18px;
            border: 4px dashed #6c757d;
            background: #ffffff;
            min-width: 200px;
            min-height: 200px;
        }
        QSlider {
            height: 30px;
            margin: 8px 0;
        }

        QSlider::groove:horizontal {
            border: 2px solid #ced4da;
            height: 10px;
            background: #e9ecef;
            border-radius: 5px;
        }

        QSlider::handle:horizontal {
            background: #007bff;
            border: 2px solid #0056b3;
            width: 24px;
            height: 24px;
            margin: -7px 0;
            border-radius: 12px;
        }

        QSlider::handle:horizontal:hover {
            background: #0056b3;
        }

        QSlider::handle:horizontal:pressed {
            background: #004085;
        }
    )";

    this->setStyleSheet(style);
}
