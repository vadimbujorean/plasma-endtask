// SPDX-License-Identifier: GPL-2.0-or-later
#include <QApplication>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QAction>
#include <QIcon>
#include <QImage>
#include <QTextStream>
#include <memory>

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
    if (!action || action->icon().isNull()) {
        err << "The KDE menu item did not load the bundled icon.\n";
        return 3;
    }
    const QImage image = action->icon().pixmap(32, 32).toImage();
    int painted = 0;
    for (int y = 0; y < image.height(); ++y) {
        for (int x = 0; x < image.width(); ++x) {
            const QColor color = image.pixelColor(x, y);
            if (color.alpha() == 0) continue;
            ++painted;
            if (color.red() != 255 || color.green() != 255 || color.blue() != 255) {
                err << "The rendered End Task icon is not white.\n";
                return 4;
            }
        }
    }
    if (painted == 0) {
        err << "The rendered End Task icon is empty.\n";
        return 5;
    }
    out << "PASS: KDE menu icon renders white (" << painted << " painted pixels).\n";
    return 0;
}
