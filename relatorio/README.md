# Relatório: Computação Gráfica 2026.2 (2ª etapa)

Relatório em LaTeX do trabalho de Computação Gráfica (IFCE, campus Fortaleza, Engenharia da
Computação, prof. Ajalmar Rocha Neto). Formatação ABNT, igual à do relatório do SAACI.

Entrega (Obs2 do enunciado): **2 arquivos**, um `.zip` com o código e um `.pdf` com este relatório.

## Estrutura

| Caminho | O que é |
|---|---|
| `main.tex` | Arquivo principal. Só junta as seções. |
| `config/preambulo.tex` | Formatação (fonte, margens, citação). Não mexer sem combinar. |
| `secoes/00-capa.tex` | Capa e sumário. |
| `secoes/01-introducao.tex` a `05-conclusao.tex` | Uma seção por arquivo. |
| `secoes/03-desenvolvimento/` | Uma subseção por etapa do enunciado (modelagem, cena, câmera, projeção, iluminação, rasterização). |
| `figuras/` | Imagens, uma pasta por seção e por etapa. |
| `referencias.bib` | Referências. A lista ABNT sai automática. |
| `ROADMAP.md` | Lista de tarefas do relatório. |

## Compilar

**No computador** (TeX Live com `biblatex-abnt`, `babel-portuges` e `biber`), dentro de `relatorio/`:

```bash
latexmk
```

**No Overleaf:** compilador **pdfLaTeX**. Envie a pasta `relatorio/` compactada em
**New Project → Upload Project**.

## Como citar e inserir figura

```latex
\cite{lorensen1987}   % (Lorensen; Cline, 1987)
\figura{04-simulacoes/cena-200px.png}{0.8\textwidth}{Cena rasterizada em 200 px}{fig:cena-200}{Os autores (2026)}
```

Figura: citada no texto antes de aparecer, legenda acima, fonte abaixo. Tudo o que falta
confirmar fica marcado com `\confirmar{...}` (aparece em vermelho no PDF).

## Trabalho em grupo

1. `git pull` antes de começar.
2. Cada pessoa escreve em um arquivo de `secoes/` por vez.
3. Commits em Conventional Commits, em português (ex.: `docs(modelagem): descreve marching cubes`).
