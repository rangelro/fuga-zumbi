"""Modo 1 (Fuga): animação passo a passo do Dijkstra e corrida pela rota mínima."""
import random

from ursina import Text, invoke

from .estilo import C_AMARELO, C_VERDE, SETA
from .grafos import G2, caminho, dijkstra, sem, sortear_nos


class ModoFuga:
    def preparar_fuga(self):
        """Início do modo 1. Com zumbis ligados, 4 prédios ficam bloqueados e o Dijkstra roda sem eles."""
        texto = ("Você está no ABRIGO (nó 1).\n\nO algoritmo de Dijkstra vai\ncalcular o caminho mais\n"
                 "curto até o prédio que você\nescolher.")
        if self.com_zumbis:
            self.bloq_nos = sortear_nos(G2, 1, 4, random)
            self.g_jogo = sem(G2, nos=self.bloq_nos)
            self.cidade.infestar(nos=self.bloq_nos)
            texto += (f"\n\nZUMBIS LIGADOS: os prédios\n{', '.join(map(str, sorted(self.bloq_nos)))} (vermelhos) estão\n"
                      "bloqueados. O Dijkstra roda\nno grafo SEM esses nós.")
        self.ui.instrucao("PASSO 1 de 3", "Clique em qualquer prédio para escolher onde o resgate vai te buscar"
                          + (" (menos os vermelhos)" if self.com_zumbis else ""),
                          "Clique: escolher o destino\nZ: liga/desliga zumbis   R: reiniciar\n"
                          "Roda: zoom   Botão direito: girar")
        self.ui.t_info.text = texto

    def fuga(self, destino):
        mp, r = self.cidade, self.rodada
        self.ocupado = True
        dist, ant, passos = dijkstra(self.g_jogo, 1)  # sem os prédios com zumbis, se ligados
        rota = caminho(ant, destino)
        mp.feixe(destino, C_VERDE, .5)
        self.ui.instrucao("PASSO 2 de 3", "Dijkstra explorando a cidade: sempre o nó mais próximo ainda não visitado",
                       "R: escolher outro destino")

        def passo(i):
            if r != self.rodada:
                return
            u, snap = passos[i]
            if i:
                mp.feixe(passos[i - 1][0], C_AMARELO, .12)
            mp.feixe(u, C_AMARELO, .6)
            mp.feixe(destino, C_VERDE, .5)
            def val(v):
                return "Z" if v not in snap else "-" if snap[v] == float("inf") else snap[v]
            cel = lambda v: f"{'>' if v == u else ' '}{v:>3}  {val(v):<5}"  # noqa: E731
            linhas = [cel(v) + "  " + cel(v + 9) for v in range(1, 10)]
            self.ui.t_info.font = "VeraMono.ttf"
            self.ui.t_info.text = (f"Destino: nó {destino}\nExplorando o nó {u}  ({i + 1}/{len(passos)})\n\n"
                                "Distância desde o abrigo:\n  nó  dist      nó  dist\n" + "\n".join(linhas)
                                + ("\n\nZ = zumbis (fora do grafo)" if self.bloq_nos else ""))

        def fim():
            if r != self.rodada:
                return
            mp.feixes_base()
            mp.feixe(destino, C_VERDE, .5)
            for a, b in zip(rota, rota[1:]):
                mp.estrada(a, b, C_VERDE)
            for k, v in enumerate(v for v in G2 if v not in rota and v not in self.bloq_nos):
                mp.zumbi(v, k * .08)
            self.ui.instrucao("PASSO 3 de 3", "Os zumbis tomaram o resto da cidade. Corra pela rota verde!", "")
            self.ui.t_info.font = Text.default_font
            self.ui.t_info.text = (f"Destino: nó {destino}\n\nCaminho mínimo:\n{SETA.join(map(str, rota))}\n\n"
                                f"Custo total: {dist[destino]}\nNós explorados: {len(passos)}")
            self.final = lambda: (self.sobrevivente.anim("acenar"),
                                  self.ui.resultado_mostrar("A SALVO!", C_VERDE, f"Custo da rota: {dist[destino]}",
                                                         "Caminho: " + SETA.join(map(str, rota))))
            self.correr([mp.p[v] for v in rota[1:]])

        for i in range(len(passos)):
            invoke(passo, i, delay=.45 * i)
        invoke(fim, delay=.45 * len(passos) + .4)
