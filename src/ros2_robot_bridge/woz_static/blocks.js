// blocks.js — Visual block programming for the WOZ robot interface

// ─── Block definitions ────────────────────────────────────────────────────────

var MOTIONS_LIST = [
  ['Debout',       'stand'],     ['Assis',        'sit'],
  ['Saluer',       'wave'],      ['Applaudir',    'applause'],
  ['Arc',          'bow'],       ['Oui',          'nod'],
  ['Non',          'shake_head'],['Bras ouverts', 'arms_open'],
  ['Donner',       'give'],      ['Pointer',      'point_forward'],
  ['Content',      'happy_anim'],['Triste',       'sad_anim'],
  ['Rire',         'laugh_anim'],['Peur',         'fear'],
  ['Confus',       'confused_anim'], ['Fort!',    'show_muscles'],
  ['Réfléchir',   'scratch_head'],['Danse',      'funny_dancer'],
  ['Coucou',       'peekaboo'],  ['Câlin',        'love_you'],
  ['Avancer',      'walk_forward'], ['Reculer',   'walk_backward'],
  ['Tourner G',    'turn_left'], ['Tourner D',   'turn_right'],
  ['Stop',         'stop'],
];

var LED_LIST = [
  ['Yeux',         'eyes'],      ['Yeux gauche',  'left_eye'],
  ['Yeux droit',   'right_eye'], ['Oreilles',     'ears'],
  ['Poitrine',     'chest'],     ['Pieds',        'feet'],
  ['Tout',         'all'],
];

var BLOCK_DEFS = {
  move: {
    label: 'Mouvement', icon: '🤖', cat: 'action', color: '#1b5e20',
    fields: [
      { name: 'motion', type: 'select', options: MOTIONS_LIST, def: 'bow' },
      { name: 'speed',  type: 'range',  label: 'Vitesse', min: 0.1, max: 1.0, step: 0.1, def: 0.5 },
    ],
  },
  speak: {
    label: 'Parler', icon: '💬', cat: 'action', color: '#0d47a1',
    fields: [
      { name: 'text', type: 'text', placeholder: 'Texte à dire…', def: 'Bonjour !' },
    ],
  },
  led: {
    label: 'LEDs', icon: '💡', cat: 'action', color: '#006064',
    fields: [
      { name: 'led_name', type: 'select', options: LED_LIST, def: 'eyes' },
      { name: 'color',    type: 'color',  def: '#ffff00' },
    ],
  },
  wait: {
    label: 'Attendre', icon: '⏱', cat: 'control', color: '#bf360c',
    fields: [
      { name: 'seconds', type: 'number', min: 0.1, max: 60, step: 0.5, def: 2, suffix: 's' },
    ],
  },
  repeat: {
    label: 'Répéter', icon: '🔁', cat: 'control', color: '#4a148c',
    container: true,
    fields: [
      { name: 'count', type: 'number', min: 1, max: 999, step: 1, def: 3, suffix: '×' },
    ],
  },
  if_else: {
    label: 'Si … Alors', icon: '🔀', cat: 'control', color: '#880e4f',
    container: true, hasElse: true,
    fields: [
      { name: 'condition', type: 'select', options: [
        ['Toujours',         'always'],
        ['Jamais',           'never'],
        ['Aléatoire 50/50',  'random'],
      ], def: 'always' },
    ],
  },
};

// ─── State ────────────────────────────────────────────────────────────────────

var prog    = [];    // root block array
var dragSrc = null;  // set during drag
var pollTimer = null;

var DRAFT_KEY = 'woz_blocks_draft_' + (typeof WOZ_RID !== 'undefined' ? WOZ_RID : '0');
var SAVED_KEY = 'woz_blocks_saved_' + (typeof WOZ_RID !== 'undefined' ? WOZ_RID : '0');

// ─── ID generator ─────────────────────────────────────────────────────────────

var _uid = 0;
function uid() { return 'b' + (++_uid); }

