"""Modo 2 (Suprimentos): Caixeiro Viajante com força bruta (5 cidades) ou heurística (18 bairros)."""
from ursina import invoke

import random

from .estilo import C_VERDE, SETA
from .grafos import G1, G2, sem, sortear_arestas, tsp_forca_bruta, tsp_heuristico


class ModoSuprimentos:
    def suprimentos(self):
        mp = self.mapa()
        bloq = []
        if self.com_zumbis:  # zumbis fecham estradas; o caixeiro tem que achar outra rota
            bloq = sortear_arestas(mp.g, 1, 3 if self.usar_g2 else 1, random, ciclo=not self.usar_g2)
            mp.infestar(arestas=bloq)
        if self.usar_g2:
            ordem, custo, rota = tsp_heuristico(sem(G2, arestas=bloq), 1) if bloq else self.tsp2
            self.ordem_tsp = ordem
            self.texto_tsp = ("Cidade grande (18 bairros).\n\nForça bruta seria impossível\n(17! rotas). Então:\n"
                              "1. Dijkstra calcula a distância\n   entre todos os pares\n"
                              "2. vizinho mais próximo\n3. melhora com 2-opt\n\n"
                              f"Ordem de visita:\n{SETA.join(map(str, ordem[:9]))}\n{SETA.join(map(str, ordem[9:]))}\n\n"
                              f"Custo total: {custo}")
        else:
            rota, custo, testadas = tsp_forca_bruta(sem(G1, arestas=bloq), 1) if bloq else self.tsp1
            self.texto_tsp = (f"5 cidades.\n\nForça bruta: o algoritmo testou\nTODAS as {testadas} rotas possíveis\n"
                              f"e ficou com a menor.\n\nMelhor rota:\n{SETA.join(map(str, rota))}\n\nCusto total: {custo}")
        if bloq:
            self.texto_tsp += ("\n\nZUMBIS LIGADOS: estradas\n"
                               + ", ".join(f"{a}-{b}" for a, b in bloq) + " (vermelhas) bloqueadas.")
        for v in mp.g:
            if v != 1:
                mp.caixa(v)
        self.visitar = list(zip(rota, rota[1:]))
        self.info_suprimentos()
        self.ui.instrucao("CAIXEIRO VIAJANTE", "O sobrevivente passa em todas as cidades e volta ao abrigo pela menor rota",
                       f"G: ver o mapa {'de 5 cidades' if self.usar_g2 else 'grande (18 bairros)'}\nZ: liga/desliga zumbis   R: repetir")
        r = self.rodada
        invoke(lambda: r == self.rodada and self.correr([mp.p[v] for v in rota[1:]]), delay=1)
        self.final = lambda: (self.sobrevivente.anim("acenar"),
                              self.ui.resultado_mostrar("SUPRIMENTOS OK!", C_VERDE, f"Custo total da rota: {custo}",
                                                     "Rota: " + SETA.join(map(str, rota if len(rota) < 12 else self.ordem_tsp))))

    def info_suprimentos(self):
        mp = self.mapa()
        total = len(mp.g) - 1
        self.ui.t_info.text = self.texto_tsp + f"\n\nCaixas coletadas: {total - len(mp.caixas)}/{total}"
