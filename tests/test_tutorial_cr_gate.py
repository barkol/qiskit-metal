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
"""The QuTiP part of the cross-resonance gate tutorial runs on QuTiP 5 (#1216).

Executes the code cells of the simulation section (everything before
"Physical Design of the CR Gate"; the layout section needs the Qt GUI).
"""

import json
import pathlib
import unittest

import numpy as np

NOTEBOOK = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "tut"
    / "4-Analysis"
    / "Design-and-Simulation-of-a-Cross-Resonance-Gate.ipynb"
)


def _simulation_cells():
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    code = []
    for cell in cells:
        source = "".join(cell["source"])
        if cell["cell_type"] == "markdown" and "Physical Design" in source:
            break
        if cell["cell_type"] == "code":
            code.append(source)
    return code


class TestCrossResonanceTutorial(unittest.TestCase):
    def test_simulation_section_runs(self):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        ns: dict = {}
        try:
            for source in _simulation_cells():
                exec(compile(source, str(NOTEBOOK.name), "exec"), ns)
        finally:
            plt.close("all")

        # Driven at the dressed frequency, the target is inverted.
        self.assertLess(float(np.min(ns["m_qubit2"])), 0.01)
        # The target rotation depends on the control state: <sigma_y> of the
        # target (rotating frame) has opposite signs for control |0> and |1>.
        H, b, w2d, phi = ns["H"], ns["b"], ns["w2_dressed"], ns["phi"]
        from qutip import basis, mesolve, tensor

        t = np.linspace(0, 90, 301)
        sy = {}
        for control in (0, 1):
            psi = tensor(basis(2, control), basis(2, 1))
            res = mesolve(H, psi, t, [], e_ops=[b], options={"nsteps": 100000})
            sy[control] = 2 * np.imag(
                res.expect[0][-1] * np.exp(1j * (w2d * t[-1] + phi))
            )
        self.assertGreater(sy[0], 0.9)
        self.assertLess(sy[1], -0.9)


if __name__ == "__main__":
    unittest.main()
