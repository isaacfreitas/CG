# Documentação e status do Trabalho CG 2026.2 (2ª etapa)

Esta branch (`novos-modelos`) parte da v1 com peças de xadrez (`main`). Ficou só o que é
aproveitável para o trabalho novo, e os objetos foram trocados por **objetos do cotidiano**.

Documentos de referência (fora do repositório, compartilhados pelo grupo):
- Enunciado: `Trabalho CG 2026_2.docx-2.pdf`
- Análise de reaproveitamento (base deste plano): `Documentacao_Projeto_CG.pdf`

---

## 1. Resumo: estamos no caminho certo?

**Sim.** O pipeline (modelagem → mundo → câmera → projeção → iluminação → rasterização)
já segue a ordem dos itens do enunciado, e os **5 objetos já estão modelados e posicionados**
na cena, sem sobreposição e dentro do limite |10|.

O que falta é, principalmente, **mostrar as etapas intermediárias** (o código hoje só mostra a
imagem final rasterizada) e alguns ajustes pontuais exigidos pelo enunciado.

| Item do enunciado | Status | Resumo |
|---|---|---|
| 1 – Modelagem dos 5 objetos | 🟢 Pronto | `modeling.criar_solido` retorna o sólido completo; `visualizar_objetos.py` mostra cada um no seu sistema |
| 2 – Cena no mundo | 🟢 Pronto | `cena.py`: M = T·Rz·Ry·Rx·S com escala e rotação reais, `validar_cena` automática; `visualizar_cena.py` plota o mundo |
| 3 – Sistema da câmera | 🟢 Pronto | `math_3d.base_camera` calcula u, v, n; `visualizar_camera.py` plota a cena em coordenadas de câmera; `--eye` troca o observador; origem marcada em (0, 0, 0) |
| 4 – Projeção perspectiva | 🟢 Pronto | Recorte pelo volume de visão (`face_no_volume_de_visao`); `visualizar_projecao.py` plota os sólidos e a janela de projeção; arestas com a equação da reta na cor do sólido |
| 5 – Iluminação | 🟢 Pronto | Phong (ambiente + difusa + especular) por vértice |
| 6 – Rasterização | 🟢 Pronto | 3 resoluções, scan-line par-ímpar, baricêntrica, equação da reta, Z-buffer; culling em coordenadas de câmera com a normal da face |
| Relatório (Obs. 1) | 🔴 Falta | Capa, introdução, objetivo, desenvolvimento, simulações, conclusão, referências |
| Entrega (Obs. 2) | 🔴 Falta | `.zip` do código (sem `.venv`, `__pycache__`) + `.pdf` do relatório |

---

