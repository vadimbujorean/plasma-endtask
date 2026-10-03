#include <QApplication>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QDebug>
#include <QTextStream>
#include <QTimer>
int main(int argc, char **argv) {
    QApplication app(argc, argv);
    QQmlEngine engine;
    QQmlComponent component(&engine, QUrl::fromLocalFile(QString::fromLocal8Bit(argv[1])));
    QTextStream out(stdout);
    if (component.isError()) {
        for (const auto &error : component.errors()) out << error.toString() << '\n';
        return 1;
    }
    if (argc > 2 && QString::fromLocal8Bit(argv[2]) == "--compile-only") {
        out << "QML_COMPILE_OK\n";
        return 0;
    }
    QObject *object = component.create();
    if (!object) {
        for (const auto &error : component.errors()) out << error.toString() << '\n';
        return 2;
    }
    out << "QML_CREATE_OK\n";
    if (argc > 2 && QString::fromLocal8Bit(argv[2]) == "--wait") {
        QTimer::singleShot(1500, &app, &QCoreApplication::quit);
        app.exec();
    }
    delete object;
    return 0;
}
