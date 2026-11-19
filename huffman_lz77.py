"""Formato HZ77 v1. Toda a lógica usa apenas recursos nativos do Python."""

ASSINATURA = b"HZ77\x01"
JANELA = 4096
MINIMO = 3
MAXIMO = 258
ALFABETO = 256 + MAXIMO - MINIMO + 1
PASSO = 32768
CABECALHO = len(ASSINATURA) + 8 + 4


class ArquivoInvalido(ValueError):
    """O conteúdo não corresponde a um arquivo HZ77 v1 íntegro."""


class No:
    def __init__(self, peso, simbolo=None, esquerda=None, direita=None):
        self.peso = peso
        self.simbolo = simbolo
        self.esquerda = esquerda
        self.direita = direita


def tokens_lz77(dados):
    """Emite (símbolo, distância). Distância zero identifica um byte literal."""
    ultimos = {}
    anteriores = [-1] * JANELA
    posicao = 0
    tamanho = len(dados)
    while posicao < tamanho:
        limite = min(MAXIMO, tamanho - posicao)
        melhor = 0
        distancia = 0
        if limite >= MINIMO:
            chave = dados[posicao:posicao + MINIMO]
            candidato = ultimos.get(chave, -1)
            inicio = max(0, posicao - JANELA)
            # Limita o custo de prefixos muito comuns. Empates favorecem o mais próximo.
            for _ in range(64):
                if candidato < inicio:
                    break
                comprimento = MINIMO
                while (comprimento < limite and
                       dados[candidato + comprimento] == dados[posicao + comprimento]):
                    comprimento += 1
                if comprimento > melhor:
                    melhor = comprimento
                    distancia = posicao - candidato
                    if melhor == limite:
                        break
                candidato = anteriores[candidato % JANELA]

        avanco = melhor or 1
        if distancia:
            yield 256 + melhor - MINIMO, distancia
        else:
            yield dados[posicao], 0

        # Indexa também o interior de uma repetição para as próximas buscas.
        for indice in range(posicao, min(posicao + avanco, tamanho - MINIMO + 1)):
            antigo = indice - JANELA
            if antigo >= 0:
                chave_antiga = dados[antigo:antigo + MINIMO]
                if ultimos.get(chave_antiga) == antigo:
                    del ultimos[chave_antiga]
            chave = dados[indice:indice + MINIMO]
            anteriores[indice % JANELA] = ultimos.get(chave, -1)
            ultimos[chave] = indice
        posicao += avanco


def montar_arvore(frequencias):
    folhas = sorted((No(peso, simbolo) for simbolo, peso in enumerate(frequencias)
                     if peso), key=lambda no: no.peso)
    if not folhas:
        return None
    # As folhas e os nós combinados formam duas filas ordenadas por peso.
    combinados = []
    folha = combinado = 0

    def retirar_menor():
        nonlocal folha, combinado
        if folha < len(folhas) and (combinado == len(combinados) or
                                    folhas[folha].peso <= combinados[combinado].peso):
            folha += 1
            return folhas[folha - 1]
        combinado += 1
        return combinados[combinado - 1]

    for _ in range(len(folhas) - 1):
        esquerda, direita = retirar_menor(), retirar_menor()
        combinados.append(No(esquerda.peso + direita.peso,
                             esquerda=esquerda, direita=direita))
    return retirar_menor()


class EscritorDeBits:
    def __init__(self):
        self.dados = bytearray()
        self.buffer = 0
        self.quantidade = 0

    def escrever(self, valor, largura):
        self.buffer = (self.buffer << largura) | valor
        self.quantidade += largura
        while self.quantidade >= 8:
            self.quantidade -= 8
            self.dados.append(self.buffer >> self.quantidade)
            self.buffer &= (1 << self.quantidade) - 1

    def finalizar(self):
        if self.quantidade:
            self.escrever(0, 8 - self.quantidade)
        return self.dados


class LeitorDeBits:
    def __init__(self, dados):
        self.dados = dados
        self.indice = CABECALHO
        self.buffer = 0
        self.quantidade = 0

    def ler(self, largura):
        while self.quantidade < largura:
            if self.indice >= len(self.dados):
                raise ArquivoInvalido("O arquivo termina antes do esperado.")
            self.buffer = (self.buffer << 8) | self.dados[self.indice]
            self.indice += 1
            self.quantidade += 8
        self.quantidade -= largura
        valor = self.buffer >> self.quantidade
        self.buffer &= (1 << self.quantidade) - 1
        return valor


def gravar_arvore(no, bits, codigos, codigo=0, largura=0):
    if no.simbolo is not None:
        bits.escrever(1, 1)
        bits.escrever(no.simbolo, 9)
        codigos[no.simbolo] = (codigo, max(1, largura))
        return
    bits.escrever(0, 1)
    gravar_arvore(no.esquerda, bits, codigos, codigo << 1, largura + 1)
    gravar_arvore(no.direita, bits, codigos, (codigo << 1) | 1, largura + 1)


