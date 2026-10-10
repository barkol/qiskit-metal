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
"""
Models the transmon qubit in the cooper-pair charge basis
and calculate the exact (analytic) solutions

@author: Nick Lanzillo (IBM)
"""

import numpy as np
from scipy.linalg import eigvalsh_tridiagonal
from scipy.special import mathieu_a, mathieu_b


def transmon_level(k: int, Ej: float, Ec: float, ng: float = 0.0) -> float:
    """Exact level ``k`` of ``H = 4 Ec (n - ng)**2 - Ej cos(phi)``.

    Koch et al., PRA 76, 042319 (2007), Eq. (2.11):
    ``E_k = Ec a_{2(ng + l(k, ng))}(-Ej / (2 Ec))``, the Mathieu characteristic
    value of order ``2(ng + l)``. At ``ng = 0`` and ``ng = 1/2`` (mod 1) the
    order is an integer and the even (``a``) and odd (``b``) characteristic
    values of scipy are used: ``ng = 0`` gives ``a_k`` for even ``k`` and
    ``b_{k+1}`` for odd ``k``; ``ng = 1/2`` gives ``a_{k+1}`` and ``b_k``.
    scipy has no characteristic values of non-integer order, so for any other
    ``ng`` the value is the ``k``-th eigenvalue of the Hill (tridiagonal)
    matrix of the Mathieu equation, which converges to machine precision.

    Args:
        k (int): level index (0 = ground state)
        Ej (float): Josephson energy
        Ec (float): charging energy, same unit as Ej
        ng (float): offset charge in units of 2e

    Returns:
        float: the energy of level ``k``, in the unit of Ej and Ec
    """
    k = int(k)
    if k < 0:
        raise ValueError(f"level index k must be >= 0, got {k}")
    q = -0.5 * Ej / Ec
    # the spectrum is periodic in ng with period 1 and even in ng
    ngr = abs(ng - np.round(ng))
    if np.isclose(ngr, 0.0, rtol=0, atol=1e-14):
        val = mathieu_a(k, q) if k % 2 == 0 else mathieu_b(k + 1, q)
    elif np.isclose(ngr, 0.5, rtol=0, atol=1e-14):
        val = mathieu_a(k + 1, q) if k % 2 == 0 else mathieu_b(k, q)
    else:
        ncut = k + 2 * int(np.ceil(np.sqrt(abs(q)))) + 40
        n = np.arange(-ncut, ncut + 1)
        diag = (2.0 * (n - ngr)) ** 2
        off = np.full(2 * ncut, q)
        val = eigvalsh_tridiagonal(diag, off, select="i", select_range=(k, k))[0]
    return float(Ec * val)


class Hcpb_analytic:
    """
    Analytic version of Hamiltonian-model Cooper pair box (Hcpb) class.

    Used calculate the exact eigenvalues for arbitrary Ej, Ec, ng values.
    """

    def __init__(self, Ej: float = None, Ec: float = None, ng: float = 0.5):
        """
        Generate a Cooper-pair box (CPB) model.

        Arguments:
            Ej (float): Josephson energy of the JJ
            Ec (float): Charging energy of the CPB
            ng (float): Offset charge of the CPB (ng=0.5 is the sweet spot).
                        `ng` only needs to run between -0.5 and 0.5.
                        `ng` is defined in units of cooper pairs (2e)
        """

        self._Ej = Ej
        self._Ec = Ec
        self._ng = ng
        self.evals = None
        self.evecs = None
        # Generate the diagonal and offdiagonal components of the Hamiltonian
        # self._gen_operators()
        # compute the eigenvectors and eigenvalues of the CPB
        # all properties can be derived from these
        # self._calc_H()

    def evalue_k(self, k: int):
        """
        Return the eigenvalue of the Hamiltonian for level k
        (see :func:`transmon_level`; finite for every ng).

        Arguments:
            k (int): Index of the eigenvalue

        Returns:
            float: eigenvalue of the Hamiltonian
        """
        self.evals = transmon_level(k, self._Ej, self._Ec, self._ng)
        # return self.evals[k]
        return self.evals
