"""
viz.py  -  Visualizacoes e UX do projeto.

PACOTE P5.

Este modulo NAO implementa algoritmo nem constroi grafo: ele consome o que
io.py, estados.py, graph.py e algorithms.py produzem, e so desenha.

Gera out/parte1/labirinto_interativo.html, com:
  - selecao de mapa e de algoritmo
  - animacao passo a passo do percurso (posicao, chaves, bonus, custo acumulado)
  - realce dos estados-armadilha e alternancia entre camadas
  - controle de velocidade e avanco passo a passo

Uso:
    python -m src.viz                      # gera para todos os mapas
    python -m src.viz data/mapas/m03.txt   # gera so para um
"""

import glob
import json
import os
import sys

from src.graphs import graph as gr
from src.graphs.estados import (
    ALVO,
    construir_g_est,
    estado_inicial,
    rotular,
    teto_teorico,
)
from src.graphs.io import ler_mapa

# ----------------------------------------------------------------------
# quais algoritmos do grupo estao disponiveis hoje
# ----------------------------------------------------------------------

ALGORITMOS = {}

try:
    from src.graphs.algorithms import bellman_ford
    ALGORITMOS["BELLMAN_FORD"] = bellman_ford
except ImportError:
    pass

try:
    from src.graphs.algorithms import bfs
    ALGORITMOS["BFS"] = bfs
except ImportError:
    pass

try:
    from src.graphs.algorithms import dijkstra
    ALGORITMOS["DIJKSTRA"] = dijkstra
except ImportError:
    pass


def _reconstruir(pais, destino):
    """Caminho do inicio ate `destino`, andando de tras pra frente pelo pai."""
    caminho = []
    atual = destino
    vistos = set()
    while atual is not None and atual not in vistos:
        vistos.add(atual)
        caminho.append(atual)
        atual = pais.get(atual)
    caminho.reverse()
    return caminho


def _rodar(funcao, grafo, inicio):
    """
    Chama um algoritmo do grupo e normaliza a saida.
    Aceita retorno (dist, pai) ou (dist, pai, ciclo_negativo).
    Devolve (dist, pai, ciclo) ou None se o algoritmo nao couber nesse formato.
    """
    try:
        resultado = funcao(grafo, inicio)
    except Exception:
        return None
    if not isinstance(resultado, tuple) or len(resultado) < 2:
        return None
    dist, pai = resultado[0], resultado[1]
    if not isinstance(dist, dict) or not isinstance(pai, dict):
        return None
    ciclo = resultado[2] if len(resultado) > 2 else None
    return dist, pai, ciclo


# ----------------------------------------------------------------------
# coleta dos dados de um mapa
# ----------------------------------------------------------------------

def coletar(caminho_mapa):
    """Monta o dicionario com tudo que a pagina precisa para um mapa."""
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    inicio = estado_inicial(grade)

    estados = [e for e in grafo if e != ALVO]

    # camadas: para cada conjunto de chaves, as casas que existem nela
    camadas = {}
    for e in estados:
        camadas.setdefault(e[2] or "-", set()).add((e[0], e[1]))

    # estados-armadilha: no grafo transposto, quem o ALVO nao alcanca.
    # usa o Bellman-Ford do grupo como teste de alcancabilidade.
    armadilhas = []
    if "BELLMAN_FORD" in ALGORITMOS:
        saida = _rodar(ALGORITMOS["BELLMAN_FORD"], gr.transposto(grafo), ALVO)
        if saida is not None:
            dist_re = saida[0]
            inf = float("inf")
            armadilhas = [e for e in estados if dist_re.get(e, inf) == inf]

    # percursos, um por algoritmo disponivel
    percursos = {}
    for apelido, funcao in ALGORITMOS.items():
        saida = _rodar(funcao, grafo, inicio)
        if saida is None:
            continue
        dist, pai, ciclo = saida
        if ciclo:
            percursos[apelido] = {
                "status": "CICLO_NEGATIVO",
                "passos": [],
                "custo": None,
                "ciclo": [rotular(e) for e in ciclo],
            }
            continue
        if dist.get(ALVO, float("inf")) == float("inf"):
            percursos[apelido] = {"status": "SEM_SOLUCAO", "passos": [], "custo": None}
            continue
        caminho = _reconstruir(pai, ALVO)
        passos = []
        for estado in caminho:
            if estado == ALVO:
                continue
            l, c, chaves, bonus = estado
            passos.append({
                "l": l, "c": c,
                "chaves": chaves,
                "bonus": sorted(int(b) for b in bonus),
                "custo": dist[estado] if dist[estado] != float("inf") else None,
                "rotulo": rotular(estado),
            })
        percursos[apelido] = {
            "status": "OK",
            "passos": passos,
            "custo": dist[ALVO],
            "n_passos": len(passos) - 1,
        }

    return {
        "nome": nome,
        "grade": grade,
        "linhas": len(grade),
        "colunas": len(grade[0]) if grade else 0,
        "metricas": {
            "ordem": gr.ordem(grafo) - 1,
            "tamanho": gr.tamanho(grafo),
            "densidade": round(gr.densidade(grafo), 6),
            "teto": teto_teorico(grade),
        },
        "camadas": {k: sorted(map(list, v)) for k, v in sorted(camadas.items())},
        "armadilhas": sorted([e[0], e[1], e[2] or "-"] for e in armadilhas),
        "percursos": percursos,
    }