## 2. Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # numpy, matplotlib, scikit-image
python3 main.py                        # eye padrão da Tela 1
python3 main.py --eye 26 18 28         # outro eye na Tela 1 (item 3e)
python3 visualizar_camera.py --eye 26 18 28   # cena em coordenadas de câmera (item 3)
python3 visualizar_projecao.py --eye 26 18 28 # sólidos 3D + janela de projeção (item 4a)
```

Saída do `main.py`:
- **Terminal:** o eye e a base da câmera principal (`u`, `v`, `n`).
- **Tela 1:** a cena pela câmera principal (padrão `EYE_PRINCIPAL = (9.75, 13, 6.5)`, ou o valor de
  `--eye`) em 200, 400 e 800 px.
- **Tela 2:** segunda vista (`EYE_SECUNDARIO = (26, 18, 28)`) em 800 px, com a
  gaiola da cena.
- **Nas duas telas:** uma pequena cruz laranja marca a origem do mundo, exatamente em (0, 0, 0).

> A renderização é em Python puro, pixel a pixel: a resolução de 800×800 leva alguns minutos.

O `visualizar_camera.py` é leve (segundos). Ele imprime a base, leva os vértices de todos os
sólidos para o sistema da câmera e mostra o resultado em 3D, com os eixos `u`, `v`, `n` e um
ponto preto na origem do mundo.

---

## 3. Estrutura do projeto

| Arquivo | Responsabilidade | Status |
|---|---|---|
| `primitives.py` | Formas implícitas F(x,y,z) (F<0 dentro) e operações CSG | Pronto (+ `cilindro_x` novo) |
| `modeling.py` | `extrair_malha` (Marching Cubes), os 5 objetos, `criar_solido`/`obter_solido` e o catálogo `MODELOS` (limites e cor) | Pronto |
| `visualizar_objetos.py` | Item 1e: plot 3D de cada sólido no sistema do objeto | Pronto |
| `math_3d.py` | Matrizes 4×4: translação, escala, rotações X/Y/Z, `matriz_mundo`, `matriz_normal`, `aplicar_transformacao`, `base_camera` (u, v, n), look-at, perspectiva | Pronto |
| `cena.py` | `CENA` (posição, rotação, escala), `montar_cena`, `validar_cena` (limite |10| e sobreposição) | Pronto |
| `visualizar_cena.py` | Item 2b: plot 3D da cena no mundo com eixos, origem e cubo |10| | Pronto |
| `visualizar_camera.py` | Item 3: plot 3D da cena em coordenadas de câmera, com a origem do mundo e os eixos u, v, n (`--eye`) | Pronto |
| `visualizar_projecao.py` | Item 4a: sólidos em coordenadas de câmera, janela de projeção e polígonos visíveis projetados (3D + vista frontal da janela; `--eye`) | Pronto |
| `illumination.py` | Modelo de Phong por vértice | Pronto |
| `rasterizer.py` | Equação da reta, área, baricêntricas, scan-line par-ímpar | Pronto |
| `main.py` | Configuração (`CENA`, câmeras, luz), renderização e exibição | Pronto para o item 6 (`--eye` e origem do mundo incluídos); faltam as visualizações dos itens 2 e 4 |
| `requirements.txt` | `numpy==2.2.6`, `matplotlib==3.10.9`, `scikit-image==0.25.2` | Pronto |

### Pipeline (o que acontece em `main.py`)

```
Campo F(x,y,z) ──► Marching Cubes ──► Matriz do mundo (T·R·S) ──► View (look_at)
   (primitives)       (modeling)          (obj → mundo)              (mundo → câmera)
                                                                          │
Imagem RGB ◄── Z-buffer ◄── Baricêntrica ◄── Scan-line ◄── Phong ◄── Culling ◄── Recorte ◄── Projeção ÷w
              (+ arestas                     par-ímpar    por vértice                         (→ NDC → pixel)
               eq. da reta)
