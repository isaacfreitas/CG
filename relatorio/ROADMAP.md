# Roadmap do relatório

Entrega: `.zip` do código + `.pdf` do relatório, em grupo de 3. A nota vem da apresentação,
com estes entregáveis como insumo. Data de entrega e de apresentação: a definir pelo professor.

O relatório precisa ter: capa, introdução, objetivo, desenvolvimento, simulações
computacionais, conclusão e referências (Obs1).

## Fase 0: Configuração

- [x] 0.1 Esqueleto LaTeX criado (main, preâmbulo, seções, figuras, referências)
- [ ] 0.2 Compilar o esqueleto sem erro (`latexmk`)
- [x] 0.3 Capa: nomes dos 3 integrantes e título do trabalho
- [ ] 0.4 Definir quem escreve cada seção

## Fase 1: Texto base

- [x] 1.1 Introdução
- [x] 1.2 Objetivos (geral e específicos)

## Fase 2: Desenvolvimento (uma subseção por etapa do enunciado)

Depende do código: cada etapa só é escrita depois de a visualização correspondente existir
em `main.py` (ver `DOCUMENTACAO.md`, seção 1).

- [x] 2.1 Modelagem dos 5 objetos (item 1): objetos, Marching Cubes, normais, função que retorna o sólido
- [x] 2.2 Composição da cena (item 2): matriz do mundo, limite $|10|$, sem interseção
- [x] 2.3 Sistema da câmera (item 3): base vetorial, transformação, origem do mundo, outros valores de eye
- [x] 2.4 Projeção em perspectiva (item 4): volume de visão, polígonos não visíveis, cor por sólido
- [x] 2.5 Iluminação (item 5): Phong, ambiente, difusa e especular
- [x] 2.6 Rasterização (item 6): culling, equação da reta, scan line par-ímpar, baricêntrica, Z-buffer

## Fase 3: Simulações computacionais

- [x] 3.1 Gerar e salvar as imagens dos 5 objetos nos próprios sistemas
- [x] 3.2 Gerar cena no mundo e na câmera (pelo menos 2 valores de eye)
- [x] 3.3 Gerar projeção e rasterização em 3 resoluções (200, 400, 800 px)
- [x] 3.4 Descrever ambiente, parâmetros e tempo de execução

## Fase 4: Fechamento

- [x] 4.1 Conclusão
- [ ] 4.2 Referências: livro-texto (subseção 5.2.1) e conferir todas as citações
- [ ] 4.3 Revisar o texto e resolver todos os `\confirmar{...}`
- [ ] 4.4 Gerar o PDF final
- [ ] 4.5 Gerar o `.zip` do código sem `.venv` e sem `__pycache__`
- [ ] 4.6 Subir os 2 arquivos (zip + pdf), sem link de drive
- [ ] 4.7 Preparar a apresentação
