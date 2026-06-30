// vocal.js — Voice input via MediaRecorder + server-side Whisper transcription

var VOICE_COMMANDS = [
    // Postures
    { words: ['debout', 'lève-toi', 'leve toi', 'mets-toi debout', 'stand'], motion: 'stand' },
    { words: ['assis', 'assieds-toi', 'sit', 'pose-toi'], motion: 'sit' },
    { words: ['accroupi', 'baisse-toi', 'crouch'], motion: 'crouch' },
    // Gestes
    { words: ['salue', 'bonjour', 'coucou', 'salut', 'wave', 'dis bonjour'], motion: 'wave' },
    { words: ['applaudis', 'bravo', 'clap'], motion: 'applause' },
    { words: ['oui', 'acquiesce', 'hoche la tête', 'nod'], motion: 'nod' },
    { words: ['non', 'secoue la tête', 'shake'], motion: 'shake_head' },
    { words: ['révérence', 'incline-toi', 'bow', 'arc'], motion: 'bow' },
    { words: ['bras ouverts', 'ouvre les bras', 'arms open'], motion: 'arms_open' },
    { words: ['donne', 'tends la main', 'give'], motion: 'give' },
    { words: ['pointe', 'montre', 'point'], motion: 'point_forward' },
    { words: ['muscle', 'fort', 'muscles'], motion: 'show_muscles' },
    { words: ['câlin', 'love you', 'calin'], motion: 'love_you' },
    // Émotions corps
    { words: ['content', 'heureux', 'joyeux', 'happy'], motion: 'happy_anim' },
    { words: ['triste', 'sad', 'pleure'], motion: 'sad_anim' },
    { words: ['ris', 'rire', 'laugh', 'haha'], motion: 'laugh_anim' },
    { words: ['peur', 'scared', 'effrayé', 'fear'], motion: 'fear' },
    { words: ['confus', 'confused', 'perdu'], motion: 'confused_anim' },
    { words: ['timide', 'shy'], motion: 'shy_anim' },
    { words: ['excité', 'excited'], motion: 'excited_anim' },
    { words: ['colère', 'angry', 'fâché'], motion: 'angry_anim' },
    { words: ['réfléchis', 'pense', 'think'], motion: 'think' },
    // Danse
    { words: ['danse', 'dance', 'bouge'], motion: 'funny_dancer' },
    { words: ['guitare', 'guitar'], motion: 'air_guitar' },
    { words: ['robot dance', 'danse robot'], motion: 'robot_dance' },
    { words: ['zombie'], motion: 'zombie' },
    { words: ['kung fu', 'kungfu'], motion: 'kung_fu' },
    // Marche
    { words: ['avance', 'avancer', 'en avant', 'forward', 'marche'], motion: 'walk_forward' },
    { words: ['recule', 'reculer', 'en arrière', 'backward'], motion: 'walk_backward' },
    { words: ['à gauche', 'va à gauche', 'gauche', 'left'], motion: 'walk_left' },
    { words: ['à droite', 'va à droite', 'droite', 'right'], motion: 'walk_right' },
    { words: ['tourne gauche', 'turn left'], motion: 'turn_left' },
    { words: ['tourne droite', 'turn right'], motion: 'turn_right' },
    { words: ['stop', 'arrête', 'arrête-toi', 'halte', 'immobile'], motion: 'stop' },
    // Moteurs
    { words: ['relax', 'détends-toi', 'repos', 'déstiffène', 'soft', 'mou'], relax: true },
    { words: ['stiffen', 'raidis-toi', 'active-toi', 'réveille-toi', 'dur'], stiffen: true },
];

var mediaRecorder = null;
var audioChunks = [];
var isRecording = false;
var currentMode = 'repeat';
var currentSpeed = parseFloat(localStorage.getItem('woz_vocal_speed') || '0.5');

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = function(e) {
                if (e.data.size > 0) audioChunks.push(e.data);
            };

            mediaRecorder.onstop = function() {
                stream.getTracks().forEach(function(t) { t.stop(); });
                var blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
                sendForTranscription(blob);
            };

            mediaRecorder.start();
            isRecording = true;
            setStatus('listening', 'En écoute... (cliquez pour arrêter)');
            document.getElementById('btn-mic').classList.add('vocal-btn--active');
            document.querySelector('.vocal-mic-label').textContent = 'Cliquer pour arrêter';
        })
        .catch(function(err) {
            if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                setStatus('error', 'Micro refusé — autorisez l\'accès au micro dans le navigateur.');
            } else if (err.name === 'NotFoundError') {
                setStatus('error', 'Aucun microphone détecté.');
            } else {
                setStatus('error', 'Erreur micro: ' + err.message);
            }
        });
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById('btn-mic').classList.remove('vocal-btn--active');
        document.querySelector('.vocal-mic-label').textContent = 'Appuyer pour parler';
        setStatus('idle', 'Transcription en cours...');
    }
}

