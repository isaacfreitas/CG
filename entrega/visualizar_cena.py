"""
visualizar_cena.py — Item 2b do enunciado
==========================================
Mostra os 5 sólidos juntos no sistema de coordenadas do mundo, com os eixos x, y, z,
a origem do mundo e o cubo [-10, 10]^3 que limita a cena.

Uso:
    python3 visualizar_cena.py            # abre a janela
"""

from itertools import product

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import cena
from visualizar_objetos import para_plot

RESOLUCAO = 50   # grade do Marching Cubes (baixa, só para o plot ficar leve)


def desenhar_caixa(ax, minimo, maximo, **estilo):
    """Arestas da caixa alinhada aos eixos, entre os cantos minimo e maximo (x, y, z)."""
    cantos = np.array(list(product(*zip(minimo, maximo))))
    for i, j in product(range(8), repeat=2):
        # dois cantos formam uma aresta quando diferem em exatamente uma coordenada
        if i < j and np.count_nonzero(cantos[i] != cantos[j]) == 1:
            seg = para_plot(cantos[[i, j]])
            ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], **estilo)


def desenhar_cubo_limite(ax):
    """Cubo [-10, 10]^3: todos os vértices da cena têm de ficar aqui dentro."""
    L = cena.LIMITE
    desenhar_caixa(ax, [-L] * 3, [L] * 3, color="0.6", linewidth=0.8, linestyle="--")


def desenhar_chao(ax):
    """Plano do chão (y = Y_CHAO), onde os objetos ficam apoiados."""
    L, y = cena.LIMITE, cena.Y_CHAO
    cantos = np.array([[-L, y, -L], [L, y, -L], [L, y, L], [-L, y, L]])
    ax.add_collection3d(Poly3DCollection([para_plot(cantos)], facecolor="0.85",
                                         edgecolor="0.6", alpha=0.35, zorder=0))
    ax.text(*para_plot([0, y, L]), f"chão (y = {y:g})", ha="center", fontsize=9, zorder=10)


def desenhar_eixos_mundo(ax, tamanho=9.0):
    """Eixos do mundo saindo da origem, e um ponto marcando a origem."""
    for direcao, rotulo, cor in [((1, 0, 0), "x", "red"), ((0, 1, 0), "y", "blue"),
                                 ((0, 0, 1), "z", "green")]:
        d = para_plot(np.array(direcao, dtype=float) * tamanho)
        ax.plot([0, d[0]], [0, d[1]], [0, d[2]], color=cor, linewidth=2, zorder=5)
        ax.text(*(d * 1.06), rotulo, color=cor, fontsize=13, weight="bold", zorder=10)
    ax.scatter([0], [0], [0], color="black", s=40, zorder=6)


def mostrar_cena(objetos_cena, ax):
    for obj in objetos_cena:
        solido = obj["solido"]
        triangulos = para_plot(obj["vertices_mundo"][solido["faces"]])
        ax.add_collection3d(Poly3DCollection(
            triangulos, facecolor=solido["cor"], edgecolor=solido["cor"] * 0.85,
            linewidths=0.2, zorder=1))
        v = obj["vertices_mundo"]
        # Caixa do objeto: a mesma que validar_cena usa. Caixas que não se tocam = sem sobreposição
        desenhar_caixa(ax, v.min(axis=0), v.max(axis=0), color=solido["cor"], linewidth=0.8,
                       linestyle=":", zorder=2)
        rotulo = np.array([v[:, 0].mean(), v[:, 1].max() + 1.0, v[:, 2].mean()])
        ax.text(*para_plot(rotulo), obj["nome"], fontsize=10, ha="center", zorder=10,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1))

    desenhar_chao(ax)
    desenhar_cubo_limite(ax)
    desenhar_eixos_mundo(ax)

    L = cena.LIMITE
    ax.set_xlim(-L, L); ax.set_ylim(-L, L); ax.set_zlim(-L, L)
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlabel("x"); ax.set_ylabel("z"); ax.set_zlabel("y")
    # O 2º eixo do gráfico guarda -z; o rótulo mostra o valor de z de verdade.
    ax.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{-valor + 0.0:g}"))
    ax.set_title("Cena no sistema de coordenadas do mundo\n"
                 "ponto preto: origem do mundo   tracejado: limite |10|\n"
                 "pontilhado colorido: caixa de cada objeto (não se tocam)")
    ax.view_init(elev=25, azim=-60)


def main():
    objetos_cena = cena.montar_cena(cena.criar_solidos(RESOLUCAO))
    cena.imprimir_resumo(objetos_cena)

    fig = plt.figure(figsize=(8, 8))
    # computed_zorder=False: o matplotlib não faz z-buffer entre objetos diferentes, então
    # fixamos a ordem de desenho (malhas, depois eixos, depois textos) para nada sumir.
    ax = fig.add_subplot(projection="3d", computed_zorder=False)
    mostrar_cena(objetos_cena, ax)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
