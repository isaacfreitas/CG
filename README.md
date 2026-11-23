# Pré-requisitos

- Python 3.10 ou superior

# Instalação

Crie um ambiente virtual e instale as dependências (numpy, matplotlib, scikit-image):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Execução

```bash
python3 main.py                                # renderização completa (leva alguns minutos)
python3 main.py --eye 26 18 28                 # troca a posição do observador na Tela 1
python3 visualizar_camera.py --eye 26 18 28    # cena em coordenadas de câmera (rápido)
python3 visualizar_objetos.py                  # cada sólido no seu sistema de coordenadas
```
