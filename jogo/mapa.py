"""Um grafo montado em 3D: prédios, estradas, feixes de luz, caixas e zumbis."""
import math
import random

from ursina import BoxCollider, Entity, Vec3, color, curve, destroy

from .estilo import C_AZUL, C_ESTRADA, C_VERMELHO, glb, mundo, rotulo, sem_luz
from .personagem import Personagem


class Mapa(Entity):
    """Um grafo montado em 3D: prédios (nós), estradas (arestas), feixes, caixas e zumbis."""

    def __init__(self, g, pos, grafo2, ao_clicar, ao_passar):
        super().__init__()
        self.g, self.p = g, mundo(pos, grafo2)
        self.estradas, self.feixes, self.caixas, self.zumbis, self.predios = {}, {}, {}, [], {}
        self.bloq_nos, self.bloq_arestas = set(), []
        xs, zs = [c.x for c in self.p.values()], [c.z for c in self.p.values()]
        self.centro = Vec3((min(xs) + max(xs)) / 2, 0, (min(zs) + max(zs)) / 2)
        self.largura = max(xs) - min(xs) + 6
        self.profundidade = max(zs) - min(zs) + 6
        self.letra = max(1, self.largura / 47)  # mapa maior = câmera mais longe = rótulos maiores

        for a in g:
            for b, w in g[a].items():
                if a < b:
                    pa, pb = self.p[a], self.p[b]
                    meio = (pa + pb) / 2
                    e = Entity(parent=self, model="cube", color=C_ESTRADA, position=meio + Vec3(0, .03, 0),
                               scale=(.95, .06, (pb - pa).length()))
                    e.look_at(Vec3(pb.x, e.y, pb.z))
                    for k in range(-2, 3):  # faixas tracejadas
                        sem_luz(Entity(parent=e, model="cube", color=color.rgb32(200, 180, 90),
                                       position=(0, .55, k * .2), scale=(.06, .1, .08)))
                    self.estradas[(a, b)] = self.estradas[(b, a)] = e
                    rotulo(str(w), self, meio + Vec3(0, 1, 0), color.rgb32(255, 225, 140), 16 * self.letra)

        for v, c in self.p.items():
            Entity(parent=self, model="cube", color=color.rgb32(85, 88, 96), position=c, scale=(2.8, .25, 2.8))
            if v == 1:
                predio = glb("predio2", self, position=c + Vec3(0, .12, 0), scale=1.6)
                for k in range(10):  # barricada de caixas em volta do abrigo
                    ang = math.radians(k * 36 + 18)
                    glb("caixa", self, scale=.42, rotation_y=k * 36,
                        position=c + Vec3(1.45 * math.cos(ang), .33, 1.45 * math.sin(ang)))
            else:
                predio = glb(random.choice(["predio1", "predio2"]), self, position=c + Vec3(0, .12, 0),
                             scale=random.uniform(1.3, 1.7), rotation_y=random.choice([0, 90, 180, 270]))
            predio.collider = BoxCollider(predio, center=Vec3(0, 1, 0), size=Vec3(1.4, 2.2, 1.4))
            predio.on_click = (lambda n=v: ao_clicar(n))
            predio.on_mouse_enter = (lambda n=v: ao_passar(n))
            predio.on_mouse_exit = (lambda: ao_passar(None))
            self.predios[v] = predio
            predio.escala = predio.scale_x
            rotulo(("ABRIGO " if v == 1 else "") + str(v), self, c + Vec3(0, 4.6, 0),
                   C_AZUL if v == 1 else color.white, 24 * self.letra)
            feixe = sem_luz(Entity(parent=self, model="cube", position=c + Vec3(0, 6, 0), scale=(.7, 12, .7),
                                   color=color.rgba(1, 1, 1, 0)))
            feixe.set_transparency(True)
            feixe.set_depth_write(False)
            self.feixes[v] = feixe
            glb("poste", self, scale=.35, position=c + Vec3(-1.25, .1, -1.25), rotation_y=45)
        self.feixe(1, C_AZUL, .3)

    # ----- efeitos
    def feixe(self, v, cor, alpha=.4):
        self.feixes[v].color = color.rgba(cor.r, cor.g, cor.b, alpha)

    def estrada(self, a, b, cor):
        e = self.estradas[(a, b)]
        e.color = cor
        if cor == C_ESTRADA:
            e.set_shader_off(False)  # volta a receber luz
            e.clear_shader()
        else:
            e.set_shader_off()  # estrada acesa: cor viva, sem sombra

    def limpar(self):
        for (a, b) in self.estradas:
            self.estrada(a, b, C_ESTRADA)
        self.bloq_nos, self.bloq_arestas = set(), []
        self.feixes_base()
        for z in self.zumbis:
            destroy(z)
        self.zumbis = []
        for c in self.caixas.values():
            destroy(c)
        self.caixas = {}

    def feixes_base(self):
        """Apaga os feixes, deixando só o abrigo (azul) e os prédios com zumbis (vermelho)."""
        for v in self.feixes:
            self.feixe(v, color.white, 0)
        self.feixe(1, C_AZUL, .3)
        for v in self.bloq_nos:
            self.feixe(v, C_VERMELHO, .45)

    def infestar(self, nos=(), arestas=()):
        """Coloca hordas de zumbis nos prédios/estradas bloqueados."""
        self.bloq_nos, self.bloq_arestas = set(nos), list(arestas)
        for v in self.bloq_nos:
            for k in range(3):
                self.zumbi(v, k * .25, raio=1.6)
        for a, b in self.bloq_arestas:
            self.estrada(a, b, C_VERMELHO)
            for k in range(3):
                self.zumbi(a, k * .25, centro=(self.p[a] + self.p[b]) / 2, raio=.7)
        self.feixes_base()

    def zumbi(self, v, atraso=0, centro=None, raio=2.1):
        ang = random.uniform(0, 2 * math.pi)
        c = self.p[v] if centro is None else centro
        z = Personagem(zumbi=True, parent=self, rotation_y=random.uniform(0, 360),
                       position=c + Vec3(raio * math.cos(ang), -2.2, raio * math.sin(ang)))
        z.vel = 5.5
        z.animate_y(.12, duration=1.2, delay=atraso, curve=curve.out_back)  # sai da terra
        self.zumbis.append(z)
        return z

    def caixa(self, v):
        c = glb("caixa", self, scale=.85, position=self.p[v] + Vec3(1.1, 1.3, 1.1))
        c.animate_y(1.8, duration=.8, loop=True, curve=curve.in_out_sine)
        c.animate_rotation_y(360, duration=4, loop=True, curve=curve.linear)
        self.caixas[v] = c

    def coletar(self, v):
        c = self.caixas.pop(v, None)
        if c:
            c.animate_y(6, duration=.6)
            c.animate_scale(0, duration=.6)
            destroy(c, delay=.7)
