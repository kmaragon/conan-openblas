#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
from glob import glob
import os


class openblasConan(ConanFile):
    name = "openblas"
    version = "0.2.20"
    url = "https://github.com/xianyi/OpenBLAS"
    homepage = "http://www.openblas.net/"
    description = "OpenBLAS is an optimized BLAS library based on GotoBLAS2 1.13 BSD version."
    license = "BSD 3-Clause"
    exports_sources = ["CMakeLists.txt", "LICENSE"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "USE_MASS": [True, False],
               "USE_OPENMP": [True, False],
               "NO_LAPACKE": [True, False]
              }
    default_options = "shared=True", "USE_MASS=False", "USE_OPENMP=False", "NO_LAPACKE=False"

    def get_make_arch(self):
        return "32" if self.settings.arch == "x86" else "64"

    def get_make_build_type_debug(self):
        return "0" if self.settings.build_type == "Release" else "1"

    def get_make_option_value(self, option):
        return "1" if option else "0"

    def configure(self):
        if self.settings.compiler == "Visual Studio":
            if not self.options.shared:
                raise Exception("Static build not supported in Visual Studio: "
                                "https://github.com/xianyi/OpenBLAS/blob/v0.2.20/CMakeLists.txt#L177")

    def source(self):
        self.output.info("source()")
        source_url = "https://sourceforge.net/projects/openblas"
        file_name = ("{0} {1} version".format("OpenBLAS", self.version))
        tools.get("{0}/files/v{1}/{2}.tar.gz".format(source_url, self.version, file_name))
        os.rename(glob("xianyi-OpenBLAS-*")[0], "sources")

    def build(self):
        if self.settings.compiler != "Visual Studio":
            make_options = "DEBUG={0} NO_SHARED={1} BINARY={2} NO_LAPACKE={3} USE_MASS={4} USE_OPENMP={5}".format(
                self.get_make_build_type_debug(),
                self.get_make_option_value(not self.options.shared),
                self.get_make_arch(),
                self.get_make_option_value(self.options.NO_LAPACKE),
                self.get_make_option_value(self.options.USE_MASS),
                self.get_make_option_value(self.options.USE_OPENMP))
            self.run("cd sources && make %s" % make_options, cwd=self.source_folder)
        else:
            self.output.warn("Building with CMake: Some options won't make any effect")
            cmake = CMake(self)
            cmake.definitions["USE_MASS"] = self.options.USE_MASS
            cmake.definitions["USE_OPENMP"] = self.options.USE_OPENMP
            cmake.definitions["NO_LAPACKE"] = self.options.NO_LAPACKE
            cmake.configure(source_dir="sources")
            cmake.build()

    def package(self):
        with tools.chdir("sources"):
            self.copy(pattern="LICENSE", dst="licenses", src="sources",
                      ignore_case=True, keep_path=False)

            if self.settings.compiler == "Visual Studio":
                self.copy(pattern="*.h", dst="include", src=".")
            else:
                self.copy(pattern="*.h", dst="include", src="sources")

            self.copy(pattern="*.dll", dst="bin", src="lib", keep_path=False)
            self.copy(pattern="*.so*", dst="lib", src="lib", keep_path=False)
            self.copy(pattern="*.dylib", dst="lib", src="lib", keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src="lib", keep_path=False)
            self.copy(pattern="*.a", dst="lib", src=".", keep_path=False)
            self.copy(pattern="*.a", dst="lib", src="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
