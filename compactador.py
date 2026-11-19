"""Inicie com: py compactador.py"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from arvore_visual import ArvoreVisual, quantidade
from estilo import ACENTO, AMBAR, BORDA, ERRO, FONTE, FUNDO, PAINEL, SUAVE, TINTA, VERDE, aplicar_estilo
from huffman_lz77 import ArquivoInvalido, compactar_em_etapas, descompactar_em_etapas


def percentual(valor):
    return f"{valor:,.2f}".translate(str.maketrans(",.", ".,")).rstrip("0").rstrip(",") + "%"


def explicar_taxa(original, compactado):
    if original == 0:
        return "Indefinida", (
            f"O TXT tem 0 bytes e o .huf ocupa {quantidade(compactado)} bytes de cabeçalho. "
            "A taxa percentual é indefinida porque o cálculo dividiria por zero."
        )
    ocupacao = percentual(100 * compactado / original)
    economia = percentual(100 * (original - compactado) / original)
    diferenca = abs(original - compactado)
    unidade = "byte" if diferenca == 1 else "bytes"
    if compactado < original:
        efeito = f"A compactação poupou {quantidade(diferenca)} {unidade}."
    elif compactado > original:
        efeito = f"O arquivo cresceu {quantidade(diferenca)} {unidade} após a compactação."
    else:
        efeito = "Os dois arquivos têm o mesmo tamanho."
    return economia, (
        f"O .huf ocupa {ocupacao} do original, incluindo cabeçalho, árvore e dados. "
        f"{efeito} A economia é (1 − tamanho compactado ÷ tamanho original) × 100."
    )


def desenhar_formatos(tela, compactando):
    """Mostra a direção da operação e distingue os dois formatos de arquivo."""
    tela.delete("all")
    meio = tela.winfo_width() / 2
    for x, tipo in zip((meio - 58, meio + 58), ("TXT", "HUF") if compactando else ("HUF", "TXT")):
        texto = tipo == "TXT"
        w, h = (48, 54) if texto else (43, 47)
        y = (80 - h) / 2
        x -= w / 2
        cor = "#bcc4d3" if texto else ACENTO
        fundo = "#303440" if texto else "#343955"
        tela.create_polygon(x, y, x+w-12, y, x+w, y+12, x+w, y+h, x, y+h,
                            outline=cor, fill=fundo, width=2)
        tela.create_line(x+w-12, y+1, x+w-12, y+12, x+w-1, y+12, fill=cor)
        if texto:
            tela.create_line(x+8, y+11, x+25, y+11, fill=cor)
            tela.create_line(x+8, y+16, x+20, y+16, fill=cor)
        else:
            for linha in range(4):
                dente = x + 9 + (linha % 2) * 3
                tela.create_line(dente, y+2+3*linha, dente+3, y+2+3*linha, fill=cor, width=2)
        tela.create_text(x+w/2, y+h-14, text=tipo, fill=cor, font=("Consolas", 10, "bold"))
    tela.create_line(meio-18, 40, meio+18, 40, fill=SUAVE, width=2,
                     arrow="last", arrowshape=(7, 8, 3))


def rotulo(pai, texto="", tamanho=10, cor=TINTA, negrito=False, **opcoes):
    fonte = (FONTE, tamanho, "bold" if negrito else "normal")
    return tk.Label(pai, text=texto, bg=pai["bg"], fg=cor, font=fonte,
                    anchor="w", justify="left", bd=0, padx=0, pady=0, **opcoes)


def quebrar_linhas(label, largura=480):
    label.configure(wraplength=largura)
    label.bind("<Configure>", lambda e: label.configure(wraplength=max(1, e.width - 2)))


class Compactador:
    def __init__(self, janela):
        self.janela = janela
        self.raiz = self.janela_arvore = self.pendente = None
        self.origem = ""
        self.compactando = True
        janela.title("Compactador de arquivos")
        janela.configure(bg=FUNDO)
        aplicar_estilo(janela)

        pagina = tk.Frame(janela, bg=FUNDO, padx=24, pady=20)
        pagina.pack(fill="x")
        rotulo(pagina, "Compactador de arquivos", 23, negrito=True).pack(anchor="w", pady=(0, 16))

        acoes = tk.Frame(pagina, bg=FUNDO)
        acoes.pack(fill="x")
        for coluna in (0, 1):
            acoes.columnconfigure(coluna, weight=1, uniform="operacoes")
        self.compactar = self.cartao(acoes, 0, True)
        self.restaurar = self.cartao(acoes, 1, False)

        self.resultado = tk.Frame(pagina, bg=PAINEL, padx=16, pady=12,
                                  highlightbackground=BORDA, highlightthickness=1)
        cabecalho = tk.Frame(self.resultado, bg=PAINEL)
        cabecalho.pack(fill="x")
        self.titulo = rotulo(cabecalho, tamanho=14, negrito=True)
        self.titulo.pack(side="left")
        self.ver_arvore = ttk.Button(cabecalho, text="Ver árvore…", command=self.abrir_arvore)
        self.mensagem = rotulo(self.resultado, cor=SUAVE)
        self.mensagem.pack(fill="x", pady=(3, 0))
        quebrar_linhas(self.mensagem)
        self.progresso = ttk.Progressbar(self.resultado, maximum=100)

        self.metricas = tk.Frame(self.resultado, bg=PAINEL)
        self.valores = []
        for coluna, titulo in enumerate(("TXT original", "Arquivo .huf", "Economia de espaço")):
            self.metricas.columnconfigure(coluna, weight=1, uniform="metricas")
            bloco = tk.Frame(self.metricas, bg=PAINEL)
            bloco.grid(column=coluna, row=0, sticky="nsew")
            rotulo(bloco, titulo, 9, SUAVE).pack(anchor="w")
            valor = rotulo(bloco, tamanho=15, negrito=True)
            valor.pack(anchor="w")
            self.valores.append(valor)
        self.explicacao = rotulo(self.resultado, cor=SUAVE)
        quebrar_linhas(self.explicacao)

        self.gravacao = tk.Frame(self.resultado, bg=PAINEL)
        self.destino = tk.StringVar()
        self.caminho = tk.Entry(self.gravacao, textvariable=self.destino, state="readonly",
                                readonlybackground=PAINEL, fg=TINTA, relief="flat",
                                highlightthickness=1, highlightbackground=BORDA,
                                highlightcolor=ACENTO, font=(FONTE, 10), width=8)
        self.salvar_novamente = ttk.Button(self.gravacao, text="Salvar resultado…", command=self.salvar)
        self.rotulo_destino = rotulo(self.gravacao, "Salvo em", cor=SUAVE)
        self.rodape = tk.Frame(pagina, bg=FUNDO)
        self.rodape.pack(fill="x", pady=(14, 0))
        largura = min(750, janela.winfo_screenwidth() - 90)
        tk.Frame(self.rodape, bg=BORDA, height=1, width=largura).pack(fill="x", pady=(0, 9))
        self.status = tk.StringVar(value="Pronto")
        rotulo(self.rodape, textvariable=self.status, cor=SUAVE, tamanho=9).pack(side="left")
        rotulo(self.rodape, "LZ77 + Huffman", 9, SUAVE).pack(side="right")
        pagina.bind("<Configure>", lambda _: self.ajustar_altura())
        self.janela.after_idle(self.ajustar_altura)

    def ajustar_altura(self):
        altura = min(self.janela.winfo_reqheight(), self.janela.winfo_screenheight() - 80)
        if self.janela.minsize() != (510, altura):
            self.janela.minsize(510, altura)

    def cartao(self, pai, coluna, compactando):
        cartao = tk.Frame(pai, bg=PAINEL, highlightbackground=BORDA, highlightthickness=1)
        cartao.grid(row=0, column=coluna, sticky="nsew", padx=(0, 6) if compactando else (6, 0))
        faixa = tk.Canvas(cartao, bg="#25283a" if compactando else "#26282e",
                          width=1, height=80, highlightthickness=0)
        faixa.pack(fill="x")
        faixa.bind("<Configure>", lambda _: desenhar_formatos(faixa, compactando))
        corpo = tk.Frame(cartao, bg=PAINEL, padx=16, pady=13)
        corpo.pack(fill="x")
        titulo = "Compactar" if compactando else "Descompactar"
        descricao = "Crie um arquivo .huf a partir do texto." if compactando else "Recupere o texto original de um .huf."
        rotulo(corpo, titulo, 15, negrito=True).pack(anchor="w")
        instrucao = rotulo(corpo, descricao, cor=SUAVE)
        instrucao.pack(fill="x", pady=(2, 12))
        quebrar_linhas(instrucao, 230)
        botao = ttk.Button(corpo, text="Escolher TXT…" if compactando else "Escolher HUF…",
                           style="Principal.TButton" if compactando else "TButton",
                           command=lambda: self.escolher(compactando))
        botao.pack(fill="x")
        return botao

    def habilitar_acoes(self, ativo):
        for botao in (self.compactar, self.restaurar):
            botao.state(["!disabled" if ativo else "disabled"])

    def escolher(self, compactando):
        tipo = ("Arquivo de texto", "*.txt") if compactando else ("Arquivo HZ77", "*.huf")
        titulo = "Escolher TXT para compactar" if compactando else "Escolher HUF para descompactar"
        origem = filedialog.askopenfilename(parent=self.janela, title=titulo, filetypes=[tipo])
        if not origem:
            return
        if self.janela_arvore:
            self.fechar_arvore()
        self.pendente = self.raiz = None
        self.origem = origem
        self.compactando = compactando
        self.habilitar_acoes(False)
        for widget in (self.ver_arvore, self.metricas, self.explicacao, self.gravacao,
                       self.caminho, self.rotulo_destino, self.salvar_novamente):
            widget.pack_forget()
        self.resultado.pack(fill="x", before=self.rodape, pady=(14, 0))
        self.titulo.config(text="Compactando…" if compactando else "Descompactando…")
        self.mensagem.config(text=self.nome_entrada, fg=SUAVE)
        self.progresso.configure(value=0)
        self.progresso.pack(fill="x", pady=(12, 2))
        self.status.set("Lendo arquivo…")
        self.janela.after(1, self.ler_arquivo)

    @property
    def nome_entrada(self):
        return self.origem.replace("\\", "/").rsplit("/", 1)[-1]

    def falha(self, erro):
        self.progresso.pack_forget()
        self.habilitar_acoes(True)
        self.titulo.config(text="Falha na operação")
        self.mensagem.config(text=str(erro) or "Memória insuficiente para processar o arquivo.", fg=ERRO)
        self.status.set("Escolha outro arquivo ou tente novamente.")
        (self.compactar if self.compactando else self.restaurar).focus_set()

    def ler_arquivo(self):
        try:
            with open(self.origem, "rb") as entrada:
                dados = entrada.read()
        except (OSError, MemoryError) as erro:
            self.falha(erro)
            return
        etapas = compactar_em_etapas(dados) if self.compactando else descompactar_em_etapas(dados)
        self.avancar(etapas, len(dados))

    def avancar(self, etapas, tamanho):
        try:
            etapa, fracao = next(etapas)
        except StopIteration as fim:
            dados, self.raiz = fim.value
            self.pendente = dados
            original, arquivo = (tamanho, len(dados)) if self.compactando else (len(dados), tamanho)
            self.mostrar_resultado(original, arquivo)
            self.salvar()
            self.habilitar_acoes(True)
            return
        except (ArquivoInvalido, MemoryError) as erro:
            self.falha(erro)
            return
        self.status.set(f"{etapa}… {fracao:.0%}")
        self.progresso.configure(value=100 * fracao)
        self.janela.after(1, self.avancar, etapas, tamanho)

    def mostrar_resultado(self, original, arquivo):
        self.progresso.pack_forget()
        self.titulo.config(text="Texto compactado" if self.compactando else "Texto restaurado")
        self.ver_arvore.pack(side="right")
        self.metricas.pack(fill="x", pady=(12, 5))
        economia, explicacao = explicar_taxa(original, arquivo)
        for campo, valor in zip(self.valores, (f"{quantidade(original)} B", f"{quantidade(arquivo)} B", economia)):
            campo.config(text=valor)
        cor = VERDE if arquivo < original else AMBAR if original and arquivo > original else TINTA
        self.valores[2].config(fg=cor)
        self.explicacao.config(text=explicacao)
        self.explicacao.pack(fill="x")
        self.gravacao.pack(fill="x", pady=(10, 0))
        self.status.set("Escolha onde salvar o resultado.")
        self.janela.update_idletasks()

    def abrir_arvore(self):
        if self.janela_arvore:
            self.janela_arvore.deiconify()
            self.janela_arvore.lift()
            self.janela_arvore.focus_set()
            return
        detalhe = tk.Toplevel(self.janela, bg=FUNDO)
        self.janela_arvore = detalhe
        detalhe.title(f"Árvore de Huffman — {self.nome_entrada}")
        detalhe.transient(self.janela)
        detalhe.geometry(f"{min(900, detalhe.winfo_screenwidth()-80)}x"
                         f"{min(500, detalhe.winfo_screenheight()-100)}")
        detalhe.minsize(520, 310)
        arvore = ArvoreVisual(detalhe)
        arvore.pack(fill="both", expand=True)
        arvore.definir(self.raiz)
        detalhe.protocol("WM_DELETE_WINDOW", self.fechar_arvore)
        detalhe.bind("<Escape>", lambda _: self.fechar_arvore())
        arvore.tela.focus_set()

    def fechar_arvore(self):
        self.janela_arvore.destroy()
        self.janela_arvore = None
        self.ver_arvore.focus_set()

    def salvar(self):
        pasta, _, nome = self.origem.replace("\\", "/").rpartition("/")
        base = nome.rsplit(".", 1)[0] or nome
        extensao = ".huf" if self.compactando else ".txt"
        sugestao = base + (".huf" if self.compactando else ".restaurado.txt")
        tipo = ("Arquivo HZ77", "*.huf") if self.compactando else ("Arquivo de texto", "*.txt")
        while True:
            destino = filedialog.asksaveasfilename(
                parent=self.janela, title="Salvar em um novo arquivo", initialdir=pasta,
                initialfile=sugestao, defaultextension=extensao, filetypes=[tipo],
                confirmoverwrite=False)
            if not destino:
                self.status.set("Gravação pendente")
                self.salvar_novamente.pack(side="left")
                self.salvar_novamente.focus_set()
                return
            try:
                with open(destino, "xb") as saida:
                    saida.write(self.pendente)
            except FileExistsError:
                messagebox.showinfo("Nome em uso", "Escolha um novo nome para preservar o arquivo existente.",
                                    parent=self.janela)
                continue
            except OSError as erro:
                messagebox.showerror("Falha na gravação", str(erro), parent=self.janela)
                continue
            self.pendente = None
            self.salvar_novamente.pack_forget()
            self.destino.set(destino)
            self.rotulo_destino.pack(side="left", padx=(0, 8))
            self.caminho.pack(side="left", fill="x", expand=True)
            self.janela.after_idle(self.caminho.xview_moveto, 1)
            self.status.set("Arquivo salvo")
            return


if __name__ == "__main__":
    janela = tk.Tk()
    Compactador(janela)
    janela.mainloop()
