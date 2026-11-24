import argparse

import numpy as np
import matplotlib.pyplot as plt
import illumination
import math_3d
import rasterizer
import cena
from cena import (EYE_PRINCIPAL, EYE_SECUNDARIO, AT, UP, FOV_PRINCIPAL,
                  Z_NEAR, Z_FAR, POSICAO_LUZ)

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================
RESOLUCAO_MARCHING_CUBES = 80               # Qualidade da malha: maior = mais detalhe, mais lento
RESOLUCOES_TELA          = [200, 400, 800]  # Resoluções comparadas na Tela 1
Z_BIAS                   = 0.005            # Tolerância do Z-buffer para evitar z-fighting

# A cena, as câmeras e a luz ficam em cena.py.


# ==============================================================================
# AUXILIARES DE VISUALIZAÇÃO
# ==============================================================================
def ndc_para_pixel(ndc, res):
    """Converte coordenadas NDC [-1, 1] para posição de pixel [0, res]."""
    x = (ndc[0] + 1.0) * 0.5 * res
    y = (1.0 - ndc[1]) * 0.5 * res
    return x, y


def projetar(p_mundo, view_matrix, proj_matrix):
    """Leva um ponto do mundo até o NDC: câmera (view), projeção e divisão por w."""
    v_camera = view_matrix @ np.append(p_mundo, 1.0)
    return math_3d.divisao_perspectiva(proj_matrix @ v_camera)


def desenhar_reta_3d_no_zbuffer(p1_mundo, p2_mundo, cor, imagem, z_buffer, view_matrix, proj_matrix, res):
    """Projeta e rasteriza uma linha 3D no Z-buffer pela equação da reta."""
    v1_ndc = projetar(p1_mundo, view_matrix, proj_matrix)
    v2_ndc = projetar(p2_mundo, view_matrix, proj_matrix)

    if abs(v1_ndc[0]) > 1.8 or abs(v1_ndc[1]) > 1.8 or abs(v2_ndc[0]) > 1.8 or abs(v2_ndc[1]) > 1.8:
        return

    x1, y1 = (int(c) for c in ndc_para_pixel(v1_ndc, res))
    x2, y2 = (int(c) for c in ndc_para_pixel(v2_ndc, res))

    pontos = rasterizer.rasterizar_reta(x1, y1, x2, y2)
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


def desenhar_aresta(p1, p2, z1, z2, cor1, cor2, imagem, z_buffer):
    """
    Desenha a aresta de uma face com a equação da reta, já em coordenadas de pixel. A cor e a
    profundidade variam linearmente entre os extremos, então a aresta tem a cor iluminada
    do próprio sólido. Usa o Z-buffer sem folga: só preenche o que ainda não está coberto.
    """
    res = imagem.shape[0]
    # Sem recorte de retas: ignora aresta com extremo muito fora da tela (evita laços enormes)
    if any(abs(c) > 2 * res for c in (*p1, *p2)):
        return

    pontos = rasterizer.rasterizar_reta(p1[0], p1[1], p2[0], p2[1])
    for idx, (px, py) in enumerate(pontos):
        if 0 <= px < res and 0 <= py < res:
            t = idx / max(len(pontos) - 1, 1)
            z = (1 - t) * z1 + t * z2
            if z < z_buffer[py, px]:
                z_buffer[py, px] = z
                cor = (1 - t) * cor1 + t * cor2
                imagem[py, px] = (np.clip(cor, 0.0, 1.0) * 255).astype(np.uint8)


def desenhar_origem_mundo(imagem, z_buffer, view_matrix, proj_matrix, res):
    """Marca a origem do mundo (0, 0, 0) com uma pequena cruz laranja (item 3d)."""
    COR_ORIGEM = [255, 110, 30]
    r = 0.4
    origem = np.zeros(3)
    for eixo in np.eye(3):
        desenhar_reta_3d_no_zbuffer(origem - r * eixo, origem + r * eixo, COR_ORIGEM,
                                    imagem, z_buffer, view_matrix, proj_matrix, res)


def desenhar_grade_chao(imagem, z_buffer, view_matrix, proj_matrix, res):
    """Desenha a grade do chão (y = Y_CHAO) entre -10 e 10, com uma linha a cada 5 unidades."""
    COR_GRADE = [205, 215, 228]
    L, y = cena.LIMITE, cena.Y_CHAO
    for g in np.arange(-L, L + 1.0, 5.0):
        for p1, p2 in (([g, y, -L], [g, y, L]), ([-L, y, g], [L, y, g])):
            desenhar_reta_3d_no_zbuffer(p1, p2, COR_GRADE, imagem, z_buffer,
                                        view_matrix, proj_matrix, res)


