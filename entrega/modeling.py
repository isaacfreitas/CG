import numpy as np
from skimage.measure import marching_cubes
from primitives import (
    cilindro, cilindro_x, cone_truncado, esfera, caixa, toro,
    uniao, subtracao
)


def extrair_malha(funcao_campo, limites=(-5, 12), resolucao=100):
    """
    Gera a grelha 3D e extrai vértices e faces usando Marching Cubes.
    """
    x, y, z = np.mgrid[
        limites[0]:limites[1]:complex(0, resolucao),
        limites[0]:limites[1]:complex(0, resolucao),
        limites[0]:limites[1]:complex(0, resolucao)
    ]
    volume = funcao_campo(x, y, z)
    vertices, faces, _, _ = marching_cubes(volume, level=0.0)
    passo = (limites[1] - limites[0]) / (resolucao - 1)
    vertices = (vertices * passo) + limites[0]
    return vertices, faces


# ==============================================================================
# SÓLIDO COMPLETO — item 1 do enunciado
# ==============================================================================

def criar_solido(funcao_campo, nome, cor, limites=(-5, 12), resolucao=80):
    """
    Constrói o sólido completo a partir da sua função de campo F(x, y, z).

    Retorna um dicionário com:
      nome             : nome do objeto
      cor              : cor RGB em [0, 1] (faces e arestas usam a mesma cor)
      vertices         : matriz (V, 3) com as coordenadas x, y, z de cada vértice
      arestas          : matriz (A, 2) com os pares de índices de vértices (sem repetição)
      faces            : matriz (F, 3) com os 3 índices de vértices de cada triângulo
      normais_faces    : matriz (F, 3) com a normal unitária de cada face, para fora
      normais_vertices : matriz (V, 3) com a normal unitária de cada vértice, para fora

    Tudo está no sistema de coordenadas do objeto.
    """
    vertices, faces = extrair_malha(funcao_campo, limites, resolucao)
    faces = faces.astype(np.int64)

    # Normal de cada face: produto vetorial de duas arestas do triângulo, com tamanho 1.
    # O Marching Cubes entrega os vértices em ordem tal que o resultado aponta para fora.
    a, b, c = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    normais_f = np.cross(b - a, c - a)
    normais_f /= np.linalg.norm(normais_f, axis=1, keepdims=True) + 1e-12

    # Normal de cada vértice: soma das normais das faces que tocam o vértice, com tamanho 1.
    # Para cada face, soma a normal dela nos 3 vértices dela.
    normais_v = np.zeros_like(vertices)
    for i, face in enumerate(faces):
        for v in face:
            normais_v[v] += normais_f[i]
    normais_v /= np.linalg.norm(normais_v, axis=1, keepdims=True) + 1e-12

    # Arestas: cada triângulo tem 3 (v0-v1, v1-v2, v2-v0). Uma aresta é compartilhada
    # por 2 triângulos, então guardamos cada par em ordem (menor, maior) num conjunto,
    # que descarta as repetidas.
    conjunto = set()
    for v0, v1, v2 in faces:
        for a_idx, b_idx in ((v0, v1), (v1, v2), (v2, v0)):
            conjunto.add((min(a_idx, b_idx), max(a_idx, b_idx)))
    arestas = np.array(sorted(conjunto))

    return {
        "nome": nome,
        "cor": np.asarray(cor, dtype=float),
        "vertices": vertices,
        "arestas": arestas,
        "faces": faces,
        "normais_faces": normais_f,
        "normais_vertices": normais_v,
    }


