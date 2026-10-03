// Test-only dialog automation. Never installed with the widget.
#include <QMessageBox>
#include <QAbstractButton>
#include <QTimer>
#include <dlfcn.h>
#include <cstdlib>

int QDialog::exec() {
    using Exec = int (*)(QDialog *);
    static auto original = reinterpret_cast<Exec>(dlsym(RTLD_NEXT, "_ZN7QDialog4execEv"));
    QTimer::singleShot(0, this, [this] {
        const bool accept = qEnvironmentVariable("ENDTASK_TEST_CHOICE") == "terminate";
        auto *box = qobject_cast<QMessageBox *>(this);
        if (!box) { reject(); return; }
        for (auto *button : box->buttons()) {
            if (box->buttonRole(button) == (accept ? QMessageBox::DestructiveRole : QMessageBox::RejectRole)) {
                button->click();
                return;
            }
        }
        reject();
    });
    return original(this);
}
