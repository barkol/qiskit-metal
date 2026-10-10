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
This code calculates the energy eigenvalues of the transmon qubit cooper pair box
as a function of the offset charge and plots the corresponding results.

Key References:
    - J. Koch et al. "Charge-insensitive qubit design derived from the Cooper pair box"
      Phys. Rev. A. 76, 042319 (2007).

"""

import numpy as np
import matplotlib.pyplot as plt

from qiskit_metal.analyses.hamiltonian.transmon_CPB_analytic import transmon_level

__all__ = ["kidx", "kidx_raw", "plot_eigenvalues", "transmon_eigenvalue"]


def kidx_raw(m, my_ng):
    """
    This function calculates the integers which correct sort the eigenstates and eigenenergies
    of the solution to Mathieu's equation.

        Args:
            m (int): The energy level of the qubit (m=0,1,2,3,etc.)
            my_ng (float): the offset charge of the Josephjunction island (in units of 2e)

        Returns:
            float: the calculated index
    """
    if my_ng == 0:
        return m + 1.0 - ((m + 1.0) % 2.0)

    return (
        m
        + 1.0
        - ((m + 1.0) % 2.0)
        + 2.0 * my_ng * ((-1.0) ** (m - 0.5 * (np.sign(my_ng) - 1.0)))
    )


def kidx(m, my_ng):
    """
    This function is a placeholder which performs an additional modulo operation
    with an offset of ng=0.5, but is not necessary when only integer values of
    kidxRAW(m, my_ng) are used. If non-integer values of kidxRAW are used, then
    the modulo operation below needs to be updated to include the offset.

        Args:
            m (int): The energy level of the qubit (m=0,1,2,3,etc.)
            ng (float): the offset charge of the Josephjunction island (in units of 2e)

        Returns:
            float: the calculated energy eigenvalue, after an ng=0.5 offset.
    """
    return kidx_raw(m, my_ng)


# define the Josephson to charging energy ratio E_J / E_C
RATIO = 1.0

# define the charing energy
E_C = 1.0


def transmon_eigenvalue(m, my_ng, Ej_over_Ec=None, Ec=None):
    """
    This function calculate the energy eigenvalue of the transmon qubit for a given
    energy level (m) and offset charge (my_ng). The input values are first used to
    calculate the index using the function defined above, and then the calculated
    index is used to calculate the energy eigenvalue using Mathieu's characteristic values.

        Args:
            m (int): The energy level of the qubit (m=0,1,2,3,etc.)
            ng (float): the offset charge of the Josephjunction island (in units of 2e)
            Ej_over_Ec (float): E_J/E_C; defaults to the module constant ``RATIO``
            Ec (float): E_C, sets the energy unit; defaults to the module
                constant ``E_C``

        Returns:
            float: the calculated energy eigenvalue.

    Odd levels use the odd Mathieu characteristic value ``b`` and any ``ng``
    gives a finite result (see :func:`.transmon_CPB_analytic.transmon_level`).
    """
    ratio = RATIO if Ej_over_Ec is None else Ej_over_Ec
    ec = E_C if Ec is None else Ec
    return transmon_level(m, ratio * ec, ec, my_ng)


# extremely coarse grid: only three points from -0.5 to 0.5. This so that only integer values
# of the index are used in the calculation of the Mathieu characteristic value.
ng = np.linspace(-0.5, 0.5, 3)

# levels on a dense offset-charge grid over two periods (Koch et al., Fig. 2)
ng_periodic = np.linspace(-2.0, 2.0, 201)

E0 = [transmon_eigenvalue(0, i) for i in ng]
E1 = [transmon_eigenvalue(1, i) for i in ng]
E2 = [transmon_eigenvalue(2, i) for i in ng]
E3 = [transmon_eigenvalue(3, i) for i in ng]

E0_periodic = [transmon_eigenvalue(0, i) for i in ng_periodic]
E1_periodic = [transmon_eigenvalue(1, i) for i in ng_periodic]
E2_periodic = [transmon_eigenvalue(2, i) for i in ng_periodic]
E3_periodic = [transmon_eigenvalue(3, i) for i in ng_periodic]


def plot_eigenvalues():
    """
    This function actually creates the plot(s) of eigenvalues as a function of
    offset charge. No arguments need to be passed.

    Returns:
        A plot of the eigenvalues as a function of offset charge.
    """
    # plot the PERIODIC eigen energies between (-2.0, 2.0)
    plt.plot(ng_periodic, E0_periodic, "k")  # m=0
    plt.plot(ng_periodic, E1_periodic, "r")  # m=1
    plt.plot(ng_periodic, E2_periodic, "b")  # m=2
    plt.plot(ng_periodic, E3_periodic, "m")  # m=3
    plt.xlabel("Offset Charge [ng]")
    plt.ylabel("Energy E_m[ng]")