def hex_para_rgb(hex_str):
    """Converte '#RRGGBB' em [r, g, b] com valores em [0, 1]."""
    hex_str = hex_str.lstrip('#')
    return [int(hex_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


# ==============================================================================
# PEÇAS — usando primitives.py
# ==============================================================================

def gerar_campo_lapis(x, y, z):
    """
    Lápis simples em pé:
      - Corpo: cilindro vertical
      - Anel: faixa mais larga perto da base, separando a borracha do corpo
      - Ponta: cone no topo do corpo
    """
    R_LAPIS     = 0.7
    ALTURA_CORPO = 5.6
    ALTURA_PONTA = 1.6
    R_ANEL       = 0.82
    Y_ANEL       = 0.7    # altura onde começa o anel (abaixo dele fica a borracha)
    ALTURA_ANEL  = 0.35

    corpo = cilindro(x, y, z, raio=R_LAPIS, y_min=0.0, y_max=ALTURA_CORPO)
    ponta = cone_truncado(x, y, z, y_min=ALTURA_CORPO - 0.01,
                          y_max=ALTURA_CORPO + ALTURA_PONTA,
                          r_base=R_LAPIS, r_topo=0.0)

    anel = cilindro(x, y, z, raio=R_ANEL, y_min=Y_ANEL, y_max=Y_ANEL + ALTURA_ANEL)

    return uniao(corpo, anel, ponta)


def gerar_campo_peao(x, y, z):

    base = cilindro(x, y, z,  raio=2, y_min=0.0, y_max=0.7)
    corpo = cone_truncado(x, y, z, y_min=0.6, y_max=3.6, r_base=1.3, r_topo=0.3)
    anel = cilindro(x, y, z, raio=1.3, y_min=3.0, y_max=3.5)
    topo = esfera(x, y, z, cx=0, cy=4.2, cz=0, raio=0.9)

    return uniao(
        base, corpo, anel, topo
    )


def gerar_campo_altere(x, y, z):
    """
    Altere simples deitado no chão, ao longo do eixo X:
      - 2 esferas, uma em cada ponta, apoiadas em y=0
      - Barra reta ligando os centros das esferas
      - união simples (mínimo): a junção barra/esfera fica com aresta viva
    """
    R_ESFERA = 1.0        # raio das esferas
    X_ESFERA = 2.0        # distância do centro de cada esfera até a origem
    Y_EIXO   = R_ESFERA   # altura do eixo: esferas encostadas no chão
    R_BARRA  = 0.42       # raio da barra

    esfera_esq = esfera(x, y, z, cx=-X_ESFERA, cy=Y_EIXO, cz=0, raio=R_ESFERA)
    esfera_dir = esfera(x, y, z, cx= X_ESFERA, cy=Y_EIXO, cz=0, raio=R_ESFERA)
    barra = cilindro_x(x, y, z, raio=R_BARRA, x_min=-X_ESFERA, x_max=X_ESFERA, cy=Y_EIXO)

    return uniao(esfera_esq, esfera_dir, barra)


def gerar_campo_martelo(x, y, z):
    """
    Martelo simples em pé:
      - Cabo: cilindro vertical
      - Cabeça: caixa horizontal (ao longo de X) no topo do cabo
    """
    R_CABO      = 0.3
    ALTURA_CABO = 4.6

    cabo = cilindro(x, y, z, raio=R_CABO, y_min=0.0, y_max=ALTURA_CABO)

    cabeca = caixa(x, y, z, cx=0.0, cy=ALTURA_CABO + 0.1, cz=0.0,
                   hx=1.5, hy=0.5, hz=0.5)

    return uniao(cabo, cabeca)


def gerar_campo_lixeira(x, y, z):
    """
    Lixeira simples em pé, aberta em cima:
      - Corpo: cone truncado (mais largo em cima) oco, por subtração
        de um cone interno menor que começa acima do fundo
      - Borda: toro contornando a boca
    """
    ALTURA    = 3.6
    R_BASE    = 1.3
    R_TOPO    = 1.6
    ESPESSURA = 0.15

    externo = cone_truncado(x, y, z, y_min=0.0, y_max=ALTURA,
                            r_base=R_BASE, r_topo=R_TOPO)
    interno = cone_truncado(x, y, z, y_min=ESPESSURA, y_max=ALTURA + 0.5,
                            r_base=R_BASE - ESPESSURA,
                            r_topo=R_TOPO - ESPESSURA + 0.5 * (R_TOPO - R_BASE) / ALTURA)
    corpo = subtracao(externo, interno)

    borda = toro(x, y, z, cx=0, cy=ALTURA, cz=0,
                 r_maior=R_TOPO - ESPESSURA / 2, r_tubo=0.14)

    return uniao(corpo, borda)


# ==============================================================================
# CATÁLOGO DOS 5 OBJETOS
# ==============================================================================
# nome -> (função de campo, limites da grade do Marching Cubes, cor)
# Os limites são o cubo [min, max]^3 onde F é avaliada; precisam envolver o objeto inteiro.
MODELOS = {
    "Peão":    (gerar_campo_peao,    (-2.5, 5.5), "#E63946"),
    "Lápis":   (gerar_campo_lapis,   (-1.5, 8.0), "#F4A261"),
    "Altere":  (gerar_campo_altere,  (-3.5, 3.5), "#2A9D8F"),
    "Martelo": (gerar_campo_martelo, (-2.0, 6.0), "#A8DADC"),
    "Lixeira": (gerar_campo_lixeira, (-2.5, 4.5), "#C77DFF"),
}


def obter_solido(nome, resolucao=80):
    """Cria o sólido completo de um dos 5 objetos do catálogo pelo nome."""
    funcao_campo, limites, cor_hex = MODELOS[nome]
    return criar_solido(funcao_campo, nome, hex_para_rgb(cor_hex), limites, resolucao)
