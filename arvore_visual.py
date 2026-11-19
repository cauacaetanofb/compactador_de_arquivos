"""Visualização da árvore usada pelo arquivo, com ramos expansíveis."""

import tkinter as tk
from tkinter import ttk

from huffman_lz77 import MINIMO


FUNDO = "#f7f9fb"
TINTA = "#162c40"
SUAVE = "#455b70"
AZUL = "#175ba5"
BORDA = "#d2dce5"
JUNCAO = "#d9eafa"
LITERAL = "#d7eee5"
COPIA = "#f9e7c5"
FONTE = "Segoe UI"


def quantidade(valor):
    return f"{valor:,}".replace(",", ".")


def rotulo(simbolo):
    if simbolo >= 256:
        return f"Copiar {simbolo - 256 + MINIMO} B"
    especiais = {9: "Tabulação", 10: "LF (\\n)", 13: "CR (\\r)", 32: "Espaço"}
    if simbolo in especiais:
        return especiais[simbolo]
    return repr(chr(simbolo)) if 33 <= simbolo < 127 else f"0x{simbolo:02X}"


class ArvoreVisual(tk.Frame):
    def __init__(self, mestre):
        super().__init__(mestre, bg="white", highlightthickness=1,
                         highlightbackground=BORDA)
        self.raiz = None
        self.abertos = set()
        self.nos = {}
        self.posicoes = {}
        self.vazio = "A árvore aparecerá aqui após a escolha de um arquivo."

        topo = tk.Frame(self, bg="white", padx=16, pady=10)
        topo.pack(fill="x")
        tk.Label(topo, text="Árvore de Huffman", bg="white", fg=TINTA,
                 font=(FONTE, 15, "bold")).pack(side="left")
        self.inicial = ttk.Button(topo, text="Visão inicial", command=self.reiniciar)
        self.inicial.pack(side="right")
        self.expandir = ttk.Button(topo, text="Expandir tudo", command=self.abrir_tudo)
        self.expandir.pack(side="right", padx=6)

        area = tk.Frame(self, bg=FUNDO)
        area.pack(fill="both", expand=True)
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.tela = tk.Canvas(area, bg=FUNDO, height=180, width=1,
                              highlightthickness=0)
        self.tela.grid(row=0, column=0, sticky="nsew")
        horizontal = ttk.Scrollbar(area, orient="horizontal", command=self.tela.xview)
        vertical = ttk.Scrollbar(area, orient="vertical", command=self.tela.yview)
        horizontal.grid(row=1, column=0, sticky="ew")
        vertical.grid(row=0, column=1, sticky="ns")
        self.tela.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        self.tela.bind("<Configure>", lambda _: self.desenhar())
        self.tela.bind("<Button-1>", self.alternar)
        self.tela.tag_bind("ramo", "<Enter>", lambda _: self.tela.config(cursor="hand2"))
        self.tela.tag_bind("ramo", "<Leave>", lambda _: self.tela.config(cursor=""))
        self.tela.bind("<MouseWheel>", lambda e: self.rolar(e, False))
        self.tela.bind("<Shift-MouseWheel>", lambda e: self.rolar(e, True))

        legenda = tk.Frame(self, bg="white", padx=16, pady=8)
        legenda.pack(fill="x")
        for cor, nome in ((JUNCAO, "Junção"), (LITERAL, "Byte literal"), (COPIA, "Cópia LZ77")):
            tk.Frame(legenda, width=10, height=10, bg=cor, highlightthickness=1,
                     highlightbackground=BORDA).pack(side="left")
            tk.Label(legenda, text=nome, bg="white", fg=SUAVE, font=(FONTE, 9)
                     ).pack(side="left", padx=(4, 14))
        tk.Label(legenda, text="Clique em uma junção para abrir ou recolher o ramo.",
                 bg="white", fg=SUAVE, font=(FONTE, 9)).pack(side="right")
        self.definir(None, self.vazio)

    def rolar(self, evento, horizontal):
        mover = self.tela.xview_scroll if horizontal else self.tela.yview_scroll
        mover(-1 if evento.delta > 0 else 1, "units")
        return "break"

    def definir(self, raiz, vazio="O TXT está vazio. Não há símbolos para montar uma árvore."):
        self.raiz = raiz
        self.vazio = vazio
        estado = "normal" if raiz is not None and raiz.simbolo is None else "disabled"
        self.expandir.configure(state=estado)
        self.inicial.configure(state=estado)
        self.reiniciar()

    def reiniciar(self):
        self.abrir(2)

    def abrir_tudo(self):
        self.abrir(None)

    def abrir(self, niveis):
        self.abertos.clear()

        def visitar(no, nivel):
            if no is None or no.simbolo is not None or nivel == niveis:
                return
            self.abertos.add(no)
            visitar(no.esquerda, nivel + 1)
            visitar(no.direita, nivel + 1)

        visitar(self.raiz, 0)
        self.desenhar()

    def alternar(self, evento):
        for tag in self.tela.gettags("current"):
            no = self.nos.get(tag)
            if no is None or no.simbolo is not None:
                continue
            if no in self.abertos:
                self.abertos.remove(no)
            else:
                self.abertos.add(no)
            self.desenhar(no, evento.x, evento.y)
            break

    def desenhar(self, ancora=None, mouse_x=None, mouse_y=None):
        tela = self.tela
        tela.delete("all")
        self.nos.clear()
        self.posicoes.clear()
        largura, altura = tela.winfo_width(), tela.winfo_height()
        if self.raiz is None:
            tela.configure(scrollregion=(0, 0, largura, altura))
            tela.create_text(largura / 2, altura / 2, text=self.vazio,
                             fill=SUAVE, font=(FONTE, 11))
            return

        passo_x, passo_y = 128, 78
        folhas = 0

        def posicionar(no, nivel):
            nonlocal folhas
            if no in self.abertos:
                x = (posicionar(no.esquerda, nivel + 1) +
                     posicionar(no.direita, nivel + 1)) / 2
            else:
                x = (folhas + 0.5) * passo_x
                folhas += 1
            self.posicoes[no] = (x, 34 + nivel * passo_y)
            return x

        posicionar(self.raiz, 0)
        total_x = max(largura, folhas * passo_x + 24)
        margem = (total_x - folhas * passo_x) / 2
        total_y = max(altura, max(y for _, y in self.posicoes.values()) + 38)
        tela.configure(scrollregion=(0, 0, total_x, total_y))

        for no, (x, y) in self.posicoes.items():
            if no not in self.abertos:
                continue
            for bit, filho in enumerate((no.esquerda, no.direita)):
                fx, fy = self.posicoes[filho]
                tela.create_line(x + margem, y + 22, fx + margem, fy - 22,
                                 fill="#92a6b9", width=2)
                bx = (x + fx) / 2 + margem
                by = (y + fy) / 2
                tela.create_oval(bx - 8, by - 8, bx + 8, by + 8, fill=FUNDO, outline="")
                tela.create_text(bx, by, text=str(bit), fill=SUAVE, font=(FONTE, 9, "bold"))

        for indice, (no, (x, y)) in enumerate(self.posicoes.items()):
            x += margem
            tag = f"no{indice}"
            self.nos[tag] = no
            if no.simbolo is None:
                nome = ("Raiz" if no is self.raiz else "Junção")
                nome += "  −" if no in self.abertos else "  +"
                cor, tags = JUNCAO, (tag, "ramo")
            else:
                nome = rotulo(no.simbolo)
                cor = LITERAL if no.simbolo < 256 else COPIA
                tags = (tag,)
            tela.create_rectangle(x - 58, y - 22, x + 58, y + 22, fill=cor,
                                  outline=BORDA, tags=tags)
            tela.create_text(x, y - 8, text=nome, font=(FONTE, 10, "bold"),
                             fill=TINTA, tags=tags)
            tela.create_text(x, y + 10, text=f"freq. {quantidade(no.peso)}",
                             font=(FONTE, 9), fill=SUAVE, tags=tags)

        foco = ancora or self.raiz
        x, y = self.posicoes[foco]
        tela.xview_moveto((x + margem - (largura / 2 if mouse_x is None else mouse_x)) / total_x)
        tela.yview_moveto(0 if mouse_y is None else (y - mouse_y) / total_y)
