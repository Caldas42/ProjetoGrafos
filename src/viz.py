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
<style>
  :root {
    --ground:#EEF0F4; --surface:#FFFFFF; --ink:#16181F; --ink-soft:#424758;
    --muted:#6B7183; --rule:#D3D7E0; --accent:#2F5FBF; --accent-bg:#E2EAF9;
    --warn:#A33A3A; --warn-bg:#FAE3E3;
    --parede:#343846; --chao:#FFFFFF; --chao-b:#D3D7E0;
    --lama:#C08C4A; --agua:#6FA8D6; --chave:#F2D750; --porta:#B49AD8;
    --inicio:#67C18A; --saida:#F0A05A; --esteira:#9AA6B8; --bonus:#E5739B; --fonte:#58C3BC;
    --trilha:#2F5FBF; --armadilha:#A33A3A;
    --cel:22px;
    --mono:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
    --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  }
  @media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
    --ground:#101219; --surface:#191C26; --ink:#E8EBF2; --ink-soft:#B6BCCC;
    --muted:#848BA0; --rule:#2B303E; --accent:#7AA2EE; --accent-bg:#1B2436;
    --warn:#E08A8A; --warn-bg:#2C1A1A;
    --parede:#0B0D13; --chao:#272C3A; --chao-b:#363C4D;
    --trilha:#7AA2EE; --armadilha:#E08A8A;
  }}
  :root[data-theme="dark"]{
    --ground:#101219; --surface:#191C26; --ink:#E8EBF2; --ink-soft:#B6BCCC;
    --muted:#848BA0; --rule:#2B303E; --accent:#7AA2EE; --accent-bg:#1B2436;
    --warn:#E08A8A; --warn-bg:#2C1A1A;
    --parede:#0B0D13; --chao:#272C3A; --chao-b:#363C4D;
    --trilha:#7AA2EE; --armadilha:#E08A8A;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
       font-size:15.5px;line-height:1.6;-webkit-font-smoothing:antialiased}
  .wrap{max-width:74rem;margin:0 auto;padding:2rem 1rem 4rem;display:flex;flex-direction:column;gap:1.5rem}

  header{display:flex;flex-direction:column;gap:0.3rem}
  h1{font-family:var(--mono);font-size:1.6rem;font-weight:600;letter-spacing:-0.02em;margin:0}
  .sub{color:var(--muted);font-size:0.9rem;margin:0}

  .painel{display:flex;flex-wrap:wrap;gap:0.9rem 1.4rem;align-items:flex-end;
          background:var(--surface);border:1px solid var(--rule);border-radius:8px;padding:1rem 1.1rem}
  .campo{display:flex;flex-direction:column;gap:0.3rem}
  .campo label{font-family:var(--mono);font-size:0.68rem;letter-spacing:0.1em;
               text-transform:uppercase;color:var(--muted)}
  select,button{font-family:inherit;font-size:0.9rem;color:var(--ink);background:var(--surface);
                border:1px solid var(--rule);border-radius:6px;padding:0.42rem 0.7rem;cursor:pointer}
  select:hover,button:hover{border-color:var(--accent)}
  button.primario{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600;min-width:6.5rem}
  button:disabled{opacity:0.45;cursor:not-allowed}
  input[type=range]{width:9rem;accent-color:var(--accent)}
  .check{display:flex;align-items:center;gap:0.4rem;font-size:0.88rem;color:var(--ink-soft);cursor:pointer}

  .corpo{display:grid;grid-template-columns:minmax(0,1fr) 17rem;gap:1.2rem;align-items:start}
  @media (max-width:60rem){.corpo{grid-template-columns:1fr}}

  .palco{background:var(--surface);border:1px solid var(--rule);border-radius:8px;
         padding:1rem;overflow:auto}
  .grade{display:inline-grid;gap:1px;background:var(--rule);padding:1px;border-radius:4px}
  .cel{width:var(--cel,22px);height:var(--cel,22px);display:flex;align-items:center;justify-content:center;
       font-family:var(--mono);font-size:calc(var(--cel,22px)*0.55);font-weight:600;
       color:var(--ink);background:var(--chao);position:relative}
  .p{background:var(--parede);color:transparent}
  .o{background:var(--chao);color:var(--chao-b)}
  .S{background:var(--inicio)} .G{background:var(--saida)}
  .m{background:var(--lama)} .w{background:var(--agua)}
  .k{background:var(--chave)} .d{background:var(--porta)}
  .e{background:var(--esteira)} .b{background:var(--bonus)} .f{background:var(--fonte)}
  .fora{opacity:0.22}
  .trilha::after{content:"";position:absolute;inset:18%;border-radius:50%;
                 background:var(--trilha);opacity:0.5}
  .armadilha{box-shadow:inset 0 0 0 2px var(--armadilha)}
  .atual{box-shadow:inset 0 0 0 3px var(--ink);z-index:2}
  .atual::before{content:"";position:absolute;inset:26%;border-radius:50%;background:var(--ink)}

  aside{display:flex;flex-direction:column;gap:0.9rem}
  .caixa{background:var(--surface);border:1px solid var(--rule);border-radius:8px;padding:0.9rem 1rem}
  .caixa h2{font-family:var(--mono);font-size:0.7rem;letter-spacing:0.1em;text-transform:uppercase;
            color:var(--muted);margin:0 0 0.6rem}
  .linha{display:flex;justify-content:space-between;gap:0.8rem;font-size:0.9rem;padding:0.18rem 0}
  .linha span:first-child{color:var(--muted)}
  .linha span:last-child{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right}
  .rotulo{font-family:var(--mono);font-size:0.95rem;font-weight:600;color:var(--accent);
          word-break:break-all;padding:0.3rem 0 0.5rem}
  .aviso{background:var(--warn-bg);color:var(--warn);border-radius:6px;padding:0.6rem 0.8rem;
         font-size:0.86rem}
  .legenda{display:flex;flex-wrap:wrap;gap:0.3rem 0.8rem;font-size:0.78rem;color:var(--muted)}
  .legenda i{width:0.8rem;height:0.8rem;border-radius:2px;display:inline-block;
             border:1px solid var(--rule);vertical-align:-0.1em;margin-right:0.25rem}
  .barra{height:4px;background:var(--rule);border-radius:2px;overflow:hidden;margin-top:0.5rem}
  .barra i{display:block;height:100%;background:var(--accent);width:0%}
  @media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="wrap">
  <header>
    <h1>Labirinto Interativo</h1>
    <p class="sub">Projeto Final — Teoria dos Grafos 2026.2 · percurso animado sobre o grafo de estados</p>
  </header>

  <div class="painel">
    <div class="campo"><label for="mapa">mapa</label><select id="mapa"></select></div>
    <div class="campo"><label for="alg">algoritmo</label><select id="alg"></select></div>
    <div class="campo"><label for="camada">camada</label><select id="camada"></select></div>
    <div class="campo"><label>&nbsp;</label>
      <div style="display:flex;gap:0.4rem">
        <button id="inicio" title="voltar ao inicio">|&#9664;</button>
        <button id="voltar" title="um passo atras">◀</button>
        <button id="tocar" class="primario">▶ Tocar</button>
        <button id="avancar" title="um passo a frente">▶</button>
        <button id="fim" title="ir para o fim">&#9654;|</button>
      </div>
    </div>
    <div class="campo"><label for="vel">velocidade · <span id="velTxt">2</span> passos/s</label>
      <input type="range" id="vel" min="1" max="12" value="2"></div>
    <div class="campo"><label>&nbsp;</label>
      <label class="check"><input type="checkbox" id="armad"> realçar armadilhas</label></div>
    <div class="campo"><label>&nbsp;</label>
      <label class="check"><input type="checkbox" id="trilhaOn" checked> mostrar trilha</label></div>
    <div class="campo"><label for="zoom">zoom</label>
      <input type="range" id="zoom" min="10" max="40" value="22"></div>
  </div>

  <div class="corpo">
    <div class="palco"><div class="grade" id="grade"></div></div>

    <aside>
      <div class="caixa">
        <h2>estado atual</h2>
        <div class="rotulo" id="rotulo">—</div>
        <div class="linha"><span>posição</span><span id="pos">—</span></div>
        <div class="linha"><span>chaves</span><span id="chaves">—</span></div>
        <div class="linha"><span>bônus consumidos</span><span id="bonus">—</span></div>
        <div class="linha"><span>custo acumulado</span><span id="custo">—</span></div>
        <div class="linha"><span>passo</span><span id="passo">—</span></div>
        <div class="barra"><i id="progresso"></i></div>
      </div>

      <div class="caixa">
        <h2>percurso</h2>
        <div class="linha"><span>algoritmo</span><span id="algInfo">—</span></div>
        <div class="linha"><span>passos</span><span id="totPassos">—</span></div>
        <div class="linha"><span>custo total</span><span id="totCusto">—</span></div>
        <div id="semSolucao"></div>
      </div>

      <div class="caixa">
        <h2>o grafo deste mapa</h2>
        <div class="linha"><span>estados (ordem)</span><span id="mOrdem">—</span></div>
        <div class="linha"><span>arcos (tamanho)</span><span id="mTam">—</span></div>
        <div class="linha"><span>densidade</span><span id="mDens">—</span></div>
        <div class="linha"><span>teto teórico</span><span id="mTeto">—</span></div>
        <div class="linha"><span>taxa de ocupação</span><span id="mOcup">—</span></div>
        <div class="linha"><span>estados-armadilha</span><span id="mArm">—</span></div>
      </div>

      <div class="caixa">
        <h2>legenda</h2>
        <div class="legenda">
          <span><i style="background:var(--parede)"></i>parede</span>
          <span><i style="background:var(--chao)"></i>chão 1</span>
          <span><i style="background:var(--lama)"></i>lama 3</span>
          <span><i style="background:var(--agua)"></i>água 5</span>
          <span><i style="background:var(--chave)"></i>chave</span>
          <span><i style="background:var(--porta)"></i>porta</span>
          <span><i style="background:var(--esteira)"></i>esteira</span>
          <span><i style="background:var(--bonus)"></i>bônus −4</span>
          <span><i style="background:var(--fonte)"></i>fonte −2</span>
          <span><i style="background:var(--inicio)"></i>início</span>
          <span><i style="background:var(--saida)"></i>saída</span>
        </div>
      </div>
    </aside>
  </div>
