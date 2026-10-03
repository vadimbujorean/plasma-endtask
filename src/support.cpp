// SPDX-License-Identifier: GPL-2.0-or-later
#include <QCoreApplication>
#include <QQmlExtensionPlugin>
#include <QQmlEngine>
#include <QLibrary>
#include <QLibraryInfo>
#include <QProcess>
#include <QVariantList>
#include <QDir>
#include <QUrl>
#include <QSet>
#include <cmath>

static QString helperPath;
class ProcessController : public QObject {
    Q_OBJECT
public:
    using QObject::QObject;
    Q_INVOKABLE bool requestTermination(const QVariantList &pids) {
        QStringList arguments;
        QSet<qint64> seen;
        for (const QVariant &value : pids) {
            bool ok = false;
            const double number = value.toDouble(&ok);
            if (!ok || !std::isfinite(number) || number <= 1 || number > 2147483647 || std::floor(number) != number) continue;
            const qint64 pid = static_cast<qint64>(number);
            if (pid == QCoreApplication::applicationPid() || seen.contains(pid)) continue;
            seen.insert(pid);
            arguments.append(QString::number(pid));
        }
        if (arguments.isEmpty()) return false;
        return QProcess::startDetached(helperPath, arguments);
    }
};

class EndTaskSupportPlugin : public QQmlExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)
public:
    void registerTypes(const char *uri) override {
        // Plasma 6.7 embeds the task manager's native QML types and resources
        // in its applet library. Keep it loaded for the entire process lifetime.
        static QLibrary original(QDir(QLibraryInfo::path(QLibraryInfo::PluginsPath)).filePath("plasma/applets/org.kde.plasma.taskmanager.so"));
        original.setLoadHints(QLibrary::PreventUnloadHint);
        if (!original.load()) {
            qWarning("Cannot load KDE task manager: %s", qPrintable(original.errorString()));
            return;
        }
        helperPath = QDir(baseUrl().toLocalFile()).filePath("endtask-helper");
        qmlRegisterType<ProcessController>(uri, 1, 0, "ProcessController");
    }
};
#include "support.moc"
