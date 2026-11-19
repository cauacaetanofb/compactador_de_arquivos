"""Cores e controles compartilhados pelas janelas do compactador."""

from tkinter import ttk


FUNDO = "#131416"
PAINEL = "#1c1d21"
RELEVO = "#292a30"
BORDA = "#3c3e46"
TINTA = "#f4f4f6"
SUAVE = "#babcc8"
ACENTO = "#a8b1ff"
SOBRE_ACENTO = "#191d39"
VERDE = "#88dbb4"
AMBAR = "#f1c789"
ERRO = "#ffaaa6"
FONTE = "Segoe UI"


def aplicar_estilo(janela):
    estilo = ttk.Style(janela)
    estilo.theme_use("clam")
    for nome, fundo, texto, ativo, pressionado, borda, foco in (
        ("TButton", RELEVO, TINTA, "#393b45", "#444754", BORDA, ACENTO),
        ("Principal.TButton", ACENTO, SOBRE_ACENTO, "#bec5ff", "#949ff1", ACENTO, SOBRE_ACENTO),
    ):
        estilo.configure(nome, font=(FONTE, 10, "bold"), padding=(14, 8),
                         background=fundo, foreground=texto, bordercolor=borda,
                         darkcolor=fundo, lightcolor=fundo, focuscolor=foco, focusthickness=1)
        cores = [("disabled", RELEVO), ("pressed", pressionado), ("active", ativo)]
        estilo.map(nome, background=cores, lightcolor=cores, darkcolor=cores,
                   foreground=[("disabled", "#9496a0")],
                   bordercolor=[("focus", foco), ("active", ativo)])
    estilo.configure("Horizontal.TProgressbar", troughcolor=RELEVO, background=ACENTO,
                     bordercolor=RELEVO, lightcolor=ACENTO, darkcolor=ACENTO, thickness=6)
    estilo.configure("TScrollbar", troughcolor=FUNDO, background=RELEVO,
                     arrowcolor=TINTA, bordercolor=BORDA, lightcolor=RELEVO, darkcolor=RELEVO)
    estilo.map("TScrollbar", background=[("active", BORDA)])
