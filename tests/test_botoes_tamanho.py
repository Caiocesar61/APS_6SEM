"""Testes automaticos do botoes_tamanho.py (rodar com: python -m pytest)."""

import os
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import botoes_tamanho as bt  # noqa: E402
from botoes_tamanho import ControleTamanho  # noqa: E402


class RelogioFalso:
    """Substitui o time.monotonic para controlar o tempo nos testes."""

    def __init__(self):
        self.agora = 0.0

    def __call__(self):
        return self.agora


@pytest.fixture
def relogio():
    return RelogioFalso()


@pytest.fixture
def controle(relogio):
    return ControleTamanho(largura_tela=1280, relogio=relogio)


def centro(botao):
    return botao.x + botao.largura // 2, botao.y + botao.altura // 2


def test_tamanhos_iniciais(controle):
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_INICIAL
    assert controle.tamanho_borracha == bt.TAMANHO_BORRACHA_INICIAL


def test_tamanho_atual_depende_da_ferramenta(controle):
    assert controle.tamanho_atual(usando_borracha=False) == controle.tamanho_pincel
    assert controle.tamanho_atual(usando_borracha=True) == controle.tamanho_borracha


def test_aumentar_e_diminuir_pincel(controle):
    controle.aumentar_pincel()
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_INICIAL + bt.PASSO_PINCEL
    controle.diminuir_pincel()
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_INICIAL


def test_aumentar_e_diminuir_borracha(controle):
    controle.aumentar_borracha()
    assert controle.tamanho_borracha == bt.TAMANHO_BORRACHA_INICIAL + bt.PASSO_BORRACHA
    controle.diminuir_borracha()
    assert controle.tamanho_borracha == bt.TAMANHO_BORRACHA_INICIAL


def test_limites_do_pincel(controle):
    for _ in range(100):
        controle.aumentar_pincel()
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_MAX
    for _ in range(100):
        controle.diminuir_pincel()
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_MIN


def test_limites_da_borracha(controle):
    for _ in range(100):
        controle.aumentar_borracha()
    assert controle.tamanho_borracha == bt.TAMANHO_BORRACHA_MAX
    for _ in range(100):
        controle.diminuir_borracha()
    assert controle.tamanho_borracha == bt.TAMANHO_BORRACHA_MIN


def test_pincel_e_borracha_sao_independentes(controle):
    controle.aumentar_pincel()
    assert controle.tamanho_borracha == bt.TAMANHO_BORRACHA_INICIAL


@pytest.mark.parametrize("indice, atributo, delta", [
    (0, "tamanho_pincel", bt.PASSO_PINCEL),
    (1, "tamanho_pincel", -bt.PASSO_PINCEL),
    (2, "tamanho_borracha", bt.PASSO_BORRACHA),
    (3, "tamanho_borracha", -bt.PASSO_BORRACHA),
])
def test_toque_em_cada_botao(controle, indice, atributo, delta):
    antes = getattr(controle, atributo)
    assert controle.verificar_toque(*centro(controle.botoes[indice]))
    assert getattr(controle, atributo) == antes + delta


def test_toque_fora_dos_botoes_nao_muda_nada(controle):
    assert not controle.verificar_toque(10, 10)
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_INICIAL
    assert controle.tamanho_borracha == bt.TAMANHO_BORRACHA_INICIAL


def test_dedo_parado_no_botao_respeita_intervalo(controle, relogio):
    pos = centro(controle.botoes[0])
    assert controle.verificar_toque(*pos)
    # varios frames seguidos com o dedo parado: so conta um clique
    for _ in range(10):
        relogio.agora += 0.01
        assert not controle.verificar_toque(*pos)
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_INICIAL + bt.PASSO_PINCEL

    relogio.agora += bt.INTERVALO_CLIQUE
    assert controle.verificar_toque(*pos)
    assert controle.tamanho_pincel == bt.TAMANHO_PINCEL_INICIAL + 2 * bt.PASSO_PINCEL


def test_botoes_cabem_na_tela_e_nao_se_sobrepoem():
    for largura in (640, 1280, 1920):
        botoes = ControleTamanho(largura_tela=largura).botoes
        for b in botoes:
            assert 0 <= b.x and b.x + b.largura <= largura
        for a, b in zip(botoes, botoes[1:]):
            assert a.y + a.altura < b.y


def test_botoes_ficam_abaixo_da_paleta(controle):
    # a paleta do sl12 ocupa a faixa de cima (y < 125)
    assert all(b.y >= 125 for b in controle.botoes)


@pytest.mark.parametrize("tecla, atributo, delta", [
    ("+", "tamanho_pincel", bt.PASSO_PINCEL),
    ("=", "tamanho_pincel", bt.PASSO_PINCEL),
    ("-", "tamanho_pincel", -bt.PASSO_PINCEL),
    ("]", "tamanho_borracha", bt.PASSO_BORRACHA),
    ("[", "tamanho_borracha", -bt.PASSO_BORRACHA),
])
def test_atalhos_de_teclado(controle, tecla, atributo, delta):
    antes = getattr(controle, atributo)
    assert controle.tratar_tecla(ord(tecla))
    assert getattr(controle, atributo) == antes + delta


def test_tecla_sem_atalho_e_ignorada(controle):
    assert not controle.tratar_tecla(ord("a"))
    assert not controle.tratar_tecla(255)  # waitKey sem tecla & 0xFF


def test_desenhar_pinta_os_botoes(controle):
    img = np.zeros((720, 1280, 3), np.uint8)
    controle.desenhar(img)
    assert img[controle.botoes[0].y + 2, controle.botoes[0].x + 2].any()
    # fora do painel continua preto
    assert not img[700, 10].any()


def test_cursor_tem_o_tamanho_do_traco(controle):
    img = np.zeros((720, 1280, 3), np.uint8)
    controle.desenhar_cursor(img, 400, 400, usando_borracha=False, cor=(0, 0, 255))
    raio = controle.tamanho_pincel // 2
    assert img[400, 400 + raio - 1].tolist() == [0, 0, 255]
    assert not img[400, 400 + raio + 3].any()


def test_traco_com_espessura_do_controle(controle):
    """Simula o que o main.py faz: cv2.line com a espessura do controle."""
    canvas = np.zeros((720, 1280, 3), np.uint8)
    for _ in range(5):
        controle.aumentar_pincel()
    esp = controle.tamanho_atual(usando_borracha=False)
    cv2.line(canvas, (100, 300), (500, 300), (255, 0, 0), esp)
    coluna = canvas[:, 300, 0]
    altura_traco = int((coluna > 0).sum())
    assert abs(altura_traco - esp) <= 1
