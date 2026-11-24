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
    f = 1.0 / np.tan(fov_rad / 2.0)  # f é o d = cotg(α/2) da aula (janela de altura 2)

    matriz = np.zeros((4, 4), dtype=float)
    matriz[0, 0] = f / aspecto
    matriz[1, 1] = f

    # Cálculo minucioso das componentes de profundidade (Z)
    matriz[2, 2] = (z_far + z_near) / (z_near - z_far)
    matriz[2, 3] = (2.0 * z_far * z_near) / (z_near - z_far)
    # w = -z (a câmera olha para -z). Dividir por w é a divisão por z da aula: x' = d·x/z
    matriz[3, 2] = -1.0

    return matriz


def divisao_perspectiva(vertice_4d):
    """ Divide x, y, z pela coordenada homogênea W. Em x e y é o x' = d·x/z da aula. """
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
    vertices = (clip_a, clip_b, clip_c)

    # Plano near: um único vértice atrás dele já descarta o triângulo
    for x, y, z, w in vertices:
        if z < -w:
            return False

    # Para cada um dos outros 5 planos, descarta se os 3 vértices estão do lado de fora
    if all(x < -w for x, y, z, w in vertices):   # esquerda
        return False
    if all(x > w for x, y, z, w in vertices):    # direita
        return False
    if all(y < -w for x, y, z, w in vertices):   # baixo
        return False
    if all(y > w for x, y, z, w in vertices):    # cima
        return False
    if all(z > w for x, y, z, w in vertices):    # far
        return False
    return True


def face_voltada_para_camera(normal_camera, vertice_camera):
    """
    Back-face culling da aula, em coordenadas de câmera: n · v < 0 desenha.
    O observador está na origem, então v = vertice_camera - eye = vertice_camera
    (vetor da câmera até a face). Se n · v < 0, a face está de frente; se n · v >= 0,
    está de costas ou de lado.
    Em perspectiva a direção de visada muda de face para face; só no centro da imagem ela
    coincide com o eixo z da câmera. Testar apenas o sinal de normal_camera[2] descartaria,
    perto das bordas, faces quase de lado que ainda são visíveis.
    """
    return np.dot(normal_camera, vertice_camera) < 0