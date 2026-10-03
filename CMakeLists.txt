# SPDX-License-Identifier: GPL-2.0-or-later
cmake_minimum_required(VERSION 3.21)
project(PlasmaEndTask VERSION 1.2.1 LANGUAGES CXX)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
    message(FATAL_ERROR "Plasma End Task requires Linux (pidfd support).")
endif()
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
find_package(Qt6 REQUIRED COMPONENTS Core Qml Widgets)

# Build a self-contained KPackage. No file in /usr is changed.
set(PACKAGE_DIR "${CMAKE_BINARY_DIR}/package")
# Refresh bundled icons and licenses to avoid stale copies on reconfigure.
file(REMOVE_RECURSE "${PACKAGE_DIR}/contents/icons" "${PACKAGE_DIR}/LICENSES")
file(COPY "${CMAKE_SOURCE_DIR}/package/" DESTINATION "${PACKAGE_DIR}")
file(COPY "${CMAKE_SOURCE_DIR}/LICENSE" "${CMAKE_SOURCE_DIR}/LICENSES"
    "${CMAKE_SOURCE_DIR}/THIRD_PARTY_NOTICES.md" DESTINATION "${PACKAGE_DIR}")
set(SUPPORT_DIR "${PACKAGE_DIR}/contents/ui/support")

add_library(endtasksupport MODULE src/support.cpp)
target_link_libraries(endtasksupport PRIVATE Qt6::Core Qt6::Qml)
set_target_properties(endtasksupport PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${SUPPORT_DIR}")
add_executable(endtask-helper src/endtask-helper.cpp)
target_link_libraries(endtask-helper PRIVATE Qt6::Widgets)
set_target_properties(endtask-helper PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${SUPPORT_DIR}")

add_executable(check-runtime src/check-runtime.cpp)
target_link_libraries(check-runtime PRIVATE Qt6::Core)
set_target_properties(check-runtime PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

option(BUILD_TESTING "Build isolated tests; not installed in the widget" OFF)
if(BUILD_TESTING)
    enable_testing()
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    add_executable(qml-check tests/qml-check.cpp)
    target_link_libraries(qml-check PRIVATE Qt6::Widgets Qt6::Qml)
    add_library(dialog-automation MODULE tests/dialog-automation.cpp)
    target_link_libraries(dialog-automation PRIVATE Qt6::Widgets ${CMAKE_DL_LIBS})
    add_test(NAME package-check
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tests/check-package.py" "${CMAKE_SOURCE_DIR}")
    add_test(NAME qml-compile
        COMMAND qml-check "${PACKAGE_DIR}/contents/ui/main.qml" --compile-only)
    set_tests_properties(qml-compile PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QT_FORCE_STDERR_LOGGING=1")
    add_test(NAME helper-safety
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tests/helper-safety.py"
            "$<TARGET_FILE:endtask-helper>" "$<TARGET_FILE:dialog-automation>")
    set_tests_properties(helper-safety PROPERTIES TIMEOUT 20)
    add_executable(menu-icon-check tests/menu-icon-check.cpp)
    target_link_libraries(menu-icon-check PRIVATE Qt6::Widgets Qt6::Qml)
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/tests")
    configure_file(tests/menu-icon.qml "${CMAKE_BINARY_DIR}/tests/menu-icon.qml" COPYONLY)
    add_test(NAME white-menu-icon
        COMMAND menu-icon-check "${CMAKE_BINARY_DIR}/tests/menu-icon.qml")
    set_tests_properties(white-menu-icon PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QT_FORCE_STDERR_LOGGING=1")
endif()
