"""
cena.py — Item 2 do enunciado: composição da cena no sistema do mundo
======================================================================
Cada sólido é levado do sistema do objeto para o do mundo pela matriz
    M = T · Rz · Ry · Rx · S
e a cena é conferida automaticamente: nenhuma coordenada passa de |10| e nenhum
objeto encosta em outro.
"""

import numpy as np

import math_3d
import modeling

LIMITE = 10.0     # maior valor permitido para cada componente de um vértice
Y_CHAO = -2.0     # altura do chão onde os objetos ficam apoiados

# ==============================================================================
# CONFIGURAÇÃO DA CENA
# ==============================================================================
# posicao : (x, z) no mundo. O y é calculado para o objeto ficar apoiado no chão.
# rotacao : ângulos em graus em torno de x, y e z (aplicados nessa ordem).
# escala  : fator em x, y e z.
CENA = [
    # Peão: só ampliado.
    {"nome": "Peão",    "posicao": (-6.5, -4.5), "rotacao": (0, 0, 0),     "escala": (1.2, 1.2, 1.2)},
    # Lápis: deitado (90° em x) e girado 45° em y, na diagonal do chão.
    {"nome": "Lápis",   "posicao": (-8.0,  0.5), "rotacao": (90, 45, 0),   "escala": (1.0, 1.0, 1.0)},
    # Altere: modelado deitado; 90° em z o deixa em pé sobre uma das esferas. Reduzido.
    {"nome": "Altere",  "posicao": (-1.5, -4.5), "rotacao": (0, 0, 90),    "escala": (0.9, 0.9, 0.9)},
    # Martelo: deitado com a cabeça apoiada no chão (-90° em x) e girado -30° em y.
    {"nome": "Martelo", "posicao": ( 1.0,  3.2), "rotacao": (-90, -30, 0), "escala": (1.0, 1.0, 1.0)},
    # Lixeira: só ampliada.
    {"nome": "Lixeira", "posicao": ( 3.5, -4.5), "rotacao": (0, 0, 0),     "escala": (1.1, 1.1, 1.1)},
]


def montar_matriz(item, vertices_objeto):
    """
    Monta a matriz do mundo de um item da CENA.

    Primeiro aplica só R·S para saber qual é o ponto mais baixo do objeto já girado e
    escalado; a translação em y é escolhida para esse ponto encostar no chão.
    """
    rs = math_3d.matriz_mundo((0.0, 0.0, 0.0), item["rotacao"], item["escala"])
    y_minimo = math_3d.aplicar_transformacao(rs, vertices_objeto)[:, 1].min()
    x, z = item["posicao"]
    return math_3d.matriz_mundo((x, Y_CHAO - y_minimo, z), item["rotacao"], item["escala"])


def montar_cena(solidos):
    """
    Recebe {nome: sólido} (no sistema do objeto) e devolve a lista de objetos da cena:
    cada um com o sólido, a matriz do mundo e os vértices já no sistema do mundo.
    """
    cena = []
    for item in CENA:
        solido = solidos[item["nome"]]
        matriz = montar_matriz(item, solido["vertices"])
        cena.append({
            **item,
            "solido": solido,
            "matriz": matriz,
            "vertices_mundo": math_3d.aplicar_transformacao(matriz, solido["vertices"]),
        })
    return cena


def validar_cena(cena, folga=0.1):
    """
    Confere a cena sozinha e devolve a lista de problemas encontrados (vazia = cena válida).

    1. Limite: nenhuma componente de nenhum vértice pode passar de |10|.
    2. Sobreposição: cada objeto é envolvido pela menor caixa alinhada aos eixos que o
       contém (AABB). Se as caixas de dois objetos não se cruzam, os objetos também não
       se cruzam. Duas caixas estão separadas quando, em pelo menos um eixo, uma termina
       antes de a outra começar. A folga exige um espaço mínimo entre elas.
    """
    problemas = []

    for obj in cena:
        maior = np.abs(obj["vertices_mundo"]).max()
        if maior > LIMITE:
            problemas.append(f"{obj['nome']}: coordenada {maior:.2f} passa do limite |{LIMITE:g}|")

    caixas = [(o["vertices_mundo"].min(axis=0), o["vertices_mundo"].max(axis=0)) for o in cena]
    for i in range(len(cena)):
        for j in range(i + 1, len(cena)):
            (min_a, max_a), (min_b, max_b) = caixas[i], caixas[j]
            separados = np.any(max_a + folga < min_b) or np.any(max_b + folga < min_a)
            if not separados:
                problemas.append(f"{cena[i]['nome']} e {cena[j]['nome']} se sobrepõem")

    return problemas


def imprimir_resumo(cena):
    """Mostra no terminal a caixa de cada objeto no mundo e o resultado da validação."""
    print(f"  {'objeto':8s} {'escala':>6s} {'rotação (x,y,z)':>16s}   caixa no mundo (min .. max)")
    for obj in cena:
        v = obj["vertices_mundo"]
        rot = "(" + ", ".join(f"{a:g}" for a in obj["rotacao"]) + ")"
        print(f"  {obj['nome']:8s} {obj['escala'][0]:6g} {rot:>16s}   "
              f"{np.round(v.min(axis=0), 2)} .. {np.round(v.max(axis=0), 2)}")
    maior = max(np.abs(o["vertices_mundo"]).max() for o in cena)
    print(f"  maior |componente| na cena: {maior:.2f} (limite {LIMITE:g})")

    problemas = validar_cena(cena)
    if problemas:
        raise ValueError("Cena inválida:\n  " + "\n  ".join(problemas))
    print("  cena válida: tudo dentro de |10| e nenhum objeto sobreposto")


if __name__ == "__main__":
    solidos = {item["nome"]: modeling.obter_solido(item["nome"], 60) for item in CENA}
    imprimir_resumo(montar_cena(solidos))
