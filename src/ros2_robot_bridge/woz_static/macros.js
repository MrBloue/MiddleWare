// macros.js — Quick-access gesture buttons + multi-action homebrew buttons

var QUICK_MOVES = [
    ['Debout',       'stand'],
    ['Assis',        'sit'],
    ['Saluer',       'wave'],
    ['Applaudir',    'applause'],
    ['Oui',          'nod'],
    ['Non',          'shake_head'],
    ['Arc',          'bow'],
    ['Donner',       'give'],
    ['Bras ouverts', 'arms_open'],
    ['Content',      'happy_anim'],
    ['Triste',       'sad_anim'],
    ['Rire',         'laugh_anim'],
    ['Peur',         'fear'],
    ['Confus',       'confused_anim'],
    ['Curieux',      'puzzled'],
    ['Fort!',        'show_muscles'],
    ['Fatigué',      'relaxation'],
    ['Réfléchir',    'scratch_head'],
    ['Danse',        'funny_dancer'],
    ['Coucou',       'peekaboo'],
    ['Câlin',        'love_you'],
    ['Relax',        'relaxation'],
    ['Avancer',      'walk_forward'],
    ['Reculer',      'walk_backward'],
    ['Stop',         'stop'],
];

// Full motion list for the dropdown, grouped
var MOTION_OPTIONS = [
    { group: 'Postures',   items: [
        ['Debout',     'stand'],
        ['Assis',      'sit'],
        ['StandInit',  'standinit'],
        ['Accroupi',   'crouch'],
    ]},
    { group: 'Gestes courants', items: [
        ['Saluer (wave)',   'wave'],
        ['Applaudir',       'applause'],
        ['Arc (bow)',        'bow'],
        ['Oui (nod)',       'nod'],
        ['Non',             'shake_head'],
        ['Bras ouverts',    'arms_open'],
        ['Donner',          'give'],
        ['Pointer',         'point_forward'],
        ['Gratter tête',    'scratch_head'],
        ['Coucou',          'peekaboo'],
        ['Câlin',           'love_you'],
        ['Relax',           'relaxation'],
        ['Fort!',           'show_muscles'],
        ['Réfléchir',       'think'],
        ['Écouter',         'listening_anim'],
        ['Enthousiaste',    'enthusiastic_g'],
    ]},
    { group: 'Émotions corps', items: [
        ['Content',         'happy_anim'],
        ['Triste',          'sad_anim'],
        ['Rire',            'laugh_anim'],
        ['Peur',            'fear'],
        ['Confus',          'confused_anim'],
        ['Curieux',         'puzzled'],
        ['Fatigué',         'relaxation'],
        ['Colère',          'angry_anim'],
        ['Timide',          'shy_anim'],
        ['Excité',          'excited_anim'],
        ['Déçu',            'disappointed'],
        ['Fier',            'proud'],
    ]},
    { group: 'Danses / spectacle', items: [
        ['Danse fun',       'funny_dancer'],
        ['Air guitare',     'air_guitar'],
        ['Robot',           'robot_dance'],
        ['Zombie',          'zombie'],
        ['Hélicoptère',     'helicopter'],
        ['Kung fu',         'kung_fu'],
    ]},
    { group: 'Marche', items: [
        ['Avancer',         'walk_forward'],
        ['Reculer',         'walk_backward'],
        ['Gauche',          'walk_left'],
        ['Droite',          'walk_right'],
        ['Tourner gauche',  'turn_left'],
        ['Tourner droite',  'turn_right'],
        ['Stop',            'stop'],
    ]},
];

var EMOTION_OPTIONS = [
    ['Content (jaune)',     'happy'],
    ['Triste (bleu)',       'sad'],
    ['Colère (rouge)',      'angry'],
    ['Neutre (blanc)',      'neutral'],
    ['Surpris (cyan)',      'surprised'],
    ['Peur (violet)',       'scared'],
    ['Excité (orange)',     'excited'],
];

var LED_GROUPS = [
    ['Yeux',            'eyes'],
    ['Yeux gauche',     'left_eye'],
    ['Yeux droit',      'right_eye'],
    ['Oreilles',        'ears'],
    ['Oreille gauche',  'left_ear'],
    ['Oreille droite',  'right_ear'],
    ['Poitrine',        'chest'],
    ['Pieds',           'feet'],
    ['Tout',            'all'],
];

