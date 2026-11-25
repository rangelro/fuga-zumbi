"""Telas 2D: painel lateral, barra de instrução, menu inicial e janela de resultado."""
from ursina import Button, Entity, Quad, Text, application, camera, color, curve

from .estilo import C_AMARELO, C_AZUL, C_LARANJA, C_VERDE, C_VERMELHO

PAINEL_X = .5          # borda esquerda do painel lateral (coordenadas da UI)
MAPA_X = (-.9125 + PAINEL_X) / 2   # centro da área do mapa na tela
C_UI = color.rgb32(12, 14, 22)
C_UI2 = color.rgb32(26, 30, 44)


def caixa_ui(x, y, w, h, cor=C_UI2, z=.5, parent=None):
    return Entity(parent=parent or camera.ui, model=Quad(radius=.015, aspect=w / h), color=cor,
                  position=(x, y, z), scale=(w, h))


def botao(texto, x, y, w, h, acao, cor=color.rgb32(150, 25, 25), parent=None, escala=1):
    b = Button(texto, parent=parent or camera.ui, position=(x, y), scale=(w, h), radius=.2,
               color=cor, highlight_color=cor.tint(.2), pressed_color=cor.tint(-.2), on_click=acao)
    b.text_entity.scale *= escala
    return b


class Interface:
    """Cria e atualiza a UI; as ações dos botões chamam o Jogo."""

    def __init__(self, jogo):
        self.jogo = jogo
        self.montar_hud()
        self.montar_menu()
        self.montar_resultado()

    # ================================================================ HUD
    def montar_hud(self):
        self.hud = Entity(parent=camera.ui)
        Entity(parent=self.hud, model="quad", color=C_UI, z=1,
               position=((PAINEL_X + .9125) / 2, 0), scale=(.9125 - PAINEL_X, 1))
        Text("FUGA ZUMBI", parent=self.hud, x=PAINEL_X + .03, y=.47, scale=1.7, color=C_VERMELHO)
        self.t_modo = Text("", parent=self.hud, x=PAINEL_X + .03, y=.415, scale=.85, color=C_AMARELO)
        self.t_info = Text("", parent=self.hud, x=PAINEL_X + .03, y=.37, scale=.75, line_height=1.1)
        # legenda de cores
        Text("LEGENDA", parent=self.hud, x=PAINEL_X + .03, y=-.1, scale=.7, color=color.light_gray)
        for i, (cor, nome) in enumerate([(C_AZUL, "Abrigo (início) e você"), (C_AMARELO, "Dijkstra explorando"),
                                         (C_VERDE, "Destino / rota do algoritmo"), (C_LARANJA, "Sua rota"),
                                         (color.white, "Prédio que você pode clicar"),
                                         (C_VERMELHO, "Zumbis: caminho bloqueado")]):
            y = -.14 - i * .032
            Entity(parent=self.hud, model="quad", color=cor, position=(PAINEL_X + .045, y), scale=.018)
            Text(nome, parent=self.hud, x=PAINEL_X + .07, y=y + .011, scale=.7)
        # barra de instrução sobre o mapa
        caixa_ui(MAPA_X, .44, 1.05, .085, color.rgba32(10, 12, 20, 230), parent=self.hud)
        self.t_passo = Text("", parent=self.hud, position=(MAPA_X, .455), origin=(0, 0), scale=.85,
                            color=C_AMARELO)
        self.t_instrucao = Text("", parent=self.hud, position=(MAPA_X, .425), origin=(0, 0), scale=1.05)
        botao("< Menu", -.84, .44, .12, .06, self.jogo.ir_menu, cor=color.rgb32(60, 64, 80), parent=self.hud, escala=.9)
        Text("CONTROLES", parent=self.hud, x=PAINEL_X + .03, y=-.35, scale=.7, color=color.light_gray)
        self.t_teclas = Text("", parent=self.hud, x=PAINEL_X + .03, y=-.375, scale=.7, line_height=1.1)
        self.dica = Text(" ", parent=camera.ui, scale=.9, z=-.5, background=True, enabled=False)

    def atualizar_zumbis(self, ligado):
        """Texto/cor do botão que liga os zumbis nos modos Fuga e Suprimentos."""
        self.b_zumbis.text = f"Zumbis em Fuga e Suprimentos: {'LIGADOS' if ligado else 'DESLIGADOS'}  (Z)"
        self.b_zumbis.color = color.rgb32(150, 25, 25) if ligado else color.rgb32(60, 64, 80)
        self.b_zumbis.highlight_color = self.b_zumbis.color.tint(.2)

    def instrucao(self, passo, texto, teclas):
        self.t_passo.text = passo
        self.t_instrucao.text = texto
        self.t_teclas.text = teclas + "\nESC / Menu: voltar ao menu"

    # ================================================================ menu inicial
    def montar_menu(self):
        self.menu = Entity(parent=camera.ui)
        Entity(parent=self.menu, model="quad", color=color.rgba32(5, 6, 12, 150), scale=(2, 1), z=1)
        Text("FUGA ZUMBI", parent=self.menu, y=.32, origin=(0, 0), scale=5, color=C_VERMELHO)
        Text("Grafos contra o apocalipse: Dijkstra e Caixeiro Viajante", parent=self.menu, y=.21,
             origin=(0, 0), scale=1.2, color=C_AMARELO)
        cartas = [(1, "FUGA", "Dijkstra", "Escolha onde o resgate\nvai te buscar e veja o\ncaminho mais curto."),
                  (2, "SUPRIMENTOS", "Caixeiro Viajante", "Passe em todas as cidades\ncoletando caixas e volte\npelo menor percurso."),
                  (3, "DESAFIO", "Você vs. o algoritmo", "Monte a rota você mesmo\ne compare com a resposta\nótima. Se errar... zumbis.")]
        for i, (m, nome, alg, desc) in enumerate(cartas):
            x = (i - 1) * .5
            caixa_ui(x, -.06, .44, .4, color.rgba32(20, 24, 36, 235), parent=self.menu)
            Text(nome, parent=self.menu, position=(x, .1), origin=(0, 0), scale=1.8, color=color.white)
            Text(alg, parent=self.menu, position=(x, .05), origin=(0, 0), scale=1, color=C_AMARELO)
            Text(desc, parent=self.menu, position=(x, -.04), origin=(0, 0), scale=.95, color=color.light_gray)
            botao(f"Jogar  ({m})", x, -.19, .3, .07, (lambda m=m: self.jogo.modo_set(m)), parent=self.menu)
        self.b_zumbis = botao("Zumbis", 0, -.3, .62, .055, self.jogo.alternar_zumbis, parent=self.menu, escala=.85)
        self.atualizar_zumbis(False)
        botao("Sair", 0, -.4, .14, .05, application.quit, cor=color.rgb32(60, 64, 80), parent=self.menu, escala=.9)

    # ================================================================ janela de resultado
    def montar_resultado(self):
        self.res = Entity(parent=camera.ui, enabled=False)
        # fica embaixo do mapa, para não cobrir a rota
        self.res_fundo = caixa_ui(MAPA_X, -.345, .9, .27, color.rgba32(10, 12, 20, 235), parent=self.res)
        self.res_titulo = Text("", parent=self.res, position=(MAPA_X, -.25), origin=(0, 0), scale=1.9)
        self.res_linha = Text("", parent=self.res, position=(MAPA_X, -.305), origin=(0, 0), scale=1.1)
        self.res_rota = Text("", parent=self.res, position=(MAPA_X, -.345), origin=(0, 0), scale=.85,
                             color=color.light_gray)
        botao("Jogar de novo  (R)", MAPA_X - .16, -.415, .28, .06, lambda: self.jogo.modo_set(self.jogo.modo), parent=self.res)
        botao("Menu", MAPA_X + .16, -.415, .28, .06, self.jogo.ir_menu, cor=color.rgb32(60, 64, 80), parent=self.res)

    def resultado_mostrar(self, titulo, cor, linha, rota):
        self.res_titulo.text, self.res_titulo.color = titulo, cor
        self.res_linha.text = linha
        self.res_rota.text = rota
        self.res.enabled = True
        self.res.y = -.2
        self.res.animate_y(0, duration=.35, curve=curve.out_back)
