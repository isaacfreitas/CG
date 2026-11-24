# Divergências entre o código e o enunciado

Só o que o código faz de forma diferente do PDF (`doc/Trabalho CG 2026_2.pdf`).
Serve para o grupo responder na apresentação. Não vai no zip.

## 1. Item 6: eliminação de faces ocultas

**O enunciado diz:** "elimine os polígonos que estão ocultos usando a informação da normal à
superfície do polígono e o eixo z da câmera".

**O código faz:** usa a normal e o vetor da câmera até o triângulo, ou seja, `n · v < 0`, em
coordenadas de câmera (`math_3d.face_voltada_para_camera`).

**Por que não usa só o eixo z:** na perspectiva, a direção em que a câmera vê cada triângulo muda
de triângulo para triângulo. Só no centro da imagem ela coincide com o eixo z. Perto das bordas,
o teste só pelo eixo z joga fora triângulos quase de lado que ainda aparecem.

**O que aconteceu no teste (eye principal, 800 × 800):**

| Critério | Faces de costas | Desenhadas | Resultado visual |
|---|---|---|---|
| `n · v < 0` (usado) | 32 204 | 30 248 | imagem limpa |
| só o eixo z (`normal_z > 0`) | 31 150 | 31 302 | falhas brancas na parede interna direita da lixeira; 1 731 pixels diferentes |

**Como mudar, se o professor exigir o eixo z:** em `math_3d.py`, a função
`face_voltada_para_camera` passa a receber só a normal e a devolver `normal_camera[2] > 0`. Depois
é preciso ajustar as 2 chamadas (`main.py` e `visualizar_projecao.py`) e refazer as figuras e os
números do relatório.

**O que dizer na apresentação:** o eixo z vale no centro da imagem. O grupo testou, viu as falhas
na borda e escolheu o vetor até o triângulo, que é o mesmo princípio (normal contra a direção de
visada) aplicado em cada ponto.

## 2. Item 4: polígonos não visíveis e o plano de projeção

**O enunciado diz:** "os polígonos que não são visíveis, não devem ser trazidos para o plano de
projeção".

**O código faz:** no `main.py`, os vértices de todos os triângulos são projetados num laço, e só
depois o recorte e o culling descartam as faces. Os triângulos descartados **não são
rasterizados nem iluminados**, mas os vértices deles chegam a ser projetados. Na figura do item
4a (`visualizar_projecao.py`), só os triângulos visíveis entram na janela.

**Efeito:** o resultado na imagem é o mesmo. Muda só a ordem das contas.
