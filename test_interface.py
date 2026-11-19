import tempfile
import unittest
from pathlib import Path
from time import monotonic
from unittest.mock import patch

try:
    import tkinter as tk
except ImportError:
    tk = None


@unittest.skipIf(tk is None, "Tkinter indisponível")
class InterfaceTest(unittest.TestCase):
    def setUp(self):
        from compactador import Compactador

        try:
            self.janela = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(str(erro))
        self.janela.withdraw()
        self.addCleanup(self.janela.destroy)
        self.ui = Compactador(self.janela)
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)

    def processar(self, botao, origem, destino):
        with patch("compactador.filedialog.askopenfilename", return_value=str(origem)), \
             patch("compactador.filedialog.asksaveasfilename", return_value=str(destino)):
            botao.invoke()
            limite = monotonic() + 10
            while self.ui.compactar.instate(["disabled"]):
                self.assertLess(monotonic(), limite, "A operação não terminou")
                self.janela.update()

    def test_operacoes_independentes_da_arvore(self):
        entrada = self.pasta / "entrada.txt"
        pacote = self.pasta / "texto.huf"
        restaurado = self.pasta / "restaurado.txt"
        entrada.write_bytes("Árvore e compactação\r\n".encode() * 2000)
        self.assertFalse(self.ui.resultado.winfo_manager())
        self.processar(self.ui.compactar, entrada, pacote)
        self.assertIsNone(self.ui.janela_arvore)
        self.ui.ver_arvore.invoke()
        detalhe = self.ui.janela_arvore
        self.assertIs(detalhe.winfo_children()[0].raiz, self.ui.raiz)
        self.ui.ver_arvore.invoke()
        self.assertIs(self.ui.janela_arvore, detalhe)
        self.processar(self.ui.restaurar, pacote, restaurado)
        self.assertFalse(detalhe.winfo_exists())
        self.assertIsNone(self.ui.janela_arvore)
        self.assertEqual(restaurado.read_bytes(), entrada.read_bytes())

    def test_salvar_apos_cancelamento_e_limpar_resultado_invalido(self):
        entrada = self.pasta / "vazio.txt"
        pacote = self.pasta / "vazio.huf"
        entrada.write_bytes(b"")
        self.processar(self.ui.compactar, entrada, "")
        self.assertTrue(self.ui.salvar_novamente.winfo_manager())
        self.assertEqual(self.ui.valores[2]["text"], "Indefinida")
        with patch("compactador.filedialog.asksaveasfilename", return_value=str(pacote)):
            self.ui.salvar_novamente.invoke()
        self.assertEqual(pacote.stat().st_size, 17)
        self.assertIsNone(self.ui.pendente)
        self.processar(self.ui.restaurar, entrada, self.pasta / "invalido.txt")
        self.assertFalse((self.pasta / "invalido.txt").exists())
        self.assertFalse(self.ui.ver_arvore.winfo_manager())
        self.assertFalse(self.ui.metricas.winfo_manager())


if __name__ == "__main__":
    unittest.main()
