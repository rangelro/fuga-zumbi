"""Bonecos low-poly (sobrevivente e zumbis) com animação procedural."""
import math
import random

from ursina import Entity, Vec3, color, curve, time

from .estilo import C_VERMELHO, VEL, sem_luz


class Personagem(Entity):
    """Boneco blocado com animação por código: correr, parado, atacar, acenar, morrer."""

    def __init__(self, zumbi=False, **kw):
        super().__init__(**kw)
        self.zumbi = zumbi
        pele = color.rgb32(110, 170, 95) if zumbi else color.rgb32(235, 190, 150)
        roupa = color.rgb32(110, 85, 70) if zumbi else color.rgb32(40, 110, 220)
        calca = color.rgb32(45, 50, 80) if zumbi else color.rgb32(40, 40, 45)
        self.corpo = Entity(parent=self)
        bloco = lambda pai, **k: Entity(parent=pai, model="cube", **k)  # noqa: E731
        bloco(self.corpo, y=1.05, scale=(.55, .62, .3), color=roupa)
        self.cabeca = Entity(parent=self.corpo, y=1.38)
        bloco(self.cabeca, y=.22, scale=.42, color=pele)
        for x in (-.09, .09):
            sem_luz(bloco(self.cabeca, position=(x, .26, .21), scale=(.08, .06, .02),
                          color=C_VERMELHO if zumbi else color.black))
        if not zumbi:  # boné laranja
            bloco(self.cabeca, position=(0, .45, .05), scale=(.46, .1, .56), color=color.rgb32(255, 140, 30))
        self.bracos, self.pernas = [], []
        for lado in (-1, 1):
            b = Entity(parent=self.corpo, position=(.37 * lado, 1.33, 0))
            bloco(b, y=-.27, scale=(.18, .56, .18), color=pele if zumbi else roupa)
            bloco(b, y=-.6, scale=(.16, .12, .16), color=pele)
            self.bracos.append(b)
            p = Entity(parent=self.corpo, position=(.14 * lado, .75, 0))
            bloco(p, y=-.37, scale=(.22, .75, .24), color=calca)
            self.pernas.append(p)
        self.fase = random.uniform(0, 6)
        self.estado = "parado"
        self.pontos = []
        self.vel = VEL
        self.ao_chegar = None
        self.alvo_vivo = None  # entidade perseguida

    def anim(self, estado):
        if estado == self.estado:
            return
        self.estado = estado
        if estado == "morto":
            self.corpo.animate_rotation_x(-90, duration=.6, curve=curve.out_bounce)
            self.corpo.animate_y(.2, duration=.6)

    def update(self):
        if self.alvo_vivo is not None:
            self.pontos = [self.alvo_vivo.position]
        if self.pontos:
            self.andar()
        self.animar()

    def andar(self):
        alvo = Vec3(self.pontos[0])
        d = alvo - self.position
        d.y = 0
        passo = self.vel * time.dt
        if self.alvo_vivo is not None and d.length() < 1.1:
            self.pontos = []
            self.anim("atacar")
            return
        if d.length() <= max(passo, .05):
            self.position = alvo
            self.pontos.pop(0)
            if self.ao_chegar:
                self.ao_chegar(alvo)
            if not self.pontos and self.estado == "correr":
                self.anim("parado")
        else:
            self.position += d.normalized() * passo
            self.look_at_2d(alvo, "y")
            self.anim("correr")

    def animar(self):
        e = self.estado
        if e == "morto":
            return
        self.fase += time.dt * (11 if e == "correr" else 3 if e == "parado" else 14)
        s = math.sin(self.fase)
        frente = -80 if self.zumbi else 0  # zumbi anda de braços esticados
        if e == "correr":
            for i, p in enumerate(self.pernas):
                p.rotation_x = s * 40 * (1 if i else -1)
            for i, b in enumerate(self.bracos):
                b.rotation_x = frente + s * (15 if self.zumbi else 45) * (-1 if i else 1)
                b.rotation_z = 0
            self.corpo.y = abs(s) * .12
            self.corpo.rotation_x = 12 if not self.zumbi else 18
            self.corpo.rotation_z = s * 6 if self.zumbi else 0
        elif e == "atacar":
            for i, b in enumerate(self.bracos):
                b.rotation_x = -100 + s * 50 * (1 if i else -1)
            self.corpo.rotation_x = 20
        elif e == "acenar":
            self.bracos[1].rotation_z = -150 + s * 25
            self.bracos[1].rotation_x = 0
            self.corpo.y = abs(math.sin(self.fase * .5)) * .25
        else:  # parado: respiração / zumbi cambaleando
            for p in self.pernas:
                p.rotation_x = 0
            for b in self.bracos:
                b.rotation_x = frente + s * 4
                b.rotation_z = 0
            self.corpo.y = 0
            self.corpo.rotation_x = 8 if self.zumbi else 0
            self.corpo.rotation_z = s * (7 if self.zumbi else 1.5)
            self.cabeca.rotation_z = s * (14 if self.zumbi else 0)