```

1. **Malha (uma vez por objeto):** `extrair_malha` avalia o campo numa grade 80³ e chama
   `skimage.measure.marching_cubes`, que devolve vértices e faces (triângulos). `criar_solido`
   calcula as normais, as arestas e guarda tudo no dicionário do sólido.
2. **Mundo:** `cena.montar_cena` monta `M = T · Rz · Ry · Rx · S` para cada item da `CENA`;
   o `t_y` é calculado para o ponto mais baixo encostar no chão (`y = -2`). As normais vão
   para o mundo pela inversa transposta de M (`math_3d.matriz_normal`).
3. **Câmera:** `base_camera(eye, at, up)` calcula `n = (eye−at)/|eye−at|`, `u = up×n`,
   `v = n×u` e devolve os três. `look_at` usa essa base para montar a view matrix, e
   `aplicar_transformacao(matriz, pontos)` leva uma lista de pontos (N, 3) de um sistema ao outro.
4. **Projeção:** `projecao_perspectiva(fov, aspecto, near, far)` + `divisao_perspectiva` → NDC;
   `ndc_para_pixel` → coordenadas da janela.
5. **Recorte:** `face_no_volume_de_visao` descarta a face inteira se algum vértice está atrás
   do near ou se os 3 estão fora do mesmo plano do frustum (sem recorte de polígonos).
6. **Culling:** em coordenadas de câmera, descarta a face se `normal_face · (−v0) ≤ 0`
   (`face_voltada_para_camera`; a normal vem de `normais_faces`).
7. **Iluminação:** Phong nos 3 vértices (ka=0.5, kd=0.8, ks=0.4, brilho=32, luz em (5, 20, 15)).
8. **Rasterização:** `scan_line_par_impar` lista os pixels do triângulo; para cada pixel, as
   coordenadas baricêntricas interpolam z (teste no Z-buffer) e a cor (Gouraud). Depois,
   `desenhar_aresta` traça as 3 arestas com a equação da reta, na cor iluminada dos vértices.

---

## 4. Os objetos

### 4.1 Como um objeto é construído

Cada objeto é uma **função de campo** `gerar_campo_<nome>(x, y, z)` em `modeling.py`, que
combina primitivas de `primitives.py`:

| Primitiva | Forma |
|---|---|
| `cilindro(raio, y_min, y_max)` | Cilindro em pé (eixo Y) |
| `cilindro_x(raio, x_min, x_max, cy, cz)` | Cilindro deitado (eixo X) — **criado neste projeto** |
| `cone_truncado(y_min, y_max, r_base, r_topo)` | Tronco de cone em Y (`r_topo=0` → cone) |
| `esfera(cx, cy, cz, raio)` | Esfera |
| `caixa(cx, cy, cz, hx, hy, hz)` | Paralelepípedo (meias-dimensões) |
| `toro(cx, cy, cz, r_maior, r_tubo)` | Toro deitado no plano XZ |

| Operação | Fórmula | Uso |
|---|---|---|
| `uniao(A, B, …)` | `min` | Juntar peças |
| `intersecao(A, B, …)` | `max` | Recortar |
| `subtracao(A, B)` | `max(A, −B)` | Furos / ocos |

Todos os objetos são modelados **no seu próprio sistema de coordenadas**: apoiados em `y = 0`
e centrados no eixo Y (ou na origem, no caso do altere).

Para adicionar/trocar um objeto: criar a função em `modeling.py` e uma linha em `CENA`
(`main.py`):

```python
# (função_de_campo, pos_x, pos_z, cor_hex, label, escala, limites_malha)
```

`limites_malha` é o cubo da grade do Marching Cubes. Quanto mais justo ao objeto, mais
detalhada a malha (a resolução é fixa em 80 amostras por eixo).

### 4.2 Peão — `gerar_campo_peao`

| Parte | Primitiva | Parâmetros |
|---|---|---|
| Base | `cilindro` | r = 2.0, y ∈ [0, 0.7] |
| Corpo | `cone_truncado` | y ∈ [0.6, 3.6], r 1.3 → 0.3 |
| Anel | `cilindro` | r = 1.3, y ∈ [3.0, 3.5] |
| Cabeça | `esfera` | centro y = 4.2, r = 0.9 |

Combinação: `uniao(base, corpo, anel, topo)`. Único objeto mantido do projeto antigo.

### 4.3 Lápis — `gerar_campo_lapis`

| Parte | Primitiva | Parâmetros |
|---|---|---|
| Corpo | `cilindro` | `R_LAPIS = 0.7`, y ∈ [0, `ALTURA_CORPO = 5.6`] |
| Anel (separa a borracha) | `cilindro` | `R_ANEL = 0.82`, y ∈ [`Y_ANEL = 0.7`, 1.05] |
| Ponta | `cone_truncado` | y ∈ [5.6, 7.2], r 0.7 → 0 |

Combinação: `uniao(corpo, anel, ponta)`. A parte abaixo do anel representa a borracha.

### 4.4 Altere — `gerar_campo_altere`

| Parte | Primitiva | Parâmetros |
|---|---|---|
| 2 esferas | `esfera` | `R_ESFERA = 1.0`, centros em x = ±`X_ESFERA` (±2.0), y = 1.0 |
| Barra | `cilindro_x` | `R_BARRA = 0.42`, x ∈ [−2, 2], eixo em y = 1.0 |

Combinação: `uniao(esfera_esq, esfera_dir, barra)` — união simples (mínimo), então a junção
barra/esfera fica com aresta viva. Deitado no chão, ao longo de X.

### 4.5 Martelo — `gerar_campo_martelo`

| Parte | Primitiva | Parâmetros |
|---|---|---|
| Cabo | `cilindro` | `R_CABO = 0.3`, y ∈ [0, `ALTURA_CABO = 4.6`] |
| Cabeça | `caixa` | centro y = 4.7, meias-dimensões (1.5, 0.5, 0.5) |

Combinação: `uniao(cabo, cabeca)`. Em pé, cabeça alinhada com X.

### 4.6 Lixeira — `gerar_campo_lixeira`

| Parte | Primitiva | Parâmetros |
|---|---|---|
| Casca externa | `cone_truncado` | y ∈ [0, `ALTURA = 3.6`], r `R_BASE = 1.3` → `R_TOPO = 1.6` |
| Oco interno | `cone_truncado` | começa em y = `ESPESSURA` (0.15) e passa da boca; raios menos a espessura |
| Borda | `toro` | na boca (y = 3.6), r_maior = 1.525, r_tubo = 0.14 |

Combinação: `uniao(subtracao(externo, interno), borda)`. O interno começa acima de y = 0 para
deixar o fundo, e passa da boca para deixá-la aberta.

### 4.7 Cena atual (`CENA` em `main.py`)

| Objeto | Posição (x, z) | Cor | Limites MC | Vértices | Faces | Caixa no mundo (min → max) |
|---|---|---|---|---|---|---|
| Peão | (−7.5, −4.5) | `#E63946` vermelho | (−5, 12) | 1662 | 3320 | (−9.5, −2, −6.5) → (−5.5, 3.1, −2.5) |
| Lápis | (−4.5, 1.5) | `#F4A261` laranja | (−1.5, 8) | 2852 | 5700 | (−5.3, −2, 0.7) → (−3.7, 5.0, 2.3) |
| Altere | (−1.5, −4.5) | `#2A9D8F` verde-azulado | (−3.5, 3.5) | 5608 | 11212 | (−4.5, −2, −5.5) → (1.5, 0, −3.5) |
| Martelo | (1.5, 1.5) | `#A8DADC` azul-claro | (−2, 6) | 2408 | 4812 | (0, −2, 1) → (3, 3.2, 2) |
| Lixeira | (4.5, −4.5) | `#C77DFF` roxo | (−2.5, 4.5) | 12660 | 25316 | (2.8, −2, −6.2) → (6.2, 1.7, −2.8) |