# ==============================================================================
# PIPELINE DE RENDERIZAÇÃO — Culling + Phong + Scan-line + Z-buffer
# ==============================================================================
def renderizar_cena_completa(resolucao_tela, view_matrix, proj_matrix, objetos_cena,
                             posicao_camera, posicao_luz):
    """
    Renderiza a cena completa. Devolve a imagem NumPy (H x W x 3) e a contagem de faces:
    total, fora_do_volume (estágio 2), de_costas (estágio 3) e desenhadas.

    Estágios por face:
      1. Transformação dos vértices/normais para o espaço do mundo
      2. Recorte pelo volume de visão (near, far e laterais)
      3. Back-face culling (normal da face e vetor até o observador, em coordenadas de câmera)
      4. Iluminação de Phong nos 3 vértices
      5. Scan-line par-ímpar → pixels internos do triângulo
      6. Interpolação baricêntrica de cor e profundidade Z
      7. Z-buffer → escreve o pixel mais próximo
      8. Arestas da face com a equação da reta, na cor iluminada dos vértices
    """
    imagem   = np.full((resolucao_tela, resolucao_tela, 3), 245, dtype=np.uint8)
    # Z-buffer: guarda a profundidade do que já foi pintado em cada pixel.
    z_buffer = np.full((resolucao_tela, resolucao_tela), np.inf)

    desenhar_grade_chao(imagem, z_buffer, view_matrix, proj_matrix, resolucao_tela)

    # Quantas faces cada estágio descartou ou desenhou (aparece no título da imagem)
    total = fora_do_volume = de_costas = desenhadas = 0

    for obj in objetos_cena:
        solido   = obj["solido"]
        faces    = solido["faces"]
        cor_base = solido["cor"]

        # Estágio 1: vértices e normais no espaço do mundo (matriz M = T·Rz·Ry·Rx·S de cena.py).
        # Normais usam a inversa transposta de M, que as mantém perpendiculares à superfície.
        # Cada linha abaixo aplica n' = N·n a todas as normais de uma vez (N = matriz_normal).
        vertices_mundo = obj["vertices_mundo"]
        N = math_3d.matriz_normal(obj["matriz"])
        normais_mundo = solido["normais_vertices"] @ N.T

        # Normais das faces no sistema da câmera, para o culling. A view é só rotação e
        # translação, então a parte 3x3 dela leva as normais (sem translação).
        normais_faces_mundo  = solido["normais_faces"] @ N.T
        normais_faces_camera = normais_faces_mundo @ view_matrix[:3, :3].T

        # Cor de Phong de cada vértice, calculada só quando uma face visível precisa dela
        cores = {}

        vertices_camera = []
        vertices_clip   = []
        vertices_tela   = []
        profundidades_z = []
        for v in vertices_mundo:
            v_mundo = np.append(v, 1.0)
            v_camera = view_matrix @ v_mundo
            v_clip = proj_matrix @ v_camera
            v_ndc = math_3d.divisao_perspectiva(v_clip)
            vertices_camera.append(v_camera[:3])
            vertices_clip.append(v_clip)
            profundidades_z.append(v_ndc[2])
            vertices_tela.append(ndc_para_pixel(v_ndc, resolucao_tela))

        for i_face, face in enumerate(faces):
            total += 1

            # Estágio 2: Recorte — descarta faces atrás do near ou fora do volume de visão
            if not math_3d.face_no_volume_de_visao(*(vertices_clip[i] for i in face)):
                fora_do_volume += 1
                continue

            # Estágio 3: Back-face culling — normal da face e vetor até o observador (câmera)
            if not math_3d.face_voltada_para_camera(normais_faces_camera[i_face],
                                                    vertices_camera[face[0]]):
                de_costas += 1
                continue
            desenhadas += 1

            # Estágio 4: Phong nos 3 vértices (Gouraud shading). Um vértice é compartilhado
            # por vários triângulos, então a cor dele é calculada uma única vez.
            for v_idx in face:
                if v_idx not in cores:
                    cores[v_idx] = illumination.calcular_iluminacao_phong(
                        vertice_mundo=vertices_mundo[v_idx],
                        normal=normais_mundo[v_idx],
                        posicao_luz=posicao_luz,
                        posicao_camera=posicao_camera,
                        cor_objeto=cor_base,
                    )
            cores_vertices = [cores[v_idx] for v_idx in face]

            pA, pB, pC = vertices_tela[face[0]], vertices_tela[face[1]], vertices_tela[face[2]]
            zA, zB, zC = profundidades_z[face[0]], profundidades_z[face[1]], profundidades_z[face[2]]

            # Estágio 5: Scan-line par-ímpar → lista de pixels internos
            pixels = rasterizer.scan_line_par_impar(
                [pA, pB, pC], largura_tela=resolucao_tela, altura_tela=resolucao_tela
            )

            # Estágios 6–7: baricêntrica + Z-buffer por pixel
            for (x, y) in pixels:
                alpha, beta, gamma = rasterizer.coordenadas_baricentricas(
                    x, y, pA[0], pA[1], pB[0], pB[1], pC[0], pC[1]
                )
                if alpha >= 0 and beta >= 0 and gamma >= 0:
                    z_pixel = alpha * zA + beta * zB + gamma * zC
                    # Menor z = mais perto da câmera: só pinta se for mais perto que o já guardado.
                    if z_pixel < z_buffer[y, x]:
                        z_buffer[y, x] = z_pixel
                        cor_pixel = (alpha * cores_vertices[0]
                                     + beta  * cores_vertices[1]
                                     + gamma * cores_vertices[2])
                        imagem[y, x] = (np.clip(cor_pixel, 0.0, 1.0) * 255).astype(np.uint8)

            # Estágio 8: arestas da face com a equação da reta, na cor iluminada dos vértices.
            # Fecham as frestas que o scan-line deixa nas bordas dos triângulos.
            c0, c1, c2 = cores_vertices
            for p1, p2, z1, z2, cor1, cor2 in [(pA, pB, zA, zB, c0, c1),
                                               (pB, pC, zB, zC, c1, c2),
                                               (pC, pA, zC, zA, c2, c0)]:
                desenhar_aresta(p1, p2, z1, z2, cor1, cor2, imagem, z_buffer)

    desenhar_origem_mundo(imagem, z_buffer, view_matrix, proj_matrix, resolucao_tela)

    contagem = {"total": total, "fora_do_volume": fora_do_volume,
                "de_costas": de_costas, "desenhadas": desenhadas}
    return imagem, contagem


# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
def ler_argumentos():
    """Lê a posição do observador da linha de comando (item 3e)."""
    parser = argparse.ArgumentParser(description="Pipeline gráfico da Tela 1 e da Tela 2")
    parser.add_argument("--eye", nargs=3, type=float, metavar=("X", "Y", "Z"),
                        default=EYE_PRINCIPAL.tolist(),
                        help="posição do observador na Tela 1 (padrão: 9.75 13 6.5)")
    return parser.parse_args()


def titulo(cabecalho, contagem):
    """Título da imagem: o cabeçalho e quantas faces cada estágio descartou ou desenhou."""
    return (f"{cabecalho}\n"
            f"{contagem['total']} faces: {contagem['desenhadas']} desenhadas\n"
            f"descartadas: {contagem['fora_do_volume']} fora do volume, "
            f"{contagem['de_costas']} de costas")


def main():
    print("=== PIPELINE CG — MALHAS + PHONG + SCAN-LINE + Z-BUFFER ===")

    args = ler_argumentos()
    eye_principal = np.array(args.eye)

    # Item 3a: base vetorial da câmera principal
    u, v, n = math_3d.base_camera(eye_principal, AT, UP)
    print(f"  eye = {eye_principal}")
    print(f"  u (x da câmera) = {np.round(u, 3)}")
    print(f"  v (y da câmera) = {np.round(v, 3)}")
    print(f"  n (z da câmera) = {np.round(n, 3)}")

    # Item 1: cada sólido é construído uma única vez (vértices, arestas, faces, normais, cor)
    solidos = cena.criar_solidos(RESOLUCAO_MARCHING_CUBES, mostrar_progresso=True)

    # Item 2: leva os sólidos para o mundo e confere |10| e sobreposição
    print("\n  Cena no mundo:")
    objetos_cena = cena.montar_cena(solidos)
    cena.imprimir_resumo(objetos_cena)

    # Matrizes de câmera e projeção para cada imagem
    view_principal  = math_3d.look_at(eye=eye_principal,  at=AT, up=UP)
    view_secundaria = math_3d.look_at(eye=EYE_SECUNDARIO, at=AT, up=UP)
    proj_principal  = math_3d.projecao_perspectiva(fov_graus=FOV_PRINCIPAL, aspecto=1.0, z_near=Z_NEAR, z_far=Z_FAR)
    proj_secundaria = math_3d.projecao_perspectiva(fov_graus=50, aspecto=1.0, z_near=Z_NEAR, z_far=Z_FAR)

    # Tela 1: comparativo das 3 resoluções
    fig1, eixos = plt.subplots(1, 3, figsize=(18, 6))
    fig1.canvas.manager.set_window_title("Tela 1: Comparativo de Resoluções")

    for ax, res in zip(eixos, RESOLUCOES_TELA):
        print(f"  Rasterizando {res}×{res}...")
        img, contagem = renderizar_cena_completa(
            res, view_principal, proj_principal,
            objetos_cena, eye_principal, POSICAO_LUZ
        )
        ax.imshow(img)
        ax.set_title(titulo(f"Resolução: {res} × {res}", contagem),
                     fontsize=9, fontweight='bold', color='#2c3e50')
        ax.axis('off')

    plt.tight_layout()
    plt.show(block=False)

    # Tela 2: segunda posição do eye (item 3e), vista oblíqua da cena
    print("\n  Rasterizando segunda imagem 800×800...")
    img_secundaria, contagem = renderizar_cena_completa(
        800, view_secundaria, proj_secundaria,
        objetos_cena, EYE_SECUNDARIO, POSICAO_LUZ
    )

    fig2, ax2 = plt.subplots(figsize=(8, 8))
    fig2.canvas.manager.set_window_title("Tela 2: segundo eye")
    ax2.imshow(img_secundaria)
    ax2.set_title(titulo(f"Segundo eye = {EYE_SECUNDARIO.tolist()}", contagem),
                  fontsize=10, fontweight='bold', color='#2c3e50')
    ax2.axis('off')

    print("Concluído.")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()