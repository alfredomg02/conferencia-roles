"""Gera index.html — painel operacional Uhull. Views: Swim Lane | Diagrama UML."""
from __future__ import annotations
import json, re
from datetime import date
from pathlib import Path
from collections import defaultdict
from html import escape as esc

BASE   = Path(__file__).parent
INPUT  = BASE / "checklists-extraidos.md"
OUTPUT = BASE / "index.html"

ROLE_ORDER = [
    "Comercial","Relacionamento","Operações","Terrestre","Aéreo",
    "Marketing","Planejamento","Planner","Concierge","Produção",
    "Financeiro","Cultura","Coordenadores","Todos","ADM","Não Definido",
]
ROLE_COLOR = {
    "Comercial":"#c62828","Relacionamento":"#ad1457","Operações":"#2e7d32",
    "Terrestre":"#388e3c","Aéreo":"#1565c0","Marketing":"#6a1b9a",
    "Planejamento":"#e65100","Planner":"#bf360c","Concierge":"#00695c",
    "Produção":"#558b2f","Financeiro":"#f57f17","Cultura":"#4caf50",
    "Coordenadores":"#546e7a","Todos":"#78909c","ADM":"#455a64",
    "Não Definido":"#9e9e9e",
}
FLOW_COLORS = ["#c62828","#ad1457","#1565c0","#2e7d32","#6a1b9a"]

_CANON = {
    "comercial":"Comercial","relacionamento":"Relacionamento","relacionamentoo":"Relacionamento",
    "operações":"Operações","operacoes":"Operações","operação":"Operações","terrestre":"Terrestre",
    "aéreo":"Aéreo","aereo":"Aéreo","marketing":"Marketing","planejamento":"Planejamento",
    "planner":"Planner","concierge":"Concierge","produção":"Produção","producao":"Produção",
    "financeiro":"Financeiro","cultura":"Cultura","coordenadores":"Coordenadores",
    "coordenador":"Coordenadores","todos":"Todos","todo":"Todos",
    "belezura":"Planejamento","adm":"ADM","plataforma":"Não Definido","gestora":"Não Definido",
}

def normalize_roles(raw):
    raw = re.sub(r"\[.*?\]|\(.*?\)","",raw).strip()
    if not raw or raw in ("-","—"): return ["Não Definido"]
    parts = re.split(r"\s*/\s*|\s*,\s*|\s*\+\s*|\s+e\s+", raw, flags=re.IGNORECASE)
    r = [_CANON.get(p.strip().lower().rstrip("."), p.strip()) for p in parts if p.strip()]
    return r or ["Não Definido"]

def parse(path):
    text   = path.read_text(encoding="utf-8")
    chunks = re.split(r"(?m)^## (Fluxo .+)$", text)
    flows  = []
    for i in range(1, len(chunks), 2):
        name  = chunks[i].strip()
        body  = chunks[i+1]
        fid   = re.sub(r"\W+","_",name.lower()).strip("_")
        color = FLOW_COLORS[len(flows) % len(FLOW_COLORS)]
        steps, data = [], defaultdict(lambda: defaultdict(list))
        for line in body.splitlines():
            if not line.startswith("|"): continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) < 3: continue
            etapa, tarefa, resp = cells[0], cells[1], cells[2]
            if etapa in ("Etapa","") or "---" in etapa or not tarefa or "---" in tarefa: continue
            tarefa = re.sub(r"\*+","",tarefa).strip()
            if etapa not in steps: steps.append(etapa)
            for role in normalize_roles(resp): data[etapa][role].append(tarefa)
        flows.append(dict(id=fid,name=name,color=color,steps=steps,data=data))
    return flows

def roles_in_flow(flow):
    seen = set(r for sd in flow["data"].values() for r in sd)
    ordered = [r for r in ROLE_ORDER if r in seen]
    for r in sorted(seen):
        if r not in ordered: ordered.append(r)
    return ordered

def hex_mix(color, alpha):
    r,g,b = int(color[1:3],16),int(color[3:5],16),int(color[5:7],16)
    return f"#{int(r*alpha+255*(1-alpha)):02x}{int(g*alpha+255*(1-alpha)):02x}{int(b*alpha+255*(1-alpha)):02x}"

def task_count(flow):
    return sum(len(t) for sd in flow["data"].values() for t in sd.values())

# ── Swim Lane ─────────────────────────────────────────────────────────────────
def li_html(task):
    return (
        f'<li data-input="" data-output="" data-role="" draggable="true">'
        f'<span class="task-drag-handle" title="Arrastar">&#8942;</span>'
        f'<span class="task-text" contenteditable="true" spellcheck="false">{esc(task)}</span>'
        f'<button class="btn-info" title="Detalhes" onclick="openTaskPanel(this.closest(\'li\'))">i</button>'
        f'<button class="btn-del" onclick="this.closest(\'li\').remove()">&#215;</button>'
        f'</li>'
    )

def build_section(flow, fi):
    color,roles,steps,data = flow["color"],roles_in_flow(flow),flow["steps"],flow["data"]
    label,n = flow["name"].split(" — ",1)[-1], task_count(flow)
    hdrs = ['<th class="role-col sticky-corner">Papel</th>'] + [
        f'<th class="step-col"><span contenteditable="true" spellcheck="false">{esc(s)}</span></th>'
        for s in steps
    ]
    rows = []
    for role in roles:
        rc,rbg = ROLE_COLOR.get(role,"#888"), hex_mix(ROLE_COLOR.get(role,"#888"),0.06)
        cells  = [
            f'<td class="role-name" style="border-left:4px solid {rc};background:{rbg};color:{rc}">'
            f'<span contenteditable="true" spellcheck="false">{esc(role)}</span></td>'
        ]
        for step in steps:
            tasks = data[step].get(role,[])
            if tasks:
                cells.append(
                    f'<td class="task-cell active" style="border-top:3px solid {hex_mix(rc,0.35)}">'
                    f'<ul>{"".join(li_html(t) for t in tasks)}</ul>'
                    f'<button class="btn-add" onclick="addTask(this)">+ tarefa</button></td>'
                )
            else:
                cells.append(
                    f'<td class="task-cell empty">'
                    f'<button class="btn-add" onclick="addTask(this)">+ tarefa</button></td>'
                )
        rows.append(f'<tr data-role="{esc(role)}">{"".join(cells)}</tr>')
    return (
        f'<section class="flow-section" id="{flow["id"]}">'
        f'<div class="flow-hd" style="background:{color}">'
        f'<div><span class="flow-num">Fluxo {fi}</span>'
        f'<h2 contenteditable="true" spellcheck="false">{esc(label)}</h2></div>'
        f'<div class="flow-stats">{len(steps)} etapas &#183; {n} tarefas</div></div>'
        f'<div class="tbl-wrap"><table class="swimlane">'
        f'<thead><tr>{"".join(hdrs)}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div></section>'
    )

# ── Diagram UML ───────────────────────────────────────────────────────────────
def build_diag_node(flow, step, node_id):
    color,data,roles = flow["color"],flow["data"],roles_in_flow(flow)
    tasks_data, groups = {}, []
    for role in roles:
        rt = data[step].get(role,[])
        if not rt: continue
        tasks_data[role] = rt
        rc    = ROLE_COLOR.get(role,"#888")
        items = "".join(f'<li>{esc(t)}</li>' for t in rt)
        groups.append(
            f'<div class="dn-rg" data-role="{esc(role)}">'
            f'<div class="dn-rg-hd"><span class="dn-dot" style="background:{rc}"></span>'
            f'<span class="dn-rname">{esc(role)}</span>'
            f'<span class="dn-rcnt">{len(rt)}</span></div>'
            f'<ul class="dn-tasks">{items}</ul></div>'
        )
    total      = sum(len(v) for v in tasks_data.values())
    tasks_attr = json.dumps(tasks_data, ensure_ascii=False).replace('"','&quot;')
    body       = "".join(groups) if groups else '<p class="dn-empty">Sem tarefas</p>'
    return (
        f'<div class="diag-node" id="{node_id}" draggable="true" data-flow="{flow["id"]}" '
        f'data-step="{esc(step)}" data-tasks="{tasks_attr}" data-color="{color}">'
        f'<span class="dn-handle dn-hl" onmousedown="startConn(event,this)"></span>'
        f'<div class="dn-hd" style="background:{color}">'
        f'<span class="dn-grip" title="Arrastar para reposicionar">&#8942;&#8942;</span>'
        f'<span class="dn-title" contenteditable="true" spellcheck="false">{esc(step)}</span>'
        f'<span class="dn-badge">{total}</span></div>'
        f'<div class="dn-body">{body}</div>'
        f'<div class="dn-ft"><button class="btn-dn-edit" '
        f'onclick="openStagePanel(this.closest(\'.diag-node\'))">&#9998; Editar</button></div>'
        f'<span class="dn-handle dn-hr" onmousedown="startConn(event,this)"></span></div>'
    )

def build_taskflow_diagram(flow, fid):
    color, steps, data = flow["color"], flow["steps"], flow["data"]
    nodes = []
    idx = 0
    for step in steps:
        nodes.append(
            f'<div class="diag-stage-sep" data-flow="{fid}">'
            f'<span style="background:{color}">{esc(step)}</span>'
            f'</div>'
        )
        for role in roles_in_flow(flow):
            rc = ROLE_COLOR.get(role, "#888")
            for task in data[step].get(role, []):
                nid = f"dtn-{fid}-{idx}"
                nodes.append(
                    f'<div class="diag-node diag-task-node" id="{nid}" draggable="true"'
                    f' data-flow="{fid}" data-step="{esc(step)}" data-role="{esc(role)}">'
                    f'<span class="dn-handle dn-hl" onmousedown="startConn(event,this)"></span>'
                    f'<div class="dn-hd" style="background:{rc}">'
                    f'<span class="dn-grip">&#8942;&#8942;</span>'
                    f'<span class="dn-title">{esc(role)}</span>'
                    f'</div>'
                    f'<div class="dn-body dtn-body">'
                    f'<p class="dtn-task">{esc(task)}</p>'
                    f'<div class="dtn-io">'
                    f'<div class="dtn-row"><span class="dtn-lbl dtn-in-lbl">&#8595; In</span>'
                    f'<span class="dtn-val" contenteditable="true" spellcheck="false" data-ph="input..."></span></div>'
                    f'<div class="dtn-row"><span class="dtn-lbl dtn-out-lbl">&#8593; Out</span>'
                    f'<span class="dtn-val" contenteditable="true" spellcheck="false" data-ph="output..."></span></div>'
                    f'</div></div>'
                    f'<span class="dn-handle dn-hr" onmousedown="startConn(event,this)"></span>'
                    f'</div>'
                )
                idx += 1
    return (
        f'<div class="diag-canvas diag-task-canvas" id="dtc-{fid}" data-color="{color}" data-conns="[]">'
        f'<svg class="diag-svg" id="dts-{fid}"></svg>'
        f'<div class="diag-row" id="dtr-{fid}">{"".join(nodes)}</div>'
        f'</div>'
    )

def build_diag_section(flow, fi):
    fid,color,steps = flow["id"],flow["color"],flow["steps"]
    label,n = flow["name"].split(" — ",1)[-1], task_count(flow)
    nodes = "".join(build_diag_node(flow, s, f"dn-{fid}-{i}") for i,s in enumerate(steps))
    add_btn = (
        f'<button class="btn-add-stage" onclick="addStage(\'{fid}\',\'{color}\')">'
        f'<span>+</span>Etapa</button>'
    )
    sub_toggle = (
        f'<div class="diag-sub-toggle">'
        f'<button class="btn-dsub active" data-sub="etapas" '
        f'onclick="setDiagSub(\'{fid}\',\'etapas\',this)">Etapas</button>'
        f'<button class="btn-dsub" data-sub="tarefas" '
        f'onclick="setDiagSub(\'{fid}\',\'tarefas\',this)">Tarefas</button>'
        f'</div>'
    )
    taskflow = build_taskflow_diagram(flow, fid)
    return (
        f'<section class="diagram-section" id="diag-{fid}">'
        f'<div class="flow-hd" style="background:{color}">'
        f'<div><span class="flow-num">Fluxo {fi}</span>'
        f'<h2 contenteditable="true" spellcheck="false">{esc(label)}</h2></div>'
        f'<div style="display:flex;align-items:center;gap:16px">'
        f'{sub_toggle}'
        f'<span class="flow-stats">{len(steps)} etapas &#183; {n} tarefas</span>'
        f'</div></div>'
        f'<div class="diag-canvas" id="dc-{fid}" data-color="{color}" data-conns="[]">'
        f'<svg class="diag-svg" id="ds-{fid}"></svg>'
        f'<div class="diag-row" id="dr-{fid}">{nodes}{add_btn}</div>'
        f'</div>'
        f'{taskflow}'
        f'</section>'
    )

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Montserrat:wght@700;800;900&display=swap');

