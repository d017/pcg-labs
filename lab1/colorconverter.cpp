#include "colorconverter.h"
#include <cmath>
#include <algorithm>

const double REF_X = 95.047;
const double REF_Y = 100.000;
const double REF_Z = 108.883;

ColorTriple rgbToHsv(double r, double g, double b) {
    r /= 255.0; g /= 255.0; b /= 255.0;

    double max = std::max({r, g, b}), min = std::min({r, g, b});
    double h, s, v = max;

    double d = max - min;
    s = max == 0 ? 0 : d / max;

    if (max == min) {
        h = 0;
    } else {
        if (max == r) h = (g - b) / d + (g < b ? 6 : 0);
        else if (max == g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h /= 6.0;
    }

    return ColorTriple(h * 360.0, s * 100.0, v * 100.0);
}

ColorTriple hsvToRgb(double h, double s, double v) {
    h = fmod(h, 360.0);
    if (h < 0) h += 360.0;
    s /= 100.0; v /= 100.0;

    int i = static_cast<int>(h / 60.0) % 6;
    double f = h / 60.0 - i;
    double p = v * (1 - s);
    double q = v * (1 - f * s);
    double t = v * (1 - (1 - f) * s);

    double r, g, b;
    switch (i) {
    case 0: r = v; g = t; b = p; break;
    case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;
    case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;
    case 5: r = v; g = p; b = q; break;
    default: r = g = b = 0;
    }

    return ColorTriple(r * 255.0, g * 255.0, b * 255.0);
}

ColorTriple rgbToXyz(double r, double g, double b) {
    r /= 255.0; g /= 255.0; b /= 255.0;

    auto gamma = [](double c) {
        return (c > 0.04045) ? pow((c + 0.055) / 1.055, 2.4) : c / 12.92;
    };
    r = gamma(r); g = gamma(g); b = gamma(b);

    double x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375;
    double y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750;
    double z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041;

    return ColorTriple(x * 100.0, y * 100.0, z * 100.0);
}

ColorTriple xyzToRgb(double x, double y, double z) {
    x /= 100.0; y /= 100.0; z /= 100.0;

    double r = x * 3.2404542 - y * 1.5371385 - z * 0.4985314;
    double g = -x * 0.9692660 + y * 1.8760108 + z * 0.0415560;
    double b = x * 0.0556434 - y * 0.2040259 + z * 1.0572252;

    auto gamma = [](double c) {
        c = std::max(0.0, c);
        return (c > 0.0031308) ? 1.055 * pow(c, 1.0/2.4) - 0.055 : 12.92 * c;
    };
    r = gamma(r); g = gamma(g); b = gamma(b);

    return ColorTriple(r * 255.0, g * 255.0, b * 255.0);
}

ColorTriple xyzToLab(double x, double y, double z) {
    x /= REF_X; y /= REF_Y; z /= REF_Z;

    auto f = [](double t) {
        return t > 0.008856 ? pow(t, 1.0/3.0) : (7.787 * t + 16.0/116.0);
    };

    double fx = f(x), fy = f(y), fz = f(z);

    double L = 116.0 * fy - 16.0;
    double a = 500.0 * (fx - fy);
    double b = 200.0 * (fy - fz);

    return ColorTriple(L, a, b);
}

ColorTriple labToXyz(double L, double a, double b) {
    double fy = (L + 16.0) / 116.0;
    double fx = a / 500.0 + fy;
    double fz = fy - b / 200.0;

    auto finv = [](double t) {
        double t3 = t * t * t;
        return t3 > 0.008856 ? t3 : (t - 16.0/116.0) / 7.787;
    };

    double x = REF_X * finv(fx);
    double y = REF_Y * finv(fy);
    double z = REF_Z * finv(fz);

    return ColorTriple(x, y, z);
}

ColorTriple labToRgb(double L, double a, double b) {
    ColorTriple xyz = labToXyz(L, a, b);
    return xyzToRgb(xyz.x, xyz.y, xyz.z);
}

ColorTriple rgbToLab(double r, double g, double b) {
    ColorTriple xyz = rgbToXyz(r, g, b);
    return xyzToLab(xyz.x, xyz.y, xyz.z);
}