# ----------------------------------------------------------------------
# a pagina
# ----------------------------------------------------------------------

PAGINA = r"""<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Labirinto Interativo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap">
<style>
  :root {
    --fundo:#12141a; --palco:#0b0d12; --painel:#1a1d26; --linha:#282c38;
    --tinta:#e9ebf2; --tinta2:#9aa0b2; --tinta3:#656b7d;
    --azul:#5598e7; --azul-forte:#86b6ef;
    --parede:#2e3342; --chao:#e4e9f0; --chao-txt:#aab2c2;
    --lama:#c08c4a; --agua:#6fa8d6; --chave:#f2d750; --porta:#b49ad8;
    --inicio:#67c18a; --saida:#f0a05a; --esteira:#8a93a6;
    --bonus:#e5739b; --fonte:#58c3bc; --alerta:#e08a8a;
    --m:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
    --cel:24px;
  }
  :root[data-theme="light"]{
    --fundo:#eceef3; --palco:#dfe3ea; --painel:#ffffff; --linha:#ccd1dc;
    --tinta:#171a21; --tinta2:#5b6173; --tinta3:#878da0;
    --azul:#2a78d6; --azul-forte:#1c5cab;
    --parede:#3a3e4a; --chao:#ffffff; --chao-txt:#b9bfcc;
  }
  *{box-sizing:border-box}
  html,body{margin:0;background:var(--fundo);color:var(--tinta);font-family:var(--m)}
  body{font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased}
  button,select,input{font-family:inherit;color:inherit}

  .topo{display:flex;flex-wrap:wrap;align-items:center;gap:1rem;
        padding:.85rem 1.25rem;border-bottom:1px solid var(--linha);background:var(--painel)}
  .marca{font-weight:700;letter-spacing:-.02em;font-size:.95rem;margin-right:auto}
  .marca b{color:var(--azul)}
  .campo{display:flex;align-items:center;gap:.45rem;font-size:.78rem;color:var(--tinta3)}
  select{background:var(--fundo);border:1px solid var(--linha);border-radius:5px;
         padding:.3rem .5rem;font-size:.82rem;font-weight:500}
  select:hover{border-color:var(--azul)}
  .tema{background:none;border:1px solid var(--linha);border-radius:5px;
        padding:.3rem .55rem;cursor:pointer;font-size:.78rem;color:var(--tinta2)}
  .tema:hover{border-color:var(--azul);color:var(--tinta)}

  .estado{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem 1.6rem;
          padding:1.1rem 1.25rem .9rem;background:var(--painel);border-bottom:1px solid var(--linha)}
  .rotulo{font-size:clamp(1.3rem,3.4vw,2.1rem);font-weight:700;letter-spacing:-.03em;
          color:var(--azul-forte);white-space:nowrap}
  .leitura{display:flex;flex-wrap:wrap;gap:.3rem 1.4rem;font-size:.8rem;color:var(--tinta3)}
  .leitura i{font-style:normal;color:var(--tinta);font-weight:500}

  .palco{background:var(--palco);padding:1.5rem 1rem;display:flex;
         justify-content:center;gap:1.5rem;overflow:auto;flex-wrap:wrap}
  .tabuleiro{display:flex;flex-direction:column;gap:.5rem;align-items:center}
  .tab-rot{font-size:.72rem;color:var(--tinta3);letter-spacing:.04em}
  .tab-rot b{color:var(--azul);font-weight:500}
  .grade{display:inline-grid;gap:1px;background:var(--linha);padding:1px;border-radius:3px}
  .cel{width:var(--cel);height:var(--cel);display:flex;align-items:center;justify-content:center;
       font-size:calc(var(--cel)*.52);font-weight:500;color:#171a21;background:var(--chao);position:relative}
  .p{background:var(--parede);color:transparent}
  .o{background:var(--chao);color:var(--chao-txt)}
  .st{background:var(--inicio)} .go{background:var(--saida)}
  .mu{background:var(--lama)} .ag{background:var(--agua)}
  .ch{background:var(--chave)} .po{background:var(--porta)}
  .es{background:var(--esteira)} .bo{background:var(--bonus)} .fo{background:var(--fonte)}
  .apagada{opacity:.18}
  .trilha::after{content:"";position:absolute;inset:32%;border-radius:50%;
                 background:var(--azul);opacity:.42}
  .presa{box-shadow:inset 0 0 0 2px var(--alerta)}
  .aqui{box-shadow:inset 0 0 0 3px #171a21,0 0 0 2px var(--azul);z-index:2}
  .aqui::before{content:"";position:absolute;inset:24%;border-radius:50%;background:#171a21}

  .transporte{display:flex;flex-wrap:wrap;align-items:center;gap:.6rem 1.1rem;
              padding:.75rem 1.25rem;background:var(--painel);border-top:1px solid var(--linha);
              border-bottom:1px solid var(--linha)}
  .botoes{display:flex;gap:.25rem}
  .botoes button{background:var(--fundo);border:1px solid var(--linha);color:var(--tinta2);
                 width:2.1rem;height:2.1rem;border-radius:5px;cursor:pointer;font-size:.8rem;
                 display:flex;align-items:center;justify-content:center}
  .botoes button:hover:not(:disabled){border-color:var(--azul);color:var(--tinta)}
  .botoes button.tocar{width:auto;padding:0 .9rem;background:var(--azul);border-color:var(--azul);
                       color:#0b0d12;font-weight:700;letter-spacing:-.01em}
  .botoes button:disabled{opacity:.35;cursor:not-allowed}
  input[type=range]{accent-color:var(--azul);width:7.5rem;background:none}
  .marca-passo{font-size:.78rem;color:var(--tinta3);margin-left:auto}
  .marca-passo b{color:var(--tinta);font-weight:500}
  .barra{height:3px;background:var(--linha);position:relative}
  .barra i{display:block;height:100%;background:var(--azul);width:0}
  .alternar{display:flex;align-items:center;gap:.4rem;font-size:.78rem;
            color:var(--tinta3);cursor:pointer;user-select:none}
  .alternar input{accent-color:var(--azul);margin:0}

  .rodape{display:flex;flex-wrap:wrap;gap:.35rem 1.6rem;padding:.8rem 1.25rem;
          font-size:.76rem;color:var(--tinta3);border-bottom:1px solid var(--linha)}
  .rodape b{color:var(--tinta);font-weight:500}
  .aviso{margin:0;padding:.75rem 1.25rem;background:#2a1a1e;color:var(--alerta);font-size:.8rem;
         border-bottom:1px solid var(--linha)}
  :root[data-theme="light"] .aviso{background:#fbe8e8}
  .aviso code{color:var(--tinta2);font-size:.74rem;word-break:break-all}

  .legenda{display:flex;flex-wrap:wrap;gap:.3rem 1rem;padding:.8rem 1.25rem;
           font-size:.74rem;color:var(--tinta3)}
  .legenda span{display:inline-flex;align-items:center;gap:.35rem}
  .sw{width:.8rem;height:.8rem;border-radius:2px;border:1px solid var(--linha)}
  :focus-visible{outline:2px solid var(--azul);outline-offset:2px}
  @media (prefers-reduced-motion:reduce){*{transition:none!important}}
  @media (max-width:720px){.rotulo{font-size:1.15rem}.estado{gap:.4rem .9rem}}
</style>

<header class="topo">
  <div class="marca">labirinto <b>interativo</b></div>
  <label class="campo">mapa <select id="mapa"></select></label>
  <label class="campo">algoritmo <select id="alg"></select></label>
  <label class="campo">camada <select id="camada"></select></label>
  <button class="tema" id="tema">tema</button>
</header>

<section class="estado">
  <div class="rotulo" id="rotulo">—</div>
  <div class="leitura">
    <span>chaves <i id="chaves">—</i></span>
    <span>bônus <i id="bonus">—</i></span>
    <span>custo acumulado <i id="custo">—</i></span>
  </div>
</section>

<div id="aviso"></div>

<div class="palco" id="palco"></div>

<div class="barra"><i id="progresso"></i></div>

<section class="transporte">
  <div class="botoes">
    <button id="inicio" title="voltar ao início">|&#9664;</button>
    <button id="voltar" title="um passo atrás">&#9664;</button>
    <button id="tocar" class="tocar">&#9654; tocar</button>
    <button id="avancar" title="um passo à frente">&#9654;</button>
    <button id="fim" title="ir para o fim">&#9654;|</button>
  </div>
  <label class="campo">velocidade <input type="range" id="vel" min="1" max="12" value="3"><i id="velTxt" style="font-style:normal;color:var(--tinta2)">3/s</i></label>
  <label class="campo">zoom <input type="range" id="zoom" min="8" max="42" value="24"></label>
  <label class="alternar"><input type="checkbox" id="armad"> armadilhas</label>
  <label class="alternar"><input type="checkbox" id="trilhaOn" checked> trilha</label>
  <label class="alternar"><input type="checkbox" id="duplo"> comparar dois algoritmos</label>
  <div class="marca-passo">passo <b id="passo">—</b></div>
</section>

<div class="rodape" id="rodape"></div>
<div class="legenda" id="legenda"></div>

<script>
const DADOS = __DADOS__;

const CLASSE = {"#":"p",".":"o","S":"st","G":"go",",":"mu","~":"ag","+":"bo","*":"fo",
                ">":"es","<":"es","^":"es","v":"es"};
const classeDe = ch => CLASSE[ch] || ("abcd".includes(ch) ? "ch" : "ABCD".includes(ch) ? "po" : "o");

const $ = id => document.getElementById(id);
let mapa = null, pistas = [], i = 0, tocando = false, timer = null;

function montar(){
  $("mapa").innerHTML = Object.keys(DADOS).sort().map(n=>`<option>${n}</option>`).join("");
  trocarMapa();
}

function trocarMapa(){
  mapa = DADOS[$("mapa").value];
  const algs = Object.keys(mapa.percursos).sort();
  $("alg").innerHTML = algs.length ? algs.map(a=>`<option>${a}</option>`).join("")
                                   : `<option value="">nenhum</option>`;
  const cam = Object.keys(mapa.camadas);
  $("camada").innerHTML = `<option value="">todas</option>` + cam.map(c=>`<option>${c}</option>`).join("");
  rodape(); legenda(); trocarAlg();
}

function algoritmosAtivos(){
  const algs = Object.keys(mapa.percursos).sort();
  if (!$("duplo").checked) return [$("alg").value].filter(Boolean);
  const primeiro = $("alg").value;
  const outro = algs.find(a => a !== primeiro && mapa.percursos[a].status === "OK");
  return outro ? [primeiro, outro] : [primeiro].filter(Boolean);
}

function trocarAlg(){
  parar();
  const ativos = algoritmosAtivos();
  pistas = ativos.map(a => ({nome:a, p:mapa.percursos[a]}));
  i = 0;
  construirPalco();
  aviso();
  render();
}

function construirPalco(){
  const palco = $("palco");
  palco.innerHTML = "";
  for (const pista of pistas){
    const caixa = document.createElement("div");
    caixa.className = "tabuleiro";
    const rot = document.createElement("div");
    rot.className = "tab-rot";
    const p = pista.p;
    const medida = pista.nome === "BFS" ? "" : (p.custo !== null ? " · custo " + p.custo : "");
    rot.innerHTML = p.status === "OK"
      ? `<b>${pista.nome}</b> · ${p.n_passos} passos${medida}`
      : `<b>${pista.nome}</b> · ${p.status.toLowerCase().replace("_"," ")}`;
    const g = document.createElement("div");
    g.className = "grade";
    g.style.gridTemplateColumns = `repeat(${mapa.colunas}, var(--cel,24px))`;
    pista.celulas = [];
    for (let l=0;l<mapa.linhas;l++){
      const linha=[];
      for (let c=0;c<mapa.colunas;c++){
        const ch = mapa.grade[l][c];
        const d = document.createElement("div");
        d.className = "cel " + classeDe(ch);
        d.textContent = ch === "#" ? "" : ch;
        d.title = `(${l},${c}) ${ch}`;
        g.appendChild(d); linha.push(d);
      }
      pista.celulas.push(linha);
    }
    caixa.append(rot, g);
    palco.appendChild(caixa);
  }
}

function maxPassos(){
  return Math.max(0, ...pistas.map(p => p.p.status === "OK" ? p.p.passos.length - 1 : 0));
}

function render(){
  const cam = $("camada").value;
  const dentro = cam ? new Set(mapa.camadas[cam].map(([l,c])=>l+","+c)) : null;

  for (const pista of pistas){
    for (const linha of pista.celulas) for (const d of linha)
      d.classList.remove("trilha","aqui","presa","apagada");

    if (dentro)
      for (let l=0;l<mapa.linhas;l++) for (let c=0;c<mapa.colunas;c++)
        if (mapa.grade[l][c] !== "#" && !dentro.has(l+","+c))
          pista.celulas[l][c].classList.add("apagada");

    if ($("armad").checked)
      for (const [l,c,ch] of mapa.armadilhas)
        if (!cam || ch === cam) pista.celulas[l][c].classList.add("presa");

    const passos = pista.p.status === "OK" ? pista.p.passos : [];
    if (!passos.length) continue;
    const k = Math.min(i, passos.length - 1);
    if ($("trilhaOn").checked)
      for (let j=0;j<=k;j++) pista.celulas[passos[j].l][passos[j].c].classList.add("trilha");
    pista.celulas[passos[k].l][passos[k].c].classList.add("aqui");
  }

  const guia = pistas.find(p => p.p.status === "OK");
  if (!guia){
    $("rotulo").textContent = "—";
    ["chaves","bonus","custo"].forEach(k=>$(k).textContent="—");
    $("passo").textContent = "—";
    $("progresso").style.width = "0";
    return;
  }
  const passos = guia.p.passos;
  const e = passos[Math.min(i, passos.length-1)];
  $("rotulo").textContent = e.rotulo;
  $("chaves").textContent = e.chaves || "—";
  $("bonus").textContent = e.bonus.length ? "{"+e.bonus.join(",")+"}" : "{}";
  $("custo").textContent = guia.nome === "BFS" ? "—" : e.custo;
  const total = maxPassos();
  $("passo").textContent = `${Math.min(i,total)} / ${total}`;
  $("progresso").style.width = (100*Math.min(i,total)/Math.max(1,total))+"%";
}

function aviso(){
  const p = pistas[0] && pistas[0].p;
  const caixa = $("aviso");
  if (!p || p.status === "OK"){ caixa.innerHTML = ""; return; }
  if (p.status === "SEM_SOLUCAO")
    caixa.innerHTML = `<p class="aviso">Sem solução. Nenhum caminho leva deste início até a saída — todos os estados alcançáveis são armadilha.</p>`;
  if (p.status === "CICLO_NEGATIVO")
    caixa.innerHTML = `<p class="aviso">Ciclo negativo. Não existe custo mínimo: dá para repetir este ciclo sem parar e o custo cai sem limite.<br><code>${p.ciclo.join("  →  ")}</code></p>`;
  if (p.status === "RECUSA")
    caixa.innerHTML = `<p class="aviso">Dijkstra recusou este mapa porque ele tem arco de peso negativo. Use o Bellman-Ford.</p>`;
}

function rodape(){
  const m = mapa.metricas;
  $("rodape").innerHTML = [
    ["estados", m.ordem], ["arcos", m.tamanho],
    ["densidade", m.densidade.toFixed(5)],
    ["teto teórico", m.teto],
    ["ocupação", m.teto ? (100*m.ordem/m.teto).toFixed(1)+"%" : "—"],
    ["armadilhas", mapa.armadilhas.length],
    ["camadas", Object.keys(mapa.camadas).length],
  ].map(([k,v])=>`<span>${k} <b>${v}</b></span>`).join("");
}

function legenda(){
  const vistos = new Set(mapa.grade.flat());
  const itens = [["#","parede","--parede"],[".","chão 1","--chao"],[",","lama 3","--lama"],
                 ["~","água 5","--agua"],["+","bônus −4","--bonus"],["*","fonte −2","--fonte"],
                 ["S","início","--inicio"],["G","saída","--saida"]];
  let html = itens.filter(([c])=>vistos.has(c))
    .map(([,n,v])=>`<span><i class="sw" style="background:var(${v})"></i>${n}</span>`).join("");
  if ([...vistos].some(c=>"abcd".includes(c))) html += `<span><i class="sw" style="background:var(--chave)"></i>chave</span>`;
  if ([...vistos].some(c=>"ABCD".includes(c))) html += `<span><i class="sw" style="background:var(--porta)"></i>porta</span>`;
  if ([...vistos].some(c=>"><^v".includes(c))) html += `<span><i class="sw" style="background:var(--esteira)"></i>esteira</span>`;
  html += `<span><i class="sw" style="background:var(--azul)"></i>trilha</span>`;
  html += `<span><i class="sw" style="box-shadow:inset 0 0 0 2px var(--alerta)"></i>armadilha</span>`;
  $("legenda").innerHTML = html;
}

function ir(n){ const t = maxPassos(); if(!t) return; i = Math.max(0, Math.min(t, n)); render(); }
function parar(){ tocando=false; clearInterval(timer); $("tocar").innerHTML="&#9654; tocar"; }
function tocar(){
  const t = maxPassos();
  if (!t) return;
  if (tocando) return parar();
  if (i >= t) i = 0;
  tocando = true; $("tocar").innerHTML="&#10073;&#10073; pausar";
  clearInterval(timer);
  timer = setInterval(()=>{ if (i >= maxPassos()) return parar(); i++; render(); },
                      1000/Number($("vel").value));
}

$("mapa").onchange = trocarMapa;
$("alg").onchange = trocarAlg;
$("duplo").onchange = trocarAlg;
$("camada").onchange = render;
$("armad").onchange = render;
$("trilhaOn").onchange = render;
$("tocar").onclick = tocar;
$("avancar").onclick = ()=>{parar(); ir(i+1);};
$("voltar").onclick  = ()=>{parar(); ir(i-1);};
$("inicio").onclick  = ()=>{parar(); ir(0);};
$("fim").onclick     = ()=>{parar(); ir(maxPassos());};
$("vel").oninput = e => { $("velTxt").textContent = e.target.value+"/s"; if (tocando){ parar(); tocar(); } };
$("zoom").oninput = e => document.documentElement.style.setProperty("--cel", e.target.value+"px");
$("tema").onclick = () => {
  const atual = document.documentElement.getAttribute("data-theme");
  document.documentElement.setAttribute("data-theme", atual === "light" ? "dark" : "light");
};
document.addEventListener("keydown", ev=>{
  if (ev.key === "ArrowRight"){ parar(); ir(i+1); }
  if (ev.key === "ArrowLeft"){ parar(); ir(i-1); }
  if (ev.key === " "){ ev.preventDefault(); tocar(); }
});

montar();
</script>
</html>
"""


