"""Modo 3 (Desafio): o jogador monta a rota, os zumbis bloqueiam caminhos e o algoritmo dá a resposta ótima."""
import random

from ursina import color, invoke

from .estilo import C_AMARELO, C_ESTRADA, C_LARANJA, C_VERDE, C_VERMELHO, SETA
from .grafos import G1, G2, caminho, custo_rota, dijkstra, sem, tsp_forca_bruta


class ModoDesafio:
    def desafio(self):
        """Prepara a rodada: zumbis bloqueiam prédios (Dijkstra) ou uma estrada (Caixeiro)."""
        mp = self.mapa()
        self.bloq_nos, self.bloq_aresta = set(), None
        if self.desafio_tsp:
            # zumbis numa estrada da rota ótima "livre", desde que ainda exista um ciclo possível
            livre = self.tsp1[0]
            for a, b in random.sample(list(zip(livre, livre[1:])), len(livre) - 1):
                g = sem(G1, arestas=[(a, b)])
                rota, custo, _ = tsp_forca_bruta(g, 1)
                if rota:
                    break
            self.g_jogo, self.bloq_aresta, self.otimo_tsp = g, (a, b), (rota, custo)
            for v in mp.g:
                if v != 1:
                    mp.caixa(v)
            mp.infestar(arestas=[(a, b)])
        else:
            # zumbis em 4 prédios; um deles sempre no caminho mais curto "livre" (pra obrigar a desviar)
            _, ant_livre, _ = dijkstra(G2, 1)
            while True:
                destino = random.choice([v for v in G2 if v != 1 and v not in G2[1]])
                meio = caminho(ant_livre, destino)[1:-1]
                if not meio:
                    continue
                bloq = {random.choice(meio), *random.sample([v for v in G2 if v not in (1, destino, *meio)], 3)}
                g = sem(G2, nos=bloq)
                if dijkstra(g, 1)[0].get(destino, float("inf")) < float("inf"):
                    break
            self.destino, self.bloq_nos, self.g_jogo = destino, bloq, g
            mp.infestar(nos=bloq)
        self.atualizar_desafio()

    def pode_ir(self, v):
        mp = self.mapa()
        if not self.desafio_tsp:
            return True
        return v not in self.jogador or (v == 1 and len(self.jogador) == len(mp.g))

    def atualizar_desafio(self):
        mp = self.mapa()
        mp.feixes_base()
        if not self.desafio_tsp:
            mp.feixe(self.destino, C_VERDE, .55)
        if not self.terminou:
            for v in self.g_jogo[self.jogador[-1]]:
                if self.pode_ir(v):
                    mp.feixe(v, color.white, .35)
        custo = custo_rota(mp.g, self.jogador)
        teclas = "Clique: andar   Backspace: desfazer\nT: trocar desafio   R: recomeçar"
        if self.desafio_tsp:
            falta = len(mp.g) - len(set(self.jogador))
            objetivo = (f"Colete as {len(mp.g) - 1} caixas e volte ao abrigo" if falta
                        else "Agora volte ao abrigo (nó 1)!")
            self.ui.instrucao("DESAFIO: CAIXEIRO VIAJANTE", objetivo + " sem usar a estrada VERMELHA", teclas)
            alvo = ("Passe em todas as cidades\ne volte ao abrigo gastando\no MENOS possível.\n\n"
                    f"REGRA: a estrada {self.bloq_aresta[0]}-{self.bloq_aresta[1]}\n(vermelha) está cheia de\nzumbis. Não dá pra usar.")
        else:
            self.ui.instrucao("DESAFIO: DIJKSTRA",
                           f"Chegue ao prédio VERDE (nó {self.destino}) sem passar pelos prédios com ZUMBIS", teclas)
            alvo = (f"Saia do abrigo (nó 1) e chegue\nao nó {self.destino} gastando o MENOS\npossível.\n\n"
                    f"REGRA: os prédios {', '.join(map(str, sorted(self.bloq_nos)))}\n(vermelhos) têm zumbis.\n"
                    "Não dá pra passar por eles.")
        self.ui.t_info.text = (alvo + "\n\nPrédios brancos = onde você\npode ir agora.\n\n"
                            f"Sua rota: {SETA.join(map(str, self.jogador))}\nSeu custo: {custo}")

    def jogada(self, v):
        mp = self.mapa()
        if self.terminou or v not in self.g_jogo[self.jogador[-1]] or not self.pode_ir(v):
            if not self.terminou and (v in self.bloq_nos or
                                      (self.bloq_aresta and {self.jogador[-1], v} == set(self.bloq_aresta))):
                self.aviso_zumbi()
            return
        a = self.jogador[-1]
        self.jogador.append(v)
        mp.estrada(a, v, C_LARANJA)
        self.correr([mp.p[v]])
        if self.desafio_tsp and len(self.jogador) == len(mp.g) + 1:
            rota, otimo = self.otimo_tsp
        elif not self.desafio_tsp and v == self.destino:
            dist, ant, _ = dijkstra(self.g_jogo, 1)  # o algoritmo também respeita os zumbis
            otimo, rota = dist[v], caminho(ant, v)
        else:
            self.atualizar_desafio()
            return
        self.terminou = True
        self.atualizar_desafio()
        voce = custo_rota(mp.g, self.jogador)
        self.final = lambda: self.placar(voce, otimo, rota)

    def desfazer(self):
        if self.modo != 3 or len(self.jogador) < 2 or self.terminou:
            return
        mp = self.mapa()
        b = self.jogador.pop()
        a = self.jogador[-1]
        if frozenset((a, b)) not in {frozenset(p) for p in zip(self.jogador, self.jogador[1:])}:
            mp.estrada(a, b, C_ESTRADA)
        self.correr([mp.p[a]])
        self.atualizar_desafio()

    def placar(self, voce, otimo, rota):
        """Primeiro desenha a rota ótima no mapa, estrada por estrada; só depois mostra o resultado."""
        mp, r = self.mapa(), self.rodada
        linha = f"Você: {voce}      Algoritmo: {otimo}"
        txt_rota = "Rota ótima (verde): " + SETA.join(map(str, rota))
        self.ui.instrucao("RESPOSTA DO ALGORITMO", f"Rota ótima: {SETA.join(map(str, rota))}  (custo {otimo})",
                          "R: recomeçar")
        self.ui.t_instrucao.color = C_VERDE
        passo = .4

        def acender(i):
            if r == self.rodada:
                a, b = rota[i], rota[i + 1]
                mp.estrada(a, b, C_VERDE)
                if b != 1:
                    mp.feixe(b, C_VERDE, .45)

        for i in range(len(rota) - 1):
            invoke(acender, i, delay=passo * i)

        def desfecho():
            if r != self.rodada:
                return
            self.ui.t_instrucao.color = color.white
            if voce == otimo:
                self.sobrevivente.anim("acenar")
                self.ui.resultado_mostrar("ROTA PERFEITA!", C_VERDE, linha, txt_rota)
            elif voce <= otimo * 1.2:
                self.ui.resultado_mostrar("SOBREVIVEU... POR POUCO", C_AMARELO, linha, txt_rota)
            else:
                vivos = list(mp.zumbis) or [mp.zumbi(v) for v in random.sample([v for v in mp.g if v != 1], 3)]
                for z in vivos:
                    z.alvo_vivo = self.sobrevivente

                def pegou():
                    if r == self.rodada:
                        self.sobrevivente.anim("morto")
                        self.ui.resultado_mostrar("OS ZUMBIS TE PEGARAM!", C_VERMELHO, linha, txt_rota)
                invoke(pegou, delay=2.2)
        invoke(desfecho, delay=passo * (len(rota) - 1) + 1.5)
