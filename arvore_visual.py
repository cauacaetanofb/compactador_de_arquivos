"""Visualização da árvore usada pelo arquivo, com ramos expansíveis."""

import tkinter as tk
from tkinter import ttk

from huffman_lz77 import MINIMO
from estilo import ACENTO, BORDA, FONTE, FUNDO, PAINEL, SUAVE, TINTA


JUNCAO = "#353951"
LITERAL = "#263f38"
COPIA = "#4a3a28"


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
        super().__init__(mestre, bg=PAINEL, highlightthickness=1,
                         highlightbackground=BORDA)
        self.raiz = None
        self.abertos = set()
        self.nos = {}
        self.posicoes = {}
        self.selecionado = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        topo = tk.Frame(self, bg=PAINEL, padx=16, pady=10)
        topo.grid(row=0, column=0, sticky="ew")
        tk.Label(topo, text="Árvore de Huffman", bg=PAINEL, fg=TINTA,
                 font=(FONTE, 15, "bold")).pack(side="left")
        self.controles = tk.Frame(topo, bg=PAINEL)
        self.inicial = ttk.Button(self.controles, text="Visão inicial", command=self.reiniciar)
        self.inicial.pack(side="right")
        self.expandir = ttk.Button(self.controles, text="Expandir tudo", command=self.abrir_tudo)
        self.expandir.pack(side="right", padx=6)

        area = self.area = tk.Frame(self, bg=FUNDO)
        area.grid(row=1, column=0, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.tela = tk.Canvas(area, bg=FUNDO, height=220, width=1,
                              takefocus=True, highlightthickness=1,
                              highlightbackground=FUNDO, highlightcolor=ACENTO)
        self.tela.grid(row=0, column=0, sticky="nsew")
        horizontal = ttk.Scrollbar(area, orient="horizontal", command=self.tela.xview)
        vertical = ttk.Scrollbar(area, orient="vertical", command=self.tela.yview)
        horizontal.grid(row=1, column=0, sticky="ew")
        vertical.grid(row=0, column=1, sticky="ns")
        self.tela.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        self.tela.bind("<Configure>", lambda _: self.desenhar())
        self.tela.bind("<Button-1>", self.alternar)
        for tecla in ("Left", "Right", "Up", "space", "Return"):
            self.tela.bind(f"<{tecla}>", self.navegar)
        self.tela.tag_bind("ramo", "<Enter>", lambda _: self.tela.config(cursor="hand2"))
        self.tela.tag_bind("ramo", "<Leave>", lambda _: self.tela.config(cursor=""))
        self.tela.bind("<MouseWheel>", lambda e: self.rolar(e, False))
        self.tela.bind("<Shift-MouseWheel>", lambda e: self.rolar(e, True))

        self.aviso = tk.Label(self, bg=PAINEL, fg=SUAVE, font=(FONTE, 10),
                              anchor="nw", justify="left")
        self.legenda = tk.Frame(self, bg=PAINEL)
        self.legenda.grid(row=2, column=0, sticky="ew")
        legenda = tk.Frame(self.legenda, bg=PAINEL, padx=16, pady=6)
        legenda.pack(fill="x")
        for cor, nome in ((JUNCAO, "Junção"), (LITERAL, "Byte literal"), (COPIA, "Cópia LZ77")):
            tk.Frame(legenda, width=10, height=10, bg=cor, highlightthickness=1,
                     highlightbackground=BORDA).pack(side="left")
            tk.Label(legenda, text=nome, bg=PAINEL, fg=SUAVE, font=(FONTE, 9)
                     ).pack(side="left", padx=(4, 14))
        tk.Label(self.legenda, text="Use as setas para navegar e Espaço para abrir ou recolher uma junção.",
                 bg=PAINEL, fg=SUAVE, font=(FONTE, 9)).pack(anchor="w", padx=14, pady=(0, 8))
        self.definir(None, "A árvore aparecerá aqui após processar um arquivo.")

    def rolar(self, evento, horizontal):
        mover = self.tela.xview_scroll if horizontal else self.tela.yview_scroll
        mover(-1 if evento.delta > 0 else 1, "units")
        return "break"

    def definir(self, raiz, vazio="O TXT está vazio. Não há símbolos para montar uma árvore."):
        self.raiz = raiz
        self.selecionado = raiz
        if raiz is None:
            self.controles.pack_forget()
            self.area.grid_remove()
            self.legenda.grid_remove()
            self.aviso.configure(text=vazio)
            self.aviso.grid(row=1, column=0, sticky="nw", padx=14, pady=(0, 12))
        else:
            self.aviso.grid_remove()
            self.controles.pack(side="right")
            self.area.grid()
            self.legenda.grid()
            estado = "disabled" if raiz.simbolo is not None else "normal"
            self.expandir.configure(state=estado)
            self.inicial.configure(state=estado)
        self.reiniciar()

    def reiniciar(self):
        self.abrir(2)

    def abrir_tudo(self):
        self.abrir(None)

    def abrir(self, niveis):
        self.abertos.clear()
        self.selecionado = self.raiz

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
            if no is None:
                continue
            self.tela.focus_set()
            self.selecionado = no
            if no.simbolo is None:
                self.alternar_ramo(no)
            self.desenhar(no, evento.x, evento.y)
            break

    def alternar_ramo(self, no):
        if no in self.abertos:
            self.abertos.remove(no)
        else:
            self.abertos.add(no)

    def navegar(self, evento):
        no = self.selecionado
        if no is None:
            return "break"
        if evento.keysym == "Up":
            no = next((pai for pai in self.posicoes if no in (pai.esquerda, pai.direita)), no)
        elif no.simbolo is None:
            if evento.keysym in ("space", "Return"):
                self.alternar_ramo(no)
            else:
                self.abertos.add(no)
                no = no.esquerda if evento.keysym == "Left" else no.direita
        self.selecionado = no
        self.desenhar(no, self.tela.winfo_width() / 2, self.tela.winfo_height() / 2)
        return "break"

    def desenhar(self, ancora=None, mouse_x=None, mouse_y=None):
        tela = self.tela
        tela.delete("all")
        self.nos.clear()
        self.posicoes.clear()
        largura, altura = tela.winfo_width(), tela.winfo_height()
        if self.raiz is None:
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
                                  outline=ACENTO if no is self.selecionado else BORDA,
                                  width=2 if no is self.selecionado else 1, tags=tags)
            tela.create_text(x, y - 8, text=nome, font=(FONTE, 10, "bold"),
                             fill=TINTA, tags=tags)
            tela.create_text(x, y + 10, text=f"freq. {quantidade(no.peso)}",
                             font=(FONTE, 9), fill=SUAVE, tags=tags)

        foco = ancora or self.raiz
        x, y = self.posicoes[foco]
        tela.xview_moveto((x + margem - (largura / 2 if mouse_x is None else mouse_x)) / total_x)
        tela.yview_moveto(0 if mouse_y is None else (y - mouse_y) / total_y)