def gerar_html(mapas=None, saida="out/parte1/labirinto_interativo.html"):
    """Gera a pagina interativa com todos os mapas informados."""
    if mapas is None:
        mapas = sorted(glob.glob("data/mapas/*.txt")) + sorted(glob.glob("data/mapas_grupo/*.txt"))

    dados = {}
    for caminho in mapas:
        try:
            info = coletar(caminho)
            dados[info["nome"]] = info
        except Exception as erro:
            print(f"  ! {os.path.basename(caminho)}: {type(erro).__name__}: {erro}")

    os.makedirs(os.path.dirname(saida), exist_ok=True)
    html = PAGINA.replace("__DADOS__", json.dumps(dados, ensure_ascii=False))
    with open(saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(html)

    return saida, dados




import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap

CORES_CASA = {
    "#": "#343846", ".": "#ffffff", "S": "#67c18a", "G": "#f0a05a",
    ",": "#c08c4a", "~": "#6fa8d6", "+": "#e5739b", "*": "#58c3bc",
}
COR_CHAVE, COR_PORTA, COR_ESTEIRA = "#f2d750", "#b49ad8", "#9aa6b8"

RAMPA_CAMADA = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]

RAMPA_SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def _tons(n):
    if n <= 1:
        return [RAMPA_CAMADA[2]]
    ultimo = len(RAMPA_CAMADA) - 1
    return [RAMPA_CAMADA[round(i * ultimo / (n - 1))] for i in range(n)]