var STORAGE_KEY = 'woz_homebrew_v2';

var pendingMotions = [];

function loadHomebrew() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }
    catch(e) { return []; }
}

function saveHomebrew(list) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

function sendActions(item) {
    var motions = item.motions && item.motions.length ? item.motions
                : (item.motion ? [{ name: item.motion, speed: 0.5, duration: 3 }] : []);
    var delay = 0;
    motions.forEach(function(m) {
        var name     = typeof m === 'string' ? m : m.name;
        var speed    = typeof m === 'object' ? (parseFloat(m.speed)    || 0.5) : 0.5;
        var duration = typeof m === 'object' ? (parseFloat(m.duration) || 3.0) : 3.0;
        setTimeout(function() {
            $.ajax({ url: WOZ_BASE + '/woz', type: 'POST', contentType: 'application/json',
                     data: JSON.stringify({ motion: name, speed: speed }) });
        }, delay * 1000);
        delay += duration;
    });
    if (item.emotion) {
        $.ajax({ url: WOZ_BASE + '/woz', type: 'POST', contentType: 'application/json',
                 data: JSON.stringify({ emotion: item.emotion }) });
    }
    if (item.led_name) {
        $.ajax({ url: WOZ_BASE + '/woz', type: 'POST', contentType: 'application/json',
                 data: JSON.stringify({ led_name: item.led_name, led_color: item.led_color || '#ffffff' }) });
    }
    if (item.speak) {
        $.ajax({ url: WOZ_BASE + '/woz', type: 'POST', contentType: 'application/json',
                 data: JSON.stringify({ speak_text: item.speak }) });
    }
}

function buildActionSummary(item) {
    var parts = [];
    var motions = item.motions && item.motions.length ? item.motions
                : (item.motion ? [{ name: item.motion, speed: 0.5, duration: 3 }] : []);
    if (motions.length) {
        var labels = motions.map(function(m) {
            var name = typeof m === 'string' ? m : m.name;
            var spd  = typeof m === 'object' ? m.speed    : 0.5;
            var dur  = typeof m === 'object' ? m.duration : 3;
            return name + ' (' + spd + '×, ' + dur + 's)';
        });
        parts.push('🤖 ' + labels.join(' → '));
    }
    if (item.emotion)  parts.push('💡 ' + item.emotion);
    if (item.led_name) parts.push('🔆 ' + item.led_name + ' ' + (item.led_color || '#ffffff'));
    if (item.speak)    parts.push('🔊 ' + item.speak.substring(0, 24) + (item.speak.length > 24 ? '…' : ''));
    return parts.join('  ');
}

function renderQuick() {
    var container = document.getElementById('quick-grid');
    container.innerHTML = '';
    QUICK_MOVES.forEach(function(item) {
        var btn = document.createElement('button');
        btn.className = 'macro-btn';
        btn.textContent = item[0];
        btn.onclick = function() {
            $.ajax({ url: WOZ_BASE + '/woz', type: 'POST', contentType: 'application/json',
                     data: JSON.stringify({ motion: item[1] }) });
        };
        container.appendChild(btn);
    });
}

function renderHomebrew() {
    var list = loadHomebrew();
    var container = document.getElementById('homebrew-grid');
    container.innerHTML = '';
    if (list.length === 0) {
        container.innerHTML = '<span class="macro-empty">Aucun bouton — utilisez le formulaire ci-dessous pour en créer.</span>';
        return;
    }
    list.forEach(function(item, idx) {
        var wrap = document.createElement('div');
        wrap.className = 'macro-btn-wrap';

        var btn = document.createElement('button');
        btn.className = 'macro-btn macro-btn--custom';
        btn.innerHTML = '<span class="macro-btn-label">' + item.label + '</span>' +
                        '<span class="macro-btn-summary">' + buildActionSummary(item) + '</span>';
        btn.onclick = function() { sendActions(item); };

        var del = document.createElement('button');
        del.className = 'macro-del';
        del.textContent = '×';
        del.title = 'Supprimer';
        del.onclick = function() {
            var l = loadHomebrew();
            l.splice(idx, 1);
            saveHomebrew(l);
            renderHomebrew();
        };

        wrap.appendChild(btn);
        wrap.appendChild(del);
        container.appendChild(wrap);
    });
}

