"""
visualizar_objetos.py — Item 1e do enunciado
=============================================
Mostra cada um dos 5 sólidos no seu próprio sistema de coordenadas (sistema do objeto),
com os eixos x, y, z na origem e setas com as normais de algumas faces.

Uso:
    python3 visualizar_objetos.py            # abre uma janela por objeto
    python3 visualizar_objetos.py --salvar   # salva os PNGs nas figuras do relatório
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import modeling

RESOLUCAO = 50          # grade do Marching Cubes (menor que a da cena, para o plot ficar leve)
NUM_NORMAIS = 60        # quantas normais de face desenhar como setas
ELEVACAO, AZIMUTE = 20, -60   # ângulo de visão do plot (graus)
PASTA_FIGURAS = Path(__file__).parent / "relatorio/figuras/03-desenvolvimento/01-modelagem"
ARQUIVOS = {"Peão": "peao", "Lápis": "lapis", "Altere": "haltere",
            "Martelo": "martelo", "Lixeira": "lixeira"}


def para_plot(pontos):
    """
    O matplotlib desenha o 3º eixo para cima. Nos nossos objetos o "para cima" é y, então,
    só na hora de desenhar, levamos (x, y, z) -> (x, -z, y). Isso é uma rotação de 90° em
    torno de x (não um espelhamento), então o sistema continua sendo de mão direita.
    """
    pontos = np.asarray(pontos, dtype=float)
    return np.stack([pontos[..., 0], -pontos[..., 2], pontos[..., 1]], axis=-1)


def mostrar_solido(solido, ax):
    vertices = solido["vertices"]
    faces = solido["faces"]
    cor = solido["cor"]

    # Faces e arestas com a mesma cor do sólido
    triangulos = para_plot(vertices[faces])
    malha = Poly3DCollection(triangulos, facecolor=cor, edgecolor=cor * 0.85,
                             linewidths=0.1, alpha=0.9)
    ax.add_collection3d(malha)

    # Normais: seta saindo do centroide de algumas faces. O matplotlib não esconde o que
    # fica atrás da malha, então só sorteamos faces viradas para quem olha o gráfico.
    e, a = np.radians(ELEVACAO), np.radians(AZIMUTE)
    olho = np.array([np.cos(e) * np.cos(a), np.sin(e), -np.cos(e) * np.sin(a)])  # em (x, y, z)
    visiveis = np.flatnonzero(solido["normais_faces"] @ olho > 0.3)
    rng = np.random.default_rng(0)
    escolhidas = rng.choice(visiveis, size=min(NUM_NORMAIS, len(visiveis)), replace=False)
    centroides = vertices[faces[escolhidas]].mean(axis=1)
    normais = solido["normais_faces"][escolhidas]
    c, n = para_plot(centroides), para_plot(normais)
    ax.quiver(c[:, 0], c[:, 1], c[:, 2], n[:, 0], n[:, 1], n[:, 2],
              length=0.5, color="black", linewidth=0.8, arrow_length_ratio=0.3)

    # Mesma escala nos 3 eixos para não deformar o objeto
    minimo, maximo = vertices.min(axis=0), vertices.max(axis=0)
    centro = (minimo + maximo) / 2
    raio = (maximo - minimo).max() / 2 + 0.3

    # Eixos do sistema do objeto, saindo da origem (compridos para sair de dentro do sólido)
    tam = max(1.5, np.abs(vertices).max(axis=0)[[0, 2]].max() + 0.8)
    for direcao, rotulo, cor_eixo in [((tam, 0, 0), "x", "red"),
                                      ((0, tam, 0), "y", "blue"),
                                      ((0, 0, tam), "z", "green")]:
        d = para_plot(np.array(direcao, dtype=float))
        ax.plot([0, d[0]], [0, d[1]], [0, d[2]], color=cor_eixo, linewidth=2)
        ax.text(*(d * 1.08), rotulo, color=cor_eixo, fontsize=12)

    raio = max(raio, tam - np.abs(centro).max() + 0.3)
    c = para_plot(centro)
    ax.set_xlim(c[0] - raio, c[0] + raio)
    ax.set_ylim(c[1] - raio, c[1] + raio)
    ax.set_zlim(c[2] - raio, c[2] + raio)
    # O 2º eixo do gráfico guarda -z; o rótulo mostra o valor de z de verdade.
    ax.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{-valor + 0.0:g}"))
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlabel("x"); ax.set_ylabel("z"); ax.set_zlabel("y")
    ax.set_title(f"{solido['nome']} no sistema do objeto\n"
                 f"{len(vertices)} vértices, {len(solido['arestas'])} arestas, "
                 f"{len(faces)} faces")
    ax.view_init(elev=ELEVACAO, azim=AZIMUTE)


def main():
    salvar = "--salvar" in sys.argv
    for nome in modeling.MODELOS:
        print(f"Criando sólido: {nome}")
        solido = modeling.obter_solido(nome, RESOLUCAO)
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(projection="3d")
        mostrar_solido(solido, ax)
        fig.tight_layout()
        if salvar:
            destino = PASTA_FIGURAS / f"{ARQUIVOS[nome]}.png"
            fig.savefig(destino, dpi=150)
            plt.close(fig)
            print(f"  salvo em {destino}")
    if not salvar:
        plt.show()


if __name__ == "__main__":
    main()