TINTA, TINTA2 = "#16181f", "#6b7183"


def _cor_da_casa(ch):
    if ch in CORES_CASA:
        return CORES_CASA[ch]
    if ch in "abcd":
        return COR_CHAVE
    if ch in "ABCD":
        return COR_PORTA
    if ch in "><^v":
        return COR_ESTEIRA
    return "#ffffff"


def _desenhar_grade(ax, grade, rotulos=True):
    n_l, n_c = len(grade), len(grade[0])
    for l in range(n_l):
        for c in range(n_c):
            ch = grade[l][c]
            ax.add_patch(Rectangle((c - .5, l - .5), 1, 1,
                                   facecolor=_cor_da_casa(ch),
                                   edgecolor="#d3d7e0", linewidth=.4))
            if rotulos and ch not in "#.":
                ax.text(c, l, ch, ha="center", va="center",
                        fontsize=max(4, min(9, 150 / n_c)), color=TINTA, weight="bold")
    ax.set_xlim(-.5, n_c - .5)
    ax.set_ylim(n_l - .5, -.5)
    ax.set_aspect("equal")
    ax.set_xlabel("coluna", fontsize=9, color=TINTA2)
    ax.set_ylabel("linha", fontsize=9, color=TINTA2)
    ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    for lado in ax.spines.values():
        lado.set_color("#d3d7e0")


