#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QSpinBox>
#include <QDoubleSpinBox>
#include <QLabel>
#include <QPushButton>
#include <QColorDialog>
#include <QMessageBox>
#include <QGridLayout>
#include <QGroupBox>
#include <QVBoxLayout>
#include <QSlider>

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void updateFromRgb();
    void updateFromHsv();
    void updateFromLab();
    void onColorPickerClicked();
    void updatePreviewColor(const QColor&);
    void showWarning(const QString& message);

private:
    bool updating = false;
    QColor currentColor;

    QSpinBox *rgbRSpin;
    QSpinBox *rgbGSpin;
    QSpinBox *rgbBSpin;

    QDoubleSpinBox *hsvHSpin;
    QDoubleSpinBox *hsvSSpin;
    QDoubleSpinBox *hsvVSpin;

    QDoubleSpinBox *labLSpin;
    QDoubleSpinBox *labASpin;
    QDoubleSpinBox *labBSpin;

    QSlider *rgbRSlider;
    QSlider *rgbGSlider;
    QSlider *rgbBSlider;

    QSlider *hsvHSlider;
    QSlider *hsvSSlider;
    QSlider *hsvVSlider;

    QSlider *labLSlider;
    QSlider *labASlider;
    QSlider *labBSlider;

    QLabel *colorPreview;
    QPushButton *colorPickerButton;

    void applyStyleSheet();

    void syncRgb();
    void syncHsv();
    void syncLab();
    void updateAll();
    void setupUi();
};

#endif // MAINWINDOW_H