// ─── Path utilities ───────────────────────────────────────────────────────────
// pathStr encodes a path to an array in the block tree:
//   ""          → prog (root)
//   "2.body"    → prog[2].body
//   "2.body.1.else_body" → prog[2].body[1].else_body

function getArr(pathStr) {
  if (!pathStr) return prog;
  var segs = pathStr.split('.');
  var arr  = prog;
  for (var i = 0; i < segs.length; i += 2) {
    arr = arr[parseInt(segs[i])][segs[i + 1]];
  }
  return arr;
}

function childPath(parentPath, idx, prop) {
  return (parentPath ? parentPath + '.' : '') + idx + '.' + prop;
}

// ─── Block factory ────────────────────────────────────────────────────────────

function makeBlock(type) {
  var def = BLOCK_DEFS[type];
  if (!def) return null;
  var params = {};
  def.fields.forEach(function(f) { params[f.name] = f.def; });
  var b = { id: uid(), type: type, params: params };
  if (def.container) b.body = [];
  if (def.hasElse)   b.else_body = [];
  return b;
}

// ─── Drag handlers ────────────────────────────────────────────────────────────

function onPaletteDragStart(e) {
  dragSrc = { palette: true, type: this.dataset.type };
  e.dataTransfer.setData('text/plain', 'palette');
  e.dataTransfer.effectAllowed = 'copy';
}

function onBlockDragStart(e) {
  e.stopPropagation();
  var arrPath = this.dataset.arrPath;
  var idx     = parseInt(this.dataset.idx);
  dragSrc = { palette: false, fromArr: getArr(arrPath), fromIdx: idx };
  e.dataTransfer.setData('text/plain', 'block');
  e.dataTransfer.effectAllowed = 'move';
  this.style.opacity = '0.4';
}

function onBlockDragEnd(e) {
  this.style.opacity = '';
}

function onDzDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  e.dataTransfer.dropEffect = dragSrc && dragSrc.palette ? 'copy' : 'move';
  this.classList.add('dz--hover');
}

function onDzDragLeave(e) {
  this.classList.remove('dz--hover');
}

function onDzDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  this.classList.remove('dz--hover');
  if (!dragSrc) return;

  var toPath = this.dataset.arrPath;
  var toIdx  = parseInt(this.dataset.idx);
  var toArr  = getArr(toPath);

  if (dragSrc.palette) {
    toArr.splice(toIdx, 0, makeBlock(dragSrc.type));
  } else {
    var fromArr = dragSrc.fromArr;
    var fromIdx = dragSrc.fromIdx;
    var block   = fromArr[fromIdx];
    // Prevent dropping a block into itself (no ancestor check needed for most cases)
    if (block === toArr || isDescendant(block, toArr)) { dragSrc = null; return; }
    fromArr.splice(fromIdx, 1);
    if (fromArr === toArr && fromIdx < toIdx) toIdx--;
    toArr.splice(toIdx, 0, block);
  }
  dragSrc = null;
  render();
}

function isDescendant(block, arr) {
  // Prevent moving a container into its own children
  var def = BLOCK_DEFS[block.type];
  if (!def || !def.container) return false;
  if (block.body === arr || block.else_body === arr) return true;
  for (var i = 0; i < block.body.length; i++) {
    if (isDescendant(block.body[i], arr)) return true;
  }
  if (block.else_body) {
    for (var j = 0; j < block.else_body.length; j++) {
      if (isDescendant(block.else_body[j], arr)) return true;
    }
  }
  return false;
}

// ─── Render ───────────────────────────────────────────────────────────────────

function render() {
  var root = document.getElementById('prog-root');
  root.innerHTML = '';
  renderList(prog, '', root);
  saveDraft();
}

function renderList(arr, pathStr, container) {
  mkDz(container, pathStr, 0, arr.length === 0);
  arr.forEach(function(block, idx) {
    renderBlock(container, block, pathStr, idx);
    mkDz(container, pathStr, idx + 1, false);
  });
}