def _legenda_casas(ax, grade):
    presentes, itens = {ch for linha in grade for ch in linha}, []
    rotulo = [("#", "parede"), (".", "chão · 1"), (",", "lama · 3"), ("~", "água · 5"),
              ("+", "bônus · −4"), ("*", "fonte · −2"), ("S", "início"), ("G", "saída")]
    for ch, nome in rotulo:
        if ch in presentes:
            itens.append(Patch(facecolor=_cor_da_casa(ch), edgecolor="#d3d7e0", label=nome))
    if presentes & set("abcd"):
        itens.append(Patch(facecolor=COR_CHAVE, edgecolor="#d3d7e0", label="chave"))
    if presentes & set("ABCD"):
        itens.append(Patch(facecolor=COR_PORTA, edgecolor="#d3d7e0", label="porta"))
    if presentes & set("><^v"):
        itens.append(Patch(facecolor=COR_ESTEIRA, edgecolor="#d3d7e0", label="esteira"))
    return itens


def _percurso(grade, algoritmo="DIJKSTRA"):
    grafo = construir_g_est(grade)
    inicio = estado_inicial(grade)
    for nome in (algoritmo, "BELLMAN_FORD", "BFS"):
        if nome not in ALGORITMOS:
            continue
        saida = _rodar(ALGORITMOS[nome], grafo, inicio)
        if saida is None:
            continue
        dist, pai, ciclo = saida
        if ciclo or dist.get(ALVO, float("inf")) == float("inf"):
            continue
        caminho = [e for e in _reconstruir(pai, ALVO) if e != ALVO]
        return caminho, dist, nome
    return None, None, None


