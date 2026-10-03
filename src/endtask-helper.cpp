// SPDX-License-Identifier: GPL-2.0-or-later
#include <QApplication>
#include <QMessageBox>
#include <QPushButton>
#include <QFile>
#include <QSet>
#include <QStringList>
#include <QTextStream>
#include <QProcess>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <unistd.h>
#include <signal.h>
#include <cerrno>
#include <cstring>
#include <vector>

struct Target { int pid; int fd; QString name; };

int main(int argc, char **argv) {
    QApplication app(argc, argv);
    app.setApplicationName("End Task");
    app.setQuitOnLastWindowClosed(false);
    QStringList arguments = app.arguments().mid(1);
    const bool checkOnly = arguments.removeOne("--check");
    std::vector<Target> targets;
    QSet<int> seen;
    for (const QString &argument : arguments) {
        bool ok = false;
        const int pid = argument.toInt(&ok);
        if (!ok || pid <= 1 || pid == getpid() || seen.contains(pid)) continue;
        seen.insert(pid);
        const int fd = syscall(SYS_pidfd_open, pid, 0);
        if (fd < 0) continue;
        struct stat info {};
        const QByteArray directory = QString("/proc/%1").arg(pid).toLocal8Bit();
        if (stat(directory.constData(), &info) != 0 || info.st_uid != getuid()) {
            close(fd);
            continue;
        }
        QFile comm(QString("/proc/%1/comm").arg(pid));
        if (!comm.open(QIODevice::ReadOnly)) { close(fd); continue; }
        const QString name = QString::fromLocal8Bit(comm.readAll()).trimmed();
        // Do not allow this menu to bring down the desktop or compositor.
        if (name == "plasmashell" || name == "kwin_wayland" || name == "kwin_x11") {
            close(fd);
            continue;
        }
        if (syscall(SYS_pidfd_send_signal, fd, 0, nullptr, 0) != 0) { close(fd); continue; }
        targets.push_back({pid, fd, name});
    }
    if (checkOnly) {
        QTextStream out(stdout);
        for (const auto &target : targets) {
            out << target.pid << ' ' << target.name << '\n';
            close(target.fd);
        }
        return targets.empty() ? 1 : 0;
    }
    if (targets.empty()) {
        QMessageBox::information(nullptr, "End Task", "No eligible process found. The app may have already closed, or its PID is unavailable.");
        return 0;
    }
    QStringList descriptions;
    for (const auto &target : targets) descriptions.append(QString("%1 (PID %2)").arg(target.name).arg(target.pid));
    QMessageBox question(QMessageBox::Warning, "End Task",
        "Force-quit these processes?\n\n" + descriptions.join('\n') +
        "\n\nUnsaved data will be lost. All windows managed by these processes will close, including windows on other desktops.",
        QMessageBox::NoButton);
    question.setTextFormat(Qt::PlainText);
    auto *terminateButton = question.addButton("End Task", QMessageBox::DestructiveRole);
    auto *cancelButton = question.addButton("Cancel", QMessageBox::RejectRole);
    question.setDefaultButton(cancelButton);
    question.setEscapeButton(cancelButton);
    question.exec();
    QStringList errors;
    if (question.clickedButton() == terminateButton) {
        for (const auto &target : targets) {
            // A pidfd refers to the original process, never to a reused PID.
            if (syscall(SYS_pidfd_send_signal, target.fd, SIGKILL, nullptr, 0) != 0 && errno != ESRCH)
                errors.append(QString("%1: %2").arg(target.name, QString::fromLocal8Bit(strerror(errno))));
        }
    }
    for (const auto &target : targets) close(target.fd);
    if (!errors.isEmpty()) QMessageBox::warning(nullptr, "End Task", errors.join('\n'));
    return errors.empty() ? 0 : 1;
}
