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

    def test_arvore_aberta_abaixo_do_resultado_nas_duas_operacoes(self):
        entrada = self.pasta / "entrada.txt"
        pacote = self.pasta / "texto.huf"
        restaurado = self.pasta / "restaurado.txt"
        entrada.write_bytes("Árvore e compactação\r\n".encode() * 2000)
        self.janela.attributes("-alpha", 0)
        self.janela.deiconify()
        self.janela.update()
        arvore = self.ui.arvore
        self.assertTrue(arvore.aviso.winfo_ismapped())
        self.processar(self.ui.compactar, entrada, pacote)
        self.assertTrue(arvore.tela.winfo_ismapped())
        self.assertGreater(len(arvore.posicoes), 1)
        self.assertIs(arvore.winfo_toplevel(), self.janela)
        self.assertGreaterEqual(arvore.winfo_rooty(),
                                self.ui.resultado.winfo_rooty() + self.ui.resultado.winfo_height())
        raiz_anterior = arvore.raiz
        arvore.expandir.invoke()
        self.assertGreater(len(arvore.posicoes), 7)
        self.processar(self.ui.restaurar, pacote, restaurado)
        self.assertIsNot(arvore.raiz, raiz_anterior)
        self.assertIn(arvore.raiz, arvore.abertos)
        self.assertTrue(arvore.tela.winfo_ismapped())
        self.assertEqual(restaurado.read_bytes(), entrada.read_bytes())

    def test_salvar_apos_cancelamento_e_limpar_resultado_invalido(self):
        entrada = self.pasta / "vazio.txt"
        pacote = self.pasta / "vazio.huf"
        entrada.write_bytes(b"")
        self.processar(self.ui.compactar, entrada, "")
        self.assertTrue(self.ui.salvar_novamente.winfo_manager())
        self.assertEqual(self.ui.valores[2]["text"], "Indefinida")
        self.assertIn("vazio", self.ui.arvore.aviso["text"])
        with patch("compactador.filedialog.asksaveasfilename", return_value=str(pacote)):
            self.ui.salvar_novamente.invoke()
        self.assertEqual(pacote.stat().st_size, 17)
        self.assertIsNone(self.ui.pendente)
        self.processar(self.ui.restaurar, entrada, self.pasta / "invalido.txt")
        self.assertFalse((self.pasta / "invalido.txt").exists())
        self.assertIsNone(self.ui.arvore.raiz)
        self.assertFalse(self.ui.arvore.posicoes)
        self.assertIn("válido", self.ui.arvore.aviso["text"])
        self.assertFalse(self.ui.metricas.winfo_manager())


if __name__ == "__main__":
    unittest.main()