def figura_percurso(caminho_mapa, saida=None):
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    saida = saida or f"out/parte1/percurso_{nome.split('_')[0]}.png"
    grade = ler_mapa(caminho_mapa)
    caminho, dist, alg = _percurso(grade)
    if caminho is None:
        print(f"  ! {nome}: nenhum algoritmo devolveu caminho")
        return None

    ordem_camadas = []
    for e in caminho:
        if e[2] not in ordem_camadas:
            ordem_camadas.append(e[2])
    tons = _tons(len(ordem_camadas))
    cor_de = {ch: tons[i] for i, ch in enumerate(ordem_camadas)}

    n_l, n_c = len(grade), len(grade[0])
    fig, ax = plt.subplots(figsize=(max(6, n_c * .34), max(4, n_l * .34 + 2.2)))
    _desenhar_grade(ax, grade, rotulos=n_c <= 30)

    for a, b in zip(caminho, caminho[1:]):
        ax.plot([a[1], b[1]], [a[0], b[0]], color=cor_de[b[2]],
                linewidth=3.2, solid_capstyle="round", zorder=3,
                path_effects=None)
    for e in caminho:
        ax.plot(e[1], e[0], "o", markersize=4.6, color=cor_de[e[2]],
                markeredgecolor="#ffffff", markeredgewidth=1.0, zorder=4)

    for a, b in zip(caminho, caminho[1:]):
        if b[2] != a[2]:
            nova = (set(b[2]) - set(a[2])).pop()
            ax.annotate(f"pegou {nova}", (b[1], b[0]),
                        textcoords="offset points", xytext=(0, 13),
                        ha="center", fontsize=7.5, color=TINTA, weight="bold",
                        bbox=dict(boxstyle="round,pad=0.22", fc="#ffffff",
                                  ec=cor_de[b[2]], lw=1.0), zorder=6)

    itens = [Line2D([], [], color=cor_de[ch], lw=3.2,
                    label=f"com {ch}" if ch else "sem chaves")
             for ch in ordem_camadas]
    itens += _legenda_casas(ax, grade)
    ax.legend(handles=itens, loc="upper center", bbox_to_anchor=(.5, -.14),
              ncol=min(5, len(itens)), fontsize=7.5, frameon=False)

    ax.set_title(f"Caminho de menor custo — {nome}\n"
                 f"{alg} · {len(caminho)-1} passos · custo {dist[ALVO]} · "
                 f"{len(ordem_camadas)} camada(s)",
                 fontsize=11, color=TINTA, weight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)
    return saida


