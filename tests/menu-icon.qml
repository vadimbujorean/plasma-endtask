// SPDX-License-Identifier: GPL-2.0-or-later
import org.kde.plasma.extras as PlasmaExtras

PlasmaExtras.MenuItem {
    text: "End Task"
    icon: decodeURIComponent(Qt.resolvedUrl("../package/contents/icons/end-task-white.svg").toString().replace("file://", ""))
}
