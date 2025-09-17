#ifndef COLORCONVERTER_H
#define COLORCONVERTER_H

#include <QColor>
#include <QVector3D>
#include <QDebug>

struct ColorTriple {
    double x, y, z;
    ColorTriple(double a = 0, double b = 0, double c = 0) : x(a), y(b), z(c) {}
};

ColorTriple rgbToHsv(double r, double g, double b);
ColorTriple hsvToRgb(double h, double s, double v);

ColorTriple rgbToXyz(double r, double g, double b);
ColorTriple xyzToRgb(double x, double y, double z);

ColorTriple xyzToLab(double x, double y, double z);
ColorTriple labToXyz(double l, double a, double b);

ColorTriple labToRgb(double l, double a, double b);
ColorTriple rgbToLab(double r, double g, double b);

double hue2rgb(double p, double q, double t);
double labf(double t);

#endif // COLORCONVERTER_H
