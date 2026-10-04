"""
botoes_tamanho.py - Botoes para aumentar/diminuir o tamanho do pincel e da borracha.

Responsavel: Caio

O modulo nao depende do mrm.py: ele so recebe a imagem (frame do OpenCV) e
a posicao (x, y) da ponta do dedo indicador. Assim pode ser usado pelo
interface.py / main.py sem acoplar com a deteccao da mao.

Uso basico no main.py:

    from botoes_tamanho import ControleTamanho

    controle = ControleTamanho()

    # dentro do loop, depois de desenhar a paleta:
    controle.desenhar(img)

    # no modo selecao (indicador + medio levantados):
    controle.verificar_toque(x1, y1)

    # no modo desenho:
    espessura = controle.tamanho_atual(cor_atual == COR_BORRACHA)

    # teclado (opcional): + / - pincel, ] / [ borracha
    controle.tratar_tecla(cv2.waitKey(1) & 0xFF)
"""

import time

import cv2

# --- Constantes (podem ir para o config.py depois) ---------------------------
TAMANHO_PINCEL_INICIAL = 15
TAMANHO_PINCEL_MIN = 2
TAMANHO_PINCEL_MAX = 60
PASSO_PINCEL = 3

TAMANHO_BORRACHA_INICIAL = 50
TAMANHO_BORRACHA_MIN = 10
TAMANHO_BORRACHA_MAX = 150
PASSO_BORRACHA = 10

# Tempo minimo entre dois "cliques" seguidos. Sem isso o dedo parado em cima
# do botao aumentaria o tamanho em todo frame (~30 vezes por segundo).
INTERVALO_CLIQUE = 0.4

# Layout dos botoes: painel vertical na lateral direita, abaixo da paleta.
LARGURA_BOTAO = 50
ALTURA_BOTAO = 50
MARGEM_DIREITA = 10
TOPO_PAINEL = 160
ESPACO_ENTRE_GRUPOS = 30

COR_BOTAO = (60, 60, 60)
COR_BOTAO_ATIVO = (0, 200, 0)
COR_TEXTO = (255, 255, 255)
# -----------------------------------------------------------------------------


class Botao:
    """Retangulo clicavel com um texto no meio."""

    def __init__(self, x, y, largura, altura, texto, acao):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.texto = texto
        self.acao = acao

    def contem(self, px, py):
        return (self.x <= px <= self.x + self.largura
                and self.y <= py <= self.y + self.altura)

    def desenhar(self, img, destacado=False):
        cor = COR_BOTAO_ATIVO if destacado else COR_BOTAO
        p1 = (self.x, self.y)
        p2 = (self.x + self.largura, self.y + self.altura)
        cv2.rectangle(img, p1, p2, cor, cv2.FILLED)
        cv2.rectangle(img, p1, p2, COR_TEXTO, 1)
        (tw, th), _ = cv2.getTextSize(self.texto, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        tx = self.x + (self.largura - tw) // 2
        ty = self.y + (self.altura + th) // 2
        cv2.putText(img, self.texto, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX,
                    1, COR_TEXTO, 2)


class ControleTamanho:
    """Guarda o tamanho do pincel e da borracha e desenha os botoes +/-."""

    def __init__(self, largura_tela=1280, relogio=time.monotonic):
        self.tamanho_pincel = TAMANHO_PINCEL_INICIAL
        self.tamanho_borracha = TAMANHO_BORRACHA_INICIAL
        self._relogio = relogio
        self._ultimo_clique = float("-inf")
        self._botao_destacado = None
        self.botoes = self._criar_botoes(largura_tela)

    # --- Alteracao dos tamanhos ---------------------------------------------
    def aumentar_pincel(self):
        self.tamanho_pincel = min(self.tamanho_pincel + PASSO_PINCEL,
                                  TAMANHO_PINCEL_MAX)

    def diminuir_pincel(self):
        self.tamanho_pincel = max(self.tamanho_pincel - PASSO_PINCEL,
                                  TAMANHO_PINCEL_MIN)

    def aumentar_borracha(self):
        self.tamanho_borracha = min(self.tamanho_borracha + PASSO_BORRACHA,
                                    TAMANHO_BORRACHA_MAX)

    def diminuir_borracha(self):
        self.tamanho_borracha = max(self.tamanho_borracha - PASSO_BORRACHA,
                                    TAMANHO_BORRACHA_MIN)

    def tamanho_atual(self, usando_borracha):
        """Espessura a usar no cv2.line, conforme a ferramenta selecionada."""
        return self.tamanho_borracha if usando_borracha else self.tamanho_pincel

    # --- Interacao ------------------------------------------------------------
    def verificar_toque(self, x, y):
        """Chamar no modo selecao com a ponta do indicador.

        Retorna True se algum botao foi acionado neste frame.
        """
        self._botao_destacado = None
        for botao in self.botoes:
            if botao.contem(x, y):
                self._botao_destacado = botao
                agora = self._relogio()
                if agora - self._ultimo_clique >= INTERVALO_CLIQUE:
                    self._ultimo_clique = agora
                    botao.acao()
                    return True
                return False
        return False

    def tratar_tecla(self, tecla):
        """Atalhos de teclado: + / - para o pincel, ] / [ para a borracha."""
        acoes = {
            ord("+"): self.aumentar_pincel,
            ord("="): self.aumentar_pincel,  # '+' sem shift
            ord("-"): self.diminuir_pincel,
            ord("]"): self.aumentar_borracha,
            ord("["): self.diminuir_borracha,
        }
        acao = acoes.get(tecla)
        if acao is None:
            return False
        acao()
        return True

    # --- Desenho --------------------------------------------------------------
    def desenhar(self, img):
        """Desenha os dois grupos de botoes e o tamanho atual de cada um."""
        for botao in self.botoes:
            botao.desenhar(img, destacado=botao is self._botao_destacado)

        self._rotulo(img, f"Pincel {self.tamanho_pincel}", self.botoes[0])
        self._rotulo(img, f"Borracha {self.tamanho_borracha}", self.botoes[2])
        self._botao_destacado = None

    def desenhar_cursor(self, img, x, y, usando_borracha, cor):
        """Circulo na ponta do dedo mostrando o tamanho real do traco."""
        raio = max(self.tamanho_atual(usando_borracha) // 2, 1)
        if usando_borracha:
            cv2.circle(img, (x, y), raio, COR_TEXTO, 2)
        else:
            cv2.circle(img, (x, y), raio, cor, cv2.FILLED)

    # --- Interno --------------------------------------------------------------
    @staticmethod
    def _rotulo(img, texto, botao):
        """Escreve o texto acima do botao, alinhado pela direita dele."""
        (tw, _), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        x = botao.x + botao.largura - tw
        cv2.putText(img, texto, (x, botao.y - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, COR_TEXTO, 2)

    def _criar_botoes(self, largura_tela):
        x = largura_tela - MARGEM_DIREITA - LARGURA_BOTAO
        y = TOPO_PAINEL
        passo = ALTURA_BOTAO + 5
        y_borracha = y + 2 * passo + ESPACO_ENTRE_GRUPOS
        return [
            Botao(x, y, LARGURA_BOTAO, ALTURA_BOTAO, "+", self.aumentar_pincel),
            Botao(x, y + passo, LARGURA_BOTAO, ALTURA_BOTAO, "-",
                  self.diminuir_pincel),
            Botao(x, y_borracha, LARGURA_BOTAO, ALTURA_BOTAO, "+",
                  self.aumentar_borracha),
            Botao(x, y_borracha + passo, LARGURA_BOTAO, ALTURA_BOTAO, "-",
                  self.diminuir_borracha),
        ]
