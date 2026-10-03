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
#include <QGuiApplication>
#include <QEvent>
#include <QIcon>
#include <QPalette>
#include <KIconColors>
#include <KIconLoader>
#include <cmath>

static QString helperPath;
static QString iconPath;
class ProcessController : public QObject {
    Q_OBJECT
    Q_PROPERTY(QIcon endTaskIcon READ endTaskIcon NOTIFY endTaskIconChanged)
public:
    explicit ProcessController(QObject *parent = nullptr) : QObject(parent) {
        if (auto *application = QCoreApplication::instance()) {
            application->installEventFilter(this);
        }
    }
    QIcon endTaskIcon() const {
        const QPalette palette = QGuiApplication::palette();
        KIconColors colors(palette);
        colors.setText(palette.color(QPalette::Active, QPalette::WindowText));
        // Force KDE's symbolic SVG recoloring even when loading an absolute path.
        return KDE::icon(iconPath, colors);
    }
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
Q_SIGNALS:
    void endTaskIconChanged();
protected:
    bool eventFilter(QObject *, QEvent *event) override {
        if (event->type() == QEvent::ApplicationPaletteChange
            || event->type() == QEvent::ThemeChange
            || event->type() == QEvent::StyleChange) {
            Q_EMIT endTaskIconChanged();
        }
        return false;
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
        const QDir supportDir(baseUrl().toLocalFile());
        helperPath = supportDir.filePath("endtask-helper");
        iconPath = QDir::cleanPath(supportDir.filePath("../../icons/end-task.svg"));
        qmlRegisterType<ProcessController>(uri, 1, 0, "ProcessController");
    }
};
#include "support.moc"