function mkDz(container, pathStr, idx, showHint) {
  var dz = document.createElement('div');
  dz.className = 'dz' + (showHint ? ' dz--hint' : '');
  if (showHint) dz.textContent = 'Glisser un bloc ici…';
  dz.dataset.arrPath = pathStr;
  dz.dataset.idx     = idx;
  dz.addEventListener('dragover',  onDzDragOver);
  dz.addEventListener('dragleave', onDzDragLeave);
  dz.addEventListener('drop',      onDzDrop);
  container.appendChild(dz);
}

function renderBlock(container, block, pathStr, idx) {
  var def = BLOCK_DEFS[block.type];
  if (!def) return;

  var el = document.createElement('div');
  el.className   = 'blk';
  // NOTE: draggable is on the grip only — keeping the block itself non-draggable
  // lets child drop-zones (repeat body, if/else branches) receive drag events.
  el.dataset.arrPath = pathStr;
  el.dataset.idx     = idx;

  // ── Header bar
  var hdr = document.createElement('div');
  hdr.className = 'blk-hdr';
  hdr.style.background = def.color;

  var grip = document.createElement('span');
  grip.className   = 'blk-grip';
  grip.textContent = '⠿';
  grip.title       = 'Glisser pour déplacer';
  grip.draggable   = true;
  // Capture el, pathStr, idx by value so they survive re-renders
  (function(blockEl, ap, i) {
    grip.addEventListener('dragstart', function(e) {
      e.stopPropagation();
      dragSrc = { palette: false, fromArr: getArr(ap), fromIdx: i };
      e.dataTransfer.setData('text/plain', 'block');
      e.dataTransfer.effectAllowed = 'move';
      try { e.dataTransfer.setDragImage(blockEl, 12, 12); } catch(ex) {}
      blockEl.style.opacity = '0.4';
    });
    grip.addEventListener('dragend', function() {
      blockEl.style.opacity = '';
    });
  })(el, pathStr, idx);
  hdr.appendChild(grip);

  var lbl = document.createElement('span');
  lbl.className   = 'blk-lbl';
  lbl.textContent = def.icon + ' ' + def.label;
  hdr.appendChild(lbl);

  // Fields inline in header
  def.fields.forEach(function(f) {
    hdr.appendChild(mkField(block, f));
  });

  var del = document.createElement('button');
  del.className   = 'blk-del';
  del.textContent = '×';
  del.title       = 'Supprimer';
  del.addEventListener('click', (function(ap, i) {
    return function(e) { e.stopPropagation(); getArr(ap).splice(i, 1); render(); };
  })(pathStr, idx));
  hdr.appendChild(del);

  el.appendChild(hdr);

  // ── Container body
  if (def.container) {
    var bodyPath = childPath(pathStr, idx, 'body');

    if (def.hasElse) {
      var thenLbl = document.createElement('div');
      thenLbl.className   = 'blk-branch-lbl';
      thenLbl.textContent = 'Alors :';
      el.appendChild(thenLbl);
    }

    var bodyEl = document.createElement('div');
    bodyEl.className = 'blk-body';
    renderList(block.body, bodyPath, bodyEl);
    el.appendChild(bodyEl);

    if (def.hasElse) {
      var elsePath = childPath(pathStr, idx, 'else_body');

      var elseLbl = document.createElement('div');
      elseLbl.className   = 'blk-branch-lbl';
      elseLbl.textContent = 'Sinon :';
      el.appendChild(elseLbl);

      var elseEl = document.createElement('div');
      elseEl.className = 'blk-body';
      renderList(block.else_body, elsePath, elseEl);
      el.appendChild(elseEl);
    }
  }

  container.appendChild(el);
}

