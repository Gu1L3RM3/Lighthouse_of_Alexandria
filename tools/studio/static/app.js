"use strict";

// ---------------------------------------------------------------------------
// constants
// ---------------------------------------------------------------------------

const CELL = 64;                 // circuit board cell in world pixels (core.settings.CELL_SIZE)
const BOARD_COLS = 20;
const BOARD_ROWS = 10;
const BOARD_ORIGIN_Y = 2 * CELL; // the editor keeps two cells on top for its menu
const GID_MASK = 0x1fffffff;     // Tiled stores flip flags in the top bits
const SOLID_LAYERS = new Set(["obj", "obj2"]);
const POINT_HIT_RADIUS = 9;
const HISTORY_LIMIT = 100;
const SOLVE_DELAY_MS = 250;
const TWO_CELL_PARTS = new Set(["resistor", "voltage_source", "current_source"]);
const PART_PREFIX = { resistor: "R", voltage_source: "V", current_source: "I" };
const PART_DEFAULT_VALUE = { resistor: "100", voltage_source: "10", current_source: "0.01" };
const PART_LABEL = {
  resistor: "Resistor", voltage_source: "Fonte de tensão", current_source: "Fonte de corrente",
  wire: "Fio", node: "Nó", ground: "Terra",
};
const OBJECT_LABEL = {
  control_pannel: "Painel", resistor: "Resistor para coletar", voltage_source: "Fonte de tensão para coletar",
  current_source: "Fonte de corrente para coletar", crystal_invisibility: "Cristal de invisibilidade",
  anti_reaggro_flask: "Frasco anti-perseguição", old_paper: "Carta antiga", key: "Chave", player: "Jogador (início)",
  door: "Porta", arquimedes: "Arquimedes", iron_gate: "Portão de ferro",
};
const ANSWER_LABEL = {
  voltage: "tensão", current: "corrente", power: "potência", resistance: "resistência",
  "voltage;current": "tensão e corrente (Thévenin/Norton)", "power;resistance": "potência e resistência",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const state = {
  catalog: null,
  campaign: null,
  scene: null,
  level: null,
  check: null,
  tab: "map",
  dirty: { map: false, config: false, circuit: false },
  map: {
    tool: "brush", layer: 0, gid: 1, tileset: 0,
    view: { zoom: 2, x: 24, y: 24 },
    selected: null, placing: null,
    undo: [], redo: [],
    images: new Map(), cache: null,
    drag: null, hover: null,
  },
  circuit: {
    panel: null, variant: "", doc: { schema_version: 2, elements: [] },
    part: "select", rotation: 0, selected: null, drag: null, hover: null,
    solve: null, solveTimer: null, layout: null,
  },
};

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

async function api(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Erro ${response.status}`);
  return data;
}

function say(message, isError = false) {
  const status = $("#status");
  status.textContent = message;
  status.classList.toggle("error", isError);
}

async function attempt(action) {
  try {
    await action();
  } catch (error) {
    say(error.message, true);
  }
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (value === true) node.setAttribute(key, "");
    else if (value !== false && value != null) node.setAttribute(key, value);
  }
  node.append(...children.filter((child) => child != null));
  return node;
}

function css(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function prop(obj, name) {
  const found = (obj.properties || []).find((p) => p.name === name);
  return found ? found.value : undefined;
}

function isTyping(event) {
  return ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName);
}

function anyDirty() {
  return state.dirty.map || state.dirty.config || state.dirty.circuit;
}

function objectLabel(name) {
  return OBJECT_LABEL[name] || name || "Objeto";
}

function sizeCanvas(canvas) {
  const area = $("#stage-area");
  const ratio = window.devicePixelRatio || 1;
  const width = area.clientWidth;
  const height = area.clientHeight;
  if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.imageSmoothingEnabled = false;
  return { ctx, width, height };
}

function pointerPosition(event, canvas) {
  const rect = canvas.getBoundingClientRect();
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
}

// ---------------------------------------------------------------------------
// trail
// ---------------------------------------------------------------------------

async function showTrail() {
  if (anyDirty() && !confirm("Há alterações não salvas. Sair mesmo assim?")) return;
  state.scene = null;
  state.level = null;
  state.dirty = { map: false, config: false, circuit: false };
  $("#level-view").hidden = true;
  $("#level-actions").hidden = true;
  $("#trail-view").hidden = false;
  $("#crumb").textContent = "";
  await attempt(async () => {
    state.campaign = await api("GET", "/api/campaign");
    renderTrail();
  });
}

function renderTrail() {
  const { chain, stages, issues } = state.campaign;
  const stepByScene = new Map(chain.map((step) => [step.scene, step]));

  $("#trail-issues").replaceChildren(...issues.map((issue) => el("li", {}, issue)));
  $("#stages").replaceChildren(...stages.map((stage) => {
    const previous = chain[chain.findIndex((step) => step.scene === stage.levels[0]) - 1];
    const last = stepByScene.get(stage.levels[stage.levels.length - 1]);
    return el("li", { class: "stage" },
      el("div", { class: "stage-number" }, String(stage.number)),
      el("h2", {}, stage.title),
      el("p", { class: "lead-in" },
        previous ? `Chega de ${previous.scene}. ` : "",
        `Respostas: ${stage.answer_types.map((type) => ANSWER_LABEL[type] || type).join(", ")}.`),
      el("ol", { class: "level-list" }, ...stage.levels.map((scene) => levelCard(stage, scene, stepByScene.get(scene)))),
      last && last.next ? el("p", { class: "door-arrow" }, `A última porta leva a ${last.next}.`) : null,
    );
  }));
}

function levelCard(stage, scene, step) {
  const extra = !step.original;
  const actions = el("div", { class: "row-actions" });
  if (step.next) {
    actions.append(el("button", { type: "button", onclick: () => openInsertDialog(stage, scene) }, "Inserir fase depois"));
  }
  if (extra) {
    const others = stage.levels.filter((other) => other !== scene);
    const move = el("select", { "aria-label": `Mover ${scene} para depois de` },
      el("option", { value: "" }, "Mover para depois de…"),
      ...others.map((other) => el("option", { value: other }, other)));
    move.addEventListener("change", () => move.value && attempt(async () => {
      state.campaign = await api("POST", "/api/campaign/move", { scene, after: move.value });
      renderTrail();
      say(`${scene} agora vem depois de ${move.value}.`);
    }));
    actions.append(move, el("button", {
      type: "button", class: "danger",
      onclick: () => confirm(`Apagar ${scene}? O mapa e os circuitos dela serão removidos.`) && attempt(async () => {
        state.campaign = await api("POST", "/api/campaign/remove", { scene });
        renderTrail();
        say(`${scene} foi removida e a trilha foi religada.`);
      }),
    }, "Remover"));
  }
  return el("li", { class: `level-card${extra ? "" : " original"}` },
    el("button", { type: "button", class: "open", onclick: () => openLevel(scene) }, scene),
    el("span", { class: "tag" }, extra ? "fase extra" : "fase original"),
    actions,
  );
}

function openInsertDialog(stage, after) {
  const dialog = $("#insert-dialog");
  const form = $("#insert-form");
  $("#insert-stage").textContent = stage.number;
  $("#insert-after").textContent = after;
  form.elements.name.value = state.campaign.suggested_names[stage.number];
  form.elements.template.replaceChildren(...stage.levels.map((scene) =>
    el("option", { value: scene, selected: scene === after }, `Cópia de ${scene}`)),
    el("option", { value: "__blank__" }, "Mapa em branco, só com porta e jogador"));
  dialog.onclose = () => {
    if (dialog.returnValue !== "ok") return;
    attempt(async () => {
      const name = form.elements.name.value.trim();
      state.campaign = await api("POST", "/api/campaign/insert", {
        after, name, template: form.elements.template.value,
      });
      renderTrail();
      say(`${name} foi criada depois de ${after}.`);
    });
  };
  dialog.showModal();
}

// ---------------------------------------------------------------------------
// level
// ---------------------------------------------------------------------------

async function openLevel(scene) {
  await attempt(async () => {
    state.level = await api("GET", `/api/level?scene=${encodeURIComponent(scene)}`);
    state.scene = scene;
    state.dirty = { map: false, config: false, circuit: false };
    const m = state.map;
    m.undo = []; m.redo = []; m.selected = null; m.placing = null; m.cache = null;
    m.layer = Math.max(0, state.level.map.layers.findIndex((layer) => layer.name === "ground"));
    $("#trail-view").hidden = true;
    $("#level-view").hidden = false;
    $("#level-actions").hidden = false;
    $("#crumb").textContent = `${scene}, etapa ${state.level.stage.number}: ${state.level.stage.title}`;
    await loadTilesetImages();
    m.cache = null; // a resize may have drawn the cache before the tileset images arrived
    fillMapControls();
    fillParams();
    fillPanelSelect();
    setTab("map");
    centerMap();
    await refreshCheck();
    say("Fase aberta.");
  });
}

async function saveLevel() {
  const body = {};
  if (state.dirty.map) body.map = { layers: state.level.map.layers, objectgroups: state.level.map.objectgroups };
  if (state.dirty.config) body.config = readParams();
  if (Object.keys(body).length) {
    const selectedId = selectedObject()?.id;
    const fresh = await api("PUT", `/api/level?scene=${encodeURIComponent(state.scene)}`, body);
    state.level.map = fresh.map;
    state.level.config = fresh.config;
    state.map.selected = selectedId != null ? findObjectRef(selectedId) : null;
    state.map.cache = null;
  }
  if (state.dirty.circuit) await saveCircuit();
  state.dirty.map = false;
  state.dirty.config = false;
  fillPanelSelect();
  await refreshCheck();
  renderMap();
  renderInspector();
}

async function refreshCheck() {
  state.check = await api("GET", `/api/check?scene=${encodeURIComponent(state.scene)}`);
  renderChecklist();
}

// ---------------------------------------------------------------------------
// checklist
// ---------------------------------------------------------------------------

function quantityLabel(name, quantity) {
  // The game formats resistance without a unit symbol.
  return name === "resistance" ? `${quantity.label}Ω` : quantity.label;
}

function describeExpected(expected) {
  return Object.entries(expected).map(([key, values]) => {
    if (values.label) return `${key === "resistance" ? "Resistência equivalente" : key}: ${quantityLabel(key, values)}`;
    const name = key.startsWith("thevenin_") ? `Thévenin em ${key.slice(9)}` : key;
    return `${name}: ${Object.entries(values).map(([kind, v]) => quantityLabel(kind, v)).join(", ")}`;
  }).join("; ");
}

function renderChecklist() {
  const check = state.check;
  const panels = [...check.panels].sort((a, b) => a.id - b.id);
  $("#lamps").replaceChildren(...panels.map((panel) => {
    const ok = panel.problems.length === 0;
    return el("li", {},
      el("button", {
        type: "button",
        class: `lamp ${ok ? "lit" : "fault"}`,
        title: ok ? "Abrir o gabarito deste painel" : panel.problems.join(" "),
        onclick: () => openPanelCircuit(panel.id),
      }, `Painel ${panel.id}`));
  }));
  const lines = [
    ...check.problems.map((problem) => el("li", { class: "fault" }, problem)),
    ...panels.map((panel) => panel.problems.length
      ? el("li", { class: "fault" }, `Painel ${panel.id}: ${panel.problems.join(" ")}`)
      : el("li", {}, `Painel ${panel.id} pronto. Com os valores atuais do gabarito: ${describeExpected(panel.expected) || "sem valores"}.`)),
  ];
  if (!check.panels.length && !check.problems.length) lines.push(el("li", {}, "Nenhum painel ainda."));
  $("#check-detail").replaceChildren(el("ul", {}, ...lines));
}

function openPanelCircuit(panelId) {
  attempt(async () => {
    setTab("circuit");
    $("#panel-select").value = String(panelId);
    await switchCircuit(String(panelId), "_solution");
  });
}

// ---------------------------------------------------------------------------
// tabs
// ---------------------------------------------------------------------------

function setTab(tab) {
  state.tab = tab;
  $$(".tab").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.tab === tab)));
  $("#map-toolbar").hidden = tab !== "map";
  $("#circuit-toolbar").hidden = tab !== "circuit";
  $("#map-canvas").hidden = tab !== "map";
  $("#circuit-canvas").hidden = tab !== "circuit";
  $("#params-form").hidden = tab !== "params";
  $("#palette-wrap").hidden = tab !== "map";
  $("#level-view").classList.toggle("no-inspector", tab === "params");
  if (tab === "circuit" && state.circuit.panel == null) {
    const first = $("#panel-select").value;
    if (first) attempt(() => switchCircuit(first, state.circuit.variant));
  }
  renderMap();
  renderCircuit();
  renderInspector();
}

// ---------------------------------------------------------------------------
// parameters
// ---------------------------------------------------------------------------

function fillParams() {
  const form = $("#params-form");
  for (const [key, value] of Object.entries(state.level.config)) {
    if (form.elements[key]) form.elements[key].value = value;
  }
}

function readParams() {
  const form = $("#params-form");
  return {
    title: form.elements.title.value.trim(),
    tolerance_percent: Number(form.elements.tolerance_percent.value),
    bomb_count: Number(form.elements.bomb_count.value),
    ghost_respawn_seconds: Number(form.elements.ghost_respawn_seconds.value),
  };
}

// ---------------------------------------------------------------------------
// map editor
// ---------------------------------------------------------------------------

function tilesetUrl(tileset) {
  return `/tiles?scene=${encodeURIComponent(state.scene)}&image=${encodeURIComponent(tileset.image)}`;
}

async function loadTilesetImages() {
  const images = state.map.images;
  await Promise.all(state.level.map.tilesets.filter((ts) => ts.image).map((ts) => {
    const url = tilesetUrl(ts);
    if (images.has(url)) return null;
    return new Promise((resolve) => {
      const image = new Image();
      image.onload = () => { images.set(url, image); resolve(); };
      image.onerror = () => resolve();
      image.src = url;
    });
  }));
}

function tileSource(gid) {
  const raw = gid & GID_MASK;
  if (!raw) return null;
  let tileset = null;
  for (const ts of state.level.map.tilesets) if (ts.firstgid <= raw) tileset = ts;
  if (!tileset || !tileset.image || !tileset.columns) return null;
  const image = state.map.images.get(tilesetUrl(tileset));
  if (!image) return null;
  const local = raw - tileset.firstgid;
  return {
    image,
    sx: (local % tileset.columns) * tileset.tilewidth,
    sy: Math.floor(local / tileset.columns) * tileset.tileheight,
    w: tileset.tilewidth,
    h: tileset.tileheight,
  };
}

function fillMapControls() {
  const map = state.level.map;
  $("#layer-select").replaceChildren(...map.layers.map((layer, index) =>
    el("option", { value: index, selected: index === state.map.layer },
      SOLID_LAYERS.has(layer.name) ? `${layer.name} (paredes)` : layer.name)));
  const usable = map.tilesets.map((ts, index) => [ts, index]).filter(([ts]) => ts.image && ts.columns);
  state.map.tileset = usable.length ? usable[0][1] : 0;
  $("#tileset-select").replaceChildren(...usable.map(([ts, index]) => el("option", { value: index }, ts.name)));
  const templates = state.catalog.templates;
  const groups = new Set(map.objectgroups.map((group) => group.name));
  $("#object-kind").replaceChildren(...Object.keys(templates)
    .filter((name) => groups.has(templates[name].layer))
    .sort((a, b) => objectLabel(a).localeCompare(objectLabel(b)))
    .map((name) => el("option", { value: name }, objectLabel(name))));
  setMapTool(state.map.tool);
  renderPalette();
}

function setMapTool(tool) {
  state.map.tool = tool;
  state.map.placing = null;
  $$(".tool").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.tool === tool)));
}

function renderPalette() {
  const ts = state.level.map.tilesets[state.map.tileset];
  const canvas = $("#palette");
  if (!ts || !ts.image) return;
  const image = state.map.images.get(tilesetUrl(ts));
  if (!image) return;
  const scale = paletteScale(image);
  canvas.width = image.width * scale;
  canvas.height = image.height * scale;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
  const local = (state.map.gid & GID_MASK) - ts.firstgid;
  if (local >= 0 && local < ts.tilecount) {
    ctx.strokeStyle = css("--lamp");
    ctx.lineWidth = 2;
    ctx.strokeRect((local % ts.columns) * ts.tilewidth * scale + 1, Math.floor(local / ts.columns) * ts.tileheight * scale + 1,
      ts.tilewidth * scale - 2, ts.tileheight * scale - 2);
  }
  canvas.style.width = `${canvas.width}px`;
}

function paletteScale(image) {
  const available = $("#palette-wrap").clientWidth || image.width;
  return Math.max(1, Math.min(3, Math.floor(((available - 4) / image.width) * 4) / 4));
}

function centerMap() {
  const area = $("#stage-area");
  const map = state.level.map;
  const widthPx = map.width * map.tilewidth;
  const heightPx = map.height * map.tileheight;
  const margin = 16;
  const fit = Math.min((area.clientWidth - 2 * margin) / widthPx, (area.clientHeight - 2 * margin) / heightPx);
  // Whole-step zooms keep the pixel art crisp; below 1x any fit is fine, the map must stay inside the frame.
  const zoom = fit >= 1 ? Math.min(3, Math.floor(fit)) : Math.max(0.1, fit);
  state.map.view = { zoom, x: (area.clientWidth - widthPx * zoom) / 2, y: (area.clientHeight - heightPx * zoom) / 2 };
  state.map.userMoved = false;
}

function buildCache() {
  const map = state.level.map;
  const canvas = document.createElement("canvas");
  canvas.width = map.width * map.tilewidth;
  canvas.height = map.height * map.tileheight;
  state.map.cache = canvas;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  for (let row = 0; row < map.height; row += 1) {
    for (let col = 0; col < map.width; col += 1) drawCacheCell(ctx, col, row);
  }
}

function drawCacheCell(ctx, col, row) {
  const map = state.level.map;
  const x = col * map.tilewidth;
  const y = row * map.tileheight;
  ctx.clearRect(x, y, map.tilewidth, map.tileheight);
  for (const layer of map.layers) {
    const gid = layer.data[row * layer.width + col];
    const source = gid ? tileSource(gid) : null;
    if (source) ctx.drawImage(source.image, source.sx, source.sy, source.w, source.h, x, y, map.tilewidth, map.tileheight);
  }
}

function worldFromScreen(point) {
  const view = state.map.view;
  return { x: (point.x - view.x) / view.zoom, y: (point.y - view.y) / view.zoom };
}

function cellFromWorld(world) {
  const map = state.level.map;
  const col = Math.floor(world.x / map.tilewidth);
  const row = Math.floor(world.y / map.tileheight);
  if (col < 0 || row < 0 || col >= map.width || row >= map.height) return null;
  return { col, row };
}

function objectBounds(obj) {
  if (obj.shape === "tile") return { x: obj.x, y: obj.y - (obj.height || 16), w: obj.width || 16, h: obj.height || 16 };
  if (obj.shape === "point" || !obj.width) return null;
  return { x: obj.x, y: obj.y, w: obj.width, h: obj.height || 0 };
}

function* allObjects() {
  const groups = state.level.map.objectgroups;
  for (let g = 0; g < groups.length; g += 1) {
    for (let o = 0; o < groups[g].objects.length; o += 1) yield { g, o, obj: groups[g].objects[o] };
  }
}

function selectedObject() {
  const ref = state.map.selected;
  return ref ? state.level.map.objectgroups[ref.g]?.objects[ref.o] : null;
}

function findObjectRef(id) {
  for (const { g, o, obj } of allObjects()) if (obj.id === id) return { g, o };
  return null;
}

function hitObject(world) {
  let hit = null;
  const radius = POINT_HIT_RADIUS / state.map.view.zoom * 2;
  for (const entry of allObjects()) {
    const bounds = objectBounds(entry.obj);
    if (bounds) {
      if (world.x >= bounds.x && world.x <= bounds.x + bounds.w && world.y >= bounds.y && world.y <= bounds.y + bounds.h) {
        // Prefer named objects over the circuit decorations drawn as tiles.
        if (!hit || entry.obj.name || !hit.obj.name) hit = entry;
      }
    } else if (Math.hypot(world.x - entry.obj.x, world.y - entry.obj.y) <= radius) {
      hit = entry;
    }
  }
  return hit;
}

function pushHistory() {
  const map = state.level.map;
  state.map.undo.push(JSON.stringify({ layers: map.layers, objectgroups: map.objectgroups, nextobjectid: map.nextobjectid }));
  if (state.map.undo.length > HISTORY_LIMIT) state.map.undo.shift();
  state.map.redo = [];
  state.dirty.map = true;
}

function restoreHistory(from, to) {
  const snapshot = from.pop();
  if (!snapshot) return;
  const map = state.level.map;
  to.push(JSON.stringify({ layers: map.layers, objectgroups: map.objectgroups, nextobjectid: map.nextobjectid }));
  Object.assign(map, JSON.parse(snapshot));
  state.map.selected = null;
  state.map.cache = null;
  state.dirty.map = true;
  renderMap();
  renderInspector();
}

function setTile(col, row, gid) {
  const layer = state.level.map.layers[state.map.layer];
  const index = row * layer.width + col;
  if (layer.data[index] === gid) return;
  layer.data[index] = gid;
  if (state.map.cache) drawCacheCell(state.map.cache.getContext("2d"), col, row);
}

function floodFill(col, row, gid) {
  const layer = state.level.map.layers[state.map.layer];
  const target = layer.data[row * layer.width + col];
  if (target === gid) return;
  const stack = [[col, row]];
  while (stack.length) {
    const [c, r] = stack.pop();
    if (c < 0 || r < 0 || c >= layer.width || r >= layer.height) continue;
    if (layer.data[r * layer.width + c] !== target) continue;
    setTile(c, r, gid);
    stack.push([c + 1, r], [c - 1, r], [c, r + 1], [c, r - 1]);
  }
}

function nextPanelId() {
  const ids = [...allObjects()].filter(({ obj }) => obj.name === "control_pannel").map(({ obj }) => Number(prop(obj, "pannel_id")) || 0);
  return String(Math.max(0, ...ids) + 1);
}

function placeObject(world) {
  const name = state.map.placing;
  const template = state.catalog.templates[name];
  const group = state.level.map.objectgroups.findIndex((g) => g.name === template.layer);
  if (group < 0) {
    say(`Este mapa não tem a camada ${template.layer} para ${objectLabel(name)}.`, true);
    return;
  }
  pushHistory();
  const obj = JSON.parse(JSON.stringify(template.object));
  obj.x = Math.round(world.x);
  obj.y = Math.round(world.y);
  if (name === "control_pannel") {
    const id = obj.properties.find((p) => p.name === "pannel_id");
    if (id) id.value = nextPanelId();
    // The sample panel may come from another stage, whose answer types this stage can't validate.
    const answer = obj.properties.find((p) => p.name === "type_solution");
    if (answer) answer.value = state.level.stage.answer_types[0];
  }
  state.level.map.objectgroups[group].objects.push(obj);
  state.map.selected = { g: group, o: state.level.map.objectgroups[group].objects.length - 1 };
  state.map.placing = null;
  setMapTool("select");
  say(`${objectLabel(name)} colocado. Ajuste as propriedades ao lado e salve.`);
  renderInspector();
}

function onMapPointerDown(event) {
  const canvas = event.currentTarget;
  canvas.setPointerCapture(event.pointerId);
  const point = pointerPosition(event, canvas);
  const world = worldFromScreen(point);
  const m = state.map;
  if (event.button === 1 || event.button === 2 || event.altKey) {
    m.drag = { kind: "pan", start: point, view: { ...m.view } };
    return;
  }
  if (m.placing) {
    placeObject(world);
    renderMap();
    return;
  }
  const cell = cellFromWorld(world);
  switch (m.tool) {
    case "select": {
      const hit = hitObject(world);
      m.selected = hit ? { g: hit.g, o: hit.o } : null;
      if (hit) m.drag = { kind: "move", start: world, origin: { x: hit.obj.x, y: hit.obj.y }, pushed: false };
      else m.drag = { kind: "pan", start: point, view: { ...m.view } };
      renderInspector();
      break;
    }
    case "brush":
    case "erase":
      if (!cell) return;
      pushHistory();
      setTile(cell.col, cell.row, m.tool === "erase" ? 0 : m.gid);
      m.drag = { kind: "paint" };
      break;
    case "rect":
      if (!cell) return;
      m.drag = { kind: "rect", from: cell, to: cell };
      break;
    case "fill":
      if (!cell) return;
      pushHistory();
      floodFill(cell.col, cell.row, m.gid);
      break;
    case "pick": {
      if (!cell) return;
      const layer = state.level.map.layers[m.layer];
      const gid = layer.data[cell.row * layer.width + cell.col];
      if (gid) {
        m.gid = gid;
        setMapTool("brush");
        renderPalette();
      }
      break;
    }
    default:
      break;
  }
  renderMap();
}

function onMapPointerMove(event) {
  const point = pointerPosition(event, event.currentTarget);
  const world = worldFromScreen(point);
  const m = state.map;
  m.hover = cellFromWorld(world);
  const drag = m.drag;
  if (drag?.kind === "pan") {
    m.userMoved = true;
    m.view.x = drag.view.x + point.x - drag.start.x;
    m.view.y = drag.view.y + point.y - drag.start.y;
  } else if (drag?.kind === "move") {
    const obj = selectedObject();
    if (obj) {
      if (!drag.pushed) { pushHistory(); drag.pushed = true; }
      obj.x = Math.round(drag.origin.x + world.x - drag.start.x);
      obj.y = Math.round(drag.origin.y + world.y - drag.start.y);
      renderInspector();
    }
  } else if (drag?.kind === "paint" && m.hover) {
    setTile(m.hover.col, m.hover.row, m.tool === "erase" ? 0 : m.gid);
  } else if (drag?.kind === "rect" && m.hover) {
    drag.to = m.hover;
  }
  renderMap();
}

function onMapPointerUp() {
  const m = state.map;
  if (m.drag?.kind === "rect") {
    pushHistory();
    const { from, to } = m.drag;
    for (let row = Math.min(from.row, to.row); row <= Math.max(from.row, to.row); row += 1) {
      for (let col = Math.min(from.col, to.col); col <= Math.max(from.col, to.col); col += 1) setTile(col, row, m.gid);
    }
  }
  m.drag = null;
  renderMap();
}

function zoomAt(point, factor) {
  const view = state.map.view;
  const zoom = Math.min(8, Math.max(0.1, view.zoom * factor));
  state.map.userMoved = true;
  view.x = point.x - (point.x - view.x) * (zoom / view.zoom);
  view.y = point.y - (point.y - view.y) * (zoom / view.zoom);
  view.zoom = zoom;
  renderMap();
}

function renderMap() {
  if (!state.level || state.tab !== "map") return;
  const canvas = $("#map-canvas");
  const { ctx, width, height } = sizeCanvas(canvas);
  const map = state.level.map;
  const m = state.map;
  if (!m.cache) buildCache();
  const tile = map.tilewidth;
  const colors = { line: css("--line"), soft: css("--line-soft"), lamp: css("--lamp"), fault: css("--fault"), ink: css("--ink") };

  ctx.clearRect(0, 0, width, height);
  ctx.save();
  ctx.translate(m.view.x, m.view.y);
  ctx.scale(m.view.zoom, m.view.zoom);
  ctx.fillStyle = colors.ink;
  ctx.fillRect(0, 0, map.width * tile, map.height * tile);
  ctx.drawImage(m.cache, 0, 0);

  // Walls: tiles on the solid layers block the player, so show them even where the art is subtle.
  const current = map.layers[m.layer];
  if (current && SOLID_LAYERS.has(current.name)) {
    ctx.fillStyle = colors.fault;
    ctx.globalAlpha = 0.28;
    for (const layer of map.layers.filter((l) => SOLID_LAYERS.has(l.name))) {
      layer.data.forEach((gid, index) => {
        if (gid) ctx.fillRect((index % layer.width) * tile, Math.floor(index / layer.width) * tile, tile, tile);
      });
    }
    ctx.globalAlpha = 1;
  }

  for (const { obj } of allObjects()) {
    if (obj.shape !== "tile") continue;
    const source = tileSource(obj.gid);
    if (!source) continue;
    ctx.save();
    ctx.translate(obj.x, obj.y);
    if (obj.rotation) ctx.rotate((obj.rotation * Math.PI) / 180);
    ctx.drawImage(source.image, source.sx, source.sy, source.w, source.h, 0, -(obj.height || 16), obj.width || 16, obj.height || 16);
    ctx.restore();
  }

  ctx.lineWidth = 1 / m.view.zoom;
  ctx.strokeStyle = colors.soft;
  ctx.strokeRect(0, 0, map.width * tile, map.height * tile);

  if (m.drag?.kind === "rect") {
    const { from, to } = m.drag;
    ctx.strokeStyle = colors.lamp;
    ctx.lineWidth = 2 / m.view.zoom;
    ctx.strokeRect(Math.min(from.col, to.col) * tile, Math.min(from.row, to.row) * tile,
      (Math.abs(from.col - to.col) + 1) * tile, (Math.abs(from.row - to.row) + 1) * tile);
  } else if (m.hover && m.tool !== "select" && !m.placing) {
    ctx.strokeStyle = colors.line;
    ctx.lineWidth = 1.5 / m.view.zoom;
    ctx.strokeRect(m.hover.col * tile, m.hover.row * tile, tile, tile);
  }
  ctx.restore();

  drawObjectMarkers(ctx, colors);
}

function panelPassed(obj) {
  const panel = state.check?.panels.find((p) => p.object_id === obj.id);
  return panel && panel.problems.length === 0;
}

function drawObjectMarkers(ctx, colors) {
  const view = state.map.view;
  const selected = selectedObject();
  ctx.font = `700 12px ${css("--font-ui")}`;
  ctx.textBaseline = "bottom";
  for (const { obj } of allObjects()) {
    if (obj.shape === "tile" && !obj.name) {
      if (obj === selected) outlineBounds(ctx, obj, colors.lamp);
      continue;
    }
    const sx = obj.x * view.zoom + view.x;
    const sy = obj.y * view.zoom + view.y;
    const bounds = objectBounds(obj);
    if (bounds && obj.shape !== "tile") {
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = colors.soft;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(sx, sy, bounds.w * view.zoom, bounds.h * view.zoom);
      ctx.setLineDash([]);
    } else if (!bounds) {
      ctx.beginPath();
      ctx.arc(sx, sy, 6, 0, Math.PI * 2);
      const isPanel = obj.name === "control_pannel";
      ctx.fillStyle = isPanel && panelPassed(obj) ? colors.lamp : colors.ink;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = isPanel && !panelPassed(obj) ? colors.fault : colors.line;
      ctx.stroke();
    }
    if (obj === selected) outlineBounds(ctx, obj, colors.lamp);
    if (view.zoom >= 1) {
      let label = obj.name || "";
      if (obj.name === "control_pannel") label = `Painel ${prop(obj, "pannel_id")}`;
      else if (prop(obj, "valor")) label = `${objectLabel(obj.name)} ${prop(obj, "valor")}`;
      else label = objectLabel(obj.name);
      ctx.fillStyle = colors.line;
      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = 3;
      ctx.strokeText(label, sx + 9, sy - 4);
      ctx.fillText(label, sx + 9, sy - 4);
    }
  }
}

function outlineBounds(ctx, obj, color) {
  const view = state.map.view;
  const bounds = objectBounds(obj);
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  if (bounds) {
    ctx.strokeRect(bounds.x * view.zoom + view.x - 2, bounds.y * view.zoom + view.y - 2, bounds.w * view.zoom + 4, bounds.h * view.zoom + 4);
  } else {
    ctx.beginPath();
    ctx.arc(obj.x * view.zoom + view.x, obj.y * view.zoom + view.y, 11, 0, Math.PI * 2);
    ctx.stroke();
  }
}

// ---------------------------------------------------------------------------
// inspector
// ---------------------------------------------------------------------------

function renderInspector() {
  const props = $("#props");
  const results = $("#results");
  if (!state.level) return;
  if (state.tab === "map") {
    results.replaceChildren();
    const obj = selectedObject();
    props.replaceChildren(...(obj ? objectInspector(obj) : [
      el("h2", {}, "Objeto"),
      el("p", { class: "hint" }, "Use Mover e clique num objeto para editar. Para criar, escolha em Novo objeto e clique em Colocar."),
    ]));
  } else if (state.tab === "circuit") {
    props.replaceChildren(...circuitInspector());
    renderResults();
  } else {
    props.replaceChildren();
    results.replaceChildren();
  }
}

function valueChoices(obj, name) {
  if (name === "action" && obj.name === "control_pannel") return state.catalog.panel_actions;
  if (name === "type_solution") return state.level.stage.answer_types;
  if (name === "valor") {
    if (obj.name === "resistor") return state.catalog.resistors;
    if (obj.name === "voltage_source") return state.catalog.voltage_sources;
    if (obj.name === "current_source") return state.catalog.current_sources;
  }
  return null;
}

function objectInspector(obj) {
  const rows = [
    el("h2", {}, objectLabel(obj.name)),
    el("p", { class: "coords" }, `x ${obj.x}, y ${obj.y} (arraste no mapa para mover)`),
  ];
  for (const property of obj.properties) {
    rows.push(propertyEditor(obj, property));
  }
  rows.push(el("button", {
    type: "button", class: "danger",
    onclick: () => {
      pushHistory();
      const { g, o } = state.map.selected;
      state.level.map.objectgroups[g].objects.splice(o, 1);
      state.map.selected = null;
      renderMap();
      renderInspector();
    },
  }, "Apagar objeto"));
  return rows;
}

function propertyEditor(obj, property) {
  const commit = (value) => {
    pushHistory();
    property.value = value;
    renderMap();
  };
  const id = `prop-${obj.id ?? "new"}-${property.name}`;
  if (property.type === "bool") {
    return el("label", { class: "prop-row bool", for: id },
      el("input", { id, type: "checkbox", checked: property.value === "true", onchange: (e) => commit(String(e.target.checked)) }),
      el("span", { class: "name" }, property.name));
  }
  if (property.name === "next_scene") {
    return el("div", { class: "prop-row" }, el("span", { class: "name" }, "Leva para"),
      el("strong", {}, property.value), el("small", {}, "A trilha cuida disto."));
  }
  const choices = valueChoices(obj, property.name);
  let input;
  if (choices) {
    const options = choices.includes(property.value) ? choices : [property.value, ...choices];
    input = el("select", { id, onchange: (e) => commit(e.target.value) },
      ...options.map((choice) => el("option", { value: choice, selected: choice === property.value },
        property.name === "type_solution" ? `${ANSWER_LABEL[choice] || choice} (${choice})` : choice)));
  } else if (String(property.value).length > 60) {
    input = el("textarea", { id, rows: 4, onchange: (e) => commit(e.target.value) });
    input.value = property.value;
  } else {
    const numeric = property.type === "int" || property.type === "float";
    input = el("input", {
      id, type: numeric ? "number" : "text", step: property.type === "int" ? "1" : "any",
      value: property.value, onchange: (e) => commit(e.target.value),
    });
  }
  return el("label", { class: "prop-row", for: id }, el("span", { class: "name" }, property.name), input);
}

// ---------------------------------------------------------------------------
// circuit editor
// ---------------------------------------------------------------------------

function panelObjects() {
  return [...allObjects()].map(({ obj }) => obj).filter((obj) => obj.name === "control_pannel");
}

function fillPanelSelect() {
  const select = $("#panel-select");
  const current = select.value || state.circuit.panel;
  const ids = panelObjects().map((obj) => String(prop(obj, "pannel_id"))).sort((a, b) => Number(a) - Number(b));
  select.replaceChildren(...ids.map((id) => el("option", { value: id, selected: id === current }, `Painel ${id}`)));
  if (state.circuit.panel && !ids.includes(state.circuit.panel)) state.circuit.panel = null;
}

function circuitName(panel = state.circuit.panel, variant = state.circuit.variant) {
  return `pannel${panel}${variant}`;
}

async function switchCircuit(panel, variant) {
  const c = state.circuit;
  if (state.dirty.circuit && (panel !== c.panel || variant !== c.variant)) {
    if (confirm(`Salvar ${circuitName()}.json antes de trocar?`)) await saveCircuit();
    else state.dirty.circuit = false;
  }
  c.panel = panel;
  c.variant = variant;
  c.selected = null;
  $$(".variant").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.variant === variant)));
  $("#copy-problem").hidden = variant !== "_solution";
  c.doc = await api("GET", `/api/circuit?scene=${encodeURIComponent(state.scene)}&name=${circuitName()}`);
  renderCircuit();
  renderInspector();
  scheduleSolve();
}

async function saveCircuit() {
  const c = state.circuit;
  if (c.panel == null) return;
  await api("PUT", `/api/circuit?scene=${encodeURIComponent(state.scene)}&name=${circuitName()}`, c.doc);
  state.dirty.circuit = false;
}

function markCircuitChanged() {
  state.dirty.circuit = true;
  renderCircuit();
  renderInspector();
  scheduleSolve();
}

function scheduleSolve() {
  const c = state.circuit;
  clearTimeout(c.solveTimer);
  c.solveTimer = setTimeout(() => attempt(async () => {
    c.solve = c.doc.elements.length ? await api("POST", "/api/solve", c.doc) : null;
    renderCircuit();
    if (state.tab === "circuit") renderResults();
  }), SOLVE_DELAY_MS);
}

function isVertical(element) {
  return element.rotation === 90 || element.rotation === 270;
}

function elementCells(element) {
  const col = element.x / CELL;
  const row = (element.y - BOARD_ORIGIN_Y) / CELL;
  if (!TWO_CELL_PARTS.has(element.kind)) return [[col, row]];
  return isVertical(element) ? [[col, row], [col, row + 1]] : [[col, row], [col + 1, row]];
}

function fitsBoard(element, ignore = null) {
  const cells = elementCells(element);
  if (cells.some(([col, row]) => col < 0 || row < 0 || col >= BOARD_COLS || row >= BOARD_ROWS)) return false;
  const taken = new Set();
  circuitElements().forEach((other) => {
    if (other === ignore) return;
    elementCells(other).forEach(([col, row]) => taken.add(`${col},${row}`));
  });
  return cells.every(([col, row]) => !taken.has(`${col},${row}`));
}

function circuitElements() {
  return state.circuit.doc.elements;
}

function freeName(kind) {
  const prefix = PART_PREFIX[kind];
  const used = new Set(circuitElements().map((e) => e.name));
  let index = 1;
  while (used.has(`${prefix}${index}`)) index += 1;
  return `${prefix}${index}`;
}

function boardLayout(width, height) {
  const pad = 24;
  const size = Math.max(8, Math.floor(Math.min((width - 2 * pad) / BOARD_COLS, (height - 2 * pad) / BOARD_ROWS)));
  return {
    size,
    left: Math.round((width - size * BOARD_COLS) / 2),
    top: Math.round((height - size * BOARD_ROWS) / 2),
  };
}

function boardCell(point) {
  const layout = state.circuit.layout;
  if (!layout) return null;
  const col = Math.floor((point.x - layout.left) / layout.size);
  const row = Math.floor((point.y - layout.top) / layout.size);
  if (col < 0 || row < 0 || col >= BOARD_COLS || row >= BOARD_ROWS) return null;
  return { col, row };
}

function elementAt(cell) {
  if (!cell) return null;
  const list = circuitElements();
  for (let i = list.length - 1; i >= 0; i -= 1) {
    if (elementCells(list[i]).some(([col, row]) => col === cell.col && row === cell.row)) return list[i];
  }
  return null;
}

function newElement(kind, cell, rotation) {
  const element = { kind, x: cell.col * CELL, y: BOARD_ORIGIN_Y + cell.row * CELL, rotation, editable: false };
  if (PART_PREFIX[kind]) {
    element.name = freeName(kind);
    element.value = PART_DEFAULT_VALUE[kind];
  }
  if (kind === "ground") element.rotation = 0;
  return element;
}

function onCircuitPointerDown(event) {
  const canvas = event.currentTarget;
  canvas.setPointerCapture(event.pointerId);
  const cell = boardCell(pointerPosition(event, canvas));
  const c = state.circuit;
  if (c.panel == null) {
    say("Coloque um painel no mapa antes de desenhar o circuito.", true);
    return;
  }
  if (!cell) return;
  if (c.part === "select") {
    const hit = elementAt(cell);
    c.selected = hit;
    c.drag = hit ? { element: hit, start: cell, origin: { x: hit.x, y: hit.y } } : null;
    renderCircuit();
    renderInspector();
    return;
  }
  const element = newElement(c.part, cell, c.rotation);
  if (!fitsBoard(element)) {
    say("Não cabe aí: a peça sairia do quadro ou ficaria em cima de outra.", true);
    return;
  }
  circuitElements().push(element);
  c.selected = element;
  say(`${PART_LABEL[element.kind]} colocado.`);
  markCircuitChanged();
}

function onCircuitPointerMove(event) {
  const c = state.circuit;
  const cell = boardCell(pointerPosition(event, event.currentTarget));
  c.hover = cell;
  if (c.drag && cell) {
    const { element, start, origin } = c.drag;
    const moved = { ...element, x: origin.x + (cell.col - start.col) * CELL, y: origin.y + (cell.row - start.row) * CELL };
    if (fitsBoard(moved, element) && (moved.x !== element.x || moved.y !== element.y)) {
      element.x = moved.x;
      element.y = moved.y;
      c.drag.moved = true;
    }
  }
  renderCircuit();
}

function onCircuitPointerUp() {
  const c = state.circuit;
  if (c.drag?.moved) markCircuitChanged();
  c.drag = null;
}

function rotateCircuit() {
  const c = state.circuit;
  if (c.selected) {
    if (c.selected.kind === "ground") return;
    const rotated = { ...c.selected, rotation: (c.selected.rotation + 90) % 360 };
    if (!fitsBoard(rotated, c.selected)) {
      say("Girando assim a peça sairia do quadro ou bateria em outra.", true);
      return;
    }
    c.selected.rotation = rotated.rotation;
    markCircuitChanged();
  } else {
    c.rotation = (c.rotation + 90) % 360;
    say(`Próximas peças giradas em ${c.rotation}°.`);
    renderCircuit();
  }
}

function deleteSelectedPart() {
  const c = state.circuit;
  if (!c.selected) return;
  c.doc.elements = circuitElements().filter((element) => element !== c.selected);
  c.selected = null;
  markCircuitChanged();
}

function setPart(part) {
  state.circuit.part = part;
  if (part !== "select") state.circuit.selected = null;
  $$(".part").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.part === part)));
  renderCircuit();
  renderInspector();
}

function renderCircuit() {
  if (!state.level || state.tab !== "circuit") return;
  const canvas = $("#circuit-canvas");
  const { ctx, width, height } = sizeCanvas(canvas);
  const c = state.circuit;
  const layout = boardLayout(width, height);
  c.layout = layout;
  const colors = { line: css("--line"), soft: css("--line-soft"), grid: css("--grid"), lamp: css("--lamp"), ink: css("--ink"), paper: css("--paper") };

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = colors.paper;
  ctx.fillRect(layout.left, layout.top, layout.size * BOARD_COLS, layout.size * BOARD_ROWS);
  ctx.fillStyle = colors.grid;
  for (let row = 0; row <= BOARD_ROWS; row += 1) {
    for (let col = 0; col <= BOARD_COLS; col += 1) {
      ctx.fillRect(layout.left + col * layout.size - 1, layout.top + row * layout.size - 1, 2, 2);
    }
  }
  ctx.strokeStyle = colors.soft;
  ctx.lineWidth = 1;
  ctx.strokeRect(layout.left + 0.5, layout.top + 0.5, layout.size * BOARD_COLS, layout.size * BOARD_ROWS);

  if (c.panel == null) {
    ctx.fillStyle = colors.line;
    ctx.font = `16px ${css("--font-ui")}`;
    ctx.fillText("Este mapa ainda não tem painel. Coloque um na aba Mapa.", layout.left + 16, layout.top + 32);
    return;
  }

  for (const element of circuitElements()) drawPart(ctx, element, layout, colors, element === c.selected ? colors.lamp : colors.line);

  if (c.part !== "select" && c.hover) {
    const ghost = newElement(c.part, c.hover, c.rotation);
    ctx.globalAlpha = fitsBoard(ghost) ? 0.45 : 0.15;
    drawPart(ctx, ghost, layout, colors, colors.line);
    ctx.globalAlpha = 1;
  }
}

function partCenter(element, layout) {
  const left = layout.left + (element.x / CELL) * layout.size;
  const top = layout.top + ((element.y - BOARD_ORIGIN_Y) / CELL) * layout.size;
  if (!TWO_CELL_PARTS.has(element.kind)) return { x: left + layout.size / 2, y: top + layout.size / 2 };
  return isVertical(element)
    ? { x: left + layout.size / 2, y: top + layout.size }
    : { x: left + layout.size, y: top + layout.size / 2 };
}

function drawPart(ctx, element, layout, colors, stroke) {
  const s = layout.size;
  const center = partCenter(element, layout);
  ctx.save();
  ctx.translate(center.x, center.y);
  ctx.strokeStyle = stroke;
  ctx.fillStyle = stroke;
  ctx.lineWidth = Math.max(1.5, s / 22);
  ctx.lineCap = "round";
  if (element.editable) ctx.setLineDash([s / 8, s / 10]);
  // Parts are drawn along +x from terminal A to B; the game rotates them counterclockwise on screen.
  if (element.kind === "wire") {
    if (isVertical(element)) ctx.rotate(Math.PI / 2);
    line(ctx, -s / 2, 0, s / 2, 0);
  } else if (element.kind === "node") {
    line(ctx, -s / 2, 0, s / 2, 0);
    line(ctx, 0, -s / 2, 0, s / 2);
    ctx.beginPath();
    ctx.arc(0, 0, s / 9, 0, Math.PI * 2);
    ctx.fill();
  } else if (element.kind === "ground") {
    line(ctx, 0, -s / 2, 0, 0);
    line(ctx, -s / 3, 0, s / 3, 0);
    line(ctx, -s / 5, s / 8, s / 5, s / 8);
    line(ctx, -s / 12, s / 4, s / 12, s / 4);
  } else {
    ctx.rotate((-element.rotation * Math.PI) / 180);
    drawTwoTerminal(ctx, element.kind, s);
  }
  ctx.restore();
  if (element.name) drawPartLabel(ctx, element, center, s, colors);
}

function line(ctx, x1, y1, x2, y2) {
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

function drawTwoTerminal(ctx, kind, s) {
  if (kind === "resistor") {
    const half = s * 0.45;
    line(ctx, -s, 0, -half, 0);
    line(ctx, half, 0, s, 0);
    ctx.beginPath();
    ctx.moveTo(-half, 0);
    const zigs = 6;
    for (let i = 0; i < zigs; i += 1) {
      ctx.lineTo(-half + (2 * half * (i + 0.5)) / zigs, (i % 2 ? 1 : -1) * s * 0.18);
    }
    ctx.lineTo(half, 0);
    ctx.stroke();
    return;
  }
  const radius = s * 0.36;
  line(ctx, -s, 0, -radius, 0);
  line(ctx, radius, 0, s, 0);
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);
  if (kind === "voltage_source") {
    const mark = radius * 0.32;
    line(ctx, radius * 0.45 - mark, 0, radius * 0.45 + mark, 0);
    line(ctx, radius * 0.45, -mark, radius * 0.45, mark);
    line(ctx, -radius * 0.45 - mark, 0, -radius * 0.45 + mark, 0);
  } else {
    line(ctx, -radius * 0.55, 0, radius * 0.55, 0);
    ctx.beginPath();
    ctx.moveTo(radius * 0.6, 0);
    ctx.lineTo(radius * 0.2, -radius * 0.28);
    ctx.lineTo(radius * 0.2, radius * 0.28);
    ctx.closePath();
    ctx.fill();
  }
}

function drawPartLabel(ctx, element, center, s, colors) {
  const result = state.circuit.solve?.resistors?.[element.name];
  const lines = [`${element.name} ${element.value}`];
  if (result) lines.push(`${result.voltage.label}  ${result.current.label}`);
  ctx.font = `700 ${Math.max(10, Math.round(s / 5))}px ${css("--font-ui")}`;
  ctx.fillStyle = colors.line;
  ctx.strokeStyle = colors.paper;
  ctx.lineWidth = 3;
  // Vertical parts get their label beside the symbol; it flips to the left side near the board's right edge.
  const layout = state.circuit.layout;
  const widest = Math.max(...lines.map((text) => ctx.measureText(text).width));
  const flip = center.x + s * 0.5 + widest > layout.left + layout.size * BOARD_COLS;
  ctx.textAlign = !isVertical(element) ? "center" : flip ? "right" : "left";
  const offset = isVertical(element) ? { x: flip ? -s * 0.5 : s * 0.5, y: 0 } : { x: 0, y: -s * 0.42 };
  lines.forEach((text, index) => {
    const y = center.y + offset.y + (isVertical(element) ? (index - 0.5) * s / 4 : -(lines.length - 1 - index) * s / 4);
    ctx.strokeText(text, center.x + offset.x, y);
    ctx.fillText(text, center.x + offset.x, y);
  });
  ctx.textAlign = "start";
}

function circuitInspector() {
  const c = state.circuit;
  const header = [
    el("h2", {}, c.panel == null ? "Circuito" : `${circuitName()}.json`),
    el("p", { class: "hint" }, c.variant === "_solution"
      ? "Gabarito: o circuito montado do jeito certo. O jogo calcula a resposta esperada a partir dele."
      : "Problema: o que o aluno encontra no painel. Peças tracejadas o aluno pode mover."),
  ];
  const element = c.selected;
  if (!element) {
    return [...header, el("p", { class: "hint" }, "Escolha uma peça na barra e clique no quadro. R gira, Delete apaga.")];
  }
  const rows = [...header, el("h2", {}, PART_LABEL[element.kind])];
  if (element.name != null) {
    rows.push(el("label", {}, "Nome",
      el("input", { value: element.name, onchange: (e) => { element.name = e.target.value.trim(); markCircuitChanged(); } })));
    const pool = element.kind === "resistor" ? state.catalog.resistors
      : element.kind === "voltage_source" ? state.catalog.voltage_sources : state.catalog.current_sources;
    rows.push(el("label", {}, "Valor",
      el("input", { value: element.value, list: "value-pool", onchange: (e) => { element.value = e.target.value.trim(); markCircuitChanged(); } }),
      el("datalist", { id: "value-pool" }, ...pool.map((value) => el("option", { value }))),
      el("small", {}, "Aceita 220, 1k, 4.7k, 0.01…")));
  }
  rows.push(el("label", { class: "prop-row bool" },
    el("input", { type: "checkbox", checked: element.editable, onchange: (e) => { element.editable = e.target.checked; markCircuitChanged(); } }),
    el("span", {}, "O aluno pode mover esta peça")));
  rows.push(el("button", { type: "button", class: "danger", onclick: deleteSelectedPart }, "Apagar peça"));
  return rows;
}

function renderResults() {
  const results = $("#results");
  const solve = state.circuit.solve;
  if (!solve) {
    results.replaceChildren();
    return;
  }
  if (solve.error) {
    results.replaceChildren(el("h2", {}, "Medidas"), el("p", { class: "error" }, solve.error));
    return;
  }
  const rows = Object.entries(solve.resistors).map(([name, values]) =>
    el("tr", {}, el("td", {}, name), el("td", {}, values.voltage.label), el("td", {}, values.current.label), el("td", {}, values.power.label)));
  results.replaceChildren(
    el("h2", {}, "Medidas"),
    el("table", { class: "results" },
      el("thead", {}, el("tr", {}, el("th", {}, ""), el("th", {}, "Tensão"), el("th", {}, "Corrente"), el("th", {}, "Potência"))),
      el("tbody", {}, ...rows)),
    solve.totals ? el("p", { class: "hint" }, `Resistência equivalente vista pela fonte: ${solve.totals.resistance.label}Ω`) : null,
  );
}

// ---------------------------------------------------------------------------
// wiring
// ---------------------------------------------------------------------------

function bindEvents() {
  $("#go-trail").addEventListener("click", showTrail);
  $$(".tab").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
  $$(".tool").forEach((button) => button.addEventListener("click", () => setMapTool(button.dataset.tool)));
  $$(".part").forEach((button) => button.addEventListener("click", () => setPart(button.dataset.part)));
  $$(".variant").forEach((button) => button.addEventListener("click", () =>
    attempt(() => switchCircuit($("#panel-select").value, button.dataset.variant))));
  $("#panel-select").addEventListener("change", (e) => attempt(() => switchCircuit(e.target.value, state.circuit.variant)));
  $("#rotate").addEventListener("click", rotateCircuit);
  $("#copy-problem").addEventListener("click", () => attempt(async () => {
    if (circuitElements().length && !confirm("Trocar o gabarito atual por uma cópia do problema?")) return;
    const problem = await api("GET", `/api/circuit?scene=${encodeURIComponent(state.scene)}&name=${circuitName(state.circuit.panel, "")}`);
    state.circuit.doc = problem;
    state.circuit.selected = null;
    markCircuitChanged();
    say("Cópia do problema pronta. Agora complete o gabarito.");
  }));

  $("#layer-select").addEventListener("change", (e) => { state.map.layer = Number(e.target.value); renderMap(); });
  $("#tileset-select").addEventListener("change", (e) => { state.map.tileset = Number(e.target.value); renderPalette(); });
  $("#palette").addEventListener("click", (event) => {
    const ts = state.level.map.tilesets[state.map.tileset];
    const point = pointerPosition(event, event.currentTarget);
    const scale = event.currentTarget.width / state.map.images.get(tilesetUrl(ts)).width;
    const col = Math.floor(point.x / (ts.tilewidth * scale));
    const row = Math.floor(point.y / (ts.tileheight * scale));
    const local = row * ts.columns + col;
    if (col >= ts.columns || local >= ts.tilecount) return;
    state.map.gid = ts.firstgid + local;
    if (!["brush", "rect", "fill"].includes(state.map.tool)) setMapTool("brush");
    renderPalette();
  });
  $("#add-object").addEventListener("click", () => {
    const kind = $("#object-kind").value;
    if (!kind) return;
    state.map.placing = kind;
    say(`Clique no mapa onde quer colocar: ${objectLabel(kind)}.`);
  });
  $("#undo").addEventListener("click", () => restoreHistory(state.map.undo, state.map.redo));
  $("#redo").addEventListener("click", () => restoreHistory(state.map.redo, state.map.undo));
  $("#zoom-in").addEventListener("click", () => zoomAt({ x: $("#stage-area").clientWidth / 2, y: $("#stage-area").clientHeight / 2 }, 1.25));
  $("#zoom-out").addEventListener("click", () => zoomAt({ x: $("#stage-area").clientWidth / 2, y: $("#stage-area").clientHeight / 2 }, 0.8));

  const mapCanvas = $("#map-canvas");
  mapCanvas.addEventListener("pointerdown", onMapPointerDown);
  mapCanvas.addEventListener("pointermove", onMapPointerMove);
  mapCanvas.addEventListener("pointerup", onMapPointerUp);
  mapCanvas.addEventListener("pointerleave", () => { state.map.hover = null; renderMap(); });
  mapCanvas.addEventListener("contextmenu", (e) => e.preventDefault());
  mapCanvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(pointerPosition(event, mapCanvas), event.deltaY < 0 ? 1.15 : 1 / 1.15);
  }, { passive: false });

  const circuitCanvas = $("#circuit-canvas");
  circuitCanvas.addEventListener("pointerdown", onCircuitPointerDown);
  circuitCanvas.addEventListener("pointermove", onCircuitPointerMove);
  circuitCanvas.addEventListener("pointerup", onCircuitPointerUp);
  circuitCanvas.addEventListener("pointerleave", () => { state.circuit.hover = null; renderCircuit(); });

  $("#params-form").addEventListener("input", () => { state.dirty.config = true; });
  $("#params-form").addEventListener("submit", (e) => e.preventDefault());

  $("#save").addEventListener("click", () => attempt(async () => {
    await saveLevel();
    say("Fase salva.");
  }));
  $("#play").addEventListener("click", () => attempt(async () => {
    await saveLevel();
    await api("POST", "/api/play", { scene: state.scene });
    say(`Abrindo o jogo direto em ${state.scene}…`);
  }));

  $("#help-open").addEventListener("click", () => openHelp());
  $("#help-close").addEventListener("click", () => $("#help-dialog").close());
  $$(".help-nav button").forEach((button) => button.addEventListener("click", () => showHelpPage(button.dataset.help)));
  $("#help-dialog").addEventListener("click", (event) => {
    // The backdrop counts as the dialog itself, so close only when the click lands outside the sheet.
    const sheet = event.currentTarget.getBoundingClientRect();
    if (event.clientX < sheet.left) event.currentTarget.close();
  });
  $("#fullscreen").addEventListener("click", toggleFullscreen);
  document.addEventListener("fullscreenchange", syncFullscreenButton);
  document.addEventListener("keydown", onKey);
  window.addEventListener("beforeunload", (event) => {
    if (anyDirty()) event.preventDefault();
  });
  new ResizeObserver(() => {
    // Keep the whole map in view until the teacher zooms or pans on their own.
    if (state.level && !state.map.userMoved && $("#stage-area").clientWidth) centerMap();
    renderMap();
    renderCircuit();
  }).observe($("#stage-area"));
}

function toggleFullscreen() {
  // The whole page goes fullscreen, not just the canvas, so the insert dialog and confirms still show.
  const request = document.fullscreenElement
    ? document.exitFullscreen()
    : document.documentElement.requestFullscreen({ navigationUI: "hide" });
  request.catch(() => say("O navegador não deixou usar a tela cheia.", true));
}

function syncFullscreenButton() {
  const on = Boolean(document.fullscreenElement);
  const button = $("#fullscreen");
  button.setAttribute("aria-pressed", String(on));
  button.textContent = on ? "Sair da tela cheia" : "Tela cheia";
}

const HELP_SEEN_KEY = "studio-help-seen";

function currentHelpPage() {
  return state.level ? state.tab : "trail";
}

function showHelpPage(page) {
  $$(".help-page").forEach((section) => { section.hidden = section.dataset.page !== page; });
  $$(".help-nav button").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.help === page)));
}

function openHelp(page = currentHelpPage()) {
  showHelpPage(page);
  const dialog = $("#help-dialog");
  if (!dialog.open) dialog.showModal();
}

function openHelpOnFirstVisit() {
  // Per-browser convenience only; private windows may block storage, and then help just doesn't auto-open.
  try {
    if (localStorage.getItem(HELP_SEEN_KEY)) return;
    localStorage.setItem(HELP_SEEN_KEY, "1");
  } catch {
    return;
  }
  openHelp("start");
}

function onKey(event) {
  if (event.key === "?" && !isTyping(event)) {
    event.preventDefault();
    openHelp();
    return;
  }
  if (!state.level || isTyping(event)) return;
  const key = event.key.toLowerCase();
  if ((event.ctrlKey || event.metaKey) && key === "s") {
    event.preventDefault();
    $("#save").click();
    return;
  }
  if (state.tab === "map") {
    if ((event.ctrlKey || event.metaKey) && key === "z") { event.preventDefault(); restoreHistory(state.map.undo, state.map.redo); return; }
    if ((event.ctrlKey || event.metaKey) && key === "y") { event.preventDefault(); restoreHistory(state.map.redo, state.map.undo); return; }
    const tools = { v: "select", b: "brush", e: "erase", u: "rect", f: "fill", i: "pick" };
    if (tools[key]) setMapTool(tools[key]);
    if (key === "+" || key === "=") $("#zoom-in").click();
    if (key === "-") $("#zoom-out").click();
    if ((key === "delete" || key === "backspace") && selectedObject()) $("#props button.danger").click();
    if (key === "escape") { state.map.placing = null; state.map.selected = null; renderMap(); renderInspector(); }
  } else if (state.tab === "circuit") {
    const parts = { s: "select", w: "wire", n: "node", g: "ground" };
    if (parts[key]) setPart(parts[key]);
    if (key === "r") rotateCircuit();
    if (key === "delete" || key === "backspace") deleteSelectedPart();
    if (key === "escape") setPart("select");
  }
}

async function start() {
  bindEvents();
  setPart("select");
  await attempt(async () => {
    state.catalog = await api("GET", "/api/catalog");
  });
  await showTrail();
  openHelpOnFirstVisit();
}

start();