:root{
  --pri:#B80457;--pri-d:#8B0340;--pri-l:#E0185F;--pri-xl:#FDEEF4;
  --acc:#F7A800;--acc-d:#E09500;
  --bg:#F5F3F8;--sur:#FFFFFF;--bdr:#F0D8E4;
  --txt:#1C1A2E;--mut:#6B6585;--fnt:#B0AACC;
  --r:10px;
  --s1:0 1px 4px rgba(184,4,87,.08);
  --s2:0 4px 18px rgba(184,4,87,.12);
  --s3:0 10px 40px rgba(184,4,87,.18);
  --ff:'Inter',system-ui,sans-serif;
  --ffh:'Montserrat','Inter',sans-serif;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--ff);font-size:12px;background:var(--bg);color:var(--txt);line-height:1.5}
[contenteditable]:focus{outline:none}
a{text-decoration:none}

/* ── Cover ── */
.cover{
  background:linear-gradient(135deg,#7a022e 0%,#B80457 60%,#e0186c 100%);
  color:#fff;padding:28px 40px 0;position:relative;overflow:hidden}
.cover::after{content:'';position:absolute;right:-60px;top:-60px;
  width:260px;height:260px;border-radius:50%;
  background:radial-gradient(circle,rgba(247,168,0,.18) 0%,transparent 70%);pointer-events:none}
.cover h1{font-family:var(--ffh);font-size:24px;font-weight:900;
  letter-spacing:-.5px;line-height:1.1}
.cover .meta{font-size:11px;opacity:.7;margin-top:4px;font-weight:500}
.legend{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px;padding-bottom:16px;
  position:relative;z-index:1}
.leg{display:flex;align-items:center;gap:5px;font-size:10px;font-weight:600;cursor:pointer;
  background:rgba(255,255,255,.13);padding:4px 10px;border-radius:20px;
  border:1px solid rgba(255,255,255,.18);transition:all .18s;letter-spacing:.1px}
.leg:hover{background:rgba(255,255,255,.26);border-color:rgba(255,255,255,.35);
  transform:translateY(-1px)}
.leg.rf-on{background:rgba(255,255,255,.32);border-color:rgba(255,255,255,.7);
  box-shadow:0 0 0 2px rgba(255,255,255,.35);transform:translateY(-1px)}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}

/* ── Nav wrapper — sticky, sem sombra de separação do cover ── */
.nav-wrap{position:sticky;top:0;z-index:200}
.toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  padding:7px 22px;border-bottom:none;background:var(--bg);
  box-shadow:none}
.nav-logo{height:28px;width:auto;display:block;flex-shrink:0;margin-right:8px}
.view-toggle{display:flex;gap:6px}
.btn-view{padding:5px 16px;border:1.5px solid #B80457;border-radius:6px;font-size:11px;
  font-weight:700;cursor:pointer;background:transparent;color:#B80457;
  font-family:var(--ff);transition:all .15s;letter-spacing:.1px}
.btn-view:hover:not(.active){background:rgba(184,4,87,.07)}
.btn-view.active{background:#B80457;color:#fff;border-color:#B80457;
  box-shadow:0 2px 8px rgba(184,4,87,.25)}
.toolbar-actions{display:flex;gap:6px;margin-left:auto}
.btn-action{padding:6px 14px;border-radius:8px;border:none;cursor:pointer;
  font-size:11px;font-weight:700;letter-spacing:.2px;font-family:var(--ff);
  transition:filter .15s,transform .12s}
