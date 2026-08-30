import os
import tempfile
import unittest
from pathlib import Path

from solver_runner import BASE_DIR, SOLVERS, solve_with_subtour_elimination
from visualizar import generate_figure


@unittest.skipUnless(
    os.access(SOLVERS["cadical"], os.X_OK) and os.access(SOLVERS["kissat"], os.X_OK),
    "Os SAT solvers empacotados nao estao disponiveis.",
)
class RunnerIntegrationTests(unittest.TestCase):
    def test_resolve_instancia_sat_com_laco_unico(self):
        result = solve_with_subtour_elimination(
            "cadical",
            SOLVERS["cadical"],
            BASE_DIR / "instancias" / "instancia1_3x3_sat.txt",
        )

        self.assertEqual(result.status, "SAT")
        self.assertIsNotNone(result.solution)
        self.assertEqual(result.iterations, 1)

    def test_instancia_5x5_exige_refinamento(self):
        result = solve_with_subtour_elimination(
            "kissat",
            SOLVERS["kissat"],
            BASE_DIR / "instancias" / "instancia3_5x5_sat.txt",
        )

        self.assertEqual(result.status, "SAT")
        self.assertGreater(result.cuts, 0)
        self.assertGreater(result.iterations, 1)
        self.assertIsNotNone(result.first_rejected)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "solution.svg"
            generate_figure(result, output)
            self.assertIn("<svg", output.read_text(encoding="utf-8"))

    def test_detecta_instancia_insatisfativel(self):
        result = solve_with_subtour_elimination(
            "cadical",
            SOLVERS["cadical"],
            BASE_DIR / "instancias" / "instancia5_3x3_unsat.txt",
        )

        self.assertEqual(result.status, "UNSAT")
        self.assertIsNone(result.solution)


if __name__ == "__main__":
    unittest.main()
