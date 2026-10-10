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
"""CoupledLineTee resonator-end termination, and its use in example 52 (#1217)."""

import json
import pathlib
import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee

EXAMPLE_52 = (
    pathlib.Path(__file__).resolve().parents[1]
    / "docs"
    / "circuit-examples"
    / "F.Small-quantum-chips"
    / "52-Barends_5Qubit_Xmon_Processor.ipynb"
)


def _end_gap(open_termination):
    """Etch beyond the coupled trace's far end (mm): 0 means the trace end
    touches ground (shorted resonator end)."""
    design = designs.DesignPlanar()
    clt = CoupledLineTee(
        design,
        "CLT",
        options=dict(
            coupling_length="200um",
            coupling_space="4um",
            open_termination=open_termination,
        ),
    )
    paths = design.qgeometry.tables["path"]
    rows = paths[paths["component"] == clt.id]
    trace = rows[rows["name"] == "second_cpw"].iloc[0].geometry
    etch = rows[rows["name"] == "second_cpw_sub"].iloc[0].geometry
    return min(x for x, _ in trace.coords) - min(x for x, _ in etch.coords)


class TestCoupledLineTeeTermination(unittest.TestCase):
    def test_open_and_shorted_end(self):
        self.assertAlmostEqual(_end_gap(True), 0.006, places=9)  # second_gap
        self.assertAlmostEqual(_end_gap(False), 0.0, places=12)

    def test_example_52_uses_quarter_wave_couplers(self):
        """The readout claw is the open end, so the coupler end must be
        shorted for a lambda/4 readout resonator."""
        cells = json.loads(EXAMPLE_52.read_text(encoding="utf-8"))["cells"]
        sources = [
            "".join(c["source"])
            for c in cells
            if c["cell_type"] == "code" and "CoupledLineTee(" in "".join(c["source"])
        ]
        self.assertTrue(sources)
        for source in sources:
            self.assertIn("open_termination=False", source)


if __name__ == "__main__":
    unittest.main()
