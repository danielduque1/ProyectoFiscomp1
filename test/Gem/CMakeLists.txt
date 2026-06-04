# Use the code in this section for standalone projects
cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(Gem)
if(NOT TARGET Garfield::Garfield)
  find_package(Garfield REQUIRED)
endif()

# ---Build executable------------------------------------------------------------
add_executable(Gem gem.C)
target_link_libraries(Gem Garfield::Garfield)

add_executable(Gem_mt gem_mt.C)
target_link_libraries(Gem_mt Garfield::Garfield)

add_executable(Fieldlines fieldlines.C)
target_link_libraries(Fieldlines Garfield::Garfield)

# ---Copy all files locally to the build directory-------------------------------
foreach(_file ELIST.lis MPLIST.lis NLIST.lis PRNSOL.lis)
  configure_file(${_file} ${CMAKE_CURRENT_BINARY_DIR}/${_file} COPYONLY)
endforeach()
