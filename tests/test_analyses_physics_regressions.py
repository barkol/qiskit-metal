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


class TestKappaIn(unittest.TestCase):
    """kappa_calculation.kappa_in uses angular frequencies (#1204)."""

    Z0 = 50.0

    def test_three_args_is_kappa_over_2pi(self):
        from qiskit_metal.analyses.em.kappa_calculation import kappa_in

        # kappa = (2/pi) w^2 C^2 Z0^2 w_r [rad/s] (Goeppl et al. 2008).
        f, cap, fr = 7e9, 6.81e-15, 7e9
        w, wr = 2 * np.pi * f, 2 * np.pi * fr
        kappa = (2 / np.pi) * w**2 * cap**2 * self.Z0**2 * wr
        self.assertAlmostEqual(kappa_in(f, cap, fr) / (kappa / (2 * np.pi)), 1.0)
        # About 1 MHz for this coupler, not 25 kHz.
        self.assertAlmostEqual(kappa_in(f, cap, fr) / 1e6, 0.99947, places=4)

    def test_six_args_uses_speed_of_light(self):
        from scipy.constants import c
        from scipy.special import ellipk

        from qiskit_metal.analyses.em.kappa_calculation import kappa_in

        width, gap, f, cap = 10e-6, 6e-6, 7e9, 6.81e-15
        k = width / (width + 2 * gap)
        # eps_eff of the 50 Ohm ideal CPW: Z = 30 pi K(k') / (sqrt(eps) K(k)).
        sqrt_eps = 30 * np.pi * ellipk(1 - k**2) / (self.Z0 * ellipk(k**2))
        length = c / (4 * f * sqrt_eps)  # quarter wave at f
        self.assertGreater(length, 4e-3)
        self.assertLess(length, 5e-3)
        self.assertAlmostEqual(
            kappa_in(f, cap, length, width, gap, 4.0) / kappa_in(f, cap, f), 1.0
        )

    def test_wrong_argument_count_raises(self):
        from qiskit_metal.analyses.em.kappa_calculation import kappa_in

        for n in (1, 2, 4, 5, 7):
            with self.assertRaises(TypeError):
                kappa_in(*([1.0] * n))
