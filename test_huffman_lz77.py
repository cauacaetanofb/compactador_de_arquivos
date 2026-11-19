import unittest

from huffman_lz77 import (
    ArquivoInvalido, JANELA, compactar_em_etapas, descompactar_em_etapas, tokens_lz77,
)


def concluir(etapas):
    while True:
        try:
            next(etapas)
        except StopIteration as fim:
            return fim.value


def estrutura(no):
    if no is not None:
        return no.simbolo, no.peso, estrutura(no.esquerda), estrutura(no.direita)


class CompactadorTest(unittest.TestCase):
    def test_recupera_bytes_e_arvore(self):
        texto = "Grafos, ação e coração! 🌳\r\nSegunda linha\nSem quebra final"
        casos = [b"", b"Q", b"QQ", texto.encode(), texto.encode("utf-16"),
                 b"a" * 70000, bytes(range(256)) * 20]
        for dados in casos:
            with self.subTest(tamanho=len(dados)):
                pacote, raiz = concluir(compactar_em_etapas(dados))
                restaurado, reconstruida = concluir(descompactar_em_etapas(pacote))
                self.assertEqual(restaurado, dados)
                self.assertEqual(estrutura(raiz), estrutura(reconstruida))

    def test_copia_sobreposta(self):
        dados = b"ABABABAB"
        self.assertEqual(list(tokens_lz77(dados)), [(65, 0), (66, 0), (259, 2)])
        pacote, _ = concluir(compactar_em_etapas(dados))
        self.assertEqual(concluir(descompactar_em_etapas(pacote))[0], dados)

    def test_alcance_exato_da_janela(self):
        for distancia in (JANELA, JANELA + 1):
            dados = b"ABC" + b"x" * (distancia - 3) + b"ABC"
            tokens = list(tokens_lz77(dados))
            if distancia == JANELA:
                self.assertEqual(tokens[-1], (256, JANELA))
            else:
                self.assertEqual(tokens[-3:], [(65, 0), (66, 0), (67, 0)])
            pacote, _ = concluir(compactar_em_etapas(dados))
            self.assertEqual(concluir(descompactar_em_etapas(pacote))[0], dados)

    def test_formato_de_uma_folha(self):
        # Cabeçalho, árvore com o literal A, código 0 e cinco bits de preenchimento.
        fixo = bytes.fromhex("485a373701 0000000000000001 00420042 9040")
        self.assertEqual(concluir(compactar_em_etapas(b"A"))[0], fixo)
        self.assertEqual(concluir(descompactar_em_etapas(fixo))[0], b"A")

    def test_detecta_arquivo_danificado(self):
        pacote, _ = concluir(compactar_em_etapas(b"A"))
        soma_incorreta = bytearray(pacote)
        soma_incorreta[13] ^= 1
        for invalido in (b"texto", pacote[:-1], pacote + b"\0", soma_incorreta,
                         pacote[:-1] + bytes([pacote[-1] | 1])):
            with self.subTest(arquivo=invalido), self.assertRaises(ArquivoInvalido):
                concluir(descompactar_em_etapas(invalido))


if __name__ == "__main__":
    unittest.main()