.btn-action:active{transform:scale(.96)}
.btn-action:hover{filter:brightness(.9)}
.btn-pdf{background:#1565c0;color:#fff}
.btn-save{background:#2e7d32;color:#fff}
.btn-roles{background:var(--pri);color:#fff}

/* ── Tab bar ── */
.tab-bar{display:flex;align-items:flex-end;gap:2px;padding:0 22px;overflow-x:auto;
  background:var(--bg)}
.tab-bar::-webkit-scrollbar{height:0}
.flow-tab{display:flex;align-items:center;gap:7px;
  padding:9px 18px 11px;border-radius:9px 9px 0 0;
  border:1.5px solid var(--bdr);border-bottom:none;
  background:var(--sur);cursor:pointer;font-family:var(--ff);
  white-space:nowrap;transition:background .18s,border-color .18s,color .18s;
  color:var(--mut)}
.flow-tab:hover:not(.active){border-color:var(--tc);color:var(--tc);
  background:var(--sur)}
.flow-tab.active{background:var(--tc);color:#fff;border-color:var(--tc);
  box-shadow:0 -2px 10px rgba(0,0,0,.12)}
.tab-num{font-size:9px;font-weight:900;opacity:.65;letter-spacing:.5px;line-height:1}
.tab-lbl{font-size:11px;font-weight:700;letter-spacing:.1px}
.btn-add-flow{display:flex;align-items:center;gap:5px;align-self:flex-end;
  padding:9px 14px 11px;border-radius:9px 9px 0 0;border:1.5px dashed var(--bdr);
  border-bottom:none;background:transparent;cursor:pointer;font-family:var(--ff);
  font-size:10px;font-weight:700;color:var(--mut);margin-left:4px;
  transition:all .18s;white-space:nowrap}
.btn-add-flow:hover{border-color:var(--pri);color:var(--pri);background:var(--pri-xl)}

/* ── Section visibility (tab-controlled) ── */
.flow-section,.diagram-section{display:none}
.flow-section.tab-vis,.diagram-section.tab-vis{display:block}

/* ── Flow wrappers ── */
.flow-section,.diagram-section{margin:0 22px 18px;border-radius:0 0 var(--r) var(--r);
  overflow:hidden;box-shadow:var(--s1);border:1px solid var(--bdr);border-top:none}
.flow-hd{display:flex;justify-content:space-between;align-items:center;
  padding:14px 22px;color:#fff}
.flow-hd h2{font-family:var(--ffh);font-size:14px;font-weight:800;
  display:inline;letter-spacing:-.2px}
.flow-hd h2:focus{outline:2px dashed rgba(255,255,255,.5);border-radius:3px}
.flow-num{font-size:9px;font-weight:700;opacity:.6;text-transform:uppercase;
  letter-spacing:1.5px;display:block;margin-bottom:3px}
.flow-stats{font-size:10px;opacity:.72;white-space:nowrap;font-weight:500}

/* ── Swim Lane ── */
.tbl-wrap{overflow:auto;max-height:calc(100vh - 190px);background:var(--sur)}
table.swimlane{border-collapse:collapse;width:100%}
thead th{position:sticky;top:0;z-index:2;background:#FAF8FD;border:1px solid var(--bdr);
  padding:9px 13px;font-size:10px;font-weight:700;text-align:left;vertical-align:middle;
  min-width:175px;max-width:260px;color:var(--mut);text-transform:uppercase;
  letter-spacing:.5px;font-family:var(--ff)}
thead th span[contenteditable]{display:block}
thead th span:focus{outline:2px solid var(--pri);border-radius:2px}
th.role-col,td.role-name{position:sticky;left:0;z-index:1}
th.sticky-corner{z-index:3;min-width:115px;max-width:130px}
td.role-name{font-weight:700;font-size:10px;padding:9px 13px;white-space:nowrap;
  vertical-align:top;border-right:1px solid var(--bdr);
  text-transform:uppercase;letter-spacing:.4px;background:var(--sur)}
td.task-cell{padding:8px 11px;vertical-align:top;
  border:1px solid #EDE8F5;transition:background .12s}
td.task-cell.empty{background:#FAF8FD}
td.task-cell.active{background:var(--sur)}
td.task-cell ul{list-style:none;padding:0}
td.task-cell li{margin-bottom:6px;display:flex;align-items:flex-start;
  gap:5px;line-height:1.35}
td.task-cell li::before{content:"\\2022";flex-shrink:0;margin-top:2px;
  font-size:9px;color:var(--fnt)}
.task-text{flex:1;outline:none;font-size:11px;font-family:var(--ff)}
.task-text:focus{background:#FFF8E7;border-radius:3px;
  outline:1px solid var(--acc);padding:0 2px}
.btn-del{flex-shrink:0;background:none;border:none;cursor:pointer;color:var(--fnt);
  font-size:14px;line-height:1;padding:0;opacity:0;transition:opacity .15s,color .15s}
li:hover .btn-del{opacity:1}
.btn-del:hover{color:#e53e3e}
.btn-info{flex-shrink:0;background:none;border:1px solid currentColor;border-radius:50%;
  cursor:pointer;color:var(--fnt);font-size:8px;font-weight:700;font-style:italic;
  width:13px;height:13px;line-height:1;padding:0;display:inline-flex;
  align-items:center;justify-content:center;opacity:0;
  transition:opacity .15s,color .15s;margin-top:2px}
li:hover .btn-info{opacity:1}
.btn-info:hover{color:var(--pri);border-color:var(--pri)}
li.has-meta .btn-info{opacity:.6;color:var(--pri);border-color:var(--pri)}
.btn-add{display:block;margin-top:7px;padding:4px 9px;font-size:10px;font-weight:600;
  cursor:pointer;background:transparent;border:1.5px dashed var(--bdr);
  border-radius:6px;color:var(--fnt);width:100%;text-align:left;
  transition:all .15s;opacity:0;font-family:var(--ff)}
td.task-cell:hover .btn-add{opacity:1}
.btn-add:hover{background:var(--pri-xl);color:var(--pri);border-color:var(--pri-l)}
tr:hover td.task-cell{background:#FAF8FD!important}
tr:hover td.role-name{filter:brightness(.97)}
.tbl-wrap::-webkit-scrollbar{width:5px;height:5px}
.tbl-wrap::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px}

/* ── Diagram UML ── */
.diag-canvas{position:relative;overflow:auto;background:#FAF8FD;
  background-image:radial-gradient(var(--bdr) 1px,transparent 1px);
  background-size:22px 22px;min-height:220px}
.diag-svg{position:absolute;top:0;left:0;pointer-events:none;z-index:1;overflow:visible}
.diag-row{display:flex;align-items:flex-start;gap:72px;padding:44px 40px;
  position:relative;z-index:2;width:max-content}
.diag-node{position:relative;width:220px;border:1px solid var(--bdr);
  border-radius:var(--r);background:var(--sur);box-shadow:var(--s1);
  flex-shrink:0;transition:box-shadow .2s,transform .15s}
.diag-node:hover{box-shadow:var(--s2);transform:translateY(-2px)}
.diag-node.dn-sel{outline:2px solid var(--pri);outline-offset:2px}
.diag-node.dn-dragging{opacity:.33;transform:scale(.96)}
.diag-node.dn-drop-left{box-shadow:-4px 0 0 0 var(--pri),var(--s2)}
.diag-node.dn-drop-right{box-shadow:4px 0 0 0 var(--pri),var(--s2)}
.dn-hd{padding:10px 12px;border-radius:var(--r) var(--r) 0 0;
  display:flex;justify-content:space-between;align-items:center;gap:6px}
.dn-grip{font-size:13px;color:rgba(255,255,255,.5);cursor:grab;line-height:1;
  user-select:none;flex-shrink:0;letter-spacing:-3px;padding-right:2px;
  transition:color .15s}
.dn-grip:hover{color:rgba(255,255,255,.9)}
.dn-grip:active{cursor:grabbing}
.dn-title{font-size:11px;font-weight:700;color:#fff;line-height:1.3;flex:1;
  font-family:var(--ffh)}
.dn-title:focus{background:rgba(255,255,255,.15);border-radius:3px;padding:0 3px}
.dn-badge{font-size:9px;background:rgba(255,255,255,.22);padding:2px 6px;
  border-radius:20px;color:#fff;white-space:nowrap;font-weight:700}
.dn-body{padding:9px 12px;max-height:220px;overflow-y:auto;border-top:1px solid var(--bdr)}
.dn-body::-webkit-scrollbar{width:3px}
.dn-body::-webkit-scrollbar-thumb{background:var(--bdr)}
.dn-rg+.dn-rg{margin-top:8px;padding-top:8px;border-top:1px dashed #EDE8F5}
.dn-rg-hd{display:flex;align-items:center;gap:5px;margin-bottom:4px}
.dn-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.dn-rname{font-size:9px;font-weight:700;text-transform:uppercase;
  letter-spacing:.5px;color:var(--mut);flex:1}
.dn-rcnt{font-size:9px;color:var(--fnt);background:var(--bg);
  padding:1px 5px;border-radius:20px;font-weight:600}
.dn-tasks{list-style:none;padding:0;margin:0}
.dn-tasks li{font-size:10px;color:#4a5568;padding:2px 0 2px 10px;
  position:relative;line-height:1.35}
.dn-tasks li::before{content:"\\2022";position:absolute;left:1px;
  color:var(--fnt);font-size:9px}
.dn-empty{font-size:10px;color:var(--fnt);font-style:italic}
.dn-ft{border-top:1px solid var(--bdr);padding:7px 9px}
.btn-dn-edit{width:100%;padding:5px 9px;background:none;
  border:1.5px dashed var(--bdr);border-radius:7px;font-size:10px;
  font-weight:700;color:var(--fnt);cursor:pointer;font-family:var(--ff);
  transition:all .15s;text-align:center;letter-spacing:.1px}
.btn-dn-edit:hover{background:var(--pri-xl);color:var(--pri);border-color:var(--pri-l)}
.dn-handle{position:absolute;width:13px;height:13px;border-radius:50%;
  background:var(--sur);border:2px solid var(--bdr);top:50%;
  transform:translateY(-50%);cursor:crosshair;opacity:0;z-index:4;
  transition:opacity .15s,background .15s,border-color .15s}
.dn-hl{left:-7px}.dn-hr{right:-7px}
.diag-node:hover .dn-handle{opacity:1}
.dn-handle:hover{background:var(--pri);border-color:var(--pri)}
.btn-add-stage{flex-shrink:0;align-self:center;display:flex;flex-direction:column;
  align-items:center;justify-content:center;width:54px;height:54px;border-radius:50%;
  border:2px dashed var(--bdr);background:var(--sur);cursor:pointer;
  color:var(--fnt);font-size:9px;font-weight:700;gap:1px;
  transition:all .18s;font-family:var(--ff);padding:0}
.btn-add-stage span{font-size:22px;line-height:1}
.btn-add-stage:hover{border-color:var(--pri);color:var(--pri);background:var(--pri-xl)}

/* ── Stage Panel ── */
.stage-panel{position:fixed;right:0;top:0;bottom:0;width:370px;background:var(--sur);
  border-left:2px solid var(--pri);box-shadow:-6px 0 32px rgba(184,4,87,.15);
  z-index:500;display:flex;flex-direction:column;
  transform:translateX(100%);transition:transform .28s cubic-bezier(.4,0,.2,1)}
.stage-panel.open{transform:translateX(0)}
.sp-hd{display:flex;justify-content:space-between;align-items:flex-start;
  padding:16px 18px;background:linear-gradient(135deg,var(--pri-d),var(--pri));
  color:#fff;flex-shrink:0}
.sp-hd-left{flex:1}
.sp-hd label{font-size:9px;opacity:.65;text-transform:uppercase;
  letter-spacing:1px;display:block;font-weight:700}
.sp-title{font-family:var(--ffh);font-size:16px;font-weight:800;line-height:1.2;
  margin-top:2px;border-bottom:1px dashed rgba(255,255,255,.35)}
.sp-title:focus{outline:none;border-bottom-color:rgba(255,255,255,.8)}
.sp-close{background:none;border:none;color:#fff;font-size:22px;cursor:pointer;
  padding:0 4px;opacity:.75;line-height:1}
.sp-close:hover{opacity:1}
/* sub-tabs */
.sp-subtabs{display:flex;border-bottom:1px solid var(--bdr);flex-shrink:0;background:var(--bg)}
.sp-sub{flex:1;padding:8px 6px;background:none;border:none;border-bottom:2px solid transparent;
  font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
  cursor:pointer;color:var(--mut);font-family:var(--ff);transition:all .15s;margin-bottom:-1px}
.sp-sub.active{color:var(--pri);border-bottom-color:var(--pri);background:var(--sur)}
.sp-sub:hover:not(.active){color:var(--txt);background:#f0edf8}
.sp-body{flex:1;overflow-y:auto;padding:14px 16px}
.sp-body::-webkit-scrollbar{width:4px}
.sp-body::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:2px}
.sp-role-section{margin-bottom:14px}
.sp-role-hd{display:flex;align-items:center;gap:6px;margin-bottom:6px;
  padding-bottom:5px;border-bottom:2px solid var(--bdr)}
.sp-role-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.sp-role-name{font-size:10px;font-weight:700;text-transform:uppercase;
  letter-spacing:.5px;flex:1;color:var(--mut)}
.sp-task-item{display:flex;align-items:center;gap:6px;padding:5px 6px;
  border-radius:6px;margin-bottom:3px;transition:background .12s;
  border:1.5px solid transparent;cursor:default;user-select:none}
.sp-task-item:hover{background:var(--bg)}
.sp-task-item.dragging{opacity:.35;background:var(--pri-xl)}
.sp-task-item.drop-above{border-top-color:var(--pri)}
.sp-task-item.drop-below{border-bottom-color:var(--pri)}
.sp-task-drag{font-size:13px;color:var(--fnt);cursor:grab;opacity:.4;
  flex-shrink:0;line-height:1;user-select:none;transition:opacity .12s}
.sp-task-item:hover .sp-task-drag{opacity:.85}
.sp-task-drag:active{cursor:grabbing}
.sp-role-badge{font-size:8px;font-weight:700;padding:2px 7px;border-radius:10px;
  color:#fff;white-space:nowrap;flex-shrink:0;letter-spacing:.3px}
.sp-task-main{flex:1;display:flex;flex-direction:column;gap:3px;min-width:0}
.sp-task-text{font-size:11px;color:var(--txt);outline:none;
  border-bottom:1px solid transparent;transition:border-color .15s;font-family:var(--ff)}
.sp-task-text:focus{border-bottom-color:var(--pri)}
.sp-task-io{display:flex;flex-wrap:wrap;gap:4px}
.sp-io-tag{font-size:8px;padding:2px 6px;border-radius:8px;font-weight:600;
  letter-spacing:.2px;white-space:nowrap}
.sp-io-in{background:#E3F2FD;color:#1565c0}
.sp-io-out{background:#E8F5E9;color:#2e7d32}
.sp-task-del{background:none;border:none;cursor:pointer;color:var(--fnt);
  font-size:14px;padding:0;opacity:0;transition:opacity .15s,color .15s;
  line-height:1;flex-shrink:0}
.sp-task-item:hover .sp-task-del{opacity:1}
.sp-task-del:hover{color:#e53e3e}
.sp-add-area{border-top:1px solid var(--bdr);padding:14px 16px;
  display:flex;flex-direction:column;gap:8px;flex-shrink:0}
.sp-add-area label{font-size:10px;font-weight:700;color:var(--mut);
  text-transform:uppercase;letter-spacing:.5px}
.sp-task-input,.sp-role-input-w input{width:100%;border:1.5px solid var(--bdr);
  border-radius:8px;padding:8px 11px;font-size:11px;font-family:var(--ff);outline:none;
  transition:border-color .15s,box-shadow .15s;background:var(--bg)}
.sp-task-input:focus{border-color:var(--pri);box-shadow:0 0 0 3px rgba(184,4,87,.1);background:#fff}
.sp-role-input-w{position:relative}
.sp-role-input-w input:focus{border-color:var(--pri);
  box-shadow:0 0 0 3px rgba(184,4,87,.1);background:#fff}
.sp-io-row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.sp-add-btn{padding:9px;background:linear-gradient(135deg,var(--pri-d),var(--pri));
  color:#fff;border:none;border-radius:8px;font-size:11px;font-weight:700;
  cursor:pointer;font-family:var(--ff);transition:filter .15s,transform .1s;
  box-shadow:0 2px 8px rgba(184,4,87,.3)}
.sp-add-btn:hover{filter:brightness(1.1)}
.sp-add-btn:active{transform:scale(.97)}
.sp-footer{padding:10px 16px;border-top:1px solid var(--bdr);
  display:flex;gap:8px;flex-shrink:0}
.sp-dl{flex:1;padding:8px;background:var(--bg);border:1.5px solid var(--bdr);
  border-radius:8px;font-size:10px;font-weight:700;cursor:pointer;
  color:var(--mut);font-family:var(--ff);transition:all .15s}
.sp-dl:hover{background:var(--pri-xl);color:var(--pri);border-color:var(--pri-l)}
.sp-done{padding:8px 20px;background:linear-gradient(135deg,var(--pri-d),var(--pri));
  color:#fff;border:none;border-radius:8px;font-size:11px;font-weight:700;
  cursor:pointer;font-family:var(--ff);box-shadow:0 2px 8px rgba(184,4,87,.3)}
.sp-done:hover{filter:brightness(1.1)}

/* ── Task Detail Panel ── */
.task-panel{position:fixed;right:0;top:0;bottom:0;width:340px;background:var(--sur);
  border-left:2px solid var(--pri);box-shadow:-6px 0 32px rgba(184,4,87,.15);
  z-index:510;display:flex;flex-direction:column;
  transform:translateX(100%);transition:transform .28s cubic-bezier(.4,0,.2,1)}
.task-panel.open{transform:translateX(0)}
.tp-hd{display:flex;justify-content:space-between;align-items:center;
  padding:15px 18px;background:linear-gradient(135deg,var(--pri-d),var(--pri));
  color:#fff;font-family:var(--ffh);font-size:13px;font-weight:800;flex-shrink:0}
.tp-close,.sp-close{background:none;border:none;color:#fff;font-size:22px;cursor:pointer;
  padding:0 4px;opacity:.75;line-height:1}
.tp-close:hover,.sp-close:hover{opacity:1}
.tp-body{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:16px}
.tp-field label{display:block;font-size:10px;font-weight:700;color:var(--mut);
  margin-bottom:5px;text-transform:uppercase;letter-spacing:.6px}
.help-text{font-size:10px;color:var(--mut);line-height:1.6;padding:8px 11px;
  background:var(--pri-xl);border-left:3px solid var(--pri);
  border-radius:0 6px 6px 0;margin-bottom:7px}
.help-text strong{color:var(--pri)}
.tp-field input[type=text],.tp-field textarea,.sp-task-input,.sp-role-input-w input{
  border:1.5px solid var(--bdr);border-radius:8px;padding:8px 11px;
  font-size:11px;font-family:var(--ff);outline:none;
  transition:border-color .15s,box-shadow .15s;color:var(--txt);background:var(--bg)}
.tp-field input[type=text]:focus,.tp-field textarea:focus{
  border-color:var(--pri);box-shadow:0 0 0 3px rgba(184,4,87,.1);background:#fff}
.tp-field input[type=text]{width:100%}
.tp-field textarea{width:100%;resize:vertical;min-height:72px}
.tp-footer{padding:12px 18px;border-top:1px solid var(--bdr);display:flex;gap:8px;flex-shrink:0}
.tp-save{flex:1;padding:10px;background:linear-gradient(135deg,var(--pri-d),var(--pri));
  color:#fff;border:none;border-radius:8px;font-size:11px;font-weight:700;
  cursor:pointer;font-family:var(--ff);box-shadow:0 2px 8px rgba(184,4,87,.3)}
.tp-save:hover{filter:brightness(1.1)}
.tp-cancel{padding:10px 16px;background:var(--bg);color:var(--mut);
  border:1.5px solid var(--bdr);border-radius:8px;font-size:11px;
  cursor:pointer;font-family:var(--ff)}
.tp-cancel:hover{background:var(--pri-xl);border-color:var(--pri-l);color:var(--pri)}

/* ── Autocomplete ── */
.ac-wrap{position:relative}
.ac-list{position:absolute;top:100%;left:0;right:0;background:var(--sur);
  border:1.5px solid var(--pri);border-top:none;border-radius:0 0 8px 8px;
  max-height:160px;overflow-y:auto;z-index:650;list-style:none;
  padding:4px 0;margin:0;display:none;box-shadow:var(--s2)}
.ac-list.show{display:block}
.ac-list li{display:flex;align-items:center;gap:8px;padding:7px 12px;
  font-size:11px;cursor:pointer;margin:0;font-family:var(--ff)}
.ac-list li::before{display:none}
.ac-list li:hover{background:var(--pri-xl)}
.ac-list li.ac-s{background:var(--pri-xl);color:var(--pri)}
.ac-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}

/* ── Role Management ── */
.role-overlay{position:fixed;inset:0;background:rgba(28,26,46,.55);
  z-index:700;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.role-overlay.hidden{display:none}
.role-box{background:var(--sur);border-radius:14px;width:410px;max-height:82vh;
  display:flex;flex-direction:column;box-shadow:var(--s3);overflow:hidden}
.role-box-hd{display:flex;justify-content:space-between;align-items:center;
  padding:16px 20px;background:linear-gradient(135deg,var(--pri-d),var(--pri));
  color:#fff;font-family:var(--ffh);font-size:13px;font-weight:800;flex-shrink:0}
.role-box-close{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;padding:0 4px;opacity:.75}
.role-box-close:hover{opacity:1}
.role-box-body{flex:1;overflow-y:auto;padding:18px}
.role-add-row{display:flex;gap:8px;margin-bottom:14px}
.role-add-row input{flex:1;border:1.5px solid var(--bdr);border-radius:8px;
  padding:9px 11px;font-size:11px;font-family:var(--ff);outline:none;background:var(--bg)}
.role-add-row input:focus{border-color:var(--pri);
  box-shadow:0 0 0 3px rgba(184,4,87,.1);background:#fff}
.role-add-row button{padding:9px 16px;background:linear-gradient(135deg,var(--pri-d),var(--pri));
  color:#fff;border:none;border-radius:8px;font-size:11px;font-weight:700;
  cursor:pointer;white-space:nowrap;font-family:var(--ff);
  box-shadow:0 2px 8px rgba(184,4,87,.3)}
.role-add-row button:hover{filter:brightness(1.1)}
.role-list-ul{list-style:none;display:flex;flex-direction:column;gap:6px;padding:0;margin:0}
.role-list-ul li{display:flex;align-items:center;gap:9px;padding:9px 13px;
  background:var(--bg);border-radius:8px;border:1px solid var(--bdr);margin:0}
.role-list-ul li::before{display:none}
.role-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.role-label{flex:1;font-size:11px;font-weight:600;color:var(--txt)}
.role-del{background:none;border:none;cursor:pointer;color:var(--fnt);font-size:16px;padding:0;line-height:1}
.role-del:hover{color:#e53e3e}

/* ── Role Journey ── */
.rj-overlay{position:fixed;inset:0;background:rgba(28,26,46,.6);
  z-index:720;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.rj-overlay.hidden{display:none}
.rj-box{background:var(--sur);border-radius:14px;width:660px;max-width:92vw;
  max-height:86vh;display:flex;flex-direction:column;box-shadow:var(--s3);overflow:hidden}
.rj-hd{display:flex;justify-content:space-between;align-items:center;
  padding:16px 22px;color:#fff;font-family:var(--ffh);font-size:14px;font-weight:800;flex-shrink:0}
.rj-close{background:none;border:none;color:#fff;font-size:22px;cursor:pointer;padding:0 4px;opacity:.75}
.rj-close:hover{opacity:1}
.rj-body{flex:1;overflow-y:auto;padding:20px}
.rj-flow{margin-bottom:22px}
.rj-flow-name{font-size:10px;font-weight:700;color:var(--mut);text-transform:uppercase;
  letter-spacing:.7px;margin-bottom:9px;display:flex;align-items:center;gap:7px}
.rj-flow-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.rj-stages{display:flex;flex-wrap:wrap;gap:9px}
.rj-stage{border:1px solid var(--bdr);border-radius:9px;padding:9px 11px;
  background:var(--bg);min-width:140px;max-width:200px}
.rj-stage-name{font-size:10px;font-weight:700;color:var(--txt);margin-bottom:5px;
  padding-bottom:4px;border-bottom:1px solid var(--bdr);font-family:var(--ffh)}
.rj-stage ul{list-style:none;padding:0;margin:0}
.rj-stage li{font-size:10px;color:var(--mut);padding:2px 0 2px 9px;
  position:relative;line-height:1.4}
.rj-stage li::before{content:"\\2022";position:absolute;left:1px;color:var(--fnt);font-size:9px}

/* ── Diagram sub-toggle (Etapas / Tarefas) ── */
.diag-sub-toggle{display:flex;gap:4px}
.btn-dsub{padding:4px 13px;border-radius:5px;
  border:1.5px solid rgba(255,255,255,.45);background:transparent;
  color:rgba(255,255,255,.75);cursor:pointer;font-family:var(--ff);
  font-size:10px;font-weight:700;transition:all .15s;letter-spacing:.1px}
.btn-dsub:hover:not(.active){background:rgba(255,255,255,.15);color:#fff}
.btn-dsub.active{background:rgba(255,255,255,.25);color:#fff;
  border-color:rgba(255,255,255,.85)}
/* ── Task diagram canvas ── */
.diag-task-canvas{display:none}
.diag-task-canvas .diag-row{width:auto;flex-wrap:wrap;gap:18px;row-gap:16px;align-items:flex-start}
.diag-stage-sep{flex-basis:100%;display:flex;align-items:center;gap:8px;
  padding:6px 0 2px;pointer-events:none}
.diag-stage-sep>span{font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.8px;
  padding:3px 10px;border-radius:20px;color:#fff;flex-shrink:0}
.diag-stage-sep::after{content:'';flex:1;height:1px;background:var(--bdr)}
/* task node overrides */
.diag-task-node{width:170px}
.diag-task-node .dn-hd{padding:6px 10px}
.diag-task-node .dn-title{font-size:8px;letter-spacing:.5px;text-transform:uppercase}
.dtn-body{padding:9px 11px}
.dtn-task{font-size:10px;color:var(--txt);line-height:1.45;margin-bottom:8px;font-weight:500}
.dtn-io{display:flex;flex-direction:column;gap:5px}
.dtn-row{display:flex;align-items:flex-start;gap:4px}
.dtn-lbl{font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.3px;
  flex-shrink:0;padding-top:1px}
.dtn-in-lbl{color:#1565c0}
.dtn-out-lbl{color:#2e7d32}
.dtn-val{flex:1;font-size:10px;color:var(--mut);outline:none;min-width:0;
  border-bottom:1px dashed transparent;font-family:var(--ff);line-height:1.35;
  transition:border-color .15s,color .15s}
.dtn-val:empty::before{content:attr(data-ph);color:var(--fnt);font-style:italic;pointer-events:none}
.dtn-val:focus{border-bottom-color:var(--pri);color:var(--txt)}

/* ── Task drag-to-reorder ── */
.task-drag-handle{font-size:12px;color:var(--fnt);cursor:grab;
  user-select:none;flex-shrink:0;opacity:0;transition:opacity .15s;line-height:1;
  padding-top:1px}
.task-drag-handle:active{cursor:grabbing}
li:hover .task-drag-handle{opacity:1}
td.task-cell li.task-drop-above{border-top:2px solid var(--pri);border-radius:2px 2px 0 0}
td.task-cell li.task-drop-below{border-bottom:2px solid var(--pri);border-radius:0 0 2px 2px}

/* ── Role filter bar ── */
.role-filter-bar{display:none;align-items:center;gap:8px;padding:6px 22px;
  background:var(--pri-xl);border-bottom:1px solid var(--bdr);font-size:11px;flex-wrap:wrap}
.role-filter-bar.on{display:flex}
.rfb-label{color:var(--mut);font-size:10px;font-weight:700;text-transform:uppercase;
  letter-spacing:.5px;flex-shrink:0}
.rfb-chips{display:flex;flex-wrap:wrap;gap:5px;flex:1}
.rfb-chip{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;
  border-radius:12px;color:#fff;font-size:9px;font-weight:700;letter-spacing:.2px}
.rfb-clear{padding:3px 10px;background:var(--sur);border:1.5px solid var(--bdr);
  border-radius:6px;font-size:10px;font-weight:700;cursor:pointer;
  color:var(--mut);font-family:var(--ff);transition:all .15s;flex-shrink:0}
.rfb-clear:hover{border-color:var(--pri);color:var(--pri)}
/* Filter effect */
body.rf-active .swimlane tbody tr[data-role]:not(.rf-match){display:none}
body.rf-active .dn-rg[data-role]:not(.rf-match){display:none}
body.rf-active .diag-task-canvas .diag-task-node[data-role]:not(.rf-match){display:none}

/* ── Print ── */
@media print{
  @page{size:A4 landscape;margin:8mm}
  body{background:#fff!important;font-size:8px}
  .nav-wrap,.cover,.role-filter-bar,.task-panel,.stage-panel,
  .role-overlay,.rj-overlay,.btn-del,.btn-add,.btn-info,
  .btn-dn-edit,.dn-handle,.dn-grip,.btn-add-stage,.diag-sub-toggle{display:none!important}
  /* only the marked section prints */
  .flow-section,.diagram-section{display:none!important}
  .flow-section.print-me,.diagram-section.print-me{display:block!important;
    margin:0;border-radius:0;box-shadow:none;border:none}
  /* color fidelity */
  .flow-hd,.dn-hd,td.role-name{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
  /* swim lane */
  .tbl-wrap{max-height:none!important;overflow:visible!important}
  thead th,td.role-name{position:static!important}
  table.swimlane{table-layout:auto!important;width:100%!important;font-size:7px}
  thead th,td{min-width:0!important;word-break:break-word}
  /* diagram etapas + tarefas */
  .diag-canvas{display:none!important}
  .diag-canvas.print-me{display:block!important;overflow:visible!important;
    background:none!important;background-image:none!important;min-height:0}
  .diag-svg{display:none!important}
  .diag-row{flex-wrap:wrap!important;padding:14px!important;gap:14px!important;width:auto!important;
    row-gap:14px!important}
  .diag-node{break-inside:avoid;width:160px!important}
  .diag-stage-sep{display:none!important}
  .dn-body,.dtn-body{max-height:none!important;overflow:visible!important}
}
"""

# ── JavaScript ────────────────────────────────────────────────────────────────
JS = r"""
// ── helpers ───────────────────────────────────────────────────────────────────
function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function rc(n){ return ROLE_COLORS[n]||'#888'; }

// ── view toggle ───────────────────────────────────────────────────────────────
function setView(mode){
  document.body.dataset.view=mode;
  document.querySelectorAll('.btn-view').forEach(function(b){b.classList.toggle('active',b.dataset.view===mode);});
  try{localStorage.setItem('uhull-view',mode);}catch(e){}
  if(_activeFlow) setActiveFlow(_activeFlow);
}

// ── tab / active flow ─────────────────────────────────────────────────────────
var _activeFlow=null;
function setActiveFlow(fid){
  _activeFlow=fid;
  var mode=document.body.dataset.view||'swim';
  document.querySelectorAll('.flow-section,.diagram-section').forEach(function(s){
    s.classList.remove('tab-vis');
  });
  var secId=(mode==='diag'?'diag-':'')+fid;
  var sec=document.getElementById(secId);
  if(sec) sec.classList.add('tab-vis');
  document.querySelectorAll('.flow-tab').forEach(function(t){
    t.classList.toggle('active',t.dataset.fid===fid);
  });
  try{localStorage.setItem('uhull-flow',fid);}catch(e){}
  if(mode==='diag') setTimeout(function(){drawArrows(fid);},60);
}

// ── swim lane: add task ───────────────────────────────────────────────────────
function addTask(btn){
  var cell=btn.closest('td'),ul=cell.querySelector('ul');
  if(!ul){
    ul=document.createElement('ul');cell.insertBefore(ul,btn);
    cell.classList.replace('empty','active');
    var rc2=cell.closest('tr').querySelector('td.role-name');
    if(rc2){var c=rc2.style.borderLeftColor;cell.style.borderTop='3px solid '+c.replace(')',',.35)').replace('rgb','rgba');}
  }
  var li=document.createElement('li');li.dataset.input='';li.dataset.output='';li.dataset.role='';li.draggable=true;
  var grip=document.createElement('span');grip.className='task-drag-handle';grip.title='Arrastar';grip.textContent='⋮';
  var span=document.createElement('span');span.className='task-text';span.contentEditable='true';span.spellcheck=false;span.textContent='Nova tarefa';
  var info=document.createElement('button');info.className='btn-info';info.title='Detalhes';info.textContent='i';info.onclick=function(){openTaskPanel(this.closest('li'));};
  var del=document.createElement('button');del.className='btn-del';del.innerHTML='&times;';del.onclick=function(){this.closest('li').remove();};
  li.appendChild(grip);li.appendChild(span);li.appendChild(info);li.appendChild(del);ul.appendChild(li);
  span.focus();var r=document.createRange();r.selectNodeContents(span);var s=window.getSelection();s.removeAllRanges();s.addRange(r);
}

// ── export / save ─────────────────────────────────────────────────────────────
function exportPDF(){
  // Remove any previous print-me marks
  document.querySelectorAll('.print-me').forEach(function(el){el.classList.remove('print-me');});
  var mode=document.body.dataset.view||'swim';
  if(mode==='diag'&&_activeFlow){
    var sec=document.getElementById('diag-'+_activeFlow);
    if(sec) sec.classList.add('print-me');
    // also mark the active sub-view inside the diagram
    var canvas=document.getElementById('dc-'+_activeFlow);
    var tcanvas=document.getElementById('dtc-'+_activeFlow);
    if(canvas&&canvas.style.display!=='none') canvas.classList.add('print-me');
    if(tcanvas&&tcanvas.style.display!=='none') tcanvas.classList.add('print-me');
  } else {
    var sw=document.getElementById(_activeFlow);
    if(sw) sw.classList.add('print-me');
  }
  window.print();
  // cleanup
  document.querySelectorAll('.print-me').forEach(function(el){el.classList.remove('print-me');});
}
function saveHTML(){
  var b=new Blob(['<!DOCTYPE html>\n'+document.documentElement.cloneNode(true).outerHTML],{type:'text/html;charset=utf-8'});
  var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='fluxo-uhull-editado.html';
  document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(a.href);
}

// ── diagram sub-view toggle ───────────────────────────────────────────────────
function setDiagSub(fid,mode,btn){
  var sec=document.getElementById('diag-'+fid);
  var canvas=document.getElementById('dc-'+fid);
  var tcanvas=document.getElementById('dtc-'+fid);
  if(canvas)  canvas.style.display=mode==='etapas'?'block':'none';
  if(tcanvas) tcanvas.style.display=mode==='tarefas'?'block':'none';
  sec.querySelectorAll('.btn-dsub').forEach(function(b){b.classList.toggle('active',b.dataset.sub===mode);});
  if(mode==='etapas')  setTimeout(function(){drawArrows(fid);},40);
  if(mode==='tarefas') setTimeout(function(){drawTaskArrows(fid);},40);
}

// ── diagram: draw SVG arrows ──────────────────────────────────────────────────
function getOff(el,anc){var x=0,y=0;while(el&&el!==anc){x+=el.offsetLeft;y+=el.offsetTop;el=el.offsetParent;}return{x:x,y:y};}

function _redrawCanvas(canvas){
  if(!canvas)return;
  var svg=canvas.querySelector('.diag-svg');if(!svg)return;
  var isTask=canvas.classList.contains('diag-task-canvas');
  var cid=canvas.id.replace(/[^a-z0-9_]/gi,'_');
  var ah='ah_'+cid,ahb='ahb_'+cid;
  svg.setAttribute('width',canvas.scrollWidth);svg.setAttribute('height',canvas.scrollHeight);
  svg.innerHTML='<defs>'+
    '<marker id="'+ah+'" markerWidth="9" markerHeight="6" refX="8" refY="3" orient="auto">'+
    '<polygon points="0 0,9 3,0 6" fill="#94a3b8"/></marker>'+
    '<marker id="'+ahb+'" markerWidth="9" markerHeight="6" refX="8" refY="3" orient="auto">'+
    '<polygon points="0 0,9 3,0 6" fill="#1565c0"/></marker></defs>';
  function drawPath(from,to,color,dashed,mid){
    var fo=getOff(from,canvas),t2=getOff(to,canvas);
    var x1=fo.x+from.offsetWidth,y1=fo.y+from.offsetHeight/2;
    var x2=t2.x,y2=t2.y+to.offsetHeight/2;
    var cx=(x1+x2)/2;
    var p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d','M '+x1+','+y1+' C '+cx+','+y1+' '+cx+','+y2+' '+x2+','+y2);
    p.setAttribute('stroke',color);p.setAttribute('fill','none');p.setAttribute('stroke-width','1.5');
    p.setAttribute('marker-end','url(#'+mid+')');
    if(dashed)p.setAttribute('stroke-dasharray','6,3');
    svg.appendChild(p);
  }
  if(!isTask){
    var nodes=Array.from(canvas.querySelectorAll('.diag-node:not(.diag-task-node)'));
    for(var i=0;i<nodes.length-1;i++)drawPath(nodes[i],nodes[i+1],'#94a3b8',false,ah);
  }
  JSON.parse(canvas.dataset.conns||'[]').forEach(function(c){
    var a=document.getElementById(c[0]),b=document.getElementById(c[1]);
    if(a&&b)drawPath(a,b,'#1565c0',true,ahb);
  });
}

function drawArrows(fid){_redrawCanvas(document.getElementById('dc-'+fid));}
function drawTaskArrows(fid){_redrawCanvas(document.getElementById('dtc-'+fid));}

// ── diagram: drag-to-connect ──────────────────────────────────────────────────
var _cn={active:false,fid:null,fromId:null,tmp:null,canvas:null};

function startConn(e,handle){
  e.preventDefault();e.stopPropagation();
  var node=handle.closest('.diag-node');
  _cn.active=true;_cn.fid=node.dataset.flow;_cn.fromId=node.id;
  _cn.canvas=node.closest('.diag-canvas');
  var svg=_cn.canvas.querySelector('.diag-svg');
  _cn.tmp=document.createElementNS('http://www.w3.org/2000/svg','path');
  _cn.tmp.setAttribute('stroke','#1565c0');_cn.tmp.setAttribute('fill','none');
  _cn.tmp.setAttribute('stroke-width','1.5');_cn.tmp.setAttribute('stroke-dasharray','6,3');
  svg.appendChild(_cn.tmp);
  document.addEventListener('mousemove',onConnMove);
  document.addEventListener('mouseup',onConnEnd);
}

function onConnMove(e){
  if(!_cn.active)return;
  var canvas=_cn.canvas;
  var from=document.getElementById(_cn.fromId);
  var fo=getOff(from,canvas);
  var x1=fo.x+from.offsetWidth,y1=fo.y+from.offsetHeight/2;
  var cr=canvas.getBoundingClientRect();
  var x2=e.clientX-cr.left+canvas.scrollLeft,y2=e.clientY-cr.top+canvas.scrollTop;
  var cx=(x1+x2)/2;
  _cn.tmp.setAttribute('d','M '+x1+','+y1+' C '+cx+','+y1+' '+cx+','+y2+' '+x2+','+y2);
}

function onConnEnd(e){
  document.removeEventListener('mousemove',onConnMove);
  document.removeEventListener('mouseup',onConnEnd);
  if(!_cn.active)return;_cn.active=false;
  if(_cn.tmp){_cn.tmp.remove();_cn.tmp=null;}
  var target=e.target.closest('.diag-node');
  if(target&&target.id!==_cn.fromId){
    var canvas=_cn.canvas;
    var conns=JSON.parse(canvas.dataset.conns||'[]');
    if(!conns.some(function(c){return c[0]===_cn.fromId&&c[1]===target.id;})){
      conns.push([_cn.fromId,target.id]);canvas.dataset.conns=JSON.stringify(conns);
    }
    _redrawCanvas(canvas);
  }
}

// ── add new flow ──────────────────────────────────────────────────────────────
var _flowColors=['#c62828','#ad1457','#1565c0','#2e7d32','#6a1b9a','#e65100','#00695c','#558b2f'];
function addFlow(){
  var name=prompt('Nome do novo fluxo:','Novo Fluxo');
  if(!name||!name.trim())return;
  name=name.trim();
  var tabBar=document.getElementById('tab-bar');
  var idx=tabBar.querySelectorAll('.flow-tab').length;
  var color=_flowColors[idx%_flowColors.length];
  var fid='fluxo_novo_'+Date.now();

  // Create tab
  var tab=document.createElement('button');
  tab.className='flow-tab';tab.dataset.fid=fid;
  tab.style.setProperty('--tc',color);
  tab.onclick=function(){setActiveFlow(fid);};
  tab.innerHTML='<span class="tab-num">F'+(idx+1)+'</span><span class="tab-lbl">'+esc(name)+'</span>';
  tabBar.insertBefore(tab,tabBar.querySelector('.btn-add-flow'));

  // Create swim section
  var sw=document.createElement('section');
  sw.className='flow-section';sw.id=fid;
  sw.innerHTML='<div class="flow-hd" style="background:'+color+'">'+
    '<div><span class="flow-num">Fluxo '+(idx+1)+'</span>'+
    '<h2 contenteditable="true" spellcheck="false">'+esc(name)+'</h2></div>'+
    '<div class="flow-stats">0 etapas &middot; 0 tarefas</div></div>'+
    '<div class="tbl-wrap"><table class="swimlane">'+
    '<thead><tr><th class="role-col sticky-corner"><span>Papel</span></th>'+
    '<th class="step-col"><span contenteditable="true" spellcheck="false">Etapa 1</span></th></tr></thead>'+
    '<tbody><tr>'+
    '<td class="role-name" style="border-left:4px solid #888;background:#f9f9f9;color:#888">'+
    '<span contenteditable="true" spellcheck="false">Papel</span></td>'+
    '<td class="task-cell empty">'+
    '<button class="btn-add" onclick="addTask(this)">+ tarefa</button></td>'+
    '</tr></tbody></table></div>';
  document.querySelector('.flow-section')
    ? document.querySelector('.flow-section').parentNode.insertBefore(sw, null)
    : document.body.appendChild(sw);

  // Create diagram section
  var dg=document.createElement('section');
  dg.className='diagram-section';dg.id='diag-'+fid;
  dg.innerHTML='<div class="flow-hd" style="background:'+color+'">'+
    '<div><span class="flow-num">Fluxo '+(idx+1)+'</span>'+
    '<h2 contenteditable="true" spellcheck="false">'+esc(name)+'</h2></div>'+
    '<div class="flow-stats">0 etapas</div></div>'+
    '<div class="diag-canvas" id="dc-'+fid+'" data-color="'+color+'" data-conns="[]">'+
    '<svg class="diag-svg" id="ds-'+fid+'"></svg>'+
    '<div class="diag-row" id="dr-'+fid+'">'+
    '<button class="btn-add-stage" onclick="addStage(\''+fid+'\',\''+color+'\')">'+
    '<span>+</span>Etapa</button></div></div>';
  sw.insertAdjacentElement('afterend',dg);

  initDiagDrag();
  setActiveFlow(fid);
}

// ── diagram: add stage ────────────────────────────────────────────────────────
function addStage(fid,color){
  var row=document.getElementById('dr-'+fid);
  var addBtn=row.querySelector('.btn-add-stage');
  var idx=row.querySelectorAll('.diag-node').length;
  var nodeId='dn-'+fid+'-'+idx;
  var div=document.createElement('div');
  div.className='diag-node';div.id=nodeId;
  div.dataset.flow=fid;div.dataset.step='Nova Etapa';div.dataset.tasks='{}';div.dataset.color=color;
  div.draggable=true;
  div.innerHTML=
    '<span class="dn-handle dn-hl" onmousedown="startConn(event,this)"></span>'+
    '<div class="dn-hd" style="background:'+color+'">'+
    '<span class="dn-grip" title="Arrastar para reposicionar">&#8942;&#8942;</span>'+
    '<span class="dn-title" contenteditable="true" spellcheck="false">Nova Etapa</span>'+
    '<span class="dn-badge">0</span></div>'+
    '<div class="dn-body"><p class="dn-empty">Sem tarefas</p></div>'+
    '<div class="dn-ft"><button class="btn-dn-edit" onclick="openStagePanel(this.closest(\'.diag-node\'))">&#9998; Editar</button></div>'+
    '<span class="dn-handle dn-hr" onmousedown="startConn(event,this)"></span>';
  row.insertBefore(div,addBtn);
  setTimeout(function(){drawArrows(fid);},50);
  div.querySelector('.dn-title').focus();
}

function mixColor(hex,a){
  var r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
  return 'rgb('+Math.round(r*a+255*(1-a))+','+Math.round(g*a+255*(1-a))+','+Math.round(b*a+255*(1-a))+')';
}

// ── swim lane: drag-reorder tasks ────────────────────────────────────────────
var _tdr={li:null,above:false};
function initTaskDrag(){
  document.addEventListener('dragstart',function(e){
    var li=e.target.closest('td.task-cell li');
    if(!li)return;
    if(e.target.closest('[contenteditable]'))return e.preventDefault();
    _tdr.li=li;
    setTimeout(function(){if(_tdr.li)_tdr.li.style.opacity='.35';},0);
    e.dataTransfer.effectAllowed='move';
  });
  document.addEventListener('dragend',function(){
    if(_tdr.li)_tdr.li.style.opacity='';
    document.querySelectorAll('.task-drop-above,.task-drop-below').forEach(function(el){
      el.classList.remove('task-drop-above','task-drop-below');
    });
    _tdr.li=null;
  });
  document.addEventListener('dragover',function(e){
    if(!_tdr.li)return;
    var target=e.target.closest('td.task-cell li');
    if(!target||target===_tdr.li)return;
    e.preventDefault();
    document.querySelectorAll('.task-drop-above,.task-drop-below').forEach(function(el){
      el.classList.remove('task-drop-above','task-drop-below');
    });
    var r=target.getBoundingClientRect();
    _tdr.above=e.clientY<r.top+r.height/2;
    target.classList.add(_tdr.above?'task-drop-above':'task-drop-below');
  });
  document.addEventListener('drop',function(e){
    if(!_tdr.li)return;
    var target=e.target.closest('td.task-cell li');
    if(!target||target===_tdr.li)return;
    e.preventDefault();
    var ul=target.closest('ul');
    if(_tdr.above) ul.insertBefore(_tdr.li,target);
    else ul.insertBefore(_tdr.li,target.nextSibling);
  });
}

// ── diagram: drag-reorder stages ─────────────────────────────────────────────
var _dr={id:null};

function initDiagDrag(){
  document.querySelectorAll('.diag-row').forEach(function(row){
    row.addEventListener('dragstart',function(e){
      var node=e.target.closest('.diag-node');
      if(!node)return;
      // prevent drag when user clicked a contenteditable area
      if(e.target.closest('[contenteditable]'))return e.preventDefault();
      _dr.id=node.id;
      setTimeout(function(){node.classList.add('dn-dragging');},0);
      e.dataTransfer.effectAllowed='move';
    });

    row.addEventListener('dragend',function(e){
      var node=document.getElementById(_dr.id);
      if(node) node.classList.remove('dn-dragging');
      row.querySelectorAll('.dn-drop-left,.dn-drop-right').forEach(function(n){
        n.classList.remove('dn-drop-left','dn-drop-right');
      });
      _dr.id=null;
    });

    row.addEventListener('dragover',function(e){
      if(!_dr.id)return;
      e.preventDefault();
      e.dataTransfer.dropEffect='move';
      var target=e.target.closest('.diag-node');
      row.querySelectorAll('.dn-drop-left,.dn-drop-right').forEach(function(n){
        if(n!==target){n.classList.remove('dn-drop-left','dn-drop-right');}
      });
      if(target&&target.id!==_dr.id){
        var r=target.getBoundingClientRect();
        var mid=r.left+r.width/2;
        if(e.clientX<mid){target.classList.add('dn-drop-left');target.classList.remove('dn-drop-right');}
        else{target.classList.add('dn-drop-right');target.classList.remove('dn-drop-left');}
      }
    });

    row.addEventListener('drop',function(e){
      if(!_dr.id)return;
      e.preventDefault();
      var dragged=document.getElementById(_dr.id);
      var target=e.target.closest('.diag-node');
      if(!dragged||!target||target===dragged)return;
      var r=target.getBoundingClientRect();
      if(e.clientX<r.left+r.width/2){
        row.insertBefore(dragged,target);
      } else {
        row.insertBefore(dragged,target.nextSibling);
      }
      target.classList.remove('dn-drop-left','dn-drop-right');
      var fid=dragged.dataset.flow;
      var inTask=!!dragged.closest('.diag-task-canvas');
      setTimeout(function(){if(inTask)drawTaskArrows(fid);else drawArrows(fid);},30);
    });
  });
}

// ── Stage Panel ───────────────────────────────────────────────────────────────
var _sNode=null;
var _spSub='roles';

function setSpSub(sub,btn){
  _spSub=sub;
  document.querySelectorAll('.sp-sub').forEach(function(b){b.classList.toggle('active',b.dataset.sub===sub);});
  renderSpBody();
}

function openStagePanel(node){
  _sNode=node;
  _spSub='roles';
  document.querySelectorAll('.sp-sub').forEach(function(b){b.classList.toggle('active',b.dataset.sub==='roles');});
  document.getElementById('sp-title').textContent=node.dataset.step;
  renderSpBody();
  document.getElementById('stage-panel').classList.add('open');
  document.getElementById('sp-task-in').focus();
}

function closeStagePanel(){
  if(_sNode){
    _sNode.dataset.step=document.getElementById('sp-title').textContent.trim()||_sNode.dataset.step;
    var nt=_sNode.querySelector('.dn-title');
    if(nt) nt.textContent=_sNode.dataset.step;
    syncAllViews(_sNode);
    drawArrows(_sNode.dataset.flow);
  }
  document.getElementById('stage-panel').classList.remove('open');
  _sNode=null;
}

function renderSpBody(){
  var body=document.getElementById('sp-body');
  body.innerHTML='';
  var tasks=JSON.parse(_sNode.dataset.tasks||'{}');
  if(_spSub==='roles') _renderSpRoles(body,tasks);
  else _renderSpFlat(body,tasks);
  if(!body.children.length) body.innerHTML='<p style="font-size:11px;color:#a0aec0;text-align:center;padding:20px 0">Nenhuma tarefa ainda</p>';
}

function _spIoHtml(task){
  if(!_sNode)return '';
  var ios=JSON.parse(_sNode.dataset.ios||'{}');
  var io=ios[task]||{};
  if(!io.input&&!io.output)return '';
  return '<div class="sp-task-io">'+
    (io.input?'<span class="sp-io-tag sp-io-in">&#8595; '+esc(io.input)+'</span>':'')+
    (io.output?'<span class="sp-io-tag sp-io-out">&#8593; '+esc(io.output)+'</span>':'')+
    '</div>';
}

function _makeSpItem(role,task){
  var item=document.createElement('div');item.className='sp-task-item';
  item.dataset.role=role;item.setAttribute('draggable','true');
  item.innerHTML='<span class="sp-task-drag">&#8942;</span>'+
    '<div class="sp-task-main">'+
    '<span class="sp-task-text" contenteditable="true" spellcheck="false">'+esc(task)+'</span>'+
    _spIoHtml(task)+
    '</div>'+
    '<button class="sp-task-del" onclick="delSpTask(this)" title="Remover">&#215;</button>';
  return item;
}

function _makeSpItemFlat(role,task){
  var c=rc(role);
  var item=document.createElement('div');item.className='sp-task-item';
  item.dataset.role=role;item.setAttribute('draggable','true');
  item.innerHTML='<span class="sp-task-drag">&#8942;</span>'+
    '<span class="sp-role-badge" style="background:'+c+'">'+esc(role)+'</span>'+
    '<div class="sp-task-main">'+
    '<span class="sp-task-text" contenteditable="true" spellcheck="false">'+esc(task)+'</span>'+
    _spIoHtml(task)+
    '</div>'+
    '<button class="sp-task-del" onclick="delSpTask(this)" title="Remover">&#215;</button>';
  return item;
}

function _renderSpRoles(body,tasks){
  Object.keys(tasks).forEach(function(role){
    if(!tasks[role].length)return;
    var c=rc(role);
    var sec=document.createElement('div');sec.className='sp-role-section';
    sec.innerHTML='<div class="sp-role-hd"><span class="sp-role-dot" style="background:'+c+'"></span>'+
      '<span class="sp-role-name">'+esc(role)+'</span></div>';
    tasks[role].forEach(function(task){sec.appendChild(_makeSpItem(role,task));});
    _setupSpDrag(sec,role);
    body.appendChild(sec);
  });
}

function _renderSpFlat(body,tasks){
  Object.keys(tasks).forEach(function(role){
    (tasks[role]||[]).forEach(function(task){body.appendChild(_makeSpItemFlat(role,task));});
  });
  _setupSpDrag(body,null);
}

function _setupSpDrag(container,fixedRole){
  var dragged=null;
  container.addEventListener('dragstart',function(e){
    var item=e.target.closest('.sp-task-item');
    if(!item)return;
    if(e.target.closest('[contenteditable]'))return e.preventDefault();
    dragged=item;
    setTimeout(function(){if(dragged)dragged.classList.add('dragging');},0);
    e.dataTransfer.effectAllowed='move';
  });
  container.addEventListener('dragend',function(){
    if(dragged){dragged.classList.remove('dragging');}
    dragged=null;
    container.querySelectorAll('.sp-task-item').forEach(function(i){i.classList.remove('drop-above','drop-below');});
  });
  container.addEventListener('dragover',function(e){
    if(!dragged)return;
    var target=e.target.closest('.sp-task-item');
    if(!target||target===dragged)return;
    e.preventDefault();
    var rect=target.getBoundingClientRect();
    container.querySelectorAll('.sp-task-item').forEach(function(i){i.classList.remove('drop-above','drop-below');});
    target.classList.add(e.clientY<rect.top+rect.height/2?'drop-above':'drop-below');
  });
  container.addEventListener('dragleave',function(e){
    if(!container.contains(e.relatedTarget))
      container.querySelectorAll('.sp-task-item').forEach(function(i){i.classList.remove('drop-above','drop-below');});
  });
  container.addEventListener('drop',function(e){
    if(!dragged)return;
    var target=e.target.closest('.sp-task-item');
    container.querySelectorAll('.sp-task-item').forEach(function(i){i.classList.remove('drop-above','drop-below');});
    if(!target||target===dragged)return;
    e.preventDefault();
    var rect=target.getBoundingClientRect();
    if(e.clientY<rect.top+rect.height/2) container.insertBefore(dragged,target);
    else container.insertBefore(dragged,target.nextSibling);
    _saveSpOrder(container,fixedRole);
  });
}

function _saveSpOrder(container,fixedRole){
  var tasks=JSON.parse(_sNode.dataset.tasks||'{}');
  if(fixedRole){
    var newOrder=[];
    container.querySelectorAll('.sp-task-item').forEach(function(item){
      newOrder.push(item.querySelector('.sp-task-text').textContent.trim());
    });
    tasks[fixedRole]=newOrder;
  } else {
    var newTasks={};
    container.querySelectorAll('.sp-task-item').forEach(function(item){
      var r=item.dataset.role,t=item.querySelector('.sp-task-text').textContent.trim();
      if(!newTasks[r])newTasks[r]=[];
      newTasks[r].push(t);
    });
    Object.assign(tasks,newTasks);
  }
  _sNode.dataset.tasks=JSON.stringify(tasks);
  syncAllViews(_sNode);
}

function delSpTask(btn){
  var item=btn.closest('.sp-task-item');
  var role=item.dataset.role;
  var text=item.querySelector('.sp-task-text').textContent.trim();
  var tasks=JSON.parse(_sNode.dataset.tasks||'{}');
  if(tasks[role]){tasks[role]=tasks[role].filter(function(t){return t!==text;});if(!tasks[role].length)delete tasks[role];}
  _sNode.dataset.tasks=JSON.stringify(tasks);
  renderSpBody();
  syncAllViews(_sNode);
}

function addSpTask(){
  var taskIn=document.getElementById('sp-task-in');
  var roleIn=document.getElementById('sp-role-in');
  var inputIn=document.getElementById('sp-input-in');
  var outputIn=document.getElementById('sp-output-in');
  var task=taskIn.value.trim(),role=roleIn.value.trim()||'Não Definido';
  if(!task)return;
  var inp=inputIn?inputIn.value.trim():'',out=outputIn?outputIn.value.trim():'';
  var tasks=JSON.parse(_sNode.dataset.tasks||'{}');
  if(!tasks[role])tasks[role]=[];
  tasks[role].push(task);
  _sNode.dataset.tasks=JSON.stringify(tasks);
  if(inp||out){
    var ios=JSON.parse(_sNode.dataset.ios||'{}');
    ios[task]={input:inp,output:out};
    _sNode.dataset.ios=JSON.stringify(ios);
  }
  taskIn.value='';if(inputIn)inputIn.value='';if(outputIn)outputIn.value='';
  taskIn.focus();
  renderSpBody();
  syncAllViews(_sNode);
}

function syncAllViews(node){
  var fid=node.dataset.flow;
  var step=node.dataset.step||document.getElementById('sp-title').textContent.trim();
  var tasks=JSON.parse(node.dataset.tasks||'{}');
  syncNodeBody(node);
  function syncTable(sec,makeCell){
    if(!sec)return;
    var tbl=sec.querySelector('table.swimlane');if(!tbl)return;
    var ths=tbl.querySelectorAll('thead th');
    var colIdx=-1;
    ths.forEach(function(th,i){
      var span=th.querySelector('span');
      var txt=span?span.textContent.trim():th.textContent.trim();
      if(txt===step)colIdx=i;
    });
    if(colIdx<0)return;
    tbl.querySelectorAll('tbody tr[data-role]').forEach(function(row){
      var role=row.dataset.role;
      var cell=row.querySelectorAll('td')[colIdx];
      if(cell)makeCell(cell,role,tasks[role]||[]);
    });
  }
  // swim lane
  syncTable(document.getElementById(fid),function(cell,role,rt){
    var btn=cell.querySelector('.btn-add');
    var ul=cell.querySelector('ul');
    var rn=cell.closest('tr').querySelector('td.role-name');
    var bcolor=rn?rn.style.borderLeftColor:'#888';
    if(rt.length){
      if(!ul){ul=document.createElement('ul');cell.insertBefore(ul,btn);}
      cell.classList.remove('empty');cell.classList.add('active');
      cell.style.borderTop='3px solid '+(bcolor.startsWith('rgb')?bcolor.replace(')',',.35)').replace('rgb','rgba'):bcolor);
      ul.innerHTML=rt.map(function(t){
        return '<li data-input="" data-output="" data-role="'+esc(role)+'" draggable="true">'+
          '<span class="task-drag-handle" title="Arrastar">&#8942;</span>'+
          '<span class="task-text" contenteditable="true" spellcheck="false">'+esc(t)+'</span>'+
          '<button class="btn-info" title="Detalhes" onclick="openTaskPanel(this.closest(\'li\'))">i</button>'+
          '<button class="btn-del" onclick="this.closest(\'li\').remove()">&#215;</button></li>';
      }).join('');
    } else {
      if(ul)ul.remove();
      cell.classList.remove('active');cell.classList.add('empty');
      cell.style.borderTop='';
    }
  });
  // task canvas nodes — update dtn-task text for matching nodes
  var tcanvas=document.getElementById('dtc-'+fid);
  if(tcanvas){
    tcanvas.querySelectorAll('.diag-task-node[data-step]').forEach(function(tn){
      if(tn.dataset.step!==step)return;
      var role=tn.dataset.role;
      var newTasks=tasks[role]||[];
      // update task text if it changed (simplest: no destructive changes to connections)
    });
  }
}

function syncNodeBody(node){
  var tasks=JSON.parse(node.dataset.tasks||'{}');
  var total=Object.values(tasks).reduce(function(s,t){return s+t.length;},0);
  node.querySelector('.dn-badge').textContent=total;
  var body=node.querySelector('.dn-body');body.innerHTML='';
  if(!total){body.innerHTML='<p class="dn-empty">Sem tarefas</p>';return;}
  Object.keys(tasks).forEach(function(role){
    if(!tasks[role].length)return;
    var c=rc(role);
    var g=document.createElement('div');g.className='dn-rg';
    g.innerHTML='<div class="dn-rg-hd"><span class="dn-dot" style="background:'+c+'"></span>'+
      '<span class="dn-rname">'+esc(role)+'</span>'+
      '<span class="dn-rcnt">'+tasks[role].length+'</span></div>'+
      '<ul class="dn-tasks">'+tasks[role].map(function(t){return'<li>'+esc(t)+'</li>';}).join('')+'</ul>';
    body.appendChild(g);
  });
}

function dlStageChecklist(){
  if(!_sNode)return;
  var step=_sNode.dataset.step;
  var tasks=JSON.parse(_sNode.dataset.tasks||'{}');
  var sec=_sNode.closest('.diagram-section');
  var flow=sec?sec.querySelector('h2').textContent.trim():'';
  var lines=['='.repeat(50),flow,'Etapa: '+step,'='.repeat(50),''];
  var total=0;
  Object.keys(tasks).forEach(function(role){
    lines.push('[ '+role.toUpperCase()+' ]');
    tasks[role].forEach(function(t){lines.push('  [ ] '+t);total++;});
    lines.push('');
  });
  lines.push('Total: '+total+' tarefa'+(total!==1?'s':''));
  var blob=new Blob([lines.join('\n')],{type:'text/plain;charset=utf-8'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='checklist-'+step.toLowerCase().replace(/\s+/g,'-').replace(/[^a-z0-9-]/g,'')+'.txt';
  document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(a.href);
}

// ── Task Detail Panel ─────────────────────────────────────────────────────────
var _tLi=null;
function openTaskPanel(li){
  _tLi=li;
  document.getElementById('tp-name').value=li.querySelector('.task-text').textContent.trim();
  document.getElementById('tp-input').value=li.dataset.input||'';
  document.getElementById('tp-output').value=li.dataset.output||'';
  document.getElementById('tp-role').value=li.dataset.role||'';
  document.getElementById('task-panel').classList.add('open');
  setTimeout(function(){var el=document.getElementById('tp-name');el.focus();el.select();},280);
}
function closeTaskPanel(){document.getElementById('task-panel').classList.remove('open');_tLi=null;hideAc('tp-role-list');}
function saveTaskPanel(){
  if(!_tLi)return;
  var name=document.getElementById('tp-name').value.trim();
  var inp=document.getElementById('tp-input').value.trim();
  var out=document.getElementById('tp-output').value.trim();
  var role=document.getElementById('tp-role').value.trim();
  if(name)_tLi.querySelector('.task-text').textContent=name;
  _tLi.dataset.input=inp;_tLi.dataset.output=out;_tLi.dataset.role=role;
  _tLi.classList.toggle('has-meta',!!(inp||out||role));
  closeTaskPanel();
}

// ── Autocomplete (generic) ────────────────────────────────────────────────────
function initAc(inputId,listId){
  var inp=document.getElementById(inputId),lst=document.getElementById(listId);
  if(!inp||!lst)return;
  var idx=-1;
  function show(q){
    idx=-1;
    var f=q?ROLES.filter(function(r){return r.toLowerCase().indexOf(q.toLowerCase())!==-1;}):ROLES.slice();
    lst.innerHTML='';
    if(!f.length){lst.classList.remove('show');return;}
    f.forEach(function(role){
      var li=document.createElement('li');
      var dot=document.createElement('span');dot.className='ac-dot';dot.style.background=rc(role);
      li.appendChild(dot);li.appendChild(document.createTextNode(role));
      li.addEventListener('mousedown',function(e){e.preventDefault();inp.value=role;lst.classList.remove('show');});
      lst.appendChild(li);
    });
    lst.classList.add('show');
  }
  function hide(){lst.classList.remove('show');idx=-1;}
  inp.addEventListener('input',function(){show(this.value);});
  inp.addEventListener('focus',function(){show(this.value);});
  inp.addEventListener('keydown',function(e){
    var items=lst.querySelectorAll('li');if(!items.length)return;
    if(e.key==='ArrowDown'){e.preventDefault();idx=Math.min(idx+1,items.length-1);items.forEach(function(it,i){it.classList.toggle('ac-s',i===idx);});}
    else if(e.key==='ArrowUp'){e.preventDefault();idx=Math.max(idx-1,0);items.forEach(function(it,i){it.classList.toggle('ac-s',i===idx);});}
    else if(e.key==='Enter'&&idx>=0){e.preventDefault();items[idx].dispatchEvent(new MouseEvent('mousedown'));}
    else if(e.key==='Escape')hide();
  });
  document.addEventListener('mousedown',function(e){if(!lst.contains(e.target)&&e.target!==inp)hide();});
}
function hideAc(listId){var l=document.getElementById(listId);if(l)l.classList.remove('show');}

// ── Role Management ───────────────────────────────────────────────────────────
function openRolePanel(){renderRoleList();document.getElementById('role-overlay').classList.remove('hidden');setTimeout(function(){document.getElementById('role-new-input').focus();},50);}
function closeRolePanel(){document.getElementById('role-overlay').classList.add('hidden');}
function renderRoleList(){
  var ul=document.getElementById('role-ul');ul.innerHTML='';
  ROLES.forEach(function(role){
    var li=document.createElement('li');
    var dot=document.createElement('span');dot.className='role-dot';dot.style.background=rc(role);
    var label=document.createElement('span');label.className='role-label';label.textContent=role;
    var del=document.createElement('button');del.className='role-del';del.textContent='×';
    del.onclick=(function(r){return function(){var i=ROLES.indexOf(r);if(i>-1)ROLES.splice(i,1);renderRoleList();};})(role);
    li.appendChild(dot);li.appendChild(label);li.appendChild(del);ul.appendChild(li);
  });
}
function addRoleFromInput(){
  var inp=document.getElementById('role-new-input'),name=inp.value.trim();
  if(!name||ROLES.indexOf(name)!==-1){inp.focus();return;}
  ROLES.push(name);inp.value='';renderRoleList();inp.focus();
}

// ── Role filter (inline, multi-select) ───────────────────────────────────────
var _rfRoles={};
function setRoleFilter(roleName,roleColor){
  if(_rfRoles[roleName]) delete _rfRoles[roleName];
  else _rfRoles[roleName]=roleColor||rc(roleName)||'#888';
  _applyRoleFilter();
}
function clearRoleFilter(){
  _rfRoles={};
  _applyRoleFilter();
}
function _applyRoleFilter(){
  var roles=Object.keys(_rfRoles);
  // update [data-role] elements
  document.querySelectorAll('[data-role]').forEach(function(el){
    el.classList.toggle('rf-match',roles.length>0&&roles.indexOf(el.dataset.role)>=0);
  });
  // update legend pill highlights (only .leg[data-role] pills in the cover)
  document.querySelectorAll('.leg[data-role]').forEach(function(leg){
    leg.classList.toggle('rf-on',!!_rfRoles[leg.dataset.role]);
  });
  // update filter bar
  var bar=document.getElementById('role-filter-bar');
  var chips=document.getElementById('rfb-chips');
  if(!bar)return;
  if(roles.length){
    bar.classList.add('on');
    document.body.classList.add('rf-active');
    if(chips){
      chips.innerHTML=roles.map(function(r){
        return '<span class="rfb-chip" style="background:'+_rfRoles[r]+'">'+esc(r)+'</span>';
      }).join('');
    }
  } else {
    bar.classList.remove('on');
    document.body.classList.remove('rf-active');
    if(chips) chips.innerHTML='';
  }
}

// ── Toast notification ────────────────────────────────────────────────────────
function showToast(msg,color){
  var t=document.getElementById('_toast');
  if(!t){
    t=document.createElement('div');t.id='_toast';
    t.style.cssText='position:fixed;bottom:22px;right:22px;padding:10px 18px;border-radius:8px;'+
      'color:#fff;font-size:12px;font-weight:700;z-index:9999;opacity:0;pointer-events:none;'+
      'transition:opacity .25s;box-shadow:0 4px 16px rgba(0,0,0,.2)';
    document.body.appendChild(t);
  }
  t.textContent=msg;t.style.background=color||'#2e7d32';t.style.opacity='1';
  clearTimeout(t._t);t._t=setTimeout(function(){t.style.opacity='0';},2800);
}

// ── Cloud save / load ─────────────────────────────────────────────────────────
function extractState(){
  var state={flows:[],roles:ROLES.slice(),view:document.body.dataset.view||'swim',activeFlow:_activeFlow};
  document.querySelectorAll('.flow-tab').forEach(function(tab){
    var fid=tab.dataset.fid;
    var sw=document.getElementById(fid);
    var dg=document.getElementById('diag-'+fid);
    if(!sw&&!dg)return;
    var lbl=tab.querySelector('.tab-lbl');
    var flowName=lbl?lbl.textContent.trim():fid;
    var color=tab.style.getPropertyValue('--tc').trim()||'#c62828';
    // steps from swim lane headers
    var steps=[];
    if(sw) sw.querySelectorAll('thead th.step-col span').forEach(function(s){steps.push(s.textContent.trim());});
    // tasks per step per role
    var data={};
    steps.forEach(function(s){data[s]={};});
    if(sw){
      sw.querySelectorAll('tbody tr[data-role]').forEach(function(row){
        var rn=row.querySelector('td.role-name span');if(!rn)return;
        var role=rn.textContent.trim();
        steps.forEach(function(step,si){
          var cell=row.querySelectorAll('td')[si+1];if(!cell)return;
          var tasks=[];
          cell.querySelectorAll('.task-text').forEach(function(t){var v=t.textContent.trim();if(v)tasks.push(v);});
          if(tasks.length){if(!data[step])data[step]={};data[step][role]=tasks;}
        });
      });
    }
    // diagram connections
    var dc=document.getElementById('dc-'+fid);
    var dtc=document.getElementById('dtc-'+fid);
    var stageConns=dc?JSON.parse(dc.dataset.conns||'[]'):[];
    var taskConns=dtc?JSON.parse(dtc.dataset.conns||'[]'):[];
    // task IO values keyed by node id
    var taskIO={};
    if(dtc){
      dtc.querySelectorAll('.diag-task-node').forEach(function(tn){
        var vals=tn.querySelectorAll('.dtn-val');
        var inp=vals[0]?vals[0].textContent.trim():'';
        var out=vals[1]?vals[1].textContent.trim():'';
        if(inp||out)taskIO[tn.id]={input:inp,output:out};
      });
    }
    // stage node task data (for sync)
    var stageTasks={};
    if(dg){
      dg.querySelectorAll('.diag-node:not(.diag-task-node)').forEach(function(nd){
        if(nd.dataset.step)stageTasks[nd.dataset.step]=nd.dataset.tasks||'{}';
      });
    }
    state.flows.push({id:fid,name:flowName,color:color,steps:steps,data:data,
      stageConns:stageConns,taskConns:taskConns,taskIO:taskIO,stageTasks:stageTasks});
  });
  return state;
}

function applyState(state){
  if(!state||!state.flows||!state.flows.length)return;
  // roles
  if(state.roles&&state.roles.length){
    ROLES.length=0;state.roles.forEach(function(r){ROLES.push(r);});
  }
  state.flows.forEach(function(flow){
    var fid=flow.id;
    var sw=document.getElementById(fid);
    var dg=document.getElementById('diag-'+fid);
    // update flow name in tab and header
    var tab=document.querySelector('.flow-tab[data-fid="'+fid+'"]');
    if(tab){var lbl=tab.querySelector('.tab-lbl');if(lbl)lbl.textContent=flow.name;}
    if(dg){var h2=dg.querySelector('h2');if(h2)h2.textContent=flow.name;}
    // update swim lane step headers
    if(sw&&flow.steps){
      var stepHdrs=sw.querySelectorAll('thead th.step-col span');
      flow.steps.forEach(function(step,si){if(stepHdrs[si])stepHdrs[si].textContent=step;});
    }
    // update swim lane tasks
    if(sw&&flow.data){
      sw.querySelectorAll('tbody tr[data-role]').forEach(function(row){
        var rn=row.querySelector('td.role-name span');if(!rn)return;
        var role=rn.textContent.trim();
        (flow.steps||[]).forEach(function(step,si){
          var cell=row.querySelectorAll('td')[si+1];if(!cell)return;
          var tasks=(flow.data[step]||{})[role]||[];
          var ul=cell.querySelector('ul');
          var btn=cell.querySelector('.btn-add');
          var rncell=row.querySelector('td.role-name');
          var bc=rncell?rncell.style.borderLeftColor:'#888';
          if(tasks.length){
            if(!ul){ul=document.createElement('ul');cell.insertBefore(ul,btn);}
            cell.classList.remove('empty');cell.classList.add('active');
            cell.style.borderTop='3px solid '+(bc.startsWith('rgb')?bc.replace(')',',.35)').replace('rgb','rgba'):bc);
            ul.innerHTML=tasks.map(function(t){
              return '<li data-input="" data-output="" data-role="'+esc(role)+'" draggable="true">'+
                '<span class="task-drag-handle" title="Arrastar">&#8942;</span>'+
                '<span class="task-text" contenteditable="true" spellcheck="false">'+esc(t)+'</span>'+
                '<button class="btn-info" onclick="openTaskPanel(this.closest(\'li\'))">i</button>'+
                '<button class="btn-del" onclick="this.closest(\'li\').remove()">&#215;</button></li>';
            }).join('');
          } else if(ul){
            ul.remove();cell.classList.remove('active');cell.classList.add('empty');cell.style.borderTop='';
          }
        });
      });
    }
    // restore stage diagram node task data
    if(dg&&flow.stageTasks){
      dg.querySelectorAll('.diag-node:not(.diag-task-node)').forEach(function(nd){
        if(flow.stageTasks[nd.dataset.step]) nd.dataset.tasks=flow.stageTasks[nd.dataset.step];
        syncNodeBody(nd);
      });
    }
    // restore connections
    var dc=document.getElementById('dc-'+fid);
    var dtc=document.getElementById('dtc-'+fid);
    if(dc&&flow.stageConns)dc.dataset.conns=JSON.stringify(flow.stageConns);
    if(dtc&&flow.taskConns)dtc.dataset.conns=JSON.stringify(flow.taskConns);
    // restore task IO
    if(dtc&&flow.taskIO){
      Object.keys(flow.taskIO).forEach(function(nid){
        var tn=document.getElementById(nid);if(!tn)return;
        var io=flow.taskIO[nid];
        var vals=tn.querySelectorAll('.dtn-val');
        if(vals[0]&&io.input)vals[0].textContent=io.input;
        if(vals[1]&&io.output)vals[1].textContent=io.output;
      });
    }
  });
  // set view / active flow
  if(state.view)setView(state.view);
  if(state.activeFlow)setActiveFlow(state.activeFlow);
  // redraw arrows after layout settles
  setTimeout(function(){
    state.flows.forEach(function(f){drawArrows(f.id);drawTaskArrows(f.id);});
  },120);
}

function saveToCloud(){
  var btn=document.querySelector('.btn-save');
  if(btn){btn.textContent='Salvando…';btn.disabled=true;}
  var state=extractState();
  fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state)})
    .then(function(r){return r.json();})
    .then(function(r){
      if(r.ok)showToast('✓ Salvo na nuvem','#2e7d32');
      else showToast('Erro ao salvar — verifique o banco','#c62828');
    })
    .catch(function(){showToast('Sem conexão com o servidor','#e65100');})
    .finally(function(){if(btn){btn.textContent='☁ Salvar';btn.disabled=false;}});
}

function loadFromCloud(){
  fetch('/api/load')
    .then(function(r){return r.json();})
    .then(function(state){
      if(state&&state.flows&&state.flows.length){
        applyState(state);
        showToast('Dados carregados ✓','#1565c0');
      }
    })
    .catch(function(){});
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',function(){
  var savedView=null,savedFlow=null;
  try{savedView=localStorage.getItem('uhull-view');savedFlow=localStorage.getItem('uhull-flow');}catch(e){}
  var firstTab=document.querySelector('.flow-tab');
  _activeFlow=savedFlow||(firstTab?firstTab.dataset.fid:null);
  setView(savedView||'swim');
  initAc('tp-role','tp-role-list');
  initAc('sp-role-in','sp-role-list');
  initTaskDrag();
  initDiagDrag();
  loadFromCloud();
  document.getElementById('role-new-input').addEventListener('keydown',function(e){if(e.key==='Enter')addRoleFromInput();});
  document.getElementById('sp-task-in').addEventListener('keydown',function(e){if(e.key==='Enter')addSpTask();});
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'){closeTaskPanel();closeStagePanel();closeRolePanel();clearRoleFilter();}
  });
  window.addEventListener('resize',function(){
    if(document.body.dataset.view==='diag'){
      document.querySelectorAll('[id^="dc-"]').forEach(function(c){_redrawCanvas(c);});
      document.querySelectorAll('[id^="dtc-"]').forEach(function(c){_redrawCanvas(c);});
    }
  });
});
"""

# ── Page builder ──────────────────────────────────────────────────────────────
def build_html(flows):
    import base64
    total = sum(task_count(f) for f in flows)
    gen   = date.today().strftime("%d/%m/%Y")
    logo_path = BASE / "assets" / "logo-roxo-300x82.png"
    logo_src  = ("data:image/png;base64," + base64.b64encode(logo_path.read_bytes()).decode()
                 if logo_path.exists() else "")

    roles_init = (
        "var ROLES="       + json.dumps(ROLE_ORDER, ensure_ascii=False) + ";\n"
        "var ROLE_COLORS=" + json.dumps(ROLE_COLOR,  ensure_ascii=False) + ";\n"
        "var FLOW_DATA="   + json.dumps([
            {"id":f["id"],"name":f["name"],"color":f["color"],"steps":f["steps"],
             "data":{s:dict(d) for s,d in f["data"].items()}}
            for f in flows
        ], ensure_ascii=False) + ";"
    )

    # Role legend (clickable)
    seen, seen_set = [], set()
    for f in flows:
        for sd in f["data"].values():
            for r in sd:
                if r not in seen_set: seen_set.add(r); seen.append(r)
    legend = "".join(
        f'<span class="leg" data-role="{esc(r)}" onclick="setRoleFilter(\'{esc(r)}\',\'{ROLE_COLOR.get(r,"#888")}\')">'
        f'<span class="dot" style="background:{ROLE_COLOR.get(r,"#888")}"></span>{esc(r)}</span>'
        for r in seen
    )

    # Flow tabs
    tabs = "".join(
        f'<button class="flow-tab" data-fid="{f["id"]}" '
        f'style="--tc:{f["color"]}" onclick="setActiveFlow(\'{f["id"]}\')">'
        f'<span class="tab-num">F{i}</span>'
        f'<span class="tab-lbl">{esc(f["name"].split(" — ",1)[-1])}</span>'
        f'</button>'
        for i, f in enumerate(flows, 1)
    )

    swim  = "\n".join(build_section(f, i)      for i, f in enumerate(flows, 1))
    diagr = "\n".join(build_diag_section(f, i) for i, f in enumerate(flows, 1))

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fluxos Operacionais</title>
<style>{CSS}</style>
</head>
<body data-view="swim">

<div class="cover">
  <h1>Fluxos Operacionais</h1>
  <p class="meta">{len(flows)} fluxos &#183; {total} tarefas &#183; edit&#225;vel no navegador</p>
  <div class="legend">{legend}</div>
</div>

<div class="nav-wrap">
  <div class="toolbar">
    {'<img src="' + logo_src + '" alt="Pinguim" class="nav-logo">' if logo_src else ''}
    <div class="view-toggle">
      <button class="btn-view active" data-view="swim" onclick="setView('swim')">Swim Lane</button>
      <button class="btn-view" data-view="diag" onclick="setView('diag')">Diagrama</button>
    </div>
    <div class="toolbar-actions">
      <button class="btn-action btn-roles" onclick="openRolePanel()">&#9784; Pap&#233;is</button>
      <button class="btn-action btn-save"  onclick="saveToCloud()">&#9729; Salvar</button>
      <button class="btn-action btn-pdf"   onclick="exportPDF()">&#128438; PDF</button>
    </div>
  </div>
  <div class="role-filter-bar" id="role-filter-bar">
    <span class="rfb-label">Filtro:</span>
    <div class="rfb-chips" id="rfb-chips"></div>
    <button class="rfb-clear" onclick="clearRoleFilter()">&#215; Limpar</button>
  </div>
  <div class="tab-bar" id="tab-bar">{tabs}<button class="btn-add-flow" onclick="addFlow()">+ Fluxo</button></div>
</div>

{swim}
{diagr}

<!-- Stage Panel -->
<div id="stage-panel" class="stage-panel">
  <div class="sp-hd">
    <div class="sp-hd-left">
      <label>Etapa</label>
      <div id="sp-title" class="sp-title" contenteditable="true" spellcheck="false"></div>
    </div>
    <button class="sp-close" onclick="closeStagePanel()">&#215;</button>
  </div>
  <div class="sp-subtabs">
    <button class="sp-sub active" data-sub="roles" onclick="setSpSub('roles',this)">Por Pap&#233;is</button>
    <button class="sp-sub" data-sub="tasks" onclick="setSpSub('tasks',this)">Por Tarefas</button>
  </div>
  <div class="sp-body" id="sp-body"></div>
  <div class="sp-add-area">
    <label>Adicionar Tarefa</label>
    <input type="text" class="sp-task-input" id="sp-task-in" placeholder="Descreva a tarefa&#8230;">
    <div class="ac-wrap sp-role-input-w">
      <input type="text" id="sp-role-in" placeholder="Papel respons&#225;vel&#8230;" autocomplete="off">
      <ul id="sp-role-list" class="ac-list"></ul>
    </div>
    <div class="sp-io-row">
      <input type="text" class="sp-task-input" id="sp-input-in" placeholder="Input (o que entra&#8230;)">
      <input type="text" class="sp-task-input" id="sp-output-in" placeholder="Output (o que sai&#8230;)">
    </div>
    <button class="sp-add-btn" onclick="addSpTask()">+ Adicionar Tarefa</button>
  </div>
  <div class="sp-footer">
    <button class="sp-dl" onclick="dlStageChecklist()">&#8681; Checklist</button>
    <button class="sp-done" onclick="closeStagePanel()">Conclu&#237;do</button>
  </div>
</div>

<!-- Task Detail Panel -->
<div id="task-panel" class="task-panel">
  <div class="tp-hd">
    <span>Detalhes da Tarefa</span>
    <button class="tp-close" onclick="closeTaskPanel()">&#215;</button>
  </div>
  <div class="tp-body">
    <div class="tp-field">
      <label>Tarefa</label>
      <input type="text" id="tp-name" placeholder="Nome da tarefa">
    </div>
    <div class="tp-field">
      <label>Input</label>
      <p class="help-text"><strong>Input</strong> &#233; tudo que precisa estar pronto <strong>antes</strong> desta tarefa: pr&#233;-requisitos, documentos, aprova&#231;&#245;es.</p>
      <textarea id="tp-input" placeholder="Ex: proposta aprovada, briefing do cliente&#8230;"></textarea>
    </div>
    <div class="tp-field">
      <label>Output</label>
      <p class="help-text"><strong>Output</strong> &#233; o que esta tarefa <strong>entrega</strong> ao final: resultado, documento gerado, pr&#243;xima etapa desbloqueada.</p>
      <textarea id="tp-output" placeholder="Ex: contrato assinado, roteiro enviado&#8230;"></textarea>
    </div>
    <div class="tp-field">
      <label>Papel Respons&#225;vel</label>
      <div class="ac-wrap">
        <input type="text" id="tp-role" placeholder="Digite para filtrar&#8230;" autocomplete="off">
        <ul id="tp-role-list" class="ac-list"></ul>
      </div>
    </div>
  </div>
  <div class="tp-footer">
    <button class="tp-save" onclick="saveTaskPanel()">Salvar</button>
    <button class="tp-cancel" onclick="closeTaskPanel()">Cancelar</button>
  </div>
</div>

<!-- Role Management -->
<div id="role-overlay" class="role-overlay hidden" onclick="if(event.target===this)closeRolePanel()">
  <div class="role-box">
    <div class="role-box-hd">
      <span>Cadastro de Pap&#233;is</span>
      <button class="role-box-close" onclick="closeRolePanel()">&#215;</button>
    </div>
    <div class="role-box-body">
      <div class="role-add-row">
        <input type="text" id="role-new-input" placeholder="Novo papel&#8230;">
        <button onclick="addRoleFromInput()">+ Adicionar</button>
      </div>
      <ul class="role-list-ul" id="role-ul"></ul>
    </div>
  </div>
</div>

<!-- Role Journey -->
<div id="rj-overlay" class="rj-overlay hidden" onclick="if(event.target===this)closeRoleView()">
  <div class="rj-box" id="rj-box">
    <div class="rj-hd">
      <span></span>
      <button class="rj-close" onclick="closeRoleView()">&#215;</button>
    </div>
    <div class="rj-body" id="rj-body"></div>
  </div>
</div>

<footer style="text-align:center;padding:16px 20px;color:var(--fnt);font-size:10px;background:var(--bg);border-top:1px solid var(--bdr)">
  Uhull &#183; Gerado em {gen} &#183; CHECK-LIST GERAL.xlsx + PDFs dos fluxos
</footer>

<script>
{roles_init}
{JS}
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("Lendo checklist...")
    flows = parse(INPUT)
    for f in flows:
        print(f"  {f['name']}: {len(f['steps'])} etapas, {task_count(f)} tarefas")
    print("\nGerando HTML...")
    OUTPUT.write_text(build_html(flows), encoding="utf-8")
    print(f"  Salvo: {OUTPUT.name}")
    print("\nViews: Swim Lane | Diagrama UML")
