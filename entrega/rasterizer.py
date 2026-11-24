import numpy as np
import math


def produz_fragmento(x, y):
    """
    Pixel que contém o ponto (x, y): a parte inteira de cada coordenada.
    O centro desse pixel é (int(x) + 0,5, int(y) + 0,5). A folga 1e-9 evita que um
    valor como 2,9999999 (erro de ponto flutuante) caia no pixel anterior.
    """
    return (math.floor(x + 1e-9), math.floor(y + 1e-9))


def rasterizar_reta(x1, y1, x2, y2):
    """
    Algoritmo da equação da reta: y = m·x + b.
    Se |dx| > |dy| a reta é mais deitada e anda-se de 1 em 1 em x, calculando y = m·x + b.
    Senão ela é mais em pé e anda-se de 1 em 1 em y, calculando x = (y − b)/m.
    Os pontos saem na ordem de (x1, y1) para (x2, y2), porque quem chama interpola cor e z
    pela posição na lista.

    Além do quadro: os extremos viram inteiros (o laço sempre termina), o passo pode ser
    −1 (reta da direita para a esquerda ou de cima para baixo) e a reta vertical (m infinito)
    é tratada à parte.
    """
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    dx, dy = x2 - x1, y2 - y1

    if dx == 0 and dy == 0:
        return [(x1, y1)]

    if abs(dx) > abs(dy):                       # mais deitada: anda em x
        m = dy / dx
        b = y1 - m * x1
        passo = 1 if dx > 0 else -1
        return [produz_fragmento(x, m * x + b) for x in range(x1, x2 + passo, passo)]

    passo = 1 if dy > 0 else -1                 # mais em pé: anda em y
    if dx == 0:                                 # vertical: m infinito, x não muda
        return [(x1, y) for y in range(y1, y2 + passo, passo)]
    m = dy / dx
    b = y1 - m * x1
    return [produz_fragmento((y - b) / m, y) for y in range(y1, y2 + passo, passo)]


def calcular_area_triangulo(xa, ya, xb, yb, xc, yc):
    """
    Cálculo exato da área usando o produto vetorial 2D (determinante).
    """
    return 0.5 * abs((xa * (yb - yc)) + (xb * (yc - ya)) + (xc * (ya - yb)))


def coordenadas_baricentricas(xp, yp, xa, ya, xb, yb, xc, yc):
    """
    Calcula as coordenadas alpha, beta e gamma para interpolação de cores e profundidade (Z).
    """
    area_total = calcular_area_triangulo(xa, ya, xb, yb, xc, yc)

    if area_total == 0:
        return -1, -1, -1  # Triângulo degenerado (linha)

    area_alpha = calcular_area_triangulo(xp, yp, xb, yb, xc, yc)
    area_beta = calcular_area_triangulo(xa, ya, xp, yp, xc, yc)

    alpha = area_alpha / area_total
    beta = area_beta / area_total
    gamma = 1.0 - alpha - beta

    return alpha, beta, gamma


def scan_line_par_impar(vertices_2d, largura_tela=800, altura_tela=800):
    """
    Algoritmo Par-Ímpar (Scan Line) minucioso com clamping de bordas para
    evitar processamento ao infinito em projeções distorcidas.
    """
    pixels_internos = []

    y_min = int(np.floor(min(v[1] for v in vertices_2d)))
    y_max = int(np.ceil(max(v[1] for v in vertices_2d)))

    # Proteção estrita contra coordenadas fora da tela
    y_min = max(0, y_min)
    y_max = min(altura_tela - 1, y_max)

    num_vertices = len(vertices_2d)

    for y in range(y_min, y_max + 1):
        intersecoes = []
        for i in range(num_vertices):
            p1 = vertices_2d[i]
            p2 = vertices_2d[(i + 1) % num_vertices]
            y1, y2 = p1[1], p2[1]
            x1, x2 = p1[0], p2[0]

            # Avalia interseção analítica da reta horizontal com a aresta
            if (y1 <= y < y2) or (y2 <= y < y1):
                # Equação da reta interpolada para achar o X
                x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                intersecoes.append(x_int)

        intersecoes.sort()

        # Lógica Par-Ímpar: Pinta entre pares de interseções
        for i in range(0, len(intersecoes), 2):
            if i + 1 < len(intersecoes):
                x_inicio = int(np.ceil(intersecoes[i]))
                x_fim = int(np.floor(intersecoes[i + 1]))

                x_inicio = max(0, x_inicio)
                x_fim = min(largura_tela - 1, x_fim)

                for x in range(x_inicio, x_fim + 1):
                    pixels_internos.append((x, y))

    return pixels_internos