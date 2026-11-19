"""Inicie com: py compactador.py"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from arvore_visual import ArvoreVisual, AZUL, BORDA, FONTE, FUNDO, SUAVE, TINTA, quantidade
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


class Compactador:
    def __init__(self, janela):
        self.janela = janela
        janela.title("Compactador de arquivos")
        janela.configure(bg=FUNDO)
        janela.geometry(f"{min(1080, janela.winfo_screenwidth() - 48)}x"
                        f"{min(780, janela.winfo_screenheight() - 80)}")
        janela.minsize(750, 570)

        estilo = ttk.Style(janela)
        estilo.theme_use("clam")
        estilo.configure("TButton", font=(FONTE, 10), padding=(12, 6), background="white",
                         foreground=TINTA, bordercolor=BORDA, lightcolor="white",
                         darkcolor="white", focusthickness=1)
        estilo.map("TButton", background=[("active", "#edf3f8")])
        estilo.configure("Principal.TButton", font=(FONTE, 10, "bold"), padding=(15, 9),
                         background=AZUL, foreground="white", bordercolor=AZUL,
                         lightcolor=AZUL, darkcolor=AZUL)
        estilo.map("Principal.TButton", background=[("disabled", SUAVE), ("active", "#124a88")],
                   foreground=[("disabled", "white")])
        estilo.configure("Secundario.TButton", padding=(15, 9))

        pagina = tk.Frame(janela, bg=FUNDO, padx=22, pady=16)
        pagina.pack(fill="both", expand=True)
        topo = tk.Frame(pagina, bg=FUNDO)
        topo.pack(fill="x")
        tk.Label(topo, text="Compactador de arquivos", bg=FUNDO, fg=TINTA,
                 font=(FONTE, 24, "bold")).pack(side="left")
        tk.Label(topo, text="LZ77 + Huffman", bg=FUNDO, fg=AZUL,
                 font=(FONTE, 12, "bold")).pack(side="right")
        tk.Label(pagina, text="Escolha um texto para compactar ou um arquivo .huf para restaurar.",
                 bg=FUNDO, fg=SUAVE, font=(FONTE, 11)).pack(anchor="w", pady=(0, 12))

        acoes = tk.Frame(pagina, bg=FUNDO)
        acoes.pack(fill="x")
        self.compactar = ttk.Button(acoes, text="Compactar TXT…", style="Principal.TButton",
                                    command=lambda: self.escolher(True))
        self.compactar.pack(side="left")
        self.restaurar = ttk.Button(acoes, text="Descompactar HUF…", style="Secundario.TButton",
                                    command=lambda: self.escolher(False))
        self.restaurar.pack(side="left", padx=8)

        metricas = tk.Frame(pagina, bg=FUNDO)
        metricas.pack(fill="x", pady=(16, 4))
        self.valores = []
        for coluna, titulo in enumerate(("TXT original", "Arquivo compactado", "Economia de espaço")):
            metricas.columnconfigure(coluna, weight=1, uniform="medidas")
            cartao = tk.Frame(metricas, bg="white", padx=13, pady=7,
                              highlightbackground=BORDA, highlightthickness=1)
            cartao.grid(row=0, column=coluna, sticky="nsew", padx=(0 if coluna == 0 else 8, 0))
            tk.Label(cartao, text=titulo, bg="white", fg=SUAVE, font=(FONTE, 10)).pack(anchor="w")
            valor = tk.StringVar(value="—")
            self.valores.append(valor)
            tk.Label(cartao, textvariable=valor, bg="white", fg=TINTA,
                     font=(FONTE, 17, "bold")).pack(anchor="w")

        self.explicacao = tk.Label(pagina, bg=FUNDO, fg=SUAVE, justify="left", anchor="w",
                                   font=(FONTE, 10), wraplength=700,
                                   text="O tamanho de cada arquivo e a economia aparecerão após a leitura.")
        self.explicacao.pack(fill="x", pady=(2, 12))
        self.explicacao.bind("<Configure>", lambda e: self.explicacao.config(wraplength=max(1, e.width)))
        self.arvore = ArvoreVisual(pagina)
        self.arvore.pack(fill="both", expand=True)
        self.status = tk.StringVar(value="Escolha um arquivo para começar.")
        tk.Label(pagina, textvariable=self.status, bg=FUNDO, fg=SUAVE, anchor="w",
                 font=(FONTE, 10)).pack(fill="x", pady=(8, 0))

    def escolher(self, compactando):
        tipo = ("Texto", "*.txt") if compactando else ("Arquivo HZ77", "*.huf")
        origem = filedialog.askopenfilename(parent=self.janela, title="Escolha o arquivo de entrada",
                                            filetypes=[tipo])
        if not origem:
            return
        try:
            with open(origem, "rb") as entrada:
                dados = entrada.read()
        except (OSError, MemoryError) as erro:
            motivo = str(erro) or "Memória insuficiente para ler este arquivo."
            messagebox.showerror("Falha na leitura", motivo, parent=self.janela)
            return
        self.compactar.state(["disabled"])
        self.restaurar.state(["disabled"])
        nome = origem.replace("\\", "/").rsplit("/", 1)[-1]
        self.status.set(f"Processando {nome}…")
        for valor in self.valores:
            valor.set("—")
        self.explicacao.config(text="Calculando o tamanho do texto e do arquivo compactado…")
        self.arvore.definir(None, "Lendo os símbolos do arquivo…")
        etapas = compactar_em_etapas(dados) if compactando else descompactar_em_etapas(dados)
        self.janela.after(1, self.avancar, etapas, origem, len(dados), compactando)

    def avancar(self, etapas, origem, tamanho, compactando):
        try:
            etapa, fracao = next(etapas)
        except StopIteration as fim:
            dados, raiz = fim.value
            original, arquivo = (tamanho, len(dados)) if compactando else (len(dados), tamanho)
            self.mostrar_resultado(original, arquivo, raiz)
            self.compactar.state(["!disabled"])
            self.restaurar.state(["!disabled"])
            self.salvar(dados, origem, compactando)
            return
        except (ArquivoInvalido, MemoryError) as erro:
            self.compactar.state(["!disabled"])
            self.restaurar.state(["!disabled"])
            motivo = str(erro) or "Memória insuficiente para processar este arquivo."
            self.status.set("Processamento interrompido.")
            self.explicacao.config(text=motivo)
            self.arvore.definir(None, "A árvore está indisponível.")
            messagebox.showerror("Falha no processamento", motivo, parent=self.janela)
            return
        self.status.set(f"{etapa} · {fracao:.0%}")
        self.janela.after(1, self.avancar, etapas, origem, tamanho, compactando)

    def mostrar_resultado(self, original, arquivo, raiz):
        economia, explicacao = explicar_taxa(original, arquivo)
        for campo, valor in zip(self.valores, (f"{quantidade(original)} B",
                                               f"{quantidade(arquivo)} B", economia)):
            campo.set(valor)
        self.explicacao.config(text=explicacao)
        self.arvore.definir(raiz)

    def salvar(self, dados, origem, compactando):
        pasta, _, nome = origem.replace("\\", "/").rpartition("/")
        base = nome.rsplit(".", 1)[0] or nome
        extensao = ".huf" if compactando else ".txt"
        sugestao = base + (".huf" if compactando else ".restaurado.txt")
        tipo = ("Arquivo HZ77", "*.huf") if compactando else ("Texto", "*.txt")
        self.status.set(f"{nome} processado. Escolha onde salvar o resultado.")
        while True:
            destino = filedialog.asksaveasfilename(
                parent=self.janela, title="Salvar em um novo arquivo", initialdir=pasta,
                initialfile=sugestao, defaultextension=extensao, filetypes=[tipo],
                confirmoverwrite=False)
            if not destino:
                self.status.set(f"{nome} processado. Gravação cancelada.")
                return
            try:
                # Criação exclusiva protege o texto de entrada e arquivos já existentes.
                with open(destino, "xb") as saida:
                    saida.write(dados)
            except FileExistsError:
                messagebox.showinfo("Nome em uso", "Já existe um arquivo com esse nome. "
                                    "Escolha outro nome para salvar o resultado.", parent=self.janela)
                continue
            except OSError as erro:
                messagebox.showerror("Falha na gravação", str(erro), parent=self.janela)
                continue
            self.status.set(f"Arquivo salvo em {destino}")
            return


if __name__ == "__main__":
    janela = tk.Tk()
    Compactador(janela)
    janela.mainloop()