</div>

<script>
const DADOS = __DADOS__;

const CLASSE = {"#":"p",".":"o","S":"S","G":"G",",":"m","~":"w","+":"b","*":"f",
                ">":"e","<":"e","^":"e","v":"e"};
function classeDe(ch){
  if (CLASSE[ch]) return CLASSE[ch];
  if ("abcd".includes(ch)) return "k";
  if ("ABCD".includes(ch)) return "d";
  return "o";
}

const $ = id => document.getElementById(id);
let mapaAtual=null, passos=[], i=0, tocando=false, timer=null, celulas=[];

function montarSelects(){
  $("mapa").innerHTML = Object.keys(DADOS).sort()
    .map(n=>`<option value="${n}">${n}</option>`).join("");
  trocarMapa();
}

function trocarMapa(){
  mapaAtual = DADOS[$("mapa").value];
  const algs = Object.keys(mapaAtual.percursos);
  $("alg").innerHTML = algs.length
    ? algs.sort().map(a=>`<option value="${a}">${a}</option>`).join("")
    : `<option value="">(nenhum disponível)</option>`;
  const cam = Object.keys(mapaAtual.camadas);
  $("camada").innerHTML = `<option value="">todas</option>` +
    cam.map(c=>`<option value="${c}">${c}</option>`).join("");
  desenharGrade();
  metricas();
  trocarAlg();
}

