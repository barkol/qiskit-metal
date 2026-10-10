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
"""This code calculations the wavefunction(s) of the simple harmonic oscillator
corresponding to an LC circuit.

Key References:
    - *R. Shankar*, "Principles of Quantum Mechanics", Second Edition, Springer (1994)
    - or any other undergraduate quantum mechanics textbook)
"""

from math import factorial, pi, sqrt

import numpy as np
from scipy.special import eval_hermite

__all__ = ["wavefunction"]


def wavefunction(L, C, n, x, hbar=1.0):
    r"""Return the nth normalized wavefunction of the LC harmonic oscillator.

    The charge :math:`x` is the coordinate and the inductance plays the role
    of the mass (:math:`H = L\dot{q}^2/2 + q^2/2C`), so with
    :math:`\omega = 1/\sqrt{LC}` and :math:`\xi = \sqrt{L\omega/\hbar}\,x`

    .. math::

        \psi_n(x) = \frac{1}{\sqrt{2^n n!}}
        \left(\frac{L\omega}{\pi\hbar}\right)^{1/4}
        e^{-\xi^2/2} H_n(\xi),

    normalized so that :math:`\int |\psi_n(x)|^2 dx = 1`.

    Args:
        L (float): The inductance of the inductor in an LC circuit.
        C (float): The capacitance of the capacitor in an LC circuit.
        n (int): The energy state of the harmonic oscillator (any n >= 0).
        x (float or array): The value of charge (independent variable) for
            which the wavefunction is calculated.
        hbar (float): Reduced Planck constant in the units of L, C and x.
            Defaults to 1 (natural units); pass ``scipy.constants.hbar``
            for SI values of L, C and x.

    Returns:
        float or array: Calculated wavefunction
    """
    n = int(n)
    if n < 0:
        raise ValueError(f"n must be a non-negative integer, got {n}")

    # This is the fundamental frequency of the LC circuit
    omega = 1.0 / sqrt(L * C)

    # "mass" * omega / hbar sets the width of the ground state
    alpha = L * omega / hbar
    xi = np.sqrt(alpha) * np.asarray(x, dtype=float)

    prefactor = 1.0 / sqrt((2.0**n) * factorial(n))
    quartic_root = (alpha / pi) ** 0.25

    return prefactor * quartic_root * np.exp(-(xi**2) / 2.0) * eval_hermite(n, xi)
