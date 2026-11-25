"""FUGA ZUMBI 3D — Dijkstra + Caixeiro Viajante (Ursina + simplepbr).

Mouse: clique nos prédios | botão direito arrastado = gira a câmera | roda = zoom
Teclas: 1 Fuga | 2 Suprimentos | 3 Desafio | G troca o grafo (Suprimentos)
        T troca o desafio | BACKSPACE desfaz | R reinicia | ESC menu

Rode com:  .venv/bin/python fuga_zumbi.py
"""
from ursina import AmbientLight, DirectionalLight, Entity, Ursina, Vec3, color, window

from jogo.jogo import Jogo


def criar():
    import simplepbr
    app = Ursina(title="Fuga Zumbi", borderless=False, development_mode=False)
    window.color = color.rgb32(8, 9, 16)
    window.exit_button.visible = False
    Entity.default_shader = None  # o simplepbr ilumina tudo (PBR + sombras)
    simplepbr.init(use_normal_maps=False, enable_shadows=True, use_occlusion_maps=False)
    sol = DirectionalLight(shadows=True, shadow_map_resolution=(2048, 2048), color=color.rgb(.45, .5, .75))
    sol.look_at(Vec3(.5, -1, .7))
    AmbientLight(color=color.rgba(.12, .13, .22, 1))
    Entity(model="plane", scale=220, color=color.rgb32(18, 24, 20), y=-.02)
    jogo = Jogo()
    sol.update_bounds()
    return app, jogo


if __name__ == "__main__":
    app, _ = criar()
    app.run()
