# Compactador de arquivos

Aplicação em Python que compacta textos combinando LZ77 e Huffman. A interface usa Tkinter. O módulo dos algoritmos usa somente recursos nativos do Python e não tem importações.

## Instalação e execução

### 1. Instale o Git e o Python 3 com Tkinter

O Git serve para baixar o repositório. O compactador usa a biblioteca padrão do Python e pode ser executado diretamente, sem instalar pacotes com `pip`.

- **Windows** — Instale o Git e o Python 3 pelos instaladores oficiais. Na instalação do Python, mantenha o suporte a Tcl/Tk habilitado. Depois, abra uma nova janela do PowerShell. [Git para Windows](https://git-scm.com/install/windows/) · [Python para Windows](https://www.python.org/downloads/windows/)
- **macOS** — Instale o Git e a distribuição oficial do Python 3, que inclui o Tkinter. Depois, abra o Terminal. [Git para macOS](https://git-scm.com/install/mac/) · [Python para macOS](https://www.python.org/downloads/macos/)
- **Ubuntu ou Debian** — Abra o terminal e instale os três pacotes:

  ```bash
  sudo apt update
  sudo apt install git python3 python3-tk
  ```

Para conferir a instalação, execute `git --version` e, em seguida, `py -m tkinter` no Windows ou `python3 -m tkinter` no macOS e no Linux. Quando a janela de demonstração do Tkinter abrir, feche-a para continuar no terminal.

### 2. Clone o repositório

No terminal, abra a pasta onde deseja guardar o projeto e execute:

```sh
git clone https://github.com/cauacaetanofb/compactador_de_arquivos.git
cd compactador_de_arquivos
```

### 3. Execute o compactador

Na pasta `compactador_de_arquivos`, execute o comando correspondente ao seu sistema.

**Windows (PowerShell)**

```powershell
py compactador.py
```

**macOS ou Linux**

```bash
python3 compactador.py
```

A janela **Compactador de arquivos** abrirá com as opções **Compactar** e **Descompactar**.

## Como usar

1. Em **Compactar**, clique em **Escolher TXT…**, selecione o texto e salve o arquivo `.huf`.
2. Em **Descompactar**, clique em **Escolher HUF…** para restaurar o TXT. A verificação de integridade ocorre antes de salvar. Se cancelar o salvamento, use **Salvar resultado…** para retomar.
3. O painel de resultado mostra os tamanhos dos arquivos e a economia de espaço. Para consultar a árvore do arquivo processado, clique em **Ver árvore…**. Na janela de detalhes, clique nas junções ou use as setas e a tecla Espaço. **Expandir tudo** mostra todos os ramos e Esc fecha a janela.

O programa lê e grava bytes. Isso preserva acentos, a codificação do texto, quebras de linha e a presença ou ausência da última quebra de linha. Os arquivos são processados em memória. O formato `.huf` deste projeto é identificado pela assinatura HZ77 e pela versão 1.

## Como os algoritmos trabalham juntos

O **LZ77** procura sequências de 3 a 258 bytes que já apareceram nos 4.096 bytes anteriores. Uma sequência encontrada vira uma instrução de cópia com comprimento e distância. Para limitar o tempo de busca, o programa compara até 64 posições anteriores com o mesmo prefixo de três bytes.

Por exemplo, em `ABABABAB`, o LZ77 emite os literais `A` e `B` e uma cópia de 6 bytes à distância 2. Ao restaurar, a cópia pode usar os bytes que ela própria acabou de escrever.

O **Huffman** conta as ocorrências de cada byte literal e de cada comprimento de cópia. A cada passo ele une os dois nós de menor frequência até formar a raiz. Na árvore, o ramo esquerdo vale `0` e o direito vale `1`. O caminho da raiz até uma folha forma seu código. Uma árvore de folha única usa o código `0`. As distâncias de cópia ocupam 12 bits cada.

Na visualização, **freq.** indica o número de ocorrências no fluxo gerado pelo LZ77. Uma folha **Copiar 6 B** conta quantas instruções de comprimento 6 apareceram. O peso de uma junção é a soma dos pesos dos dois filhos.

## Como interpretar a taxa

A interface calcula a economia com o tamanho **completo** do arquivo gerado, incluindo cabeçalho, árvore, bits codificados e preenchimento do último byte.

```text
Ocupação (%) = 100 × tamanho compactado / tamanho original
Economia (%) = 100 × (tamanho original − tamanho compactado) / tamanho original
```

Se um texto de 1.000 bytes gerar um arquivo de 400 bytes, o resultado ocupa 40% do original e a economia é de 60%. Uma economia negativa indica que o arquivo cresceu. Isso pode acontecer em textos curtos porque o cabeçalho e a árvore também ocupam espaço. Para um TXT vazio, o arquivo contém apenas os 17 bytes do cabeçalho e a taxa percentual é indefinida.

## Testes

Execute `py -m unittest -v` no Windows ou `python3 -m unittest -v` em outros sistemas. Os testes abrangem a restauração byte a byte, referências LZ77 sobrepostas, o limite da janela e a rejeição de arquivos danificados.