function buildMotionSelect(id) {
    var sel = document.getElementById(id);
    sel.innerHTML = '<option value="">— Aucun mouvement —</option>';
    MOTION_OPTIONS.forEach(function(group) {
        var og = document.createElement('optgroup');
        og.label = group.group;
        group.items.forEach(function(item) {
            var opt = document.createElement('option');
            opt.value = item[1];
            opt.textContent = item[0];
            og.appendChild(opt);
        });
        sel.appendChild(og);
    });
}

function buildEmotionSelect(id) {
    var sel = document.getElementById(id);
    sel.innerHTML = '<option value="">— Aucune émotion LED —</option>';
    EMOTION_OPTIONS.forEach(function(item) {
        var opt = document.createElement('option');
        opt.value = item[1];
        opt.textContent = item[0];
        sel.appendChild(opt);
    });
}

function renderMotionList() {
    var container = document.getElementById('motion-list');
    container.innerHTML = '';
    if (pendingMotions.length === 0) {
        container.innerHTML = '<span class="motion-empty">Aucun mouvement ajouté</span>';
        return;
    }
    pendingMotions.forEach(function(m, i) {
        var chip = document.createElement('span');
        chip.className = 'motion-chip';
        chip.innerHTML = '<span class="motion-chip-name">' + m.name + '</span>' +
                         '<span class="motion-chip-meta">×' + m.speed + ' ' + m.duration + 's</span>';
        var del = document.createElement('button');
        del.type = 'button';
        del.className = 'motion-chip-del';
        del.textContent = '×';
        del.onclick = function() { pendingMotions.splice(i, 1); renderMotionList(); };
        chip.appendChild(del);
        container.appendChild(chip);
    });
}

function buildLedSelect(id) {
    var sel = document.getElementById(id);
    sel.innerHTML = '<option value="">— Aucune LED —</option>';
    LED_GROUPS.forEach(function(item) {
        var opt = document.createElement('option');
        opt.value = item[1];
        opt.textContent = item[0];
        sel.appendChild(opt);
    });
}

function onLoad() {
    renderQuick();
    buildMotionSelect('new-motion-pick');
    buildEmotionSelect('new-emotion');
    buildLedSelect('new-led');
    renderMotionList();
    renderHomebrew();

    document.getElementById('btn-add-motion').addEventListener('click', function() {
        var name  = document.getElementById('new-motion-pick').value;
        if (!name) return;
        var speed    = parseFloat(document.getElementById('new-motion-speed').value)    || 0.5;
        var duration = parseFloat(document.getElementById('new-motion-duration').value) || 3.0;
        speed    = Math.min(1.0, Math.max(0.1, speed));
        duration = Math.max(0.5, duration);
        pendingMotions.push({ name: name, speed: speed, duration: duration });
        renderMotionList();
    });

    document.getElementById('btn-relax').addEventListener('click', function() {
        $.ajax({ url: WOZ_BASE + '/woz', type: 'POST', contentType: 'application/json',
                 data: JSON.stringify({ relax: true }) });
    });
    document.getElementById('btn-stiffen').addEventListener('click', function() {
        $.ajax({ url: WOZ_BASE + '/woz', type: 'POST', contentType: 'application/json',
                 data: JSON.stringify({ stiffen: true }) });
    });

    document.getElementById('add-form').addEventListener('submit', function(e) {
        e.preventDefault();
        var label    = document.getElementById('new-label').value.trim();
        var speak    = document.getElementById('new-speak').value.trim();
        var emotion  = document.getElementById('new-emotion').value;
        var led_name = document.getElementById('new-led').value;
        var led_color= document.getElementById('new-led-color').value;
        if (!label) return;
        if (!speak && !pendingMotions.length && !emotion && !led_name) {
            alert('Remplis au moins un champ (mouvement, émotion, LED ou texte).');
            return;
        }
        var list = loadHomebrew();
        list.push({ label: label, speak: speak, motions: pendingMotions.slice(),
                    emotion: emotion, led_name: led_name, led_color: led_color });
        saveHomebrew(list);
        renderHomebrew();
        document.getElementById('new-label').value = '';
        document.getElementById('new-speak').value = '';
        document.getElementById('new-motion-pick').value = '';
        document.getElementById('new-emotion').value = '';
        document.getElementById('new-led').value = '';
        document.getElementById('new-led-color').value = '#ffffff';
        pendingMotions = [];
        renderMotionList();
    });
}