function mkField(block, f) {
  var wrap = document.createElement('span');
  wrap.className = 'blk-field';

  if (f.label) {
    var lbl = document.createElement('span');
    lbl.className   = 'blk-field-lbl';
    lbl.textContent = f.label;
    wrap.appendChild(lbl);
  }

  var inp;

  if (f.type === 'select') {
    inp = document.createElement('select');
    inp.className = 'blk-select';
    f.options.forEach(function(opt) {
      var o   = document.createElement('option');
      o.value = opt[1];
      o.textContent = opt[0];
      if (opt[1] === block.params[f.name]) o.selected = true;
      inp.appendChild(o);
    });
    inp.addEventListener('change', (function(b, n) {
      return function() { b.params[n] = this.value; saveDraft(); };
    })(block, f.name));

  } else if (f.type === 'text') {
    inp = document.createElement('input');
    inp.type        = 'text';
    inp.className   = 'blk-text';
    inp.value       = block.params[f.name];
    inp.placeholder = f.placeholder || '';
    inp.addEventListener('input', (function(b, n) {
      return function() { b.params[n] = this.value; saveDraft(); };
    })(block, f.name));

  } else if (f.type === 'number') {
    inp = document.createElement('input');
    inp.type      = 'number';
    inp.className = 'blk-num';
    inp.min       = f.min;
    inp.max       = f.max;
    inp.step      = f.step;
    inp.value     = block.params[f.name];
    inp.addEventListener('change', (function(b, n) {
      return function() { b.params[n] = parseFloat(this.value); saveDraft(); };
    })(block, f.name));
    if (f.suffix) {
      wrap.appendChild(inp);
      var sfx = document.createElement('span');
      sfx.className   = 'blk-field-lbl';
      sfx.textContent = f.suffix;
      wrap.appendChild(sfx);
      return wrap;
    }

  } else if (f.type === 'range') {
    var rw = document.createElement('span');
    rw.className = 'blk-range-wrap';
    inp = document.createElement('input');
    inp.type      = 'range';
    inp.className = 'blk-range';
    inp.min       = f.min;
    inp.max       = f.max;
    inp.step      = f.step;
    inp.value     = block.params[f.name];
    var rv = document.createElement('span');
    rv.className   = 'blk-range-val';
    rv.textContent = parseFloat(block.params[f.name]).toFixed(1);
    inp.addEventListener('input', (function(b, n, ve) {
      return function() {
        b.params[n] = parseFloat(this.value);
        ve.textContent = parseFloat(this.value).toFixed(1);
        saveDraft();
      };
    })(block, f.name, rv));
    rw.appendChild(inp);
    rw.appendChild(rv);
    wrap.appendChild(rw);
    return wrap;

  } else if (f.type === 'color') {
    inp = document.createElement('input');
    inp.type      = 'color';
    inp.className = 'blk-color';
    inp.value     = block.params[f.name];
    inp.addEventListener('input', (function(b, n) {
      return function() { b.params[n] = this.value; saveDraft(); };
    })(block, f.name));
  }

  if (inp) wrap.appendChild(inp);
  return wrap;
}

// ─── Palette ──────────────────────────────────────────────────────────────────

function renderPalette() {
  ['action', 'control'].forEach(function(cat) {
    var el = document.getElementById('pal-' + cat);
    if (!el) return;
    el.innerHTML = '';
    Object.keys(BLOCK_DEFS).forEach(function(type) {
      var def = BLOCK_DEFS[type];
      if (def.cat !== cat) return;
      var btn = document.createElement('div');
      btn.className     = 'pal-blk';
      btn.style.background = def.color;
      btn.draggable     = true;
      btn.dataset.type  = type;
      btn.title         = 'Cliquer ou glisser pour ajouter';
      btn.innerHTML     = def.icon + ' <b>' + def.label + '</b>';
      btn.addEventListener('dragstart', onPaletteDragStart);
      btn.addEventListener('click', function() {
        prog.push(makeBlock(type));
        render();
      });
      el.appendChild(btn);
    });
  });
}

// ─── Run / Stop ───────────────────────────────────────────────────────────────

function runProgram() {
  setRunning(true);
  $.ajax({
    url:         WOZ_BASE + '/run_program',
    type:        'POST',
    contentType: 'application/json',
    data:        JSON.stringify({ program: prog }),
    error: function() { setRunning(false); },
  });
  pollStatus();
}

