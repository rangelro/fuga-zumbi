# Fuga Zumbi

Jogo 3D em Python (Ursina) para a atividade de Estruturas de Dados Não Lineares:
**Dijkstra** e **Caixeiro Viajante** sobre os dois grafos da atividade (5 e 18 nós).

## Como rodar

Precisa de Python 3.12 (o panda3d ainda não tem versão para 3.13+).

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python fuga_zumbi.py
```

Testes dos algoritmos:

```bash
.venv/bin/python -m tests.test_algoritmos
```

## Modos

| Tecla | Modo | Algoritmo |
|---|---|---|
| 1 | Fuga: escolha o destino e veja o caminho mínimo | Dijkstra (animado passo a passo) |
| 2 | Suprimentos: visitar todas as cidades e voltar | Caixeiro Viajante (força bruta no grafo de 5; Dijkstra + vizinho mais próximo + 2-opt no de 18) |
| 3 | Desafio: você monta a rota e compara com o algoritmo; zumbis bloqueiam prédios/estradas | Dijkstra / força bruta no grafo sem os bloqueios |

**Zumbis opcionais (tecla Z ou botão no menu):** na Fuga, 4 prédios ficam bloqueados e o Dijkstra roda no grafo
sem eles; nos Suprimentos, estradas ficam bloqueadas (1 no mapa de 5 cidades, 3 no de 18) e o Caixeiro acha outra rota.
O sorteio nunca desconecta o grafo (`sortear_nos` / `sortear_arestas` em `jogo/grafos.py`).

## Estrutura

```
fuga_zumbi.py          ponto de entrada: janela, luz, chão
jogo/
  grafos.py            dados dos grafos + algoritmos (sem Ursina, testável)
  estilo.py            cores, constantes e helpers visuais
  personagem.py        sobrevivente e zumbis (animação procedural)
  mapa.py              grafo montado em 3D (prédios, estradas, feixes, caixas)
  interface.py         painel, barra de instrução, menu e janela de resultado
  jogo.py              núcleo: troca de modo, câmera, mouse, teclado
  modo_fuga.py         modo 1
  modo_suprimentos.py  modo 2
  modo_desafio.py      modo 3
tests/
  test_algoritmos.py   asserts dos algoritmos
assets/                modelos CC0 (créditos em assets/CREDITOS.txt)
```