def figura_camadas(caminho_mapa="data/mapas/m02_uma_chave.txt",
                   saida="out/parte1/camadas_m02.png"):
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    n_l, n_c = len(grade), len(grade[0])

    camadas = sorted({e[2] for e in grafo if e != ALVO}, key=lambda s: (len(s), s))
    faixa = {ch: i for i, ch in enumerate(camadas)}
    tons = _tons(len(camadas))
    alt = n_l + 2.2

    def pos(e):
        return (e[1], (len(camadas) - 1 - faixa[e[2]]) * alt + e[0])

    fig, ax = plt.subplots(figsize=(max(7, n_c * .5), 2.4 + len(camadas) * alt * .42))

    for ch in camadas:
        y0 = (len(camadas) - 1 - faixa[ch]) * alt - .6
        ax.add_patch(Rectangle((-1.1, y0), n_c + 1.4, n_l + .2,
                               facecolor="#f3f5f8", edgecolor="#d3d7e0", lw=.8, zorder=0))
        ax.text(-1.5, y0 + n_l / 2, f"camada\n{ch or '-'}", ha="right", va="center",
                fontsize=9, weight="bold", color=tons[faixa[ch]])

    dentro = fora = 0
    for origem, vizinhos in grafo.items():
        if origem == ALVO:
            continue
        x0, y0 = pos(origem)
        for destino, _ in vizinhos:
            if destino == ALVO:
                continue
            x1, y1 = pos(destino)
            if destino[2] == origem[2]:
                ax.plot([x0, x1], [y0, y1], color="#c3c7d2", lw=.9, zorder=1)
                dentro += 1
            else:
                ax.annotate("", (x1, y1), (x0, y0), zorder=5,
                            arrowprops=dict(arrowstyle="-|>", color="#eb6834",
                                            lw=2.4, shrinkA=3, shrinkB=3))
                fora += 1

    for e in grafo:
        if e == ALVO:
            continue
        x, y = pos(e)
        ax.plot(x, y, "o", markersize=7, color=tons[faixa[e[2]]],
                markeredgecolor="#ffffff", markeredgewidth=1.0, zorder=4)

    ax.set_xlim(-3.4, n_c + .6)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(handles=[
        Line2D([], [], color="#c3c7d2", lw=1.4, label=f"arco dentro da camada ({dentro})"),
        Line2D([], [], color="#eb6834", lw=2.4, label=f"arco que TROCA de camada ({fora})"),
        Line2D([], [], marker="o", color="none", markerfacecolor=tons[0],
               markeredgecolor="#fff", markersize=8, label="estado"),
    ], loc="upper center", bbox_to_anchor=(.5, -.02), ncol=3, fontsize=8.5, frameon=False)
    ax.set_title(f"Grafo de estados em camadas — {nome}\n"
                 f"{len(grafo)-1} estados · cada camada é um conjunto de chaves · "
                 f"{fora} arco(s) trocam de camada",
                 fontsize=11, weight="bold", color=TINTA, pad=12)
    fig.tight_layout()
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)
    return saida