function stopProgram() {
  $.post(WOZ_BASE + '/stop_program');
  clearTimeout(pollTimer);
  setRunning(false);
}

function pollStatus() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(function() {
    $.getJSON(WOZ_BASE + '/program_status', function(data) {
      if (data.running) {
        pollStatus();
      } else {
        setRunning(false);
      }
    }).fail(function() { setRunning(false); });
  }, 800);
}

function setRunning(on) {
  var btnRun  = document.getElementById('btn-run');
  var btnStop = document.getElementById('btn-stop');
  var status  = document.getElementById('prog-status');
  if (btnRun)  btnRun.disabled  = on;
  if (btnStop) btnStop.disabled = !on;
  if (status) {
    status.textContent = on ? '▶ En cours…' : '';
    status.className   = on ? 'prog-status prog-status--on' : 'prog-status';
  }
}

// ─── Save / Load ──────────────────────────────────────────────────────────────

function saveDraft() {
  try { localStorage.setItem(DRAFT_KEY, JSON.stringify(prog)); } catch(e) {}
}

function loadDraft() {
  try {
    var d = localStorage.getItem(DRAFT_KEY);
    if (d) prog = JSON.parse(d);
  } catch(e) {}
}

function getSaved() {
  try { return JSON.parse(localStorage.getItem(SAVED_KEY)) || {}; } catch(e) { return {}; }
}

function saveNamed() {
  var nameEl = document.getElementById('save-name');
  var name = (nameEl && nameEl.value.trim()) || 'Programme ' + new Date().toLocaleTimeString();
  var saved = getSaved();
  saved[name] = JSON.parse(JSON.stringify(prog));
  try { localStorage.setItem(SAVED_KEY, JSON.stringify(saved)); } catch(e) {}
  if (nameEl) nameEl.value = '';
  renderSavedList();
}

function loadNamed(name) {
  var saved = getSaved();
  if (saved[name]) {
    prog = JSON.parse(JSON.stringify(saved[name]));
    render();
  }
}

function deleteNamed(name) {
  var saved = getSaved();
  delete saved[name];
  try { localStorage.setItem(SAVED_KEY, JSON.stringify(saved)); } catch(e) {}
  renderSavedList();
}

function renderSavedList() {
  var el = document.getElementById('saved-list');
  if (!el) return;
  var saved = getSaved();
  var names = Object.keys(saved);
  el.innerHTML = '';
  if (names.length === 0) {
    el.innerHTML = '<span class="saved-empty">Aucun programme sauvegardé</span>';
    return;
  }
  names.forEach(function(name) {
    var row = document.createElement('div');
    row.className = 'saved-row';

    var lbl = document.createElement('span');
    lbl.className   = 'saved-name';
    lbl.textContent = name;

    var load = document.createElement('button');
    load.textContent = '📂';
    load.title       = 'Charger';
    load.className   = 'saved-btn';
    load.addEventListener('click', (function(n) { return function() { loadNamed(n); }; })(name));

    var del = document.createElement('button');
    del.textContent = '🗑';
    del.title       = 'Supprimer';
    del.className   = 'saved-btn';
    del.addEventListener('click', (function(n) { return function() { deleteNamed(n); }; })(name));

    row.appendChild(lbl);
    row.appendChild(load);
    row.appendChild(del);
    el.appendChild(row);
  });
}

// ─── Clear ────────────────────────────────────────────────────────────────────

function clearProgram() {
  if (prog.length > 0 && !confirm('Effacer le programme ?')) return;
  prog = [];
  render();
}

// ─── Init ─────────────────────────────────────────────────────────────────────

function blocksInit() {
  renderPalette();
  loadDraft();
  render();
  renderSavedList();

  document.getElementById('btn-run').addEventListener('click',   runProgram);
  document.getElementById('btn-stop').addEventListener('click',  stopProgram);
  document.getElementById('btn-clear').addEventListener('click', clearProgram);
  document.getElementById('btn-save').addEventListener('click',  saveNamed);
}
