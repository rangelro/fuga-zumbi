"""Cores, constantes e helpers visuais compartilhados (modelos .glb, rótulos, coordenadas)."""
from pathlib import Path

from panda3d.core import CullFaceAttrib, Filename, NodePath
from ursina import Entity, Text, Vec3, color

ASSETS = Path(__file__).resolve().parent.parent / "assets"
VEL = 7  # velocidade do sobrevivente (unidades/s)
SETA = " > "

C_ESTRADA = color.rgb32(48, 50, 58)
C_VERDE = color.rgb32(0, 230, 60)
C_LARANJA = color.rgb32(255, 100, 0)
C_AMARELO = color.rgb32(255, 220, 70)
C_VERMELHO = color.rgb32(255, 60, 60)
C_AZUL = color.rgb32(80, 170, 255)


# ---------------------------------------------------------------- helpers

_modelos = {}


def glb(nome, parent, **kw):
    """Modelo .glb de assets/ (Z-up) dentro de um Entity Y-up."""
    if nome not in _modelos:
        _modelos[nome] = loader.loadModel(Filename.from_os_specific(str(ASSETS / f"{nome}.glb")))  # noqa: F821
    e = Entity(parent=parent, **kw)
    m = Entity(parent=e, model=_modelos[nome].copy_to(NodePath()), rotation_x=-90)
    m.set_attrib(CullFaceAttrib.make_reverse())  # Ursina é "y-up-left": inverte a ordem das faces do glTF
    return e


def mundo(pos, grafo2):
    """Coordenadas da imagem (x, y) -> chão 3D (x, z)."""
    if grafo2:
        return {v: Vec3((x - 560) * .12, 0, -(y - 225) * .12) for v, (x, y) in pos.items()}
    return {v: Vec3((x - 175) * .12, 0, -(y - 222) * .12) for v, (x, y) in pos.items()}


def sem_luz(e):
    """Cor chapada, sem sombreamento (feixes, olhos, estradas acesas)."""
    e.set_shader_off()
    e.set_light_off()
    return e


def rotulo(texto, parent, pos, cor=color.white, escala=14):
    return Text(texto, parent=parent, position=pos, scale=escala, origin=(0, 0), color=cor, billboard=True)
