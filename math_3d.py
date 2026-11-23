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


def aplicar_matriz(matriz, pontos):
    """
    Aplica uma matriz 4x4 a uma lista de pontos (N, 3) e devolve (N, 3).
    Acrescenta a coordenada homogênea 1 em cada ponto antes de multiplicar.
    """
    pontos = np.asarray(pontos, dtype=float)
    homogeneos = np.hstack([pontos, np.ones((len(pontos), 1))])
    return (matriz @ homogeneos.T).T[:, :3]


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