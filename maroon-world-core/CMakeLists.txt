cmake_minimum_required(VERSION 3.20)
project(maroon-world-core VERSION 4.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(maroon-world src/main.cpp)

# Godot GDExtension (when integrated)
# find_package(GodotCpp REQUIRED)
# target_link_libraries(maroon-world PRIVATE godot::cpp)