function sendForTranscription(blob) {
    var formData = new FormData();
    formData.append('audio', blob, 'audio.webm');
    $.ajax({
        url: '/woz_transcribe',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(data) {
            if (data.text && data.text.trim()) {
                dispatch(data.text.trim());
            } else {
                setStatus('idle', 'Rien entendu — réessayez.');
            }
        },

        error: function(xhr) {
            var msg = (xhr.responseJSON && xhr.responseJSON.error) ? xhr.responseJSON.error : 'Erreur serveur';
            setStatus('error', msg);
        }
    });
}

function normalize(s) {
    return s.toLowerCase()
        .normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^a-z0-9\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function dispatch(text) {
    addToHistory(text);
    if (currentMode === 'repeat') {
        sendPost({ speak_text: text });
        setStatus('idle', '« ' + text + ' »');
        return;
    }
    var norm = normalize(text);
    var matched = false;
    for (var i = 0; i < VOICE_COMMANDS.length; i++) {
        var cmd = VOICE_COMMANDS[i];
        for (var j = 0; j < cmd.words.length; j++) {
            if (norm.indexOf(normalize(cmd.words[j])) !== -1) {
                if (cmd.motion)   sendPost({ motion: cmd.motion, speed: currentSpeed });
                if (cmd.relax)    sendPost({ relax: true });
                if (cmd.stiffen)  sendPost({ stiffen: true });
                setStatus('idle', '✓ « ' + text + ' » → ' + cmd.words[j]);
                matched = true;
                break;
            }
        }
        if (matched) break;
    }
    if (!matched) {
        sendPost({ speak_text: text });
        setStatus('idle', '? « ' + text + ' » → répété');
    }
}

function sendPost(payload) {
    $.ajax({ url: '/woz', type: 'POST', contentType: 'application/json',
             data: JSON.stringify(payload) });
}

function addToHistory(text) {
    var box = document.getElementById('history');
    var entry = document.createElement('div');
    entry.className = 'vocal-history-entry';
    var time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    var icon = currentMode === 'repeat' ? '🔊' : '🤖';
    entry.innerHTML = '<span class="vocal-time">' + time + '</span>' +
                      '<span class="vocal-mode-icon">' + icon + '</span>' +
                      '<span class="vocal-text">' + text + '</span>';
    box.insertBefore(entry, box.firstChild);
    while (box.children.length > 20) box.removeChild(box.lastChild);
}

function setStatus(type, msg) {
    var el = document.getElementById('vocal-status');
    el.className = 'vocal-status vocal-status--' + type;
    el.textContent = msg;
}

function onLoad() {
    if (!navigator.mediaDevices || !window.MediaRecorder) {
        setStatus('error', 'Navigateur non supporté pour l\'audio.');
        document.getElementById('btn-mic').disabled = true;
        return;
    }
    setStatus('idle', 'Prêt');

    var slider = document.getElementById('speed-slider');
    var speedDisplay = document.getElementById('speed-value');
    slider.value = currentSpeed;
    speedDisplay.textContent = currentSpeed.toFixed(2);
    slider.addEventListener('input', function() {
        currentSpeed = parseFloat(slider.value);
        speedDisplay.textContent = currentSpeed.toFixed(2);
        localStorage.setItem('woz_vocal_speed', String(currentSpeed));
    });

    document.getElementById('btn-mic').addEventListener('click', function() {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    document.getElementById('mode-repeat').addEventListener('click', function() {
        currentMode = 'repeat';
        document.getElementById('mode-repeat').classList.add('vocal-mode-btn--on');
        document.getElementById('mode-command').classList.remove('vocal-mode-btn--on');
    });

    document.getElementById('mode-command').addEventListener('click', function() {
        currentMode = 'command';
        document.getElementById('mode-command').classList.add('vocal-mode-btn--on');
        document.getElementById('mode-repeat').classList.remove('vocal-mode-btn--on');
    });
}
