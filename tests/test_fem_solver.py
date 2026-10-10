# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""The package-mode solver: analytic models (analyses/em/package_modes.py)
and the scikit-fem Maxwell solver (analyses/fem). Tier 0: the finite-element
check is an empty box on a coarse mesh; it is skipped without gmsh and
scikit-fem."""

import subprocess
import sys
import unittest

import numpy as np

from qiskit_metal.analyses.em import package_modes as pm

C0 = 299792458.0


def _fem_available():
    try:
        import gmsh  # noqa: F401
        import skfem  # noqa: F401

        return True
    except Exception:
        return False


class TestAnalyticPackageModes(unittest.TestCase):
    def test_lsm_mode_of_the_paper_device(self):
        """30 x 30 x 3 mm box with 0.5 mm of silicon: 6.493 GHz (validation
        record in docs/architecture/open_fem_scikit_fem.md)."""
        mode = pm.lsm_mode(1, 1, Lx=30, Ly=30, Lz=3, t=0.5, eps_r=11.9)
        self.assertAlmostEqual(mode.f / 1e9, 6.493, places=2)
        approx = pm.lsm_mode_approx(1, 1, Lx=30, Ly=30, Lz=3, t=0.5, eps_r=11.9)
        self.assertLess(abs(approx["f"] / mode.f - 1), 0.02)

    def test_approx_warns_outside_validity(self):
        # follow-up to #1211: k_z,Si t << 1 is the validity condition
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            pm.lsm_mode_approx(1, 1, Lx=30, Ly=30, Lz=3, t=0.5, eps_r=11.45)
        with self.assertWarnsRegex(UserWarning, "validity"):
            pm.lsm_mode_approx(1, 1, Lx=5, Ly=5, Lz=3, t=0.5, eps_r=11.45)

    def test_without_the_slab_it_is_the_box_mode(self):
        mode = pm.lsm_mode(1, 1, Lx=30, Ly=30, Lz=3, t=1e-6, eps_r=11.9)
        tm110 = C0 / 2 * np.hypot(1 / 30e-3, 1 / 30e-3)
        self.assertLess(abs(mode.f / tm110 - 1), 1e-4)

    def test_small_boxes_give_the_lowest_root(self):
        """The bracket stays below the tan(k_s t) pole (#1211): a 4 mm box
        raised ValueError and a 2 mm box returned a higher-order root."""
        eps_r = 11.45
        f_prev = 0.0
        for L in (12, 8, 6, 5, 4, 3, 2):
            mode = pm.lsm_mode(1, 1, L, L, 3.0, 0.5, eps_r)
            ks_t = mode.kz_si * mode.t
            self.assertLess(ks_t, np.pi / 2)  # fundamental branch
            residual = mode.kz_si * np.tan(ks_t) - eps_r * mode.kz_air * np.tanh(
                mode.kz_air * (mode.Lz - mode.t)
            )
            self.assertLess(abs(residual) / mode.kz_si, 1e-6)
            self.assertGreater(mode.f, f_prev)  # smaller box, higher mode
            f_prev = mode.f
        self.assertAlmostEqual(
            pm.lsm_mode(1, 1, 2, 2, 3.0, 0.5, eps_r).f / 1e9, 51.33, places=2
        )
        self.assertAlmostEqual(
            pm.lsm_mode(1, 1, 12, 12, 3.0, 0.5, eps_r).f / 1e9, 16.072, places=3
        )

    def test_uncoupled_circuit_frequencies(self):
        C = np.diag([100e-15, 200e-15])
        L = np.diag([10e-9, 5e-9])
        expected = sorted(1 / np.sqrt(np.diag(L) * np.diag(C)))  # rad/s
        f = sorted(np.ravel(pm.circuit_eigenfrequencies(C, L)))
        np.testing.assert_allclose(f, expected, rtol=1e-12)

    def test_grid_and_amplitude_fit(self):
        centers = pm.qubit_centers(2, 3.0)
        self.assertEqual(centers[(1, 0)], (4.5, 1.5))
        n, Lx = 4, 12.0
        g = np.zeros((n, n))
        for (i, j), (x, y) in pm.qubit_centers(n, Lx / n).items():
            g[j, i] = 2.5 * np.cos(np.pi * x / Lx) * np.sin(np.pi * y / Lx)
        A, residual = pm.fit_amplitude(g, 1, 1, Lx, Lx)
        self.assertAlmostEqual(A, 2.5)
        self.assertLess(residual, 1e-12)

    def test_importing_the_solver_needs_no_scikit_fem(self):
        code = (
            "import sys; import qiskit_metal.analyses.fem as f; "
            "print('skfem' in sys.modules, 'gmsh' in sys.modules)"
        )
        out = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        )
        self.assertEqual(out.stdout.split()[-2:], ["False", "False"])


@unittest.skipUnless(_fem_available(), "gmsh and scikit-fem not installed")
class TestMaxwellFEM(unittest.TestCase):
    def test_empty_box_mode(self):
        """TM110 of an empty 6 x 6 x 3 mm box on a coarse mesh, within 3 %."""
        from qiskit_metal.analyses.fem import MaxwellFEM, Package, mesh_package

        box = Package(Lx=6.0, Ly=6.0, Lz=3.0, t=0.5, eps_r=1.0, metals={}, junctions={})
        mesh = mesh_package(box, h_max=0.6, pads=False, substrate=False)
        f = MaxwellFEM(mesh).eigenmodes(35e9, n=1)[0].f
        tm110 = C0 / 2 * np.hypot(1 / 6e-3, 1 / 6e-3)
        self.assertLess(
            abs(f / tm110 - 1), 0.03, f"{f / 1e9:.3f} GHz vs {tm110 / 1e9:.3f}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


@unittest.skipUnless(_fem_available(), "gmsh and scikit-fem not installed")
class TestMeshReproducible(unittest.TestCase):
    """mesh_package(threads=1) gives identical meshes (MPK: fem_mesh_reproducibility)."""

    def test_single_thread_is_deterministic(self):
        from qiskit_metal.analyses.fem import Package, mesh_package

        def rect(x0, y0, w, h):
            return np.array([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)])

        pkg = Package(
            4.0,
            4.0,
            3.0,
            0.5,
            11.45,
            {"pad_a": rect(1.5, 1.4, 1.0, 0.5), "pad_b": rect(1.5, 2.1, 1.0, 0.5)},
            {"Q": ((2.0, 1.9), (2.0, 2.1))},
        )
        meshes = [
            mesh_package(pkg, h_metal=0.05, h_max=0.8, threads=1) for _ in range(2)
        ]
        np.testing.assert_array_equal(meshes[0].p, meshes[1].p)
        np.testing.assert_array_equal(meshes[0].t, meshes[1].t)


class TestPackageFromDesignErrors(unittest.TestCase):
    """package_from_design explains what is missing and warns about dropped
    ground-plane cuts (MPK: fem_package_from_design_errors)."""

    def test_messages(self):
        import logging

        import qiskit_metal as qm
        from qiskit_metal import designs
        from qiskit_metal.analyses.fem import package_from_design
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

        qm.logger.setLevel(logging.ERROR)
        planar = designs.DesignPlanar()
        TransmonPocket(planar, "Q1")
        with self.assertRaisesRegex(TypeError, "MultiPlanar"):
            package_from_design(planar, 11.45)

        multi = MultiPlanar()
        multi.overwrite_enabled = True
        TransmonPocket(multi, "Q1")
        with self.assertRaisesRegex(KeyError, "sample_holder_top"):
            package_from_design(multi, 11.45)

        multi.variables["sample_holder_top"] = "2.25mm"
        multi.variables["sample_holder_bottom"] = "0.75mm"
        with self.assertWarnsRegex(UserWarning, "Q1.rect_pk"):
            package = package_from_design(multi, 11.45)
        self.assertEqual(sorted(package.metals), ["Q1.pad_bot", "Q1.pad_top"])


@unittest.skipUnless(_fem_available(), "gmsh and scikit-fem not installed")
class TestMeshKeepsCallerThreadLimits(unittest.TestCase):
    """mesh_package(threads=None) leaves the caller's per-dimension gmsh
    thread limits alone, so a single-thread setup stays reproducible
    (MPK: fem_mesh_threads_default)."""

    def tearDown(self):
        import gmsh

        if gmsh.isInitialized():
            gmsh.finalize()

    def test_single_thread_limits_survive_default_call(self):
        import gmsh

        from qiskit_metal.analyses.fem import Package, mesh_package

        def rect(x0, y0, w, h):
            return np.array([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)])

        pkg = Package(
            4.0,
            4.0,
            3.0,
            0.5,
            11.45,
            {"pad_a": rect(1.5, 1.4, 1.0, 0.5), "pad_b": rect(1.5, 2.1, 1.0, 0.5)},
            {"Q": ((2.0, 1.9), (2.0, 2.1))},
        )
        if not gmsh.isInitialized():
            gmsh.initialize()
        limits = {f"Mesh.MaxNumThreads{d}D": 1 for d in (1, 2, 3)}
        for name, value in limits.items():
            gmsh.option.setNumber(name, value)
        meshes = [mesh_package(pkg, h_metal=0.05, h_max=0.8) for _ in range(2)]
        for name, value in limits.items():
            self.assertEqual(gmsh.option.getNumber(name), value, msg=name)
        np.testing.assert_array_equal(meshes[0].p, meshes[1].p)
        np.testing.assert_array_equal(meshes[0].t, meshes[1].t)
