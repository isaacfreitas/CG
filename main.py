import argparse

import numpy as np
import matplotlib.pyplot as plt
import modeling
import illumination
import math_3d
import rasterizer
import cena

# ==============================================================================
# CONFIGURAÇÃO GLOBAL — ajuste aqui para testes rápidos
# ==============================================================================
RESOLUCAO_MARCHING_CUBES = 80               # Qualidade da malha: maior = mais detalhe, mais lento
RESOLUCOES_TELA          = [200, 400, 800]  # Resoluções comparadas na Tela 1

EYE_PRINCIPAL = np.array([7.5,  10.0,  5.0])   # Câmera da Tela 1 (visão frontal)
EYE_BLENDER   = np.array([26.0, 18.0, 28.0])   # Câmera da Tela 2 (visão oblíqua)
AT            = np.array([0.0,   0.0,  0.0])   # Ponto para onde as câmeras apontam
UP            = np.array([0.0,   1.0,  0.0])   # Vetor "cima" do mundo

POSICAO_LUZ   = np.array([5.0, 20.0, 15.0])    # Posição da fonte de luz no espaço do mundo
Z_BIAS        = 0.005                           # Tolerância do Z-buffer para evitar z-fighting

# A cena (posição, rotação e escala de cada objeto) fica em cena.py.


# ==============================================================================
# AUXILIARES DE VISUALIZAÇÃO
# ==============================================================================
def ndc_para_pixel(ndc, res):
    """Converte coordenadas NDC [-1, 1] para posição de pixel [0, res]."""
    x = (ndc[0] + 1.0) * 0.5 * res
    y = (1.0 - ndc[1]) * 0.5 * res
    return x, y


def calcular_posicao_tela_rotulo(p_mundo, view_matrix, proj_matrix, res):
    """Projeta um ponto 3D do mundo para pixel 2D (usado nos ticks do grid)."""
    v_cam = view_matrix @ np.array([p_mundo[0], p_mundo[1], p_mundo[2], 1.0])
    v_ndc = math_3d.divisao_perspectiva(proj_matrix @ v_cam)
    if abs(v_ndc[0]) > 1.0 or abs(v_ndc[1]) > 1.0:
        return None
    return ndc_para_pixel(v_ndc, res)


def desenhar_ticks(ax, view_matrix, proj_matrix, res):
    """Desenha os rótulos numéricos do grid nos eixos X e Z."""
    escala_fonte = max(6, int(res * 0.02))
    offset       = res * 0.04

    for val in [-15, -10, -5, 0, 5, 10, 15]:
        pos = calcular_posicao_tela_rotulo([val, -2.0, 10.0], view_matrix, proj_matrix, res)
        if pos:
            ax.text(pos[0], pos[1] + offset, str(val), color='#7f8c8d',
                    fontsize=escala_fonte, ha='center', va='top', weight='bold')

    for val in [-10, -5, 0, 5, 10]:
        pos = calcular_posicao_tela_rotulo([-15.0, -2.0, val], view_matrix, proj_matrix, res)
        if pos:
            ax.text(pos[0] - offset, pos[1], str(val), color='#7f8c8d',
                    fontsize=escala_fonte, ha='right', va='center', weight='bold')


def desenhar_reta_3d_no_zbuffer(p1_mundo, p2_mundo, cor, imagem, z_buffer, view_matrix, proj_matrix, res):
    """Projeta e rasteriza uma linha 3D no Z-buffer via Bresenham."""
    def projetar(p):
        v_cam = view_matrix @ np.array([p[0], p[1], p[2], 1.0])
        return math_3d.divisao_perspectiva(proj_matrix @ v_cam)

    v1_ndc = projetar(p1_mundo)
    v2_ndc = projetar(p2_mundo)

    if abs(v1_ndc[0]) > 1.8 or abs(v1_ndc[1]) > 1.8 or abs(v2_ndc[0]) > 1.8 or abs(v2_ndc[1]) > 1.8:
        return

    x1, y1 = int(ndc_para_pixel(v1_ndc, res)[0]), int(ndc_para_pixel(v1_ndc, res)[1])
    x2, y2 = int(ndc_para_pixel(v2_ndc, res)[0]), int(ndc_para_pixel(v2_ndc, res)[1])

    pontos = rasterizer.rasterizar_bresenham(x1, y1, x2, y2)
    n_pts  = len(pontos)
    if n_pts == 0:
        return

    for idx, (px, py) in enumerate(pontos):
        if 0 <= px < res and 0 <= py < res:
            t = idx / n_pts
            z = (1 - t) * v1_ndc[2] + t * v2_ndc[2]
            if z < z_buffer[py, px] + Z_BIAS:
                z_buffer[py, px] = z
                imagem[py, px]   = np.array(cor, dtype=np.uint8)


