"""
visualizar_projecao.py — Item 4a do enunciado
==============================================
Mostra a projeção em perspectiva em dois painéis:
  - 3D: os sólidos em coordenadas de câmera (como em visualizar_camera.py), a janela de
    projeção (um quadrado no plano z = -D da câmera) e os polígonos visíveis projetados nela;
  - 2D: a mesma janela vista de frente, só com os polígonos projetados.
Só entram na projeção os polígonos dentro do volume de visão e voltados para a câmera.

Uso:
    python3 visualizar_projecao.py                          # eye padrão, abre a janela
    python3 visualizar_projecao.py --eye 26 18 28           # outro eye
    python3 visualizar_projecao.py --eye 26 18 28 --salvar eye2   # salva eye2.png nas figuras do relatório
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import math_3d
from main import EYE_PRINCIPAL, AT, FOV_PRINCIPAL, Z_NEAR, Z_FAR
from visualizar_camera import desenhar_cena_na_camera
from visualizar_objetos import para_plot

FRACAO_JANELA = 0.5   # a janela fica a esta fração da distância entre o eye e o at
PASTA_FIGURAS = Path(__file__).parent / "relatorio/figuras/03-desenvolvimento/04-projecao"


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Sólidos em 3D e projeção na janela")
    parser.add_argument("--eye", nargs=3, type=float, metavar=("X", "Y", "Z"),
                        default=EYE_PRINCIPAL.tolist(), help="posição do observador")
    parser.add_argument("--salvar", metavar="NOME",
                        help="salva a figura como NOME.png na pasta de figuras do relatório")
    return parser.parse_args()


def desenhar_projecao(eye, ax, ax_janela):
    objetos = desenhar_cena_na_camera(eye, ax)
    proj = math_3d.projecao_perspectiva(FOV_PRINCIPAL, 1.0, Z_NEAR, Z_FAR)

    # A distância da janela acompanha a do eye ao at; com distância fixa, a projeção
    # encolheria até sumir quando o eye se afasta. A janela vai de -1 a 1 em NDC, o que
    # neste plano corresponde a ±meia_janela.
    distancia = FRACAO_JANELA * np.linalg.norm(np.array(eye) - AT)
    meia_janela = distancia * np.tan(np.radians(FOV_PRINCIPAL) / 2)

    # O matplotlib não resolve qual polígono fica na frente quando eles estão no mesmo plano.
    # Desenhamos do sólido mais distante para o mais próximo, cada um por cima do anterior.
    objetos.sort(key=lambda obj: obj[1][:, 2].mean())

    for ordem, (solido, vertices) in enumerate(objetos):
        # Coordenadas de recorte (x, y, z, w) e, dividindo por w, o NDC de cada vértice
        clip = np.hstack([vertices, np.ones((len(vertices), 1))]) @ proj.T
        ndc = clip[:, :3] / clip[:, 3:]

        visiveis = []   # (profundidade da face, triângulo na janela)
        for face in solido["faces"]:
            a, b, c = vertices[face]
            # Mesmas exclusões do pipeline: fora do volume de visão ou de costas para a câmera
            # (que está na origem, então o vetor até ela é -a).
            if not math_3d.face_no_volume_de_visao(*clip[face]):
                continue
            if np.dot(np.cross(b - a, c - a), -a) <= 0:
                continue
            visiveis.append((vertices[face][:, 2].mean(), ndc[face, :2] * meia_janela))

        # Dentro do sólido também vale do mais distante para o mais próximo (o painel 2D
        # não tem Z-buffer).
        visiveis.sort(key=lambda item: item[0])
        triangulos_2d = np.array([triangulo for _, triangulo in visiveis])
        triangulos_3d = np.concatenate(
            [triangulos_2d, np.full(triangulos_2d.shape[:2] + (1,), -distancia)], axis=2)

        cor = solido["cor"]
        ax.add_collection3d(Poly3DCollection(para_plot(triangulos_3d), facecolor=cor,
                                             edgecolor=cor, linewidths=0.1, zorder=3 + ordem))
        ax_janela.add_collection(PolyCollection(triangulos_2d, facecolor=cor, edgecolor=cor,
                                                linewidths=0.1))

    # Contorno da janela de projeção no painel 3D
    cantos = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]) * meia_janela
    contorno = para_plot(np.column_stack([cantos, np.full(len(cantos), -distancia)]))
    ax.plot(contorno[:, 0], contorno[:, 1], contorno[:, 2], color="black", linestyle="--",
            linewidth=1.2, zorder=20)
    ax.text(*contorno[2], "janela de projeção", fontsize=9, zorder=21)
    ax.set_title("Sólidos na câmera e projeção na janela")

    # Painel 2D: a mesma janela vista de frente
    ax_janela.set_xlim(-meia_janela, meia_janela)
    ax_janela.set_ylim(-meia_janela, meia_janela)
    ax_janela.set_aspect("equal")
    ax_janela.set_xlabel("x da janela")
    ax_janela.set_ylabel("y da janela")
    ax_janela.set_title("Janela de projeção (vista de frente)")


def main():
    args = ler_argumentos()
    fig = plt.figure(figsize=(12, 6))
    # computed_zorder=False: usamos a ordem de desenho definida acima (ver visualizar_cena.py)
    ax = fig.add_subplot(1, 2, 1, projection="3d", computed_zorder=False)
    ax_janela = fig.add_subplot(1, 2, 2)
    desenhar_projecao(np.array(args.eye), ax, ax_janela)
    fig.tight_layout()

    if args.salvar:
        destino = PASTA_FIGURAS / f"{args.salvar}.png"
        fig.savefig(destino, dpi=150)
        print(f"salvo em {destino}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
