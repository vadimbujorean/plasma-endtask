// SPDX-License-Identifier: GPL-2.0-or-later
#include <QApplication>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QAction>
#include <QIcon>
#include <QImage>
#include <QPalette>
#include <QTextStream>
#include <cmath>
#include <memory>

struct PaletteCase { const char *name; QColor text; QColor background; };

int main(int argc, char **argv) {
    QApplication app(argc, argv);
    QTextStream out(stdout), err(stderr);
    if (argc != 2) {
        err << "Usage: menu-icon-check /path/to/menu-icon.qml\n";
        return 1;
    }
    QQmlEngine engine;
    QQmlComponent component(&engine, QUrl::fromLocalFile(QString::fromLocal8Bit(argv[1])));
    std::unique_ptr<QObject> item(component.create());
    if (!item) {
        for (const auto &error : component.errors()) err << error.toString() << '\n';
        return 2;
    }
    QAction *action = item->property("action").value<QAction *>();
    if (!action) {
        err << "The KDE menu item did not create an action.\n";
        return 3;
    }
    // Reuse the same menu item to prove that live palette changes refresh it.
    const PaletteCase cases[] = {
        {"dark", QColor("#fcfcfc"), QColor("#232629")},
        {"light", QColor("#232629"), QColor("#fcfcfc")},
        {"custom", QColor("#3daee9"), QColor("#202020")},
        {"dark-again", QColor("#fcfcfc"), QColor("#232629")},
    };
    for (const auto &test : cases) {
        QPalette palette = app.palette();
        palette.setColor(QPalette::WindowText, test.text);
        palette.setColor(QPalette::Text, test.text);
        palette.setColor(QPalette::Window, test.background);
        palette.setColor(QPalette::Base, test.background);
        app.setPalette(palette);
        app.processEvents();
        if (action->icon().isNull()) {
            err << "The End Task icon is empty for palette " << test.name << '\n';
            return 4;
        }
        const QImage image = action->icon().pixmap(32, 32).toImage();
        int samples = 0;
        for (int y = 0; y < image.height(); ++y) {
            for (int x = 0; x < image.width(); ++x) {
                const QColor color = image.pixelColor(x, y);
                // Ignore antialiased edge pixels where unpremultiplication rounds RGB.
                if (color.alpha() < 240) continue;
                ++samples;
                if (std::abs(color.red() - test.text.red()) > 2
                    || std::abs(color.green() - test.text.green()) > 2
                    || std::abs(color.blue() - test.text.blue()) > 2) {
                    err << "Palette " << test.name << ": expected " << test.text.name()
                        << ", rendered " << color.name() << '\n';
                    return 5;
                }
            }
        }
        if (samples == 0) {
            err << "No visible icon pixels for palette " << test.name << '\n';
            return 6;
        }
        out << "PASS: " << test.name << " palette renders " << test.text.name()
            << " (" << samples << " color samples).\n";
    }
    return 0;
}