def desenhar_origem_mundo(imagem, z_buffer, view_matrix, proj_matrix, res):
    """Marca a origem do mundo (0, 0, 0) com uma pequena cruz laranja (item 3d)."""
    COR_ORIGEM = [255, 110, 30]
    r = 0.4
    origem = np.zeros(3)
    for eixo in np.eye(3):
        desenhar_reta_3d_no_zbuffer(origem - r * eixo, origem + r * eixo, COR_ORIGEM,
                                    imagem, z_buffer, view_matrix, proj_matrix, res)


def desenhar_caixa_proporcao_mundo(imagem, z_buffer, view_matrix, proj_matrix, res):
    """Desenha o grid de chão e a gaiola cúbica delimitando o espaço da cena."""
    COR_CAIXA = [205, 215, 228]
    COR_GRADE = [234, 240, 246]
    X_MIN, X_MAX = -10.0, 10.0
    Z_MIN, Z_MAX = -10.0, 10.0
    Y_CHAO, Y_TETO = -2.0, 7.0

    def reta(p1, p2, cor):
        desenhar_reta_3d_no_zbuffer(p1, p2, cor, imagem, z_buffer, view_matrix, proj_matrix, res)

    # Grade de chão (a cada 5 unidades)
    for gx in np.arange(X_MIN, X_MAX + 1.0, 5.0):
        reta([gx, Y_CHAO, Z_MIN], [gx, Y_CHAO, Z_MAX], COR_GRADE)
    for gz in np.arange(Z_MIN, Z_MAX + 1.0, 5.0):
        reta([X_MIN, Y_CHAO, gz], [X_MAX, Y_CHAO, gz], COR_GRADE)

    # Gaiola cúbica (12 arestas)
    for p1, p2 in [
        ([X_MIN, Y_CHAO, Z_MIN], [X_MAX, Y_CHAO, Z_MIN]),
        ([X_MIN, Y_CHAO, Z_MAX], [X_MAX, Y_CHAO, Z_MAX]),
        ([X_MIN, Y_CHAO, Z_MIN], [X_MIN, Y_CHAO, Z_MAX]),
        ([X_MAX, Y_CHAO, Z_MIN], [X_MAX, Y_CHAO, Z_MAX]),
        ([X_MIN, Y_CHAO, Z_MIN], [X_MIN, Y_TETO, Z_MIN]),
        ([X_MAX, Y_CHAO, Z_MIN], [X_MAX, Y_TETO, Z_MIN]),
        ([X_MIN, Y_CHAO, Z_MAX], [X_MIN, Y_TETO, Z_MAX]),
        ([X_MAX, Y_CHAO, Z_MAX], [X_MAX, Y_TETO, Z_MAX]),
        ([X_MIN, Y_TETO, Z_MIN], [X_MAX, Y_TETO, Z_MIN]),
        ([X_MIN, Y_TETO, Z_MAX], [X_MAX, Y_TETO, Z_MAX]),
        ([X_MIN, Y_TETO, Z_MIN], [X_MIN, Y_TETO, Z_MAX]),
        ([X_MAX, Y_TETO, Z_MIN], [X_MAX, Y_TETO, Z_MAX]),
    ]:
        reta(p1, p2, COR_CAIXA)