def figura_arvore_bfs(caminho_mapa="data/mapas/m02_uma_chave.txt",
                      saida="out/parte1/arvore_bfs_m02.png"):
    if "BFS" not in ALGORITMOS:
        print("  ! arvore BFS: a funcao bfs() ainda nao existe em algorithms.py")
        return None
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    inicio = estado_inicial(grade)
    saida_bfs = _rodar(ALGORITMOS["BFS"], grafo, inicio)
    if saida_bfs is None:
        return None
    niveis, pais = saida_bfs[0], saida_bfs[1]

    por_nivel = {}
    for no, n in niveis.items():
        if no != ALVO:
            por_nivel.setdefault(n, []).append(no)
    for n in por_nivel:
        por_nivel[n].sort()

    pos = {}
    for n, nos in por_nivel.items():
        for i, no in enumerate(nos):
            pos[no] = (n, i - (len(nos) - 1) / 2)

    fundo = max(por_nivel)
    fig, ax = plt.subplots(figsize=(max(8, fundo * .42), 4.6))

    for no, (x, y) in pos.items():
        pai = pais.get(no)
        if pai in pos:
            px, py = pos[pai]
            ax.plot([px, x], [py, y], color="#c3c7d2", lw=1.0, zorder=1)

    ordem_ch = sorted({no[2] for no in pos}, key=lambda t: (len(t), t))
    tons = dict(zip(ordem_ch, _tons(len(ordem_ch))))
    for no, (x, y) in pos.items():
        cor = tons[no[2]]
        ax.plot(x, y, "o", markersize=5.6, color=cor,
                markeredgecolor="#ffffff", markeredgewidth=.9, zorder=3)

    for n in range(0, fundo + 1, max(1, fundo // 12)):
        ax.axvline(n, color="#e7eaf0", lw=.7, zorder=0)

    largura = max(len(v) for v in por_nivel.values())
    ax.set_ylim(-largura / 2 - .8, largura / 2 + .8)
    ax.set_xlim(-.8, fundo + .8)

    chaves = ordem_ch
    ax.legend(handles=[Line2D([], [], marker="o", color="none",
                              markerfacecolor=tons[ch],
                              markeredgecolor="#fff", markersize=8,
                              label=f"com {ch}" if ch else "sem chaves")
                       for ch in chaves],
              loc="upper center", bbox_to_anchor=(.5, -.08),
              ncol=len(chaves), fontsize=8.5, frameon=False)

    ax.set_xlabel("nível da BFS  (número de passos desde o início)",
                  fontsize=9.5, color=TINTA2)
    ax.set_yticks([])
    ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#d3d7e0")
    ax.set_title(f"Árvore BFS do grafo de estados — {nome}\n"
                 f"{len(pos)} estados alcançáveis · profundidade {fundo} níveis",
                 fontsize=11, weight="bold", color=TINTA, pad=10)
    fig.tight_layout()
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)
    return saida


def figura_heatmap(caminho_mapa="data/mapas/m08_grande.txt",
                   saida="out/parte1/heatmap_m08.png"):
    nome = os.path.splitext(os.path.basename(caminho_mapa))[0]
    grade = ler_mapa(caminho_mapa)
    grafo = construir_g_est(grade)
    n_l, n_c = len(grade), len(grade[0])

    mult = [[0] * n_c for _ in range(n_l)]
    for e in grafo:
        if e != ALVO:
            mult[e[0]][e[1]] += 1
    maximo = max(max(linha) for linha in mult)
    casas_no_max = sum(1 for l in range(n_l) for c in range(n_c) if mult[l][c] == maximo)

    cmap = LinearSegmentedColormap.from_list("seq_azul", RAMPA_SEQ)
    fig, ax = plt.subplots(figsize=(max(8, n_c * .22), max(5, n_l * .22 + 1.8)))

    dados = [[float("nan") if grade[l][c] == "#" else mult[l][c] for c in range(n_c)]
             for l in range(n_l)]
    cmap.set_bad(CORES_CASA["#"])
    im = ax.imshow(dados, cmap=cmap, vmin=0, vmax=maximo, interpolation="nearest")

    ax.set_xlabel("coluna", fontsize=9, color=TINTA2)
    ax.set_ylabel("linha", fontsize=9, color=TINTA2)
    ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    for lado in ax.spines.values():
        lado.set_color("#d3d7e0")

    barra = fig.colorbar(im, ax=ax, fraction=.026, pad=.015)
    barra.set_label("estados por casa (multiplicidade)", fontsize=9, color=TINTA2)
    barra.ax.tick_params(labelsize=7, colors=TINTA2, length=2)
    barra.outline.set_edgecolor("#d3d7e0")

    ax.set_title(f"Multiplicidade das casas — {nome}\n"
                 f"{len(grafo)-1} estados em {sum(1 for l in range(n_l) for c in range(n_c) if grade[l][c] != '#')} casas livres · "
                 f"máximo {maximo} (em {casas_no_max} casa(s)) · cinza escuro = parede",
                 fontsize=11, weight="bold", color=TINTA, pad=10)
    fig.savefig(saida, dpi=160, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)
    return saida, maximo, casas_no_max


def gerar_figuras():
    os.makedirs("out/parte1", exist_ok=True)
    feitas = []
    for mapa in ("data/mapas/m03_tres_chaves.txt", "data/mapas/m08_grande.txt"):
        f = figura_percurso(mapa)
        if f:
            feitas.append(f)
    for fn in (figura_camadas, figura_arvore_bfs):
        f = fn()
        if f:
            feitas.append(f)
    r = figura_heatmap()
    if r:
        feitas.append(r[0])
        print(f"  multiplicidade maxima no m08: {r[1]} (em {r[2]} casa(s))")
    return feitas


def main():
    alvo = sys.argv[1] if len(sys.argv) > 1 else "tudo"

    if alvo in ("tudo", "html"):
        destino, dados = gerar_html()
        print(f"{destino}  ({os.path.getsize(destino)/1024:.0f} KB, {len(dados)} mapas)")

    if alvo in ("tudo", "figuras"):
        for f in gerar_figuras():
            print(f"{f}  ({os.path.getsize(f)/1024:.0f} KB)")

    print(f"algoritmos disponiveis: {', '.join(sorted(ALGORITMOS)) or '(nenhum)'}")


if __name__ == "__main__":
    main()
