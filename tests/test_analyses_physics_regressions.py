# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Regression tests for analysis formulas, checked against closed-form physics."""

import unittest

import numpy as np
from scipy.integrate import trapezoid

from qiskit_metal.analyses.hamiltonian.HO_wavefunctions import wavefunction


class TestHOWavefunction(unittest.TestCase):
    """HO_wavefunctions.wavefunction (#1202)."""

    def test_normalized_and_orthogonal(self):
        x = np.linspace(-15, 15, 30001)
        for L, C in [(1.0, 1.0), (4.0, 1.0), (0.3, 2.5)]:
            psis = [wavefunction(L, C, n, x) for n in range(8)]
            for m, pm in enumerate(psis):
                for n, pn in enumerate(psis):
                    overlap = trapezoid(pm * pn, x)
                    self.assertAlmostEqual(overlap, float(m == n), places=6)

    def test_width_uses_omega_one_over_sqrt_lc(self):
        # Charge is the coordinate, L the mass: <q^2>_n = (n + 1/2) hbar/(L w)
        # with w = 1/sqrt(LC), i.e. (n + 1/2) sqrt(C/L).
        L, C = 4.0, 1.0
        x = np.linspace(-20, 20, 40001)
        for n in range(4):
            var = trapezoid(x**2 * wavefunction(L, C, n, x) ** 2, x)
            self.assertAlmostEqual(var, (n + 0.5) * np.sqrt(C / L), places=6)

    def test_ground_state_peak(self):
        # psi_0(0) = (L w / pi hbar)^(1/4) -> pi^(-1/4) for L = C = 1.
        self.assertAlmostEqual(wavefunction(1.0, 1.0, 0, 0.0), np.pi**-0.25)

    def test_si_units(self):
        from scipy.constants import hbar

        L, C = 12e-9, 65e-15
        q_zpf = np.sqrt(hbar / (2 * np.sqrt(L / C)))
        x = np.linspace(-12 * q_zpf, 12 * q_zpf, 20001)
        psi = wavefunction(L, C, 0, x, hbar=hbar)
        self.assertAlmostEqual(trapezoid(psi**2, x), 1.0, places=6)


class TestHcpbParamsFromFreqFixEC(unittest.TestCase):
    """Hcpb.params_from_freq_fixEC inverts fij(0, 1) at fixed Ec (#1203)."""

    def test_recovers_ej(self):
        from qiskit_metal.analyses.hamiltonian.transmon_charge_basis import Hcpb

        # Tutorial 4.34 numbers (MHz), plus a less transmon-like point.
        for ej, ec, ng in [(13971.3, 295.2, 0.5), (2500.0, 400.0, 0.0)]:
            f01 = Hcpb(nlevels=15, Ej=ej, Ec=ec, ng=ng).fij(0, 1)
            h = Hcpb(nlevels=15, Ej=1.0, Ec=ec, ng=ng)
            ej_fit = h.params_from_freq_fixEC(f01, ec)
            self.assertAlmostEqual(ej_fit / ej, 1.0, places=6)
            self.assertAlmostEqual(h.fij(0, 1), f01, places=4)
