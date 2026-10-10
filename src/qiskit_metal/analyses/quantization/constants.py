"""Physical constants and Josephson-junction unit converters used by the
quantization analyses.

The ``Ic_from_Lj`` / ``Ej_from_Lj`` / ``Ec_from_Cs`` helpers are
vendored from ``pyEPR.calcs.convert.Convert`` so the analyses path
doesn't carry a runtime pyEPR dependency. The formulas are textbook.

The physical constants are the exact SI (2019) values from
``scipy.constants``, and both flux quanta are derived from them, so
``phinot == h / (2 * e)`` and ``phi0 == hbar / (2 * e)`` hold to
machine precision. (Until #1207 ``phinot`` was the truncated
``2.067e-15``, 4e-4 low, while other call sites used the full
``hbar / 2e``.)

``phi0`` here is the **reduced** flux quantum (ℏ/2e). ``phinot`` is
the **full** flux quantum (h/2e). This matches the pre-vendor
convention used by ``lumped_capacitive.py`` and others — don't swap
them.
"""

import numpy as np
import scipy.constants as _sc

MHzRad = 2 * np.pi * 1e6
GHzRad = 2 * np.pi * 1e9

NANO = 1e-9
FEMTO = 1e-15
ONE_OVER_FEMTO = 1e15

# Exact SI (2019) values from scipy.constants.
e = _sc.e  # electron charge
h = _sc.h  # Planck's constant
hbar = _sc.hbar  # reduced Planck's constant
phinot = h / (2 * e)  # magnetic flux quantum (full, h/2e)
phi0 = hbar / (2 * e)  # reduced magnetic flux quantum (ℏ/2e)


# ---------------------------------------------------------------------------
# Vendored Josephson-junction unit converters
# ---------------------------------------------------------------------------
#
# These mirror ``pyEPR.calcs.convert.Convert.Ic_from_Lj`` etc. The pyEPR
# originals route through pint; the call sites in metal only use a
# small fixed set of units, so we use direct lookup tables (avoids
# importing pint into pure-Python math and keeps the helpers fast).

_LENGTH_FACTORS = {"H": 1.0, "nH": 1e-9, "pH": 1e-12}
_CURRENT_FACTORS = {"A": 1.0, "mA": 1e-3, "uA": 1e-6, "nA": 1e-9}
_CAP_FACTORS = {"F": 1.0, "uF": 1e-6, "nF": 1e-9, "pF": 1e-12, "fF": 1e-15}
_FREQ_FACTORS = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6, "GHz": 1e9, "THz": 1e12}


def _factor(table: dict, unit: str, label: str) -> float:
    try:
        return table[unit]
    except KeyError:
        raise ValueError(f"Unknown {label} unit {unit!r}. Supported: {sorted(table)}")


def Ic_from_Lj(Lj, units_in: str = "nH", units_out: str = "A") -> float:
    """Josephson junction critical current from Josephson inductance.

    Ic = φ₀ / Lj, where φ₀ = ℏ / (2e) is the reduced flux quantum.

    Mirrors ``pyEPR.calcs.convert.Convert.Ic_from_Lj``.
    """
    Lj_SI = Lj * _factor(_LENGTH_FACTORS, units_in, "inductance")
    Ic_SI = phi0 / Lj_SI
    return Ic_SI / _factor(_CURRENT_FACTORS, units_out, "current")


def Ej_from_Lj(Lj, units_in: str = "nH", units_out: str = "MHz") -> float:
    """Josephson energy from Josephson inductance.

    Ej = φ₀² / Lj  (in Joules), returned as a frequency via Ej/h.
    """
    Lj_SI = Lj * _factor(_LENGTH_FACTORS, units_in, "inductance")
    Ej_J = phi0**2 / Lj_SI
    Ej_Hz = Ej_J / h
    return Ej_Hz / _factor(_FREQ_FACTORS, units_out, "frequency")


def Ec_from_Cs(Cs, units_in: str = "fF", units_out: str = "MHz") -> float:
    """Charging energy from shunt capacitance.

    Ec = e² / (2 Cs)  (in Joules), returned as a frequency via Ec/h.
    """
    Cs_SI = Cs * _factor(_CAP_FACTORS, units_in, "capacitance")
    Ec_J = e**2 / (2.0 * Cs_SI)
    Ec_Hz = Ec_J / h
    return Ec_Hz / _factor(_FREQ_FACTORS, units_out, "frequency")