Verificações feitas (resolução 80):
- **Limite |10|:** maior componente = 9.5 (peão). ✅
- **Sobreposição:** nenhum par de caixas envolventes se intersecta. ✅
- **Normais para fora:** em 100% das faces a ordem dos vértices é coerente com a normal
  invertida do Marching Cubes (que aponta para fora). ✅
- **Cores:** uma cor por sólido, todas diferentes. ✅

---

## 5. O que falta fazer (checklist)

### Item 1 — Modelagem
- [x] **Função que retorna o sólido** completo (exigência explícita): vértices, **arestas**,
      faces, normais por face e por vértice, cor. Proposta pronta em
      `Documentacao_Projeto_CG.pdf`, seção 6.2 (`criar_solido`).
- [x] **Mostrar cada sólido no seu sistema do objeto** (item 1e): plot 3D (matplotlib
      `Poly3DCollection`) com eixos do objeto e setas das normais (`quiver`) nos centroides.
- [ ] Confirmar com o professor se os 5 objetos são únicos na turma (o haltere aparece como
      sugestão na documentação de apoio, então outras equipes podem ter escolhido também).

### Item 2 — Cena no mundo
- [x] Criar `rotacao_x` e `rotacao_z` em `math_3d.py` e generalizar a matriz do mundo
      (`M = T · Rz · Ry · Rx · S`).
- [x] **Usar de fato escala e rotação** na `CENA` (hoje todos têm escala 1.0 e rotação 0;
      o enunciado pede "usando transformações em escala, rotação e translação").
      Ex.: girar o martelo/altere em Y e escalar algum objeto.
