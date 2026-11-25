"""Núcleo do jogo: troca de modos, câmera, mouse e teclado."""
import math
import random

from ursina import Entity, Text, Vec3, application, camera, color, destroy, invoke, lerp, mouse, scene, time

from .estilo import C_AZUL, C_VERDE, C_VERMELHO, sem_luz
from .grafos import G1, G2, POS1, POS2, gerar_grafo, gerar_grafo_ciclo, tsp_forca_bruta, tsp_heuristico
from .interface import Interface
from .mapa import Mapa
from .modo_desafio import ModoDesafio
from .modo_fuga import ModoFuga
from .modo_suprimentos import ModoSuprimentos
from .personagem import Personagem


# Desafio com mapa aleatório: nós no Dijkstra / no Caixeiro (força bruta: (n - 1)!)
TAMANHOS = {"pequeno": (25, 7), "medio": (35, 8), "grande": (50, 9)}


class Jogo(ModoFuga, ModoSuprimentos, ModoDesafio, Entity):
    """Estado da partida, câmera, mouse e teclado. A lógica de cada modo fica em modo_*.py."""
    MODOS = {1: "FUGA  ·  Dijkstra", 2: "SUPRIMENTOS  ·  Caixeiro Viajante", 3: "VOCÊ vs. O ALGORITMO"}

    def __init__(self):
        super().__init__()
        self.tsp1 = tsp_forca_bruta(G1, 1)
        self.tsp2 = tsp_heuristico(G2, 1)
        random.seed(7)
        self.cidade = Mapa(G2, POS2, True, self.clique, self.passar)
        self.regiao = Mapa(G1, POS1, False, self.clique, self.passar)
        self.sobrevivente = Personagem()
        self.sobrevivente.ao_chegar = self.chegou
        self.marcador = sem_luz(Entity(parent=self.sobrevivente, model="sphere", y=2.7, scale=.4, color=C_AZUL))

        self.pivo = Entity()
        camera.parent = self.pivo
        camera.rotation_x = 62
        camera.fov = 62
        self.cam_alvo = Vec3(0, 40, -28)
        self.zoom = 1.0

        self.ui = Interface(self)

        self.modo = 0
        self.usar_g2 = False
        self.desafio_tsp = False
        self.com_zumbis = False  # zumbis opcionais nos modos 1 e 2 (tecla Z)
        self.tamanho = None  # Desafio: None = mapa da atividade; senão uma chave de TAMANHOS
        self.mapa_aleatorio = None
        self.rodada = 0
        self.hover = None
        self.modo_set(0)

    # ================================================================ estado
    def mapa(self):
        if self.modo == 3 and self.mapa_aleatorio is not None:
            return self.mapa_aleatorio
        if self.modo == 2 and not self.usar_g2 or self.modo == 3 and self.desafio_tsp:
            return self.regiao
        return self.cidade

    def ir_menu(self):
        self.modo_set(0)

    def enquadrar(self, mp):
        """Câmera fixa que mostra o mapa inteiro na área à esquerda do painel."""
        self.pivo.position = mp.centro
        self.pivo.rotation_y = 0
        d = max(mp.largura / .74, mp.profundidade / .55) * self.zoom
        ang = math.radians(62)
        self.cam_alvo = Vec3(.12 * d, d * math.sin(ang), -d * math.cos(ang))

    def modo_set(self, m, iniciar=False):
        """Troca de modo. No Desafio, sem `iniciar`, mostra o menu do desafio antes de começar."""
        self.modo = m
        self.rodada += 1  # invalida animações agendadas da rodada anterior
        menu_desafio = m == 3 and not iniciar
        if menu_desafio:
            self.trocar_mapa_aleatorio(None)
        for mapa in (self.cidade, self.regiao, self.mapa_aleatorio):
            if mapa:
                mapa.limpar()
        mp = self.mapa()
        for mapa in (self.cidade, self.regiao, self.mapa_aleatorio):
            if mapa:
                mapa.enabled = mapa is mp
        self.ui.menu.enabled = m == 0
        self.ui.menu_des.enabled = menu_desafio
        self.ui.hud.enabled = m != 0
        self.ui.res.enabled = False
        self.ui.dica.enabled = False
        s = self.sobrevivente
        s.parent = mp
        s.alvo_vivo = None
        s.pontos = []
        s.position = mp.p[1] + Vec3(0, .12, -2.1)
        s.rotation_y = 180
        s.corpo.rotation_x = 0
        s.corpo.y = 0
        s.estado = "parado"
        s.enabled = m != 0
        self.ocupado = False
        self.destino = None
        self.jogador = [1]
        self.visitar = []
        self.final = None
        self.terminou = False
        self.bloq_nos, self.bloq_aresta, self.g_jogo = set(), None, mp.g
        self.enquadrar(mp)
        self.ui.t_info.font = Text.default_font
        if m:
            self.ui.t_modo.text = self.MODOS[m]

        if m == 0:
            self.cam_alvo = Vec3(0, 30, -36)
            for v in random.sample(range(2, 19), 8):
                self.cidade.zumbi(v, random.uniform(0, 2))
        elif m == 1:
            self.preparar_fuga()
        elif m == 2:
            self.suprimentos()
        elif menu_desafio:
            self.terminou = True  # nada de cliques no mapa enquanto o menu está aberto
            self.ui.instrucao("DESAFIO", "Escolha o tipo de desafio e o mapa, depois clique em Começar",
                              "T: abrir este menu   R: nova rodada")
            self.ui.t_info.text = ("Dijkstra: chegue ao destino\npelo caminho mais curto.\n\n"
                                   "Caixeiro: passe em todas as\ncidades e volte ao abrigo.\n\n"
                                   "Mapa aleatório: um grafo novo\na cada rodada, com mais nós.")
            self.ui.atualizar_menu_desafio(self.desafio_tsp, self.tamanho, TAMANHOS)
        elif m == 3:
            self.desafio()

    # ================================================================ mouse sobre prédios
    def passar(self, v):
        mp = self.mapa()
        if self.hover is not None and self.hover in mp.predios:
            p = mp.predios[self.hover]
            p.animate_scale(p.escala, duration=.1)
        self.hover = v
        if v is None or self.modo == 0:
            self.ui.dica.enabled = False
            return
        p = mp.predios[v]
        p.animate_scale(p.escala * 1.12, duration=.1)
        if self.modo == 1:
            t = ("Abrigo (você está aqui)" if v == 1 else f"Bairro {v}: ZUMBIS! O resgate não vem aqui"
                 if v in self.bloq_nos else f"Bairro {v}: clique para ir até aqui")
        elif self.modo == 3 and not self.terminou:
            atual = self.jogador[-1]
            if v in self.bloq_nos:
                t = f"Bairro {v}: ZUMBIS! Não dá pra passar"
            elif self.bloq_aresta and {atual, v} == set(self.bloq_aresta):
                t = f"Bairro {v}: estrada bloqueada por zumbis"
            elif v in self.g_jogo[atual] and self.pode_ir(v):
                t = f"Bairro {v}: estrada de custo {mp.g[atual][v]}"
            else:
                t = f"Bairro {v}: não dá pra ir daqui"
        else:
            t = "Abrigo" if v == 1 else f"Bairro {v}"
        self.ui.dica.text = " " + t + " "
        self.ui.dica.enabled = True

    # ================================================================ modo 1: Dijkstra
    def clique(self, v):
        if self.modo == 1 and v in self.bloq_nos:
            self.aviso_zumbi()
        elif self.modo == 1 and v != 1 and not self.ocupado:
            self.fuga(v)
        elif self.modo == 3:
            self.jogada(v)

    # ================================================================ menu do desafio
    def escolher_desafio(self, tsp=None, tamanho="manter"):
        if tsp is not None:
            self.desafio_tsp = tsp
        if tamanho != "manter":
            self.tamanho = tamanho
        self.modo_set(3)

    def iniciar_desafio(self):
        """Começa uma rodada do Desafio; com mapa aleatório, gera um grafo novo."""
        self.trocar_mapa_aleatorio(None)
        if self.tamanho:
            n = TAMANHOS[self.tamanho][1 if self.desafio_tsp else 0]
            g, pos = (gerar_grafo_ciclo if self.desafio_tsp else gerar_grafo)(n, random)
            self.mapa_aleatorio = Mapa(g, pos, True, self.clique, self.passar)
        self.modo_set(3, iniciar=True)

    def trocar_mapa_aleatorio(self, novo):
        if self.mapa_aleatorio is not None:
            self.sobrevivente.parent = scene  # não destruir o sobrevivente junto com o mapa
            destroy(self.mapa_aleatorio)
        self.mapa_aleatorio = novo

    def repetir(self):
        self.iniciar_desafio() if self.modo == 3 else self.modo_set(self.modo)

    def aviso_zumbi(self):
        self.ui.t_instrucao.text = "Aí tem ZUMBI! Escolha outro prédio."
        self.ui.t_instrucao.color = C_VERMELHO
        invoke(setattr, self.ui.t_instrucao, "color", color.white, delay=1.2)

    def alternar_zumbis(self):
        self.com_zumbis = not self.com_zumbis
        self.ui.atualizar_zumbis(self.com_zumbis)
        if self.modo in (1, 2):
            self.modo_set(self.modo)

    def correr(self, pontos):
        self.sobrevivente.pontos += [Vec3(p.x, .12, p.z) for p in pontos]

    def chegou(self, ponto):
        mp = self.mapa()
        v = min(mp.p, key=lambda n: (mp.p[n] - Vec3(ponto.x, 0, ponto.z)).length())
        if self.modo == 2 or (self.modo == 3 and self.desafio_tsp):
            mp.coletar(v)
            if self.modo == 2:
                self.info_suprimentos()
        if self.visitar:
            a, b = self.visitar.pop(0)
            mp.estrada(a, b, C_VERDE)
        if not self.sobrevivente.pontos and self.final:
            f, self.final = self.final, None
            f()

    # ================================================================ loop
    def update(self):
        if self.modo == 0:
            self.pivo.rotation_y += 4 * time.dt
        elif mouse.right:
            self.pivo.rotation_y += mouse.velocity[0] * 200
        camera.position = lerp(camera.position, self.cam_alvo, min(1, time.dt * 3))
        self.marcador.y = 2.7 + math.sin(time.time() * 4) * .15
        if self.ui.dica.enabled:
            self.ui.dica.position = (mouse.x + .02, mouse.y + .05)

    def input(self, key):
        if key in ("1", "2", "3"):
            self.modo_set(int(key))
        elif key == "g" and self.modo == 2:
            self.usar_g2 = not self.usar_g2
            self.modo_set(2)
        elif key == "t" and self.modo == 3:
            self.modo_set(3)
        elif key == "z" and self.modo != 3:
            self.alternar_zumbis()
        elif key == "r" and self.modo:
            self.repetir()
        elif key == "backspace":
            self.desfazer()
        elif key in ("scroll up", "scroll down") and self.modo:
            self.zoom = max(.5, min(1.4, self.zoom + (-.1 if key == "scroll up" else .1)))
            self.enquadrar(self.mapa())
        elif key == "escape":
            self.modo_set(0) if self.modo else application.quit()
