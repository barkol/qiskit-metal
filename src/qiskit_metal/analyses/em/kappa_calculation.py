"""This code calculates the photon loss (kappa) due to the capacitive coupling
between CPWs and input/output transmission lines in a quantum circuit.

Two cases are treated: In the first case, three arguments are passed to the function kappa_in
and the resonant frequency of the CPW is input as a float. In the second case, six arguments
are passed to kappa_in and the frequency of the CPW is calculated assuming an ideal CPW.

The result is kappa/2pi in Hz, from the standard expression for a resonator
capacitively coupled to a matched line (e.g. Goeppl et al., J. Appl. Phys. 104,
113904 (2008)), kappa = (2/pi) * omega**2 * C_in**2 * Z0**2 * omega_res,
written with angular frequencies omega = 2*pi*freq.

Key References:

D. Schuster, Ph.D. Thesis, Yale University (2007)
https://rsl.yale.edu/sites/default/files/files/RSL_Theses/SchusterThesis.pdf

T. McConkey, Ph.D. Thesis, University of Waterloo (2018)
https://uwspace.uwaterloo.ca/bitstream/handle/10012/13464/McConkey_Thomas.pdf?sequence=3&isAllowed=y

Mohebbi and Majedi, Superconducting Science and Technology 22, 125028 (2009)
https://iopscience.iop.org/article/10.1088/0953-2048/22/12/125028/meta

P. Krantz, et al. Physical Review Applied 6, 021318 (2019)
https://aip.scitation.org/doi/10.1063/1.5089550
"""

from math import pi

from scipy.constants import c as speed_of_light
from scipy.special import ellipk

__all__ = ["kappa_in"]


def kappa_in(*argv):
    """A simple calculator for the kappa value of a readout resonator.

    Call it as ``kappa_in(freq, C_in, freq_res)`` or
    ``kappa_in(freq, C_in, length, res_width, res_gap, eta)``.

    The photon loss rate is
    ``kappa = (2/pi) * omega**2 * C_in**2 * Z0**2 * omega_res`` with
    ``omega = 2*pi*freq``, ``omega_res = 2*pi*freq_res`` and ``Z0 = 50`` Ohm
    (a resonator capacitively coupled to a matched line). The function returns
    ``kappa / (2*pi)``, in Hz.

    Args:
        freq (float): The frequency of interest, in Hz
        C_in (float): Effective capacitance between CPW and environment (from Q3D), in Farads
        freq_res (float): Lowest resonant frequency of a CPW (from HFSS), in Hz
        length (float): Length of the CPW readout resonator, in meters
        res_width (float): Width of the resonator trace (center) line, in meters
        res_gap (float): Width of resonator gap (dielectric space), in meters
        eta (float): 2.0 for half-wavelength resonator; 4.0 for quarter-wavelength resonator

    In the six-argument form the resonance frequency is that of an ideal
    50 Ohm CPW of this geometry, ``freq_res = c / (eta * length * sqrt(eps_eff))``,
    with ``sqrt(eps_eff) = 30*pi*K(k')/(Z_res*K(k))`` from the conformal-mapping
    impedance ``Z_res = 30*pi*K(k')/(sqrt(eps_eff)*K(k))``.

    Returns:
        float: kappa / 2pi, in Hz

    Raises:
        TypeError: If the number of arguments is not 3 or 6.
    """

    # Effective impedance of the CPW transmission line, in Ohms
    Z_tran = 50.0

    # Effective impedance of the readout resonator, in Ohms
    Z_res = 50.0

    # If three arguments are passed to kappa_in, then the lowest resonator frequency is assumed to be an input
    if len(argv) == 3:
        freq, C_in, freq_res = argv

    # If six arguments are passed to kappa_in, the lowest resonator frequency of the resonator is calculated in the ideal case
    elif len(argv) == 6:
        freq, C_in, length, res_width, res_gap, eta = argv

        # Arguments for elliptic integrals (scipy's ellipk takes m = k**2)
        k0 = (res_width) / (res_width + 2.0 * res_gap)
        k01 = (1.0 - k0**2.0) ** (0.5)

        # Effective permittivity of an ideal CPW with impedance Z_res
        sqrt_eps_eff = 30.0 * pi * ellipk(k01**2.0) / (Z_res * ellipk(k0**2.0))

        # Calculation of the first resonant frequency of an ideal resonator
        freq_res = speed_of_light / (eta * length * sqrt_eps_eff)

    # Only three or six arguments accepted by kappa_in, otherwise the calculation in invalid.
    else:
        raise TypeError(
            f"kappa_in takes 3 or 6 positional arguments ({len(argv)} given)"
        )

    # kappa = (2/pi) w^2 C^2 Z0^2 w_res in rad/s; return kappa/2pi in Hz
    omega = 2.0 * pi * freq
    omega_res = 2.0 * pi * freq_res
    kappa = (2.0 / pi) * omega**2.0 * C_in**2.0 * Z_tran**2.0 * omega_res
    return kappa / (2.0 * pi)