- [x] Validação automática do limite |10| e da não-sobreposição (`validar_cena`, seção 6.3
      da documentação). A conferência deste documento foi manual.
- [x] **Plot 3D da cena no mundo** (item 2b), com eixos.

### Item 3 — Câmera
- [x] Função `base_camera(eye, at, up)` que devolve `u, v, n`; `main.py` e
      `visualizar_camera.py` imprimem a base (item 3a).
- [x] Transformar os vértices para coordenadas da câmera e **plotar em 3D** (itens 3b, 3c):
      `visualizar_camera.py`.
- [x] **Ponto na origem do mundo** (item 3d): cruz laranja em `(0, 0, 0)` no `main.py` e ponto
      preto no `visualizar_camera.py`.
- [x] **Eye variável** (item 3e): `--eye X Y Z` no `main.py` e no `visualizar_camera.py`.
- [x] Figuras `eye1.png` e `eye2.png` do relatório refeitas com `visualizar_camera.py`.

### Item 4 — Projeção
- [x] **Recorte pelo volume de visão:** `math_3d.face_no_volume_de_visao` descarta a face
      inteira se algum vértice está atrás do near ou se os 3 estão fora do mesmo plano do
      frustum; é chamada no `main.py` antes do culling.
- [x] **Plot 3D com a janela de projeção** (item 4a): `visualizar_projecao.py` mostra, no
      mesmo eixo 3D, os sólidos em coordenadas de câmera e os polígonos visíveis projetados
      no plano da janela; um segundo painel mostra a janela vista de frente (`--eye`).
- [x] **Arestas e faces com a mesma cor** por sólido: `main.desenhar_aresta` desenha as
      arestas de cada face visível com a equação da reta, na cor iluminada do sólido.

### Item 5 — Iluminação
- [x] Phong com ambiente, difusa e especular nos vértices visíveis.
- [ ] Apenas explicar coeficientes e equações no relatório.

### Item 6 — Rasterização
- [x] 3 resoluções (200, 400, 800), scan-line par-ímpar, baricêntrica, Z-buffer, equação da reta.
- [x] **Culling em coordenadas de câmera** (o enunciado pede "normal + eixo z da câmera"):
      `math_3d.face_voltada_para_camera` usa a normal da face (`normais_faces` do sólido, levada
      à câmera) e o vetor até o observador, que na câmera é `-v0`. O teste só pelo sinal de
      `normal_z` foi medido e descartado: abria uma falha visível na borda da lixeira.
- [x] Retas: trocado o Bresenham pelo algoritmo da equação da reta, que é o dado em aula (30/09).

### Ajustes de cena / qualidade
- [x] A **lixeira saía cortada** na borda direita da câmera principal (Tela 1). Resolvido
      recuando o `EYE_PRINCIPAL` de (7.5, 10, 5) para (9.75, 13, 6.5), na mesma direção de
      visada (a base u, v, n não muda). Maior |NDC| de qualquer vértice: de 1.18 para 0.87.
- [ ] Salvar as imagens com `plt.savefig` para o relatório.

### Entrega
- [ ] Relatório completo (capa, introdução, objetivo, desenvolvimento, simulações,
      conclusão, referências) — estrutura sugerida na seção 6.8 da documentação.
- [ ] `.zip` do código sem `.venv/` e `__pycache__/`.

---

## 6. Ordem sugerida para terminar

1. `criar_solido` + plot de cada objeto no seu sistema (item 1).
2. `rotacao_x/z`, rotação/escala na `CENA`, `validar_cena`, plot do mundo (item 2).
3. ~~`base_camera`, plot no sistema da câmera com a origem marcada, eye por parâmetro (item 3).~~ Feito.
4. ~~Recorte + plot 3D com a janela de projeção + arestas na cor do sólido (item 4).~~ Feito.
5. ~~Culling em coordenadas de câmera no `renderizar_cena_completa` (item 6).~~ Feito.
6. Gerar as figuras e escrever o relatório.
