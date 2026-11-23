"""
visualizar_camera.py — Item 3 do enunciado
===========================================
Mostra a cena no sistema de coordenadas da câmera, em 3D:
  3a. imprime a base vetorial u, v, n da câmera
  3b. leva todos os vértices do mundo para o sistema da câmera
  3c. desenha os sólidos nesse sistema
  3d. marca a origem do mundo com um ponto preto
  3e. o eye muda pela linha de comando e gera uma nova imagem

Uso:
    python3 visualizar_camera.py                          # eye padrão, abre a janela
    python3 visualizar_camera.py --eye 26 18 28           # outro eye
    python3 visualizar_camera.py --eye 26 18 28 --salvar eye2   # salva eye2.png nas figuras do relatório
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import cena
import math_3d
import modeling
from main import EYE_PRINCIPAL, AT, UP
from visualizar_objetos import para_plot

RESOLUCAO = 50          # grade do Marching Cubes (menor que a da cena, para o plot ficar leve)
TAMANHO_EIXOS = 5.0     # comprimento das setas u, v, n
ELEVACAO, AZIMUTE = 20, -60   # ângulo de visão do plot (graus)
PASTA_FIGURAS = Path(__file__).parent / "relatorio/figuras/03-desenvolvimento/03-camera"


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Cena em coordenadas de câmera")
    parser.add_argument("--eye", nargs=3, type=float, metavar=("X", "Y", "Z"),
                        default=EYE_PRINCIPAL.tolist(), help="posição do observador")
    parser.add_argument("--salvar", metavar="NOME",
                        help="salva a figura como NOME.png na pasta de figuras do relatório")
    return parser.parse_args()


def desenhar_cena_na_camera(eye, ax):
    """Desenha a cena em coordenadas de câmera e devolve [(sólido, vértices na câmera)]."""
    # 3a: base da câmera
    u, v, n = math_3d.base_camera(eye, AT, UP)
    print(f"eye = {eye}")
    print(f"u (x da câmera) = {np.round(u, 3)}")
    print(f"v (y da câmera) = {np.round(v, 3)}")
    print(f"n (z da câmera) = {np.round(n, 3)}")

    view = math_3d.look_at(eye, AT, UP)
    todos_os_pontos = [np.zeros((1, 3))]  # o centro da câmera também precisa caber no gráfico
    objetos_na_camera = []

    # 3b e 3c: vértices do mundo -> câmera (cena.montar_cena já leva objeto -> mundo)
    solidos = {item["nome"]: modeling.obter_solido(item["nome"], RESOLUCAO) for item in cena.CENA}
    for obj in cena.montar_cena(solidos):
        solido = obj["solido"]
        vertices = math_3d.aplicar_transformacao(view, obj["vertices_mundo"])
        todos_os_pontos.append(vertices)
        objetos_na_camera.append((solido, vertices))

        cor = solido["cor"]
        triangulos = para_plot(vertices[solido["faces"]])
        ax.add_collection3d(Poly3DCollection(triangulos, facecolor=cor, edgecolor=cor * 0.85,
                                             linewidths=0.1, alpha=0.9))

    # 3d: origem do mundo vista da câmera
    origem = math_3d.aplicar_transformacao(view, np.zeros((1, 3)))
    todos_os_pontos.append(origem)
    o = para_plot(origem[0])
    ax.scatter(*o, color="black", s=40)
    ax.text(*o, "  origem do mundo", fontsize=9)

    # Eixos u, v, n saindo do centro da câmera (que é (0, 0, 0) neste sistema)
    for direcao, rotulo, cor_eixo in [((1, 0, 0), "u (x)", "red"),
                                      ((0, 1, 0), "v (y)", "blue"),
                                      ((0, 0, 1), "n (z)", "green")]:
        d = para_plot(np.array(direcao) * TAMANHO_EIXOS)
        ax.plot([0, d[0]], [0, d[1]], [0, d[2]], color=cor_eixo, linewidth=2)
        ax.text(*d, rotulo, color=cor_eixo, fontsize=10)

    # Mesma escala nos 3 eixos para não deformar a cena
    pontos = para_plot(np.vstack(todos_os_pontos))
    centro = (pontos.min(axis=0) + pontos.max(axis=0)) / 2
    raio = (pontos.max(axis=0) - pontos.min(axis=0)).max() / 2 + 0.5
    ax.set_xlim(centro[0] - raio, centro[0] + raio)
    ax.set_ylim(centro[1] - raio, centro[1] + raio)
    ax.set_zlim(centro[2] - raio, centro[2] + raio)
    ax.set_box_aspect((1, 1, 1))

    # O 2º eixo do gráfico guarda -z; o rótulo mostra o valor de z de verdade.
    ax.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{-valor + 0.0:g}"))
    ax.set_xlabel("x da câmera")
    ax.set_ylabel("z da câmera")
    ax.set_zlabel("y da câmera")
    ax.view_init(elev=ELEVACAO, azim=AZIMUTE)
    return objetos_na_camera


def main():
    args = ler_argumentos()
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(projection="3d")
    desenhar_cena_na_camera(np.array(args.eye), ax)
    fig.tight_layout()

    if args.salvar:
        destino = PASTA_FIGURAS / f"{args.salvar}.png"
        fig.savefig(destino, dpi=150)
        print(f"salvo em {destino}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