function desenharGrade(){
  const g = $("grade");
  g.style.gridTemplateColumns = `repeat(${mapaAtual.colunas}, var(--cel, 22px))`;
  g.innerHTML = "";
  celulas = [];
  for (let l=0; l<mapaAtual.linhas; l++){
    const linha = [];
    for (let c=0; c<mapaAtual.colunas; c++){
      const ch = mapaAtual.grade[l][c];
      const d = document.createElement("div");
      d.className = "cel " + classeDe(ch);
      d.textContent = ch === "#" ? "" : ch;
      d.title = `(${l},${c}) ${ch}`;
      g.appendChild(d);
      linha.push(d);
    }
    celulas.push(linha);
  }
}

function metricas(){
  const m = mapaAtual.metricas;
  $("mOrdem").textContent = m.ordem;
  $("mTam").textContent = m.tamanho;
  $("mDens").textContent = m.densidade.toFixed(5);
  $("mTeto").textContent = m.teto;
  $("mOcup").textContent = m.teto ? (100*m.ordem/m.teto).toFixed(1)+"%" : "—";
  $("mArm").textContent = mapaAtual.armadilhas.length;
}

function trocarAlg(){
  parar();
  const a = $("alg").value;
  const p = mapaAtual.percursos[a];
  $("semSolucao").innerHTML = "";
  if (!p || p.status !== "OK"){
    passos = [];
    $("algInfo").textContent = a || "—";
    $("totPassos").textContent = "—";
    $("totCusto").textContent = "—";
    if (p && p.status === "SEM_SOLUCAO")
      $("semSolucao").innerHTML = `<div class="aviso">Este algoritmo não encontrou caminho até o ALVO neste mapa.</div>`;
    if (p && p.status === "CICLO_NEGATIVO")
      $("semSolucao").innerHTML = `<div class="aviso"><b>Ciclo negativo detectado.</b> Não existe custo mínimo neste mapa: dá para repetir o ciclo abaixo indefinidamente e o custo cai para −∞.<br><br><span style="font-family:var(--mono);font-size:0.78rem;word-break:break-all">`
        + p.ciclo.join(" → ") + `</span></div>`;
  } else {
    passos = p.passos;
    $("algInfo").textContent = a;
    $("totPassos").textContent = p.n_passos;
    $("totCusto").textContent = p.custo;
  }
  i = 0;
  render();
}

