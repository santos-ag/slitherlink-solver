import tempfile
import unittest
from pathlib import Path

from gerador import SlitherlinkCNF, parse_grid_file, parse_grid_lines, validate_dimacs


class GeradorTests(unittest.TestCase):
    def test_mapeamento_e_contagem_1x1_com_dica_4(self):
        instance = SlitherlinkCNF(1, 1, [[4]])

        self.assertEqual(instance.num_vars, 4)
        self.assertEqual(instance.var_h(0, 0), 1)
        self.assertEqual(instance.var_h(1, 0), 2)
        self.assertEqual(instance.var_v(0, 0), 3)
        self.assertEqual(instance.var_v(0, 1), 4)
        self.assertEqual(len(instance.clauses), 13)
        self.assertEqual(validate_dimacs(instance.generate_dimacs()), (4, 13))

    def test_instancia_sem_dicas_exige_laco_nao_vazio(self):
        instance = SlitherlinkCNF(1, 1, [[None]])

        self.assertEqual(instance.clauses[-1], [1, 2, 3, 4])

    def test_rejeita_dica_5(self):
        with self.assertRaisesRegex(ValueError, "Dica invalida"):
            parse_grid_lines(["1 1", "5"])

    def test_rejeita_linha_com_dimensao_incorreta(self):
        with self.assertRaisesRegex(ValueError, "possui 2 celulas"):
            parse_grid_lines(["1 3", "1 2"])

    def test_parse_arquivo_valido(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "instance.txt"
            path.write_text("2 2\n1 .\n. 3\n", encoding="utf-8")

            self.assertEqual(parse_grid_file(path), (2, 2, [[1, None], [None, 3]]))

    def test_detecta_cabecalho_com_contagem_incorreta(self):
        with self.assertRaisesRegex(ValueError, "Numero de clausulas inconsistente"):
            validate_dimacs("p cnf 2 2\n1 0")

    def test_detecta_literal_fora_do_intervalo(self):
        with self.assertRaisesRegex(ValueError, "fora do intervalo"):
            validate_dimacs("p cnf 2 1\n3 0")

    def test_cnfs_versionados_correspondem_as_entradas(self):
        instances_dir = Path(__file__).resolve().parents[1] / "instancias"
        for txt_path in instances_dir.glob("*.txt"):
            with self.subTest(instance=txt_path.name):
                rows, cols, grid = parse_grid_file(txt_path)
                expected = SlitherlinkCNF(rows, cols, grid).generate_dimacs()
                actual = txt_path.with_suffix(".cnf").read_text(encoding="utf-8")
                self.assertEqual(actual.strip(), expected.strip())


if __name__ == "__main__":
    unittest.main()
