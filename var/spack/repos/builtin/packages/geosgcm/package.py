# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Geosgcm(CMakePackage):
    """
    GEOS Earth System Model GEOSgcm Fixture
    """

    homepage = "https://github.com/GEOS-ESM/GEOSgcm"
    url = "https://github.com/GEOS-ESM/GEOSgcm/archive/refs/tags/v11.5.2.tar.gz"
    list_url = "https://github.com/GEOS-ESM/GEOSgcm/tags"
    git = "https://github.com/GEOS-ESM/GEOSgcm.git"

    maintainers("mathomp4", "tclune")

    version("main", branch="main")

    variant("debug", default=False, description="Build with debugging")
    variant("f2py", default=False, description="Build with f2py support")
    variant("extdata2g", default=True, description="Use ExtData2G")
    variant(
        "develop",
        default=False,
        description="Update GEOSgcm_GridComp GEOSgcm_App GMAO_Shared GEOS_Util "
        "subrepos to their develop branches (used internally for testing)",
    )

    variant(
        "build_type",
        default="Release",
        description="The build type to build",
        values=("Debug", "Release", "Aggressive"),
    )

    depends_on("cmake@3.17:", type="build")
    depends_on("ecbuild", type="build")

    depends_on("mpi")

    # These are for MAPL AGC and stubber
    depends_on("python@3:")
    depends_on("py-pyyaml")
    depends_on("py-numpy")
    depends_on("perl")

    # These are similarly the dependencies of MAPL. Not sure if we'll ever use MAPL as library
    depends_on("hdf5")
    depends_on("netcdf-c")
    depends_on("netcdf-fortran")
    depends_on("esmf@8.6.1:")
    depends_on("esmf~debug", when="~debug")
    depends_on("esmf+debug", when="+debug")

    depends_on("gftl@1.13.0:")
    depends_on("gftl-shared@1.8.0:")
    depends_on("pflogger@1.14.0:")
    depends_on("fargparse@1.7.0:")

    # when using apple-clang version 15.x or newer, need to use the llvm-openmp library
    depends_on("llvm-openmp", when="%apple-clang@15:", type=("build", "run"))

    # MAPL as library would be like:
    #  depends_on("mapl@2.46.1")
    # but we don't want to do this in general due to the speed of MAPL development

    # When we move to FMS as library, we'll need to add something like this:
    # depends_on("fms@2024.01:~gfs_phys+fpic~quad_precision+32bit+64bit+yaml constants=GEOS")

    # We also depend on mepo
    depends_on("mepo", type="build")

    @run_before("cmake")
    def clone_mepo(self):
        with working_dir(self.stage.source_path):
            # Now we need to run "mepo clone" which is a python script
            # that will clone the other repositories that are needed

            # First we need the path to the mepo script
            mepo = self.spec["mepo"].command

            # Note: Some of the repos used by GEOSgcm have big histories
            #       and it was found that blobless clones can save a lot of
            #       time
            mepo("clone", "--partial=blobless")

    def cmake_args(self):
        args = [
            self.define_from_variant("USE_F2PY", "f2py"),
            self.define_from_variant("USE_EXTDATA2G", "extdata2g"),
            self.define("CMAKE_MODULE_PATH", self.spec["esmf"].prefix.cmake),
        ]

        # Compatibility flags for gfortran
        fflags = []
        if self.compiler.name in ["gcc", "clang", "apple-clang"]:
            fflags.append("-ffree-line-length-none")
            gfortran_major_ver = int(
                spack.compiler.get_compiler_version_output(self.compiler.fc, "-dumpversion").split(
                    "."
                )[0]
            )
            if gfortran_major_ver >= 10:
                fflags.append("-fallow-invalid-boz")
                fflags.append("-fallow-argument-mismatch")
        if fflags:
            args.append(self.define("CMAKE_Fortran_FLAGS", " ".join(fflags)))

        # Scripts often need to know the MPI stack used to setup the environment.
        # Normally, we can autodetect this, but building with Spack does not
        # seem to work. We need to pass in the MPI stack used to CMake
        # via -DMPI_STACK on the CMake command line. We use the following
        # names for the MPI stacks:
        #
        # - MPICH --> mpich
        # - Open MPI --> openmpi
        # - Intel MPI --> intelmpi
        # - MVAPICH --> mvapich
        # - HPE MPT --> mpt

        if self.spec.satisfies("^mpich"):
            args.append(self.define("MPI_STACK", "mpich"))
        elif self.spec.satisfies("^openmpi"):
            args.append(self.define("MPI_STACK", "openmpi"))
        elif self.spec.satisfies("^intel-oneapi-mpi"):
            args.append(self.define("MPI_STACK", "intelmpi"))
        elif self.spec.satisfies("^mvapich"):
            args.append(self.define("MPI_STACK", "mvapich"))
        elif self.spec.satisfies("^mpt"):
            args.append(self.define("MPI_STACK", "mpt"))
        else:
            raise InstallError("Unsupported MPI stack")

        return args

    def setup_build_environment(self, env):
        # esma_cmake, an internal dependency of mapl, is
        # looking for the cmake argument -DBASEDIR, and
        # if it doesn't find it, it's looking for an
        # environment variable with the same name. This
        # name is common and used all over the place,
        # and if it is set it breaks the mapl build.
        env.unset("BASEDIR")
