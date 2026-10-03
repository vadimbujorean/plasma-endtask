// SPDX-License-Identifier: GPL-2.0-or-later
import org.kde.plasma.extras as PlasmaExtras
import "../package/contents/ui/support" as EndTaskSupport

PlasmaExtras.MenuItem {
    readonly property EndTaskSupport.ProcessController controller: EndTaskSupport.ProcessController {}
    text: "End Task"
    icon: controller.endTaskIcon
}
