# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Mepo(Package):
    """Tool to manage (m)ultiple git r(epo)sitories"""

    homepage = "https://github.com/GEOS-ESM/mepo"
    url = "https://github.com/GEOS-ESM/mepo/archive/refs/tags/v1.51.1.tar.gz"

    maintainers("mathomp4", "pchakraborty", "climbfuji")

    version("1.52.0", sha256="553876e9ce13484e25abb2e93b261e9f69b529cd4a62070b23dcbd0115b89ad9")
    version("1.51.1", sha256="543c1e7487afb2d62e5e8c8a2f69a85af1b1951f588f3dfc7471763e90847360")

    depends_on("python", type="run")
    depends_on("py-pyyaml@5.4:", type="run")

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install_tree(".", prefix)
        # Symlink mepo to bin directory
        symlink(join_path(prefix, "mepo"), join_path(prefix.bin, "mepo"))
