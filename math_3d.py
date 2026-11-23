import numpy as np


def translacao(tx, ty, tz):
    """ Matriz de Translação 4x4 """
    return np.array([
        [1.0, 0.0, 0.0, tx],
        [0.0, 1.0, 0.0, ty],
        [0.0, 0.0, 1.0, tz],
        [0.0, 0.0, 0.0, 1.0]
    ])


def escala(sx, sy, sz):
    """ Matriz de Escala 4x4 """
    return np.array([
        [sx, 0.0, 0.0, 0.0],
        [0.0, sy, 0.0, 0.0],
        [0.0, 0.0, sz, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def rotacao_y(theta_radianos):
    """ Matriz de Rotação em torno do eixo Y 4x4 """
    cos_t = np.cos(theta_radianos)
    sin_t = np.sin(theta_radianos)
    return np.array([
        [cos_t, 0.0, sin_t, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-sin_t, 0.0, cos_t, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def rotacao_x(theta_radianos):
    """ Matriz de Rotação em torno do eixo X 4x4 """
    cos_t = np.cos(theta_radianos)
    sin_t = np.sin(theta_radianos)
    return np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, cos_t, -sin_t, 0.0],
        [0.0, sin_t, cos_t, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def rotacao_z(theta_radianos):
    """ Matriz de Rotação em torno do eixo Z 4x4 """
    cos_t = np.cos(theta_radianos)
    sin_t = np.sin(theta_radianos)
    return np.array([
        [cos_t, -sin_t, 0.0, 0.0],
        [sin_t, cos_t, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matriz_mundo(translacao_xyz, rotacao_graus=(0.0, 0.0, 0.0), escala_xyz=(1.0, 1.0, 1.0)):
    """
    Matriz do mundo M = T · Rz · Ry · Rx · S (leva do sistema do objeto para o do mundo).

    Lida da direita para a esquerda: primeiro a escala, depois as rotações em x, y e z
    (todas em torno da origem do objeto) e, por último, a translação até a posição na cena.
    """
    rx, ry, rz = np.radians(rotacao_graus)
    return (translacao(*translacao_xyz)
            @ rotacao_z(rz) @ rotacao_y(ry) @ rotacao_x(rx)
            @ escala(*escala_xyz))


def aplicar_transformacao(matriz, pontos):
    """
    Aplica uma matriz 4x4 a uma lista de pontos (N, 3).
    Cada ponto vira (x, y, z, 1) em coordenadas homogêneas, é multiplicado pela matriz
    e volta para (x, y, z).
    """
    homogeneos = np.hstack([pontos, np.ones((len(pontos), 1))])
    return (homogeneos @ matriz.T)[:, :3]


def matriz_normal(matriz):
    """
    Matriz 3x3 que transforma normais: inversa transposta da parte 3x3 de M.
    Com escala não uniforme, transformar a normal por M a deixaria torta em relação à
    superfície; a inversa transposta mantém a normal perpendicular.
    """
    return np.linalg.inv(matriz[:3, :3]).T


def base_camera(eye, at, up):
    """
    Calcula a base vetorial (u, v, n) do sistema de coordenadas da câmera.
    Os três vetores são unitários e perpendiculares entre si.
    """
    eye = np.array(eye, dtype=float)
    at = np.array(at, dtype=float)
    up = np.array(up, dtype=float)

    # 1. Vetor n (eixo Z da câmera): aponta de 'at' para 'eye'
    n = eye - at
    if np.linalg.norm(n) == 0:
        raise ValueError("eye e at são o mesmo ponto: não há direção de visada")
    n = n / np.linalg.norm(n)

    # 2. Vetor u (eixo X da câmera): perpendicular a 'up' e a 'n'
    u = np.cross(up, n)
    if np.linalg.norm(u) == 0:
        raise ValueError("eye está na mesma vertical de at: o vetor up fica paralelo a n")
    u = u / np.linalg.norm(u)

    # 3. Vetor v (eixo Y da câmera): perpendicular a 'n' e a 'u'
    v = np.cross(n, u)

    return u, v, n


def look_at(eye, at, up):
    """
    Matriz de visualização 4x4: leva pontos do mundo para o sistema da câmera.
    """
    eye = np.array(eye, dtype=float)
    u, v, n = base_camera(eye, at, up)

    # Matriz de Visualização (View Matrix) = Alinhamento de base * Translação
    view_matrix = np.array([
        [u[0], u[1], u[2], -np.dot(u, eye)],
        [v[0], v[1], v[2], -np.dot(v, eye)],
        [n[0], n[1], n[2], -np.dot(n, eye)],
        [0.0, 0.0, 0.0, 1.0]
    ])

    return view_matrix


def projecao_perspectiva(fov_graus, aspecto, z_near, z_far):
    """
    Matriz de Projeção em Perspectiva 4x4 estrita.
    """
    fov_rad = np.radians(fov_graus)
    f = 1.0 / np.tan(fov_rad / 2.0)

    matriz = np.zeros((4, 4), dtype=float)
    matriz[0, 0] = f / aspecto
    matriz[1, 1] = f

    # Cálculo minucioso das componentes de profundidade (Z)
    matriz[2, 2] = (z_far + z_near) / (z_near - z_far)
    matriz[2, 3] = (2.0 * z_far * z_near) / (z_near - z_far)
    matriz[3, 2] = -1.0  # Guarda o Z original na componente W para a divisão perspectiva

    return matriz


def divisao_perspectiva(vertice_4d):
    """ Divide x, y, z pela coordenada homogênea W """
    if vertice_4d[3] != 0:
        return vertice_4d[:3] / vertice_4d[3]
    return vertice_4d[:3]


def face_no_volume_de_visao(clip_a, clip_b, clip_c):
    """
    Diz se um triângulo pode aparecer na imagem (True) ou deve ser descartado (False).
    Recebe os 3 vértices em coordenadas de recorte (x, y, z, w), antes da divisão por w.
    Nessas coordenadas, um ponto está dentro do volume de visão quando
    -w <= x, y, z <= w; cada desigualdade é um dos 6 planos do frustum.

    Descarta o triângulo inteiro (não há recorte de polígonos) quando:
      1. Algum vértice está atrás do near (z < -w). Depois da divisão por w, esse
         vértice cairia do lado errado da câmera e deformaria o triângulo.
      2. Os 3 vértices estão fora do mesmo plano (esquerda, direita, baixo, cima ou far).
         Se estivessem em planos diferentes, o triângulo ainda poderia cruzar a tela.
    """
    x, y, z, w = np.array([clip_a, clip_b, clip_c]).T

    if np.any(z < -w):
        return False
    for coordenada in (x, y):
        if np.all(coordenada < -w) or np.all(coordenada > w):
            return False
    return not np.all(z > w)