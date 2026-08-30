import unittest

from refinamento import (
    detectar_componentes_conexos,
    gerar_clausula_bloqueio,
    menor_componente,
)


class RefinamentoTests(unittest.TestCase):
    def setUp(self):
        self.arestas = [
            ((0, 0), (0, 1)),
            ((0, 1), (1, 1)),
            ((1, 1), (1, 0)),
            ((1, 0), (0, 0)),
            ((2, 2), (2, 3)),
            ((2, 3), (3, 3)),
            ((3, 3), (3, 2)),
            ((3, 2), (2, 2)),
        ]
        self.variaveis = {aresta: index for index, aresta in enumerate(self.arestas, 1)}

    def test_detecta_dois_componentes(self):
        componentes = detectar_componentes_conexos(self.arestas)

        self.assertEqual(len(componentes), 2)
        self.assertEqual(sorted(map(len, componentes)), [4, 4])

    def test_gera_clausula_que_bloqueia_subtour(self):
        componentes = detectar_componentes_conexos(self.arestas)
        componente = menor_componente(componentes)

        clausula = gerar_clausula_bloqueio(componente, self.arestas, self.variaveis)

        self.assertEqual(len(clausula), 4)
        self.assertTrue(all(literal < 0 for literal in clausula))

    def test_solucao_vazia_nao_tem_componentes(self):
        self.assertEqual(detectar_componentes_conexos([]), [])


if __name__ == "__main__":
    unittest.main()