def ler_arvore(bits):
    vistos = set()
    internos = 0

    def visitar():
        nonlocal internos
        if bits.ler(1):
            simbolo = bits.ler(9)
            if simbolo in vistos:
                raise ArquivoInvalido("A árvore contém um símbolo duplicado.")
            vistos.add(simbolo)
            return No(0, simbolo)
        internos += 1
        if internos >= ALFABETO:
            raise ArquivoInvalido("A árvore excede o número possível de símbolos.")
        return No(0, esquerda=visitar(), direita=visitar())

    return visitar()


def somar_pesos(no):
    if no.simbolo is None:
        no.peso = somar_pesos(no.esquerda) + somar_pesos(no.direita)
    elif no.peso == 0:
        raise ArquivoInvalido("A árvore contém uma folha sem ocorrências.")
    return no.peso


def verificar_em_etapas(dados):
    """Calcula Adler-32 em blocos e devolve o controle à interface entre blocos."""
    a, b = 1, 0
    for inicio in range(0, len(dados), PASSO):
        bloco = dados[inicio:inicio + PASSO]
        for valor in bloco:
            a += valor
            b += a
        a %= 65521
        b %= 65521
        yield "Verificando integridade", (inicio + len(bloco)) / len(dados)
    return (b << 16) | a


def compactar_em_etapas(dados):
    """Produz eventos de progresso e retorna (arquivo HZ77, árvore de Huffman)."""
    frequencias = [0] * ALFABETO
    referencias = []
    posicao = 0
    proximo = PASSO
    for simbolo, distancia in tokens_lz77(dados):
        frequencias[simbolo] += 1
        if distancia:
            referencias.append((posicao, simbolo, distancia))
            posicao += simbolo - 256 + MINIMO
        else:
            posicao += 1
        if posicao >= proximo:
            yield "Buscando repetições", posicao / len(dados)
            proximo = posicao + PASSO

    raiz = montar_arvore(frequencias)
    bits = EscritorDeBits()
    codigos = {}
    if raiz is not None:
        gravar_arvore(raiz, bits, codigos)
    posicao = 0
    # Uma sentinela permite tratar os últimos literais como qualquer outro trecho.
    referencias.append((len(dados), None, 0))
    proximo = PASSO
    for inicio, simbolo, distancia in referencias:
        while posicao < inicio:
            bits.escrever(*codigos[dados[posicao]])
            posicao += 1
            if posicao >= proximo:
                yield "Codificando com Huffman", posicao / len(dados)
                proximo = posicao + PASSO
        if distancia:
            bits.escrever(*codigos[simbolo])
            bits.escrever(distancia - 1, 12)
            posicao += simbolo - 256 + MINIMO
            if posicao >= proximo:
                yield "Codificando com Huffman", posicao / len(dados)
                proximo = posicao + PASSO

    soma = yield from verificar_em_etapas(dados)
    cabecalho = ASSINATURA + len(dados).to_bytes(8, "big") + soma.to_bytes(4, "big")
    return cabecalho + bits.finalizar(), raiz


def descompactar_em_etapas(arquivo):
    """Produz eventos de progresso e retorna (bytes originais, árvore reconstruída)."""
    if len(arquivo) < CABECALHO or not arquivo.startswith(ASSINATURA):
        raise ArquivoInvalido("Escolha um .huf criado por este compactador (HZ77 v1).")
    tamanho = int.from_bytes(arquivo[5:13], "big")
    esperado = int.from_bytes(arquivo[13:17], "big")
    bits = LeitorDeBits(arquivo)
    raiz = ler_arvore(bits) if tamanho else None
    saida = bytearray()
    proximo = PASSO
    while len(saida) < tamanho:
        no = raiz
        if no.simbolo is not None:
            if bits.ler(1):
                raise ArquivoInvalido("Código inválido para uma árvore de folha única.")
        else:
            while no.simbolo is None:
                no = no.direita if bits.ler(1) else no.esquerda
        no.peso += 1
        if no.simbolo < 256:
            saida.append(no.simbolo)
        else:
            comprimento = no.simbolo - 256 + MINIMO
            distancia = bits.ler(12) + 1
            if distancia > len(saida) or len(saida) + comprimento > tamanho:
                raise ArquivoInvalido("O arquivo contém uma referência LZ77 inválida.")
            # A cópia pode usar os bytes que ela própria acabou de produzir.
            for _ in range(comprimento):
                saida.append(saida[-distancia])
        if len(saida) >= proximo:
            yield "Reconstruindo o texto", len(saida) / tamanho
            proximo = len(saida) + PASSO
    if bits.indice != len(arquivo) or bits.buffer:
        raise ArquivoInvalido("Há dados inesperados no final do arquivo.")
    soma = yield from verificar_em_etapas(saida)
    if soma != esperado:
        raise ArquivoInvalido("A verificação de integridade falhou. O arquivo está danificado.")
    if raiz is not None:
        somar_pesos(raiz)
    return bytes(saida), raiz