function render(){
  // limpa marcacoes
  for (const linha of celulas) for (const d of linha)
    d.classList.remove("trilha","atual","armadilha","fora");

  // camada selecionada: apaga o que nao existe nela
  const cam = $("camada").value;
  if (cam){
    const dentro = new Set(mapaAtual.camadas[cam].map(([l,c])=>l+","+c));
    for (let l=0;l<mapaAtual.linhas;l++) for (let c=0;c<mapaAtual.colunas;c++)
      if (mapaAtual.grade[l][c] !== "#" && !dentro.has(l+","+c))
        celulas[l][c].classList.add("fora");
  }

  // armadilhas
  if ($("armad").checked)
    for (const [l,c,ch] of mapaAtual.armadilhas)
      if (!cam || ch === cam) celulas[l][c].classList.add("armadilha");

  if (!passos.length){
    $("rotulo").textContent = "—";
    ["pos","chaves","bonus","custo","passo"].forEach(k=>$(k).textContent="—");
    $("progresso").style.width = "0%";
    return;
  }

  // trilha ate o passo atual
  if ($("trilhaOn").checked)
    for (let k=0;k<=i;k++){
      const e = passos[k];
      celulas[e.l][e.c].classList.add("trilha");
    }

  const e = passos[i];
  celulas[e.l][e.c].classList.add("atual");

  $("rotulo").textContent = e.rotulo;
  $("pos").textContent = `(${e.l}, ${e.c})`;
  $("chaves").textContent = e.chaves || "—";
  $("bonus").textContent = e.bonus.length ? "{"+e.bonus.join(",")+"}" : "{}";
  $("custo").textContent = e.custo;
  $("passo").textContent = `${i} / ${passos.length-1}`;
  $("progresso").style.width = (100*i/Math.max(1,passos.length-1))+"%";
}

function ir(n){ if(!passos.length) return; i = Math.max(0, Math.min(passos.length-1, n)); render(); }
function parar(){ tocando=false; clearInterval(timer); $("tocar").textContent="▶ Tocar"; }
function tocar(){
  if (!passos.length) return;
  if (tocando){ parar(); return; }
  if (i >= passos.length-1) i = 0;
  tocando = true; $("tocar").textContent="⏸ Pausar";
  clearInterval(timer);
  timer = setInterval(()=>{
    if (i >= passos.length-1){ parar(); return; }
    i++; render();
  }, 1000/Number($("vel").value));
}

$("mapa").onchange = trocarMapa;
$("alg").onchange = trocarAlg;
$("camada").onchange = render;
$("armad").onchange = render;
$("trilhaOn").onchange = render;
$("tocar").onclick = tocar;
$("avancar").onclick = ()=>{parar(); ir(i+1);};
$("voltar").onclick  = ()=>{parar(); ir(i-1);};
$("inicio").onclick  = ()=>{parar(); ir(0);};
$("fim").onclick     = ()=>{parar(); ir(passos.length-1);};
$("vel").oninput = e => { $("velTxt").textContent = e.target.value; if (tocando){ parar(); tocar(); } };
$("zoom").oninput = e => document.documentElement.style.setProperty("--cel", e.target.value+"px");
document.addEventListener("keydown", ev=>{
  if (ev.key === "ArrowRight"){ parar(); ir(i+1); }
  if (ev.key === "ArrowLeft"){ parar(); ir(i-1); }
  if (ev.key === " "){ ev.preventDefault(); tocar(); }
});

montarSelects();
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


if __name__ == "__main__":
    alvos = sys.argv[1:] or None
    destino, dados = gerar_html(alvos)
    tamanho = os.path.getsize(destino) / 1024
    print(f"gerado: {destino}  ({tamanho:.0f} KB)")
    print(f"mapas : {len(dados)}")
    print(f"algoritmos disponiveis: {', '.join(sorted(ALGORITMOS)) or '(nenhum)'}")
