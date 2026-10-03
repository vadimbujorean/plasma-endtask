// SPDX-License-Identifier: GPL-2.0-or-later
#include <QCoreApplication>
#include <QLibrary>
#include <QLibraryInfo>
#include <QDir>
#include <QFile>
#include <QTextStream>
#include <sys/syscall.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>

int main(int argc, char **argv) {
    QCoreApplication app(argc, argv);
    QTextStream out(stdout), err(stderr);
    const QString path = QDir(QLibraryInfo::path(QLibraryInfo::PluginsPath))
        .filePath("plasma/applets/org.kde.plasma.taskmanager.so");
    QLibrary original(path);
    if (!original.load()) {
        err << "Native Task Manager unavailable: " << path << '\n'
            << original.errorString() << '\n'
            << "Install the supported plasma-desktop version and its matching Qt6 libraries.\n";
        return 1;
    }
    const QString prefix = ":/qt/qml/plasma/applet/org/kde/plasma/taskmanager/";
    if (!QFile::exists(prefix + "main.qml") || !QFile::exists(prefix + "main.xml")) {
        err << "Unsupported KDE resource layout. This project requires Plasma 6.7.x.\n";
        return 2;
    }
    const int fd = syscall(SYS_pidfd_open, getpid(), 0);
    if (fd < 0) {
        err << "pidfd_open unavailable: " << strerror(errno)
            << ". Linux >= 5.3 with pidfd access is required.\n";
        return 3;
    }
    const int signalResult = syscall(SYS_pidfd_send_signal, fd, 0, nullptr, 0);
    const int signalError = errno;
    close(fd);
    if (signalResult != 0) {
        err << "pidfd_send_signal unavailable: " << strerror(signalError) << '\n';
        return 4;
    }
    out << "KDE runtime and pidfd support available; Qt " << QT_VERSION_STR << '\n';
    return 0;
}
