import numpy as np
from skimage.measure import marching_cubes
from primitives import (
    cilindro, cilindro_x, cone_truncado, esfera, elipsoide, caixa, toro,
    uniao, intersecao, subtracao, uniao_suave
)


def extrair_malha(funcao_campo, limites=(-5, 12), resolucao=100):
    """
    Gera a grelha 3D e extrai vértices, faces e normais usando Marching Cubes.
    """
    x, y, z = np.mgrid[
        limites[0]:limites[1]:complex(0, resolucao),
        limites[0]:limites[1]:complex(0, resolucao),
        limites[0]:limites[1]:complex(0, resolucao)
    ]
    volume = funcao_campo(x, y, z)
    vertices, faces, normals, values = marching_cubes(volume, level=0.0)
    passo = (limites[1] - limites[0]) / (resolucao - 1)
    vertices = (vertices * passo) + limites[0]
    return vertices, faces, normals


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
      - uniao_suave cria a curva suave na junção barra/esfera
    """
    R_ESFERA = 1.0        # raio das esferas
    X_ESFERA = 2.0        # distância do centro de cada esfera até a origem
    Y_EIXO   = R_ESFERA   # altura do eixo: esferas encostadas no chão
    R_BARRA  = 0.42       # raio da barra

    esferas = uniao(
        esfera(x, y, z, cx=-X_ESFERA, cy=Y_EIXO, cz=0, raio=R_ESFERA),
        esfera(x, y, z, cx= X_ESFERA, cy=Y_EIXO, cz=0, raio=R_ESFERA),
    )

    barra = cilindro_x(x, y, z, raio=R_BARRA, x_min=-X_ESFERA, x_max=X_ESFERA, cy=Y_EIXO)

    return uniao_suave(esferas, barra, k=0.5)


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
