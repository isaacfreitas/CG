# Renderização 3D de objetos do cotidiano (CG 2026.2, 2ª etapa)

Pipeline gráfico em Python: lápis, peão, haltere, martelo e lixeira, do objeto até a imagem.
Só o *Marching Cubes* vem pronto (scikit-image). O resto é implementado aqui.

## Instalar (Python 3.10 ou superior)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Rodar

Cada comando abre uma janela, e cada um mostra um item do enunciado.

| Item | Comando | O que mostra | Arquivo |
|---|---|---|---|
| 1 | `python3 visualizar_objetos.py` | cada sólido no seu sistema | `modeling.py` |
| 2 | `python3 visualizar_cena.py` | cena no mundo | `cena.py` |
| 3 | `python3 visualizar_camera.py --eye 26 18 28` | cena no sistema da câmera | `math_3d.py` |
| 4 | `python3 visualizar_projecao.py` | sólidos em 3D e projeção na janela | `math_3d.py` |
| 5 e 6 | `python3 main.py` | iluminação e rasterização em 200, 400 e 800 px | `illumination.py`, `rasterizer.py` |

Nos itens 3 a 6, `--eye X Y Z` troca a posição do observador. O `main.py` leva poucos segundos.
