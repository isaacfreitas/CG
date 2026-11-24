# Guia do Projeto — Trabalho de Computação Gráfica 2026.2 (2ª etapa)

Este guia explica **o que o projeto faz, como os dados fluem pelo pipeline e como cada item do
enunciado (`doc/Trabalho CG 2026_2.pdf`) foi resolvido**, com os conceitos de Computação Gráfica
por trás de cada etapa, onde está no código e as perguntas que podem aparecer na apresentação.

Todos os números citados aqui (vértices, caixas, base da câmera, matrizes) foram obtidos rodando o
próprio código com a configuração atual.

---

## Sumário

0. [Visão geral e fluxo do pipeline](#0-visão-geral-e-fluxo-do-pipeline)
1. [Item 1 — Modelagem dos 5 sólidos](#1-item-1--modelagem-dos-5-sólidos)
2. [Item 2 — Cena no sistema do mundo](#2-item-2--cena-no-sistema-do-mundo)
3. [Item 3 — Sistema de coordenadas da câmera](#3-item-3--sistema-de-coordenadas-da-câmera)
4. [Item 4 — Projeção em perspectiva e volume de visão](#4-item-4--projeção-em-perspectiva-e-volume-de-visão)
5. [Item 5 — Iluminação de Phong](#5-item-5--iluminação-de-phong)
6. [Item 6 — Rasterização](#6-item-6--rasterização)
7. [Como executar](#7-como-executar)
8. [Limitações conhecidas (e como responder sobre elas)](#8-limitações-conhecidas-e-como-responder-sobre-elas)
9. [Banco de perguntas rápidas](#9-banco-de-perguntas-rápidas)
10. [Glossário](#10-glossário)

---

## 0. Visão geral e fluxo do pipeline

O projeto é um **pipeline gráfico implementado do zero em Python**, sem OpenGL: toda a matemática
de transformações, câmera, projeção, iluminação e rasterização está escrita à mão com NumPy. As
únicas bibliotecas externas são:

| Biblioteca | Para quê | Permitido pelo enunciado? |
|---|---|---|
| `numpy` | vetores, matrizes, produto escalar/vetorial | sim (só álgebra) |
| `scikit-image` | **somente** a função `marching_cubes`, que gera a malha | sim: item 1b diz “não precisa implementar esse algoritmo, basta usar de alguma API” |
| `matplotlib` | mostrar a imagem final (`imshow`) e os gráficos 3D de apoio | sim (só exibição) |

### Arquivos e responsabilidades

| Arquivo | Papel | Itens do enunciado |
|---|---|---|
| [primitives.py](primitives.py) | Formas implícitas (cilindro, cone, esfera, caixa, toro) e operações booleanas | 1 |
| [modeling.py](modeling.py) | Os 5 objetos, Marching Cubes, normais, arestas → “sólido completo” | 1 |
| [math_3d.py](math_3d.py) | Matrizes 4×4 (T, R, S), base da câmera, look-at, projeção, recorte, culling | 2, 3, 4, 6 |
| [cena.py](cena.py) | Posição/rotação/escala de cada objeto, câmeras, luz, validação da cena | 2, 3, 5 |
| [illumination.py](illumination.py) | Modelo de Phong (ambiente + difusa + especular) | 5 |
| [rasterizer.py](rasterizer.py) | Equação da reta, scan-line par-ímpar, coordenadas baricêntricas | 6 |
| [main.py](main.py) | Junta tudo: renderiza a cena em 200, 400 e 800 px e com um 2º eye | 3e, 4, 5, 6 |
| [visualizar_objetos.py](visualizar_objetos.py) | Cada sólido no seu sistema do objeto, com normais | 1e |
| [visualizar_cena.py](visualizar_cena.py) | Todos os sólidos no sistema do mundo | 2b |
| [visualizar_camera.py](visualizar_camera.py) | A cena no sistema da câmera, eixos u, v, n, origem do mundo | 3a–3e |
| [visualizar_projecao.py](visualizar_projecao.py) | Sólidos 3D + seus polígonos projetados na janela | 4a |

### O fluxo de um vértice, do começo ao fim

```
 F(x,y,z) implícita ──Marching Cubes──► malha (vértices, faces) no SISTEMA DO OBJETO
                                         + normais das faces e dos vértices + arestas
        │
        │  M = T · Rz · Ry · Rx · S          (cena.py / math_3d.matriz_mundo)
        ▼
 SISTEMA DO MUNDO  (tudo dentro de [-10, 10]³, sem sobreposição)
        │
        │  View = [u v n | -u·eye, -v·eye, -n·eye]   (math_3d.look_at)
        ▼
 SISTEMA DA CÂMERA (eye na origem, olhando para -z)
        │
        │  P (perspectiva, fov 58°, near 0.1, far 100)   (math_3d.projecao_perspectiva)
        ▼
 COORDENADAS DE RECORTE (x, y, z, w)  ──► recorte pelo volume de visão (descarta a face)
        │
        │  ÷ w  (divisão perspectiva)
        ▼
 NDC  [-1, 1]³  ──► pixel: x = (x_ndc+1)/2·res ; y = (1−y_ndc)/2·res
        │
        ▼
 Por face visível:
   back-face culling (n·v < 0) → Phong nos 3 vértices → scan-line par-ímpar
   → baricêntrica (cor e z) → Z-buffer → arestas com a equação da reta
        │
        ▼
 IMAGEM (res × res × 3)  em 200, 400 e 800 px
```

A função que executa os estágios por face é `renderizar_cena_completa`
([main.py:110](main.py#L110)). A docstring dela lista os 8 estágios na mesma ordem do diagrama.

---

## 1. Item 1 — Modelagem dos 5 sólidos

> **Enunciado:** escolha 5 objetos do cotidiano; crie uma malha de triângulos (algoritmo próprio ou
> Marching Cubes por API); cada polígono deve ter uma normal apontando para fora; mostre cada sólido
> no seu sistema de coordenadas; crie uma função que retorne o sólido (vértices, arestas, faces,
> atributos).

### 1.1 Os objetos escolhidos

| Objeto | Construção (CSG sobre formas implícitas) | Cor | Vértices | Arestas | Faces |
|---|---|---|---|---|---|
| **Peão** | cilindro (base) ∪ cone truncado (corpo) ∪ cilindro (anel) ∪ esfera (cabeça) | `#E63946` vermelho | 7 756 | 23 262 | 15 508 |
| **Lápis** | cilindro (corpo) ∪ cilindro mais largo (anel da borracha) ∪ cone (ponta) | `#F4A261` laranja | 2 852 | 8 550 | 5 700 |
| **Altere** | 2 esferas ∪ cilindro em X (barra) | `#2A9D8F` verde-azulado | 5 560 | 16 674 | 11 116 |
| **Martelo** | cilindro (cabo) ∪ caixa (cabeça) | `#A8DADC` azul-claro | 2 408 | 7 218 | 4 812 |
| **Lixeira** | (cone truncado externo − cone truncado interno) ∪ toro (borda) | `#C77DFF` lilás | 12 660 | 37 974 | 25 316 |

(Contagens com a resolução 80 do Marching Cubes, usada no `main.py`.)

Funções de campo: `gerar_campo_lapis`, `gerar_campo_peao`, `gerar_campo_altere`,
`gerar_campo_martelo`, `gerar_campo_lixeira` em [modeling.py:91-188](modeling.py#L91-L188);
catálogo `MODELOS` em [modeling.py:193](modeling.py#L193).

### 1.2 Conceito: superfícies implícitas

Uma **superfície implícita** é descrita por uma função escalar `F(x, y, z)`:

- `F < 0` → ponto **dentro** do sólido
- `F = 0` → ponto **na superfície**
- `F > 0` → ponto **fora**

Exemplos implementados em [primitives.py](primitives.py):

| Forma | Função | Linha |
|---|---|---|
| Esfera | `(x−cx)² + (y−cy)² + (z−cz)² − r²` | [primitives.py:103](primitives.py#L103) |
| Cilindro (eixo Y) | `max(x² + z² − r², y − y_max, y_min − y)` | [primitives.py:57](primitives.py#L57) |
| Cone truncado | igual ao cilindro, mas com `r(y) = r_base + t·(r_topo − r_base)`, `t = (y−y_min)/h` | [primitives.py:77](primitives.py#L77) |
| Caixa | `max(|x−cx|−hx, |y−cy|−hy, |z−cz|−hz)` | [primitives.py:115](primitives.py#L115) |
| Toro (plano XZ) | `(√((x−cx)²+(z−cz)²) − R)² + (y−cy)² − r²` | [primitives.py:132](primitives.py#L132) |
| Cilindro (eixo X) | `max((y−cy)²+(z−cz)² − r², x − x_max, x_min − x)` | [primitives.py:150](primitives.py#L150) |

### 1.3 Conceito: CSG (Constructive Solid Geometry) com funções implícitas

Combinar sólidos vira operação sobre os valores de `F` ([primitives.py:20-50](primitives.py#L20-L50)):

| Operação | Fórmula | Lógica sobre o sinal |
|---|---|---|
| União `A ∪ B` | `min(A, B)` | dentro se estiver em **qualquer** um (OU) |
| Interseção `A ∩ B` | `max(A, B)` | dentro se estiver em **todos** (E) |
| Subtração `A − B` | `max(A, −B)` | dentro de A **e** fora de B (−B inverte dentro/fora) |

- O **cilindro finito** é a interseção de um tubo infinito com dois semiespaços (tampas).
- A **lixeira oca** é `subtracao(externo, interno)`: o cone interno começa em `y = 0,15`
  (deixa o fundo) e passa do topo (`ALTURA + 0,5`) para abrir a boca.
- O **altere** é a união simples das 2 esferas com a barra; a junção fica com aresta viva.

### 1.4 Conceito: Marching Cubes (geração da malha de triângulos)

O Marching Cubes (Lorensen & Cline, 1987) transforma um campo escalar amostrado em uma grade 3D na
malha de triângulos da superfície `F = 0`:

1. Avalia `F` em todos os nós de uma grade `res × res × res`.
2. Para cada cubinho (8 cantos), classifica cada canto como dentro/fora → 2⁸ = 256 casos
   (reduzidos por simetria a 15 configurações).
3. Em cada aresta do cubo onde o sinal muda, acha o ponto de cruzamento por **interpolação linear**.
4. Uma tabela diz quais triângulos ligar entre esses pontos.

**Implementação** — `extrair_malha` ([modeling.py:9](modeling.py#L9)):

```python
x, y, z = np.mgrid[lim0:lim1:complex(0,res), ...]   # grade 3D
volume = funcao_campo(x, y, z)                      # F em cada nó (vetorizado)
vertices, faces, _, _ = marching_cubes(volume, level=0.0)
vertices = vertices * passo + limites[0]            # índice da grade → coordenada real
```

O `marching_cubes` devolve os vértices em **índices da grade**; a última linha converte para as
coordenadas do objeto. Os `limites` de cada objeto (em `MODELOS`) são o cubo onde `F` é avaliada e
precisam envolver o objeto inteiro, senão a malha sai cortada.

### 1.5 Conceito: normais das faces e dos vértices

**Normal da face** ([modeling.py:47-51](modeling.py#L47-L51)): produto vetorial de duas arestas do
triângulo, normalizado:

```
n_face = (B − A) × (C − A) / |(B − A) × (C − A)|
```

O sentido do produto vetorial depende da **ordem dos vértices** (regra da mão direita). O Marching
Cubes entrega os triângulos com uma ordem consistente, de modo que a normal aponta **para fora**
(itens 1c e 1d). Isso é conferido visualmente no `visualizar_objetos.py`, que desenha setas pretas
saindo das faces.

**Normal do vértice** ([modeling.py:53-59](modeling.py#L53-L59)): soma das normais das faces que
tocam aquele vértice, normalizada. É usada na iluminação (Gouraud) para a cor variar suavemente
entre triângulos vizinhos.

O `+ 1e-12` no denominador evita divisão por zero em triângulos degenerados (área zero).

### 1.6 Arestas

Cada triângulo tem 3 arestas, mas cada aresta é compartilhada por 2 triângulos. O código guarda cada
par como `(menor, maior)` num `set`, que descarta as repetidas ([modeling.py:61-68](modeling.py#L61-L68)).

**Prova de que a malha está correta (fechada):** para toda malha triangular fechada sem buracos
(genus 0), vale a **característica de Euler** `V − A + F = 2` e também `A = 3F/2`. Todos os 5 objetos
satisfazem as duas:

| Objeto | V − A + F | 3F/2 |
|---|---|---|
| Peão | 7756 − 23262 + 15508 = **2** | 23 262 ✓ |
| Lápis | 2852 − 8550 + 5700 = **2** | 8 550 ✓ |
| Altere | 5608 − 16818 + 11212 = **2** | 16 818 ✓ |
| Martelo | 2408 − 7218 + 4812 = **2** | 7 218 ✓ |
| Lixeira | 12660 − 37974 + 25316 = **2** | 37 974 ✓ |

### 1.7 A função que retorna o sólido

`criar_solido` ([modeling.py:29](modeling.py#L29)) e o atalho `obter_solido(nome)`
([modeling.py:202](modeling.py#L202)) retornam um dicionário, exatamente o que o enunciado pede:

```python
{
  "nome": "Peão",
  "cor": [r, g, b],              # atributo: faces e arestas com a mesma cor
  "vertices": (V, 3),            # matriz de vértices
  "arestas": (A, 2),             # pares de índices
  "faces": (F, 3),               # triângulos (índices dos vértices)
  "normais_faces": (F, 3),       # normal unitária de cada face, para fora
  "normais_vertices": (V, 3),    # normal unitária de cada vértice
}
```

### 1.8 Item 1e — cada sólido no seu sistema do objeto

`visualizar_objetos.py` desenha cada sólido com os eixos x (vermelho), y (azul), z (verde) saindo
da origem **do objeto**, mais 60 setas de normais. Figuras em
[relatorio/figuras/03-desenvolvimento/01-modelagem/](relatorio/figuras/03-desenvolvimento/01-modelagem/).

Detalhe: o matplotlib desenha o 3º eixo “para cima”, e nos objetos o “cima” é **y**. A função
`para_plot` faz `(x, y, z) → (x, −z, y)` só na hora de desenhar. Isso é uma **rotação de 90° em
torno de x** (não um espelhamento), então o sistema continua de mão direita.

### Perguntas prováveis — Item 1

**P: Por que Marching Cubes e não um algoritmo próprio?**
R: O enunciado permite usar Marching Cubes por API. A vantagem é que modelamos cada objeto como uma
função implícita e combinamos formas com CSG (união/interseção/subtração), o que é muito mais simples
do que montar triângulos à mão para formas como o toro da lixeira ou o altere.

**P: Como vocês garantem que a normal aponta para fora?**
R: A normal é `(B−A)×(C−A)`; o sentido depende da ordem dos vértices. O Marching Cubes devolve os
triângulos numa ordem consistente que, com `F < 0` dentro, faz a normal apontar para fora. Conferimos
desenhando as normais como setas (`visualizar_objetos.py`) e, na prática, o back-face culling do item 6
só funciona porque elas estão para fora — se estivessem invertidas, veríamos o interior dos objetos.

**P: Qual a diferença entre normal de face e normal de vértice? Onde cada uma é usada?**
R: A de face é perpendicular ao triângulo e é usada no **back-face culling**. A de vértice é a média
(soma normalizada) das normais das faces vizinhas e é usada na **iluminação**, para o sombreamento
ficar suave (Gouraud).

**P: O que acontece se aumentar a resolução do Marching Cubes?**
R: A grade fica mais fina, a malha ganha mais triângulos e a superfície fica mais fiel à função
implícita (menos “facetada”), mas o custo cresce com `res³` para avaliar e com o número de faces para
rasterizar. Usamos 80 no `main.py` e 50 nos gráficos de apoio.

**P: Como a lixeira fica oca?**
R: Subtração CSG: `max(externo, −interno)`. O cone interno começa um pouco acima do fundo (sobra o
fundo) e vai além do topo (abre a boca). A borda é um toro unido ao corpo.

**P: Como sabem que a malha não tem buracos?**
R: Pela característica de Euler: `V − A + F = 2` em todos os 5 objetos, e `A = 3F/2` (cada aresta é
compartilhada por exatamente 2 triângulos).

---

## 2. Item 2 — Cena no sistema do mundo

> **Enunciado:** componha uma cena com os sólidos no sistema do mundo, sem sobreposição, usando
> escala, rotação e translação; nenhuma componente de vértice pode passar de |10|; mostre em 3D.

### 2.1 Conceito: coordenadas homogêneas e transformações afins

Com um ponto `(x, y, z)` escrito como `(x, y, z, 1)`, **translação, rotação e escala viram
multiplicações por matrizes 4×4**, e podem ser compostas numa única matriz
([math_3d.py:4-57](math_3d.py#L4-L57)):

```
T(tx,ty,tz) = | 1 0 0 tx |     S(sx,sy,sz) = | sx 0  0  0 |
              | 0 1 0 ty |                   | 0  sy 0  0 |
              | 0 0 1 tz |                   | 0  0  sz 0 |
              | 0 0 0 1  |                   | 0  0  0  1 |

Rx(θ) = | 1  0    0   0 |   Ry(θ) = |  cos 0 sin 0 |   Rz(θ) = | cos −sin 0 0 |
        | 0 cos −sin  0 |           |   0  1  0  0 |           | sin  cos 0 0 |
        | 0 sin  cos  0 |           | −sin 0 cos 0 |           |  0    0  1 0 |
        | 0  0    0   1 |           |   0  0  0  1 |           |  0    0  0 1 |
```

Sem coordenadas homogêneas a translação seria uma soma, e não daria para encadear tudo numa matriz.

### 2.2 A matriz do mundo `M = T · Rz · Ry · Rx · S`

`matriz_mundo` ([math_3d.py:60](math_3d.py#L60)). Lida **da direita para a esquerda**:

1. **Escala** (em torno da origem do objeto)
2. **Rotação** em x, depois y, depois z (em torno da origem do objeto)
3. **Translação** até a posição na cena

**A ordem importa** (multiplicação de matrizes não é comutativa): se transladássemos primeiro, a
rotação giraria o objeto em torno da origem do **mundo**, fazendo ele “orbitar” e sair do lugar.

Aplicação a todos os vértices de uma vez ([math_3d.py:73](math_3d.py#L73)):
`(homogeneos @ M.T)[:, :3]`, que é o mesmo que `M · p` para cada ponto `p`.

### 2.3 A cena montada

Configuração em `CENA` ([cena.py:34](cena.py#L34)):

| Objeto | Posição (x, z) | Rotação (x, y, z)° | Escala | Caixa no mundo (mín .. máx) |
|---|---|---|---|---|
| Peão | (−6,5; −4,5) | (0, 0, 0) | 1,2 | [−8,90 −2,00 −6,90] .. [−4,10 4,12 −2,10] |
| Lápis | (−8,0; 0,5) | (90, 45, 0) — deitado e na diagonal | 1,0 | [−8,46 −2,00 0,04] .. [−3,00 −0,37 5,50] |
| Altere | (−1,5; −4,5) | (0, 0, 90) — em pé sobre uma esfera | 0,9 | [−3,30 −2,00 −5,40] .. [−1,50 3,40 −3,60] |
| Martelo | (1,0; 3,2) | (−90, −30, 0) — deitado | 1,0 | [0,76 −2,00 −2,05] .. [4,86 −1,00 3,32] |
| Lixeira | (3,5; −4,5) | (0, 0, 0) | 1,1 | [1,68 −2,00 −6,32] .. [5,33 2,11 −2,67] |

Maior componente na cena: **8,90** (limite 10). As três transformações (escala, rotação e translação)
são de fato usadas, como o enunciado exige.

**Apoio no chão** — `montar_matriz` ([cena.py:58](cena.py#L58)): primeiro aplica só `R·S`, descobre o
`y` mínimo do objeto já girado/escalado e escolhe `ty = Y_CHAO − y_min`. Assim todo objeto encosta
exatamente em `y = −2` (repare que o `y` mínimo de todas as caixas é −2,00).

### 2.4 Validação automática

`validar_cena` ([cena.py:89](cena.py#L89)) confere a cena sozinha:

1. **Limite |10|:** `max(|vértice|) ≤ 10` para cada objeto.
2. **Sem sobreposição:** envolve cada objeto na sua **AABB** (Axis-Aligned Bounding Box, a menor
   caixa alinhada aos eixos que o contém). Duas caixas estão separadas se, em **pelo menos um eixo**,
   uma termina antes de a outra começar (teorema do eixo separador para AABBs). Se as caixas não se
   tocam, os objetos também não. Exige ainda uma folga de 0,1.

Se algo falhar, `imprimir_resumo` lança um erro — a cena nunca é renderizada inválida.

### 2.5 Item 2b — mostrar em 3D

`visualizar_cena.py` desenha os sólidos no mundo, os eixos x/y/z, a origem (ponto preto), o chão em
`y = −2`, o cubo `[−10, 10]³` tracejado e a AABB pontilhada de cada objeto (mostra que não se tocam).
Figura: [relatorio/figuras/03-desenvolvimento/02-cena/cena-mundo.png](relatorio/figuras/03-desenvolvimento/02-cena/cena-mundo.png).

### Perguntas prováveis — Item 2

**P: Por que usar matriz 4×4 e não 3×3?**
R: Porque translação não é linear em 3D (é uma soma). Em coordenadas homogêneas ela vira
multiplicação, e assim escala, rotação e translação se combinam numa única matriz.

**P: Por que a ordem T·R·S? O que acontece se inverter?**
R: Escala e rotação precisam acontecer com o objeto na origem dele. Se transladar antes, a rotação
seria em torno da origem do mundo e o objeto mudaria de posição; a escala também multiplicaria a
translação.

**P: Como garantem que não há interseção?**
R: Pelas AABBs: se as caixas envolventes não se cruzam, os objetos dentro delas também não. É um teste
conservador (pode recusar cenas que na verdade não se tocam), mas nunca aceita uma que se toca.

**P: Como uma rotação de 90° em z deixa o altere em pé?**
R: O altere foi modelado deitado ao longo de x. `Rz(90°)` leva o eixo x para o eixo y, então a barra
fica vertical.

**P: Como as normais são transformadas para o mundo?**
R: Com a **inversa transposta** da parte 3×3 de M (`matriz_normal`, [math_3d.py:83](math_3d.py#L83)).
Com escala não uniforme, transformar a normal pela própria M a deixaria inclinada em relação à
superfície. A inversa transposta preserva a perpendicularidade. (Na nossa cena as escalas são
uniformes, mas o código já está correto para o caso geral.)

---

## 3. Item 3 — Sistema de coordenadas da câmera

> **Enunciado:** escolha um eye; compute a base vetorial; transforme os objetos do mundo para a
> câmera; mostre em 3D; marque a origem do mundo; o eye pode mudar e uma nova imagem deve ser gerada.

### 3.1 Conceito: base ortonormal da câmera (u, v, n)

Dados `eye` (posição do observador), `at` (ponto para onde olha) e `up` (o “cima” do mundo),
`base_camera` ([math_3d.py:92](math_3d.py#L92)) calcula:

```
n = (eye − at) / |eye − at|        eixo z da câmera (aponta para TRÁS, do at para o eye)
u = (up × n)   / |up × n|          eixo x da câmera (direita)
v =  n × u                         eixo y da câmera (cima); já é unitário
```

Os três são **unitários e perpendiculares entre si** (ortonormais) e formam um sistema de mão direita.
Como `n` aponta para trás, a câmera **olha na direção −z** (convenção do OpenGL).

Valores reais com a câmera principal (`eye = (9,75; 13; 6,5)`, `at = (0, 0, 0)`, `up = (0, 1, 0)`):

```
u = ( 0,555;  0,000; −0,832)
v = (−0,618;  0,670; −0,412)
n = ( 0,557;  0,743;  0,371)
```

O código trata os dois casos degenerados: `eye = at` (sem direção de visada) e `eye` na mesma vertical
do `at` (`up` paralelo a `n`, produto vetorial nulo) — lança erro explicativo.

### 3.2 Matriz de visualização (look-at)

`look_at` ([math_3d.py:119](math_3d.py#L119)):

```
View = | u_x u_y u_z  −u·eye |
       | v_x v_y v_z  −v·eye |
       | n_x n_y n_z  −n·eye |
       |  0   0   0     1    |
```

É a composição **R · T(−eye)**: primeiro translada o eye para a origem, depois roda o mundo para os
eixos da câmera coincidirem com x, y, z (as linhas da rotação são u, v, n). Para a câmera principal:

```
| 0,555  0      −0,832    0      |
| −0,618 0,670  −0,412    0      |
| 0,557  0,743   0,371  −17,502  |      ← 17,502 = |eye − at|
| 0      0       0        1      |
```

(As duas primeiras translações dão 0 porque `at` é a origem: o eye está exatamente sobre o eixo n.)

### 3.3 Itens 3b–3e na prática

- **3a** — `main.py` e `visualizar_camera.py` imprimem u, v, n no terminal.
- **3b** — `aplicar_transformacao(view, vertices_mundo)` leva todos os vértices para a câmera.
- **3c** — `visualizar_camera.py` desenha os sólidos nesse sistema, com os eixos u, v, n saindo da
  origem (que é o eye) e o volume de visão (pirâmide tracejada) até o plano do `at`.
- **3d** — origem do mundo: ponto preto em `View · (0,0,0,1)` no `visualizar_camera.py`; na imagem
  rasterizada, uma **cruz laranja** (`desenhar_origem_mundo`, [main.py:87](main.py#L87)).
- **3e** — o eye muda pela linha de comando: `--eye X Y Z` em `main.py`, `visualizar_camera.py` e
  `visualizar_projecao.py`. Além disso, o `main.py` sempre gera uma **Tela 2** com um segundo eye
  `(26, 18, 28)`. Figuras: [eye1.png](relatorio/figuras/03-desenvolvimento/03-camera/eye1.png) e
  [eye2.png](relatorio/figuras/03-desenvolvimento/03-camera/eye2.png).

### Perguntas prováveis — Item 3

**P: Por que n aponta do at para o eye, e não o contrário?**
R: Convenção de sistema de mão direita (OpenGL): com u para a direita e v para cima, o z positivo sai
da tela em direção ao observador; logo a câmera olha para −z.

**P: Por que precisa do vetor up?**
R: Só `eye` e `at` definem a direção de visada, mas a câmera ainda poderia girar em torno dela. O `up`
fixa essa rotação: `u = up × n` fica horizontal e `v` fica o mais próximo possível do “cima” do mundo.

**P: Por que v = n × u não precisa ser normalizado?**
R: Porque n e u já são unitários e perpendiculares: `|n × u| = |n|·|u|·sen 90° = 1`.

**P: O que acontece se o eye estiver exatamente acima do at?**
R: `up` fica paralelo a `n`, o produto vetorial dá zero e a base não existe. O código detecta e
lança erro (seria preciso escolher outro `up`).

**P: Qual a relação entre a matriz View e a base?**
R: As linhas da parte 3×3 são u, v e n; a última coluna é `−(u·eye, v·eye, n·eye)`, que é a translação
do eye para a origem já escrita na nova base. Como é uma matriz ortonormal + translação, ela preserva
distâncias e ângulos (é uma transformação rígida).

**P: Como a imagem muda com outro eye?**
R: Só a matriz View muda; a cena no mundo é a mesma. Por isso basta recalcular u, v, n e reprojetar.

---

## 4. Item 4 — Projeção em perspectiva e volume de visão

> **Enunciado:** projeção perspectiva dos sólidos no volume de visão, polígono a polígono, na janela
> de projeção; polígonos não visíveis não vão para o plano; arestas e faces de um sólido com a mesma
> cor, sólidos diferentes com cores diferentes; apresentar em 2D na janela (com o 3D junto).

### 4.1 Conceito: projeção perspectiva

Por **semelhança de triângulos**, um ponto `(x, y, z)` da câmera projeta numa janela a distância `d`
em:

```
x' = d · x / (−z)        y' = d · y / (−z)
```

Objetos mais distantes (|z| maior) ficam menores — é isso que dá a sensação de profundidade.

### 4.2 A matriz de projeção

`projecao_perspectiva(fov=58°, aspecto=1, near=0.1, far=100)` ([math_3d.py:137](math_3d.py#L137)):

```
f = cotg(fov/2)

P = | f/aspecto  0        0                    0           |
    |   0        f        0                    0           |
    |   0        0   (far+near)/(near−far)  2·far·near/(near−far) |
    |   0        0       −1                    0           |
```

Valores reais (fov 58°):

```
| 1,804  0      0       0    |
| 0      1,804  0       0    |
| 0      0     −1,002  −0,2  |
| 0      0     −1       0    |
```

- `f = cotg(29°) ≈ 1,804` é o `d` da aula (para uma janela de altura 2, de −1 a 1).
- A última linha faz **w = −z**. Depois, a **divisão perspectiva** (`divisao_perspectiva`,
  [math_3d.py:157](math_3d.py#L157)) divide x, y, z por w — é exatamente o `x' = d·x/(−z)` da aula.
- A 3ª linha mapeia a profundidade: `z = −near → z_ndc = −1` e `z = −far → z_ndc = +1`. Esse `z_ndc`
  é guardado para o Z-buffer.

O resultado são as **NDC** (Normalized Device Coordinates), em `[−1, 1]³`. Depois
`ndc_para_pixel` ([main.py:27](main.py#L27)) leva para a tela:

```
x_pixel = (x_ndc + 1) / 2 · res
y_pixel = (1 − y_ndc) / 2 · res        ← inverte y: na imagem a linha 0 fica em cima
```

### 4.3 Volume de visão e recorte

O **volume de visão** (frustum) é a pirâmide truncada entre os planos near e far, limitada pelo fov.
Em **coordenadas de recorte** (antes de dividir por w), um ponto está dentro quando
`−w ≤ x, y, z ≤ w` — cada desigualdade é um dos 6 planos.

`face_no_volume_de_visao` ([math_3d.py:164](math_3d.py#L164)) descarta o **triângulo inteiro** quando:

1. **Algum vértice está atrás do near** (`z < −w`). Depois da divisão por w, esse vértice “passaria
   para o outro lado” da câmera e deformaria o triângulo.
2. **Os 3 vértices estão fora do mesmo plano** (esquerda, direita, baixo, cima ou far). Se estivessem
   fora de planos diferentes, o triângulo ainda poderia cruzar a tela, por isso é mantido.

Faces parcialmente fora que sobrevivem são cortadas na rasterização, que só pinta pixels dentro da
tela (clamping no scan-line).

### 4.4 “Polígonos não visíveis não devem ir para o plano”

Antes de projetar, cada face passa por dois filtros: **recorte** (acima) e **back-face culling**
(detalhado no item 6). O `main.py` conta e mostra no título de cada imagem quantas faces foram
desenhadas, quantas caíram fora do volume e quantas estavam de costas.

### 4.5 Cores

Cada sólido tem uma cor única (`MODELOS`). Faces e arestas usam **a mesma cor do sólido**: as arestas
são desenhadas com a equação da reta na cor iluminada dos próprios vértices (`desenhar_aresta`,
[main.py:65](main.py#L65)).

### 4.6 Item 4a — 3D e 2D juntos

`visualizar_projecao.py` mostra dois painéis:

- **3D:** os sólidos em coordenadas de câmera, a **janela de projeção** (quadrado tracejado no plano
  `z = −distância`) e, sobre ela, os triângulos visíveis já projetados. Uma reta pontilhada liga o eye
  ao centro de cada sólido e cruza a janela exatamente no ponto projetado (`x' = x·d/(−z)`).
- **2D:** a mesma janela vista de frente.

Como o matplotlib não tem Z-buffer, os triângulos são ordenados do mais distante para o mais próximo
(**algoritmo do pintor**) só nesse gráfico de apoio.

### Perguntas prováveis — Item 4

**P: Por que precisa da coordenada w e da divisão perspectiva?**
R: A projeção perspectiva divide por z, e divisão não é uma operação linear — não cabe numa matriz. O
truque é a matriz copiar `−z` para w; a divisão por w acontece depois, separadamente.

**P: O que são NDC?**
R: Coordenadas normalizadas em `[−1, 1]` nos três eixos, independentes da resolução. O mesmo NDC vira
200, 400 ou 800 pixels só mudando o `res` em `ndc_para_pixel`.

**P: Qual a diferença entre o recorte e o back-face culling?**
R: O recorte tira o que está **fora do campo de visão** (atrás do near, além do far ou fora das
laterais). O culling tira o que está **dentro** do campo de visão mas **de costas** para a câmera.

**P: Por que o recorte é feito antes da divisão por w?**
R: Porque um vértice atrás da câmera tem w negativo; dividir por w inverteria o sinal de x e y e ele
apareceria espelhado na tela. Em coordenadas de recorte o teste é só comparar com ±w.

**P: Vocês recortam o triângulo (Sutherland-Hodgman)?**
R: Não: o triângulo é aceito ou descartado inteiro. O que passa do limite da tela é cortado na
rasterização (só pixels dentro da imagem são pintados). Para a nossa cena, com todos os objetos à
frente da câmera, isso não causa perda visível.

**P: Para que serve o near e o far?**
R: Limitam a profundidade do volume de visão e definem o mapeamento do z para `[−1, 1]`. O near não pode
ser 0 porque a divisão por z explodiria.

---

## 5. Item 5 — Iluminação de Phong

> **Enunciado:** aplique iluminação aos vértices dos polígonos visíveis, calculando as componentes
> ambiente, difusa e especular para obter o RGB dos vértices/pixels.

### 5.1 Conceito

O **modelo de reflexão de Phong** (1975) soma três termos:

```
I = ka·Ia·O  +  kd·Il·O·max(N·L, 0)  +  ks·Il·max(R·V, 0)^α
     ambiente        difusa (Lambert)           especular
```

| Vetor | Significado (todos unitários) |
|---|---|
| **N** | normal da superfície no vértice |
| **L** | do vértice até a luz |
| **V** | do vértice até o observador (eye) |
| **R** | reflexão de L em torno de N: `R = 2(N·L)N − L` |

- **Ambiente:** luz indireta, constante; evita que o lado sem luz fique preto.
- **Difusa (Lei do cosseno de Lambert):** proporcional ao cosseno do ângulo entre N e L. Superfície
  de frente para a luz = mais clara. Não depende do observador.
- **Especular:** o brilho (“highlight”). É forte quando o observador está perto da direção de
  reflexão R. O expoente α (brilho) controla o tamanho da mancha: maior = mancha menor e mais nítida.

### 5.2 Implementação

`calcular_iluminacao_phong` ([illumination.py:11](illumination.py#L11)):

| Parâmetro | Valor |
|---|---|
| `ka, kd, ks` | 0,5; 0,8; 0,4 |
| Expoente de brilho α | 32 |
| Cor da luz | branca (1, 1, 1) |
| Posição da luz | (5, 20, 15) — `POSICAO_LUZ` em [cena.py:26](cena.py#L26) |
| Observador | o eye da câmera atual |

Detalhes:
- Ambiente e difusa são multiplicadas pela cor do objeto; **a especular não**, então o brilho sai
  branco (como num objeto plástico real).
- Se `N·L ≤ 0` (luz atrás da superfície), difusa e especular são zero.
- O resultado é limitado com `clip` a `[0, 1]`.
- O cálculo é feito **no sistema do mundo**, com as normais transformadas pela inversa transposta
  (`normais_mundo` em [main.py:145](main.py#L145)).

### 5.3 Só nos vértices visíveis, e uma vez só

No `main.py` ([main.py:184-195](main.py#L184-L195)), Phong roda **depois** do recorte e do culling —
só para vértices de faces visíveis, como o enunciado pede. Um vértice é compartilhado por ~6
triângulos, então a cor é guardada num dicionário `cores` e calculada uma única vez.

Calcular a cor nos vértices e interpolar dentro do triângulo é o **sombreamento de Gouraud**.

### Perguntas prováveis — Item 5

**P: Qual a diferença entre o modelo de Phong e o sombreamento de Phong?**
R: O **modelo** de Phong é a equação de iluminação (ambiente + difusa + especular). O **sombreamento**
de Phong interpola as *normais* e aplica o modelo em cada pixel. Nós usamos o modelo de Phong com
**sombreamento de Gouraud**: aplicamos a equação nos vértices e interpolamos as *cores* com a
baricêntrica.

**P: Por que a difusa não depende do observador?**
R: Uma superfície difusa (Lambertiana) espalha a luz igualmente em todas as direções, então parece igual
de qualquer ângulo. Só depende de quanta luz chega, que é proporcional a `cos θ = N·L`.

**P: O que o expoente 32 faz?**
R: Controla o quão concentrado é o brilho especular. `cos^32` cai muito rápido longe de R, gerando uma
mancha pequena; com expoente 2 a mancha seria grande e espalhada.

**P: Como se calcula R?**
R: Decompondo L na parte paralela à normal, `(N·L)N`, e espelhando a parte perpendicular:
`R = 2(N·L)N − L`.

**P: Por que normalizar os vetores?**
R: Porque o produto escalar só é igual ao cosseno do ângulo quando os vetores são unitários.

**P: Por que a especular aparece branca?**
R: Ela multiplica só a cor da luz (branca), não a do objeto — imita materiais como plástico, onde o
reflexo especular tem a cor da fonte de luz.

---

## 6. Item 6 — Rasterização

> **Enunciado:** rasterize em pelo menos 3 resoluções; antes, elimine polígonos ocultos usando a normal
> e o eixo z da câmera; depois, calcule a cor dos pixels por interpolação baricêntrica; use a
> rasterização de retas (livro, subseção 5.2.1) e de polígonos (par-ímpar com scan-line).

### 6.1 Três resoluções

`RESOLUCOES_TELA = [200, 400, 800]` ([main.py:17](main.py#L17)). A Tela 1 do `main.py` mostra as três
lado a lado; com `--salvar` gera os PNGs em
[relatorio/figuras/04-simulacoes/](relatorio/figuras/04-simulacoes/). Como tudo até as NDC é igual,
só a conversão para pixel muda — dá para comparar o efeito do **aliasing** (serrilhado) na resolução
baixa.

### 6.2 Back-face culling (eliminação de faces ocultas)

`face_voltada_para_camera` ([math_3d.py:198](math_3d.py#L198)):

```
desenha a face  ⇔  n · v < 0
```

- `n` = normal da face **no sistema da câmera** (normal do objeto → mundo com a inversa transposta →
  câmera com a parte 3×3 da View, [main.py:149-150](main.py#L149-L150)).
- `v` = vetor do observador até a face. Na câmera o eye é a origem, então `v = vértice − eye = vértice`.
- `n · v < 0` → a normal aponta **contra** a direção de visada → face de frente.
- `n · v ≥ 0` → de costas ou de lado → descartada.

**Por que não testar só o sinal de `n_z` (o eixo z da câmera)?** Em projeção **perspectiva** a direção
de visada muda de face para face; só no centro da imagem ela coincide com o eixo z. Testar apenas
`n_z` descartaria, perto das bordas, faces quase de lado que ainda são visíveis. O teste `n·v` é o
geral e, no centro da imagem (`v ≈ (0, 0, −1)`), ele se reduz a `n_z > 0`, isto é, à condição do
enunciado com o eixo z da câmera.

Em objetos fechados, o culling elimina cerca de metade das faces — economia grande antes da etapa cara
(rasterizar pixel a pixel).

### 6.3 Rasterização de retas — equação da reta

`rasterizar_reta` ([rasterizer.py:14](rasterizer.py#L14)), o algoritmo dado em aula:

- Calcula `dx = x2 − x1`, `dy = y2 − y1`, `m = dy/dx` e `b = y1 − m·x1`.
- Se `|dx| > |dy|` (reta mais deitada): anda de 1 em 1 em x e calcula `y = m·x + b`.
- Senão (reta mais em pé): anda de 1 em 1 em y e calcula `x = (y − b)/m`.
- Cada ponto vira um fragmento em `produz_fragmento` ([rasterizer.py:5](rasterizer.py#L5)): o pixel
  é a **parte inteira** de x e de y, e o centro dele fica em `(int(x) + 0,5, int(y) + 0,5)`.
- Além do quadro: os extremos viram inteiros (o laço sempre termina), o passo pode ser −1 (reta da
  direita para a esquerda ou de cima para baixo) e a reta vertical (`dx = 0`, m infinito) é tratada à
  parte. Os pontos saem na ordem de p1 para p2, porque a cor e o z são interpolados pela posição na lista.

Exemplo de (0,0) a (5,2): m = 0,4, e os pixels são (0,0), (1,0), (2,0), (3,1), (4,1), (5,2). Como o
algoritmo trunca, y = 0,8 em x = 2 ainda cai no pixel 0.

Onde é usado:
- **Arestas de cada face** (`desenhar_aresta`, [main.py:65](main.py#L65)), na cor iluminada dos
  vértices, interpolando cor e z ao longo da reta. Isso também **fecha frestas** que o scan-line pode
  deixar nas bordas dos triângulos.
- **Grade do chão** e **cruz da origem** (`desenhar_reta_3d_no_zbuffer`, [main.py:40](main.py#L40)).

### 6.4 Rasterização de polígonos — scan-line par-ímpar

`scan_line_par_impar` ([rasterizer.py:72](rasterizer.py#L72)):

1. Acha `y_min` e `y_max` do polígono (limitados à tela).
2. Para **cada linha horizontal** `y` (scan line), calcula a interseção com cada aresta:
   `x = x1 + (y − y1)·(x2 − x1)/(y2 − y1)`.
3. A condição `y1 ≤ y < y2` (intervalo semiaberto) evita contar duas vezes um vértice compartilhado por
   duas arestas e ignora arestas horizontais.
4. Ordena as interseções e **pinta entre os pares** (1ª–2ª, 3ª–4ª, ...) — regra **par-ímpar**: um ponto
   está dentro se uma semirreta a partir dele cruza a borda um número ímpar de vezes.
5. `ceil` no início e `floor` no fim do intervalo: só entram pixels cujo centro está dentro.

O algoritmo é genérico (qualquer polígono); aqui ele recebe triângulos.

### 6.5 Interpolação baricêntrica

`coordenadas_baricentricas` ([rasterizer.py:53](rasterizer.py#L53)). Para um pixel P dentro do
triângulo ABC:

```
α = área(P, B, C) / área(A, B, C)
β = área(A, P, C) / área(A, B, C)
γ = 1 − α − β
```

As áreas vêm do determinante (produto vetorial 2D) em `calcular_area_triangulo`
([rasterizer.py:46](rasterizer.py#L46)). Propriedades: `α + β + γ = 1`, e P está dentro se as três são
≥ 0 — o código usa isso como verificação extra.

Com elas o `main.py` interpola ([main.py:206-218](main.py#L206-L218)):

```
cor_pixel = α·cor_A + β·cor_B + γ·cor_C        ← Gouraud
z_pixel   = α·z_A   + β·z_B   + γ·z_C          ← para o Z-buffer
```

### 6.6 Z-buffer (extra, além do pedido)

Matriz `res × res` iniciada com `+∞` ([main.py:128](main.py#L128)). Para cada pixel, só pinta se
`z_pixel < z_buffer[y, x]` (mais perto da câmera) e atualiza o buffer. Resolve corretamente a
visibilidade **entre objetos** e **dentro de objetos côncavos** (ex.: o interior da lixeira), coisa
que o culling sozinho não resolve. `Z_BIAS = 0,005` dá uma folga nas retas da grade/origem para
evitar *z-fighting* (cintilação quando duas superfícies têm quase o mesmo z).

### 6.7 Elementos extras na imagem

- **Grade do chão** em `y = −2`, de −10 a 10, a cada 5 unidades ([main.py:97](main.py#L97)).
- **Cruz laranja na origem do mundo** (item 3d) ([main.py:87](main.py#L87)).
- **Título** com a contagem: total de faces, desenhadas, fora do volume e de costas.

### Perguntas prováveis — Item 6

**P: Por que andar em x quando |dx| > |dy| e em y no caso contrário?**
R: Para não deixar buracos. Andando sempre em x, uma reta em pé (m > 1) subiria mais de um pixel em y
a cada passo e ficaria pontilhada. Andando no eixo que mais varia, cada passo muda no máximo 1 pixel
no outro eixo.

**P: E a reta vertical?**
R: Nela `dx = 0` e m é infinito, então `x = (y − b)/m` não pode ser calculado. O código trata à parte:
x fica fixo e y anda de 1 em 1.

**P: Qual a diferença para o Bresenham?**
R: A equação da reta calcula `m·x + b` em ponto flutuante a cada passo e trunca o resultado. O
Bresenham (aprimoramento) decide o próximo pixel só com soma e subtração de inteiros e uma variável de
erro, e escolhe o pixel mais perto da reta (arredonda). De (0,0) a (5,2), ele daria (2,1) e (4,2) onde
a equação da reta dá (2,0) e (4,1).

**P: Explique a regra par-ímpar.**
R: Traçando uma linha horizontal pelo polígono, ela entra e sai alternadamente. Ordenando as
interseções, os trechos entre a 1ª e a 2ª, a 3ª e a 4ª etc. estão dentro.

**P: Por que o intervalo `y1 ≤ y < y2` (semiaberto)?**
R: Num vértice onde duas arestas se encontram, a scan line tocaria as duas e contaria a interseção
duas vezes, quebrando a paridade. O intervalo semiaberto conta cada vértice uma vez só e descarta
arestas horizontais (`y1 = y2`), que causariam divisão por zero.

**P: O que são coordenadas baricêntricas?**
R: Os pesos (α, β, γ) que escrevem P como combinação dos vértices: `P = αA + βB + γC`, com soma 1. Cada
peso é a razão entre a área do subtriângulo oposto ao vértice e a área total. Quanto mais perto de A,
maior α.

**P: Por que fazer culling se já tem Z-buffer?**
R: Desempenho: o culling descarta cerca de metade das faces com um único produto escalar, antes da
etapa cara (Phong + rasterização por pixel). O Z-buffer resolve o que sobra: objetos na frente de
outros e partes côncavas de um mesmo objeto.

**P: O culling basta para remover superfícies ocultas?**
R: Só para um objeto **convexo** sozinho. Na lixeira (côncava) ou quando um objeto está na frente de
outro, faces de frente também podem estar escondidas — por isso o Z-buffer.

**P: Qual o efeito da resolução?**
R: Em 200×200 cada pixel cobre uma área maior da cena: as bordas ficam serrilhadas (aliasing) e
triângulos pequenos podem sumir. Em 800×800 a imagem fica mais fiel, mas o custo cresce com o número
de pixels (16× mais pixels que 200×200).

**P: Por que desenhar as arestas por cima das faces?**
R: Dois motivos: o enunciado pede arestas da mesma cor do sólido, e o scan-line com `ceil/floor` pode
deixar frestas de um pixel entre triângulos vizinhos; a aresta fecha essas frestas.

**P: Por que o renderizador demora?**
R: É Python puro, pixel a pixel, por fidelidade didática ao algoritmo da aula. Uma implementação real
vetorizaria com NumPy ou usaria a GPU.

---

## 7. Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 visualizar_objetos.py                  # item 1e — cada sólido no seu sistema
python3 visualizar_cena.py                     # item 2b — cena no mundo
python3 cena.py                                # item 2  — só imprime caixas e valida
python3 visualizar_camera.py                   # item 3  — cena no sistema da câmera
python3 visualizar_camera.py --eye 26 18 28    # item 3e — outro eye
python3 visualizar_projecao.py                 # item 4a — 3D + janela de projeção
python3 main.py                                # itens 4, 5, 6 — imagem final (alguns minutos)
python3 main.py --eye 26 18 28                 # item 3e na imagem final
python3 main.py --salvar eye1                  # salva eye1-200/400/800.png no relatório
```

**Roteiro sugerido para a apresentação:** seguir a ordem acima — mostra a evolução objeto → mundo →
câmera → projeção → imagem final, exatamente na ordem dos itens do enunciado. Para o item 3e, rodar
`visualizar_camera.py` com dois eyes (é rápido) em vez do `main.py`.

---

## 8. Limitações conhecidas (e como responder sobre elas)

| Limitação | Resposta |
|---|---|
| Recorte descarta o triângulo inteiro, sem Sutherland-Hodgman | Os objetos ficam todos à frente da câmera; triângulos parcialmente fora das laterais são cortados pelo clamping na rasterização. Recortar polígonos seria a evolução natural. |
| Interpolação de cor em espaço de tela (não corrigida por perspectiva) | Gouraud clássico. Em triângulos pequenos (malha fina do Marching Cubes) a diferença é imperceptível. A profundidade `z_ndc`, por outro lado, é afim no espaço de tela, então a interpolação dela está correta. |
| Teste de sobreposição por AABB | É conservador: pode recusar uma cena que não se toca, mas nunca aceita uma que se toca. |
| Malha depende do Marching Cubes por API | Permitido explicitamente pelo item 1b. |
| Renderização lenta | Python puro por pixel, para seguir os algoritmos da aula literalmente. |
| Z-buffer não foi pedido | É um extra; o culling pedido está implementado e é aplicado antes. |

---

## 9. Banco de perguntas rápidas

| Pergunta | Resposta curta | Onde |
|---|---|---|
| Quais são os sistemas de coordenadas do pipeline? | Objeto → mundo → câmera → recorte → NDC → tela | §0 |
| O que retorna a função do sólido? | dict com vértices, arestas, faces, normais de face e vértice, cor | [modeling.py:29](modeling.py#L29) |
| Como se combina formas implícitas? | união = min, interseção = max, subtração = max(A, −B) | [primitives.py:20](primitives.py#L20) |
| Como se calcula a normal de um triângulo? | `(B−A)×(C−A)` normalizado | [modeling.py:50](modeling.py#L50) |
| Como transformar normais? | inversa transposta da parte 3×3 | [math_3d.py:83](math_3d.py#L83) |
| Ordem da matriz do mundo? | T·Rz·Ry·Rx·S (escala, rotação, translação) | [math_3d.py:60](math_3d.py#L60) |
| Como checar |10|? | `max(|vértices|) ≤ 10` | [cena.py:101](cena.py#L101) |
| Como checar sobreposição? | AABBs separadas em algum eixo | [cena.py:106](cena.py#L106) |
| Base da câmera? | n = (eye−at)/‖·‖, u = up×n /‖·‖, v = n×u | [math_3d.py:92](math_3d.py#L92) |
| Para onde a câmera olha? | −z | [math_3d.py:152](math_3d.py#L152) |
| O que faz w = −z? | permite a divisão perspectiva x' = d·x/(−z) | [math_3d.py:153](math_3d.py#L153) |
| Teste do volume de visão? | −w ≤ x, y, z ≤ w | [math_3d.py:164](math_3d.py#L164) |
| Teste de culling? | n·v < 0 em coordenadas de câmera | [math_3d.py:198](math_3d.py#L198) |
| Componentes de Phong? | ambiente ka·O, difusa kd·O·(N·L), especular ks·(R·V)^32 | [illumination.py:11](illumination.py#L11) |
| Fórmula de R? | 2(N·L)N − L | [illumination.py:38](illumination.py#L38) |
| Gouraud ou Phong shading? | Gouraud (cor nos vértices, interpolada) | [main.py:184](main.py#L184) |
| Algoritmo de reta? | equação da reta, y = m·x + b, anda no eixo que mais varia | [rasterizer.py:14](rasterizer.py#L14) |
| Algoritmo de polígono? | scan-line par-ímpar | [rasterizer.py:72](rasterizer.py#L72) |
| Baricêntrica? | razão de áreas, α+β+γ=1 | [rasterizer.py:53](rasterizer.py#L53) |
| Resoluções? | 200, 400, 800 | [main.py:17](main.py#L17) |
| NDC → pixel? | x=(x+1)/2·res, y=(1−y)/2·res | [main.py:27](main.py#L27) |
| Visibilidade entre objetos? | Z-buffer (menor z vence) | [main.py:213](main.py#L213) |
| Como provar que a malha é fechada? | V − A + F = 2 e A = 3F/2 | §1.6 |

---

## 10. Glossário

- **AABB** — caixa envolvente alinhada aos eixos.
- **Back-face culling** — descarte de faces voltadas para longe do observador.
- **CSG** — modelagem por combinação booleana de sólidos (união, interseção, subtração).
- **Coordenadas homogêneas** — `(x, y, z, w)`; permitem translação e perspectiva como matrizes.
- **Coordenadas de recorte (clip)** — resultado de `P · View · M · p`, antes da divisão por w.
- **Divisão perspectiva** — dividir x, y, z por w; leva de clip para NDC.
- **Frustum / volume de visão** — pirâmide truncada entre near e far que a câmera enxerga.
- **Gouraud** — iluminação calculada nos vértices e interpolada nos pixels.
- **Marching Cubes** — algoritmo que extrai uma malha de triângulos de um campo escalar.
- **NDC** — coordenadas normalizadas do dispositivo, em `[−1, 1]³`.
- **Par-ímpar** — regra de preenchimento: dentro se cruzar a borda um número ímpar de vezes.
- **Superfície implícita** — superfície definida por `F(x, y, z) = 0`.
- **Z-buffer** — matriz com a profundidade do que já foi pintado em cada pixel.
- **Z-fighting** — cintilação quando duas superfícies têm profundidades quase iguais.
