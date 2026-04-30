cmake_minimum_required(VERSION 3.16)

project(PTZCamTools VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)

qt_add_executable(PTZCamTools
    main.cpp
    mainwindow.h
    mainwindow.cpp
)

qt_add_qml_module(PTZCamTools
    URI PTZCamTools
    VERSION 1.0
)

set_target_properties(PTZCamTools PROPERTIES
    WIN32_EXECUTABLE TRUE
    MACOSX_BUNDLE TRUE
)

target_link_libraries(PTZCamTools PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
)

# Windows-specific
if(WIN32)
    set_property(TARGET PTZCamTools PROPERTY WIN32_EXECUTABLE TRUE)
endif()

# macOS-specific
if(APPLE)
    set_property(TARGET PTZCamTools PROPERTY MACOSX_BUNDLE TRUE)
endif()