# ==============================================================================
# PIPELINE DE RENDERIZAÇÃO — Culling + Phong + Scan-line + Z-buffer
# ==============================================================================
def renderizar_cena_completa(resolucao_tela, view_matrix, proj_matrix, objetos_cena,
                             posicao_camera, posicao_luz):
    """
    Renderiza a cena completa em uma imagem NumPy (H x W x 3).

    Estágios por face:
      1. Transformação dos vértices/normais para o espaço do mundo
      2. Back-face culling
      3. Iluminação de Phong nos 3 vértices
      4. Scan-line par-ímpar → pixels internos do triângulo
      5. Interpolação baricêntrica de cor e profundidade Z
      6. Z-buffer → escreve o pixel mais próximo
    """
    imagem   = np.full((resolucao_tela, resolucao_tela, 3), 245, dtype=np.uint8)
    z_buffer = np.full((resolucao_tela, resolucao_tela), np.inf)

    desenhar_caixa_proporcao_mundo(imagem, z_buffer, view_matrix, proj_matrix, resolucao_tela)

    for obj in objetos_cena:
        solido   = obj["solido"]
        faces    = solido["faces"]
        cor_base = solido["cor"]

        # Estágio 1: vértices e normais no espaço do mundo (matriz M = T·Rz·Ry·Rx·S de cena.py).
        # Normais usam a inversa transposta de M, que as mantém perpendiculares à superfície.
        vertices_mundo = obj["vertices_mundo"]
        normais_mundo  = solido["normais_vertices"] @ math_3d.matriz_normal(obj["matriz"]).T

        vertices_tela   = []
        profundidades_z = []
        for v in vertices_mundo:
            v_mundo = np.append(v, 1.0)
            v_ndc = math_3d.divisao_perspectiva(proj_matrix @ (view_matrix @ v_mundo))
            profundidades_z.append(v_ndc[2])
            vertices_tela.append(ndc_para_pixel(v_ndc, resolucao_tela))

        for face in faces:
            v0, v1, v2 = vertices_mundo[face[0]], vertices_mundo[face[1]], vertices_mundo[face[2]]

            # Estágio 2: Back-face culling — descarta faces voltadas para longe da câmera
            normal_face = np.cross(v1 - v0, v2 - v0)
            if np.dot(normal_face, posicao_camera - v0) <= 0:
                continue

            # Estágio 3: Phong nos 3 vértices (Gouraud shading)
            cores_vertices = [
                illumination.calcular_iluminacao_phong(
                    vertice_mundo=vertices_mundo[v_idx],
                    normal=normais_mundo[v_idx],
                    posicao_luz=posicao_luz,
                    posicao_camera=posicao_camera,
                    cor_objeto=cor_base,
                    coeficientes=(0.5, 0.8, 0.4),
                    brilho=32,
                )
                for v_idx in face
            ]

            pA, pB, pC = vertices_tela[face[0]], vertices_tela[face[1]], vertices_tela[face[2]]
            zA, zB, zC = profundidades_z[face[0]], profundidades_z[face[1]], profundidades_z[face[2]]

            # Estágio 4: Scan-line par-ímpar → lista de pixels internos
            pixels = rasterizer.scan_line_par_impar(
                [pA, pB, pC], largura_tela=resolucao_tela, altura_tela=resolucao_tela
            )

            # Estágios 5–6: baricêntrica + Z-buffer por pixel
            for (x, y) in pixels:
                alpha, beta, gamma = rasterizer.coordenadas_baricentricas(
                    x, y, pA[0], pA[1], pB[0], pB[1], pC[0], pC[1]
                )
                if alpha >= 0 and beta >= 0 and gamma >= 0:
                    z_pixel = alpha * zA + beta * zB + gamma * zC
                    if z_pixel < z_buffer[y, x]:
                        z_buffer[y, x] = z_pixel
                        cor_pixel = (alpha * cores_vertices[0]
                                     + beta  * cores_vertices[1]
                                     + gamma * cores_vertices[2])
                        imagem[y, x] = (np.clip(cor_pixel, 0.0, 1.0) * 255).astype(np.uint8)

    desenhar_origem_mundo(imagem, z_buffer, view_matrix, proj_matrix, resolucao_tela)

    return imagem


# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
def ler_argumentos():
    """Lê a posição do observador da linha de comando (item 3e)."""
    parser = argparse.ArgumentParser(description="Pipeline gráfico da Tela 1 e da Tela 2")
    parser.add_argument("--eye", nargs=3, type=float, metavar=("X", "Y", "Z"),
                        default=EYE_PRINCIPAL.tolist(),
                        help="posição do observador na Tela 1 (padrão: 7.5 10 5)")
    return parser.parse_args()


def main():
    print("=== PIPELINE CG — MALHAS + PHONG + SCAN-LINE + Z-BUFFER ===")

    eye_principal = np.array(ler_argumentos().eye)

    # Item 3a: base vetorial da câmera principal
    u, v, n = math_3d.base_camera(eye_principal, AT, UP)
    print(f"  eye = {eye_principal}")
    print(f"  u (x da câmera) = {np.round(u, 3)}")
    print(f"  v (y da câmera) = {np.round(v, 3)}")
    print(f"  n (z da câmera) = {np.round(n, 3)}")

    # Item 1: cada sólido é construído uma única vez (vértices, arestas, faces, normais, cor)
    solidos = {}
    total = len(cena.CENA)
    for i, item in enumerate(cena.CENA):
        print(f"  [{i + 1}/{total}] Criando sólido: {item['nome']}")
        solidos[item["nome"]] = modeling.obter_solido(item["nome"], RESOLUCAO_MARCHING_CUBES)

    # Item 2: leva os sólidos para o mundo e confere |10| e sobreposição
    print("\n  Cena no mundo:")
    objetos_cena = cena.montar_cena(solidos)
    cena.imprimir_resumo(objetos_cena)

    # Matrizes de câmera e projeção para cada viewport
    view_principal = math_3d.look_at(eye=eye_principal, at=AT, up=UP)
    view_blender   = math_3d.look_at(eye=EYE_BLENDER,   at=AT, up=UP)
    proj_principal = math_3d.projecao_perspectiva(fov_graus=58, aspecto=1.0, z_near=0.1, z_far=100)
    proj_blender   = math_3d.projecao_perspectiva(fov_graus=50, aspecto=1.0, z_near=0.1, z_far=100)

    # Tela 1: comparativo das 3 resoluções
    fig1, eixos = plt.subplots(1, 3, figsize=(18, 6))
    fig1.canvas.manager.set_window_title("Tela 1: Comparativo de Resoluções")

    for ax, res in zip(eixos, RESOLUCOES_TELA):
        print(f"  Rasterizando {res}×{res}...")
        img = renderizar_cena_completa(
            res, view_principal, proj_principal,
            objetos_cena, eye_principal, POSICAO_LUZ
        )
        ax.imshow(img)
        ax.set_title(f"Resolução: {res} × {res}", fontsize=11, fontweight='bold', color='#2c3e50')
        ax.axis('off')
        desenhar_ticks(ax, view_principal, proj_principal, res)

    plt.tight_layout()
    plt.show(block=False)

    # Tela 2: viewport oblíqua estilo Blender com origem e pirâmide da câmera
    print("\n  Rasterizando viewport externa 800×800...")
    img_blender = renderizar_cena_completa(
        800, view_blender, proj_blender,
        objetos_cena, EYE_BLENDER, POSICAO_LUZ
    )

    fig2, ax2 = plt.subplots(figsize=(8, 8))
    fig2.canvas.manager.set_window_title("Tela 2: Viewport Blender")
    ax2.imshow(img_blender)
    ax2.set_title("Visão Global — Espaço do Mundo", fontsize=12, fontweight='bold', color='#2c3e50')
    ax2.axis('off')
    desenhar_ticks(ax2, view_blender, proj_blender, 800)

    print("Concluído.")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()