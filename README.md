# APS_6SEM
DESENHE APENAS COM CAMERA E GESTOS

## Requisitos

- Python **3.9 a 3.12** (o MediaPipe usado no projeto ainda não suporta 3.13)
- Webcam

## Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/caiocesar61/aps_6sem.git
cd aps_6sem

# 2. Criar e ativar um ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt
```

> Se já existir `opencv-python` instalado no ambiente, desinstale antes
> (`pip uninstall opencv-python`): ele conflita com o `opencv-contrib-python`
> que vem junto do MediaPipe.

## Como executar

```bash
python main.py
```

Pressione `q` para sair.

## Como usar

| Gesto / tecla | Ação |
|---|---|
| Só o indicador levantado | Desenha |
| Indicador + médio levantados | Modo seleção (escolher cor / botões) |
| Modo seleção sobre **+ / −** (Pincel) | Aumenta / diminui o pincel |
| Modo seleção sobre **+ / −** (Borracha) | Aumenta / diminui a borracha |
| Teclas `+` / `-` | Aumenta / diminui o pincel |
| Teclas `]` / `[` | Aumenta / diminui a borracha |

Os botões de tamanho ficam na lateral direita, abaixo da paleta. Manter o dedo
parado em cima de um botão repete o clique a cada 0,4 s.

## Testes

```bash
python -m pytest
```

## Estrutura

```
├── mrm.py              # detecção da mão (MediaPipe) — não mexer
├── interface.py        # paleta, HUD
├── botoes_tamanho.py   # botões de tamanho do pincel e da borracha
├── desenho.py          # traço, borracha, espelhamento, spray
├── main.py             # loop principal
├── config.py           # constantes compartilhadas
├── tests/              # testes automáticos (pytest)
└── requirements.txt
```
