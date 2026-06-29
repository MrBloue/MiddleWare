// vocal.js — Voice input via MediaRecorder + server-side Whisper transcription

var VOICE_COMMANDS = [
    // Postures
    { words: ['debout', 'lève-toi', 'leve-toi', 'mets-toi debout', 'stand up', 'lève toi'], motion: 'stand' },
    { words: ['assis', 'assieds-toi', 'assied-toi', 'sit down', 'pose-toi', 'assieds toi'], motion: 'sit' },
    { words: ['accroupi', 'baisse-toi', 'accroupis-toi', 'crouch', 'penche-toi'], motion: 'crouch' },
    { words: ['position initiale', 'stand init', 'initialise', 'position de départ'], motion: 'standinit' },
    // Gestes courants
    { words: ['salue', 'salut', 'bonjour', 'coucou', 'wave', 'dis bonjour', 'au revoir'], motion: 'wave' },
    { words: ['applaudis', 'bravo', 'clap', 'applaudir', 'tape des mains'], motion: 'applause' },
    { words: ['oui', 'acquiesce', 'hoche la tête', 'nod', 'approuve', 'confirme'], motion: 'nod' },
    { words: ['non', 'secoue la tête', 'shake', 'refuse', 'nie', 'pas question'], motion: 'shake_head' },
    { words: ['révérence', 'incline-toi', 'bow', 'arc', 'salut japonais', 'incline'], motion: 'bow' },
    { words: ['bras ouverts', 'ouvre les bras', 'écarte les bras', 'viens', 'accueil'], motion: 'arms_open' },
    { words: ['donne', 'tends la main', 'give', 'offre', 'présente', 'tend la main'], motion: 'give' },
    { words: ['pointe', 'montre', 'point', 'indique', 'désigne', 'regarde là'], motion: 'point_forward' },
    { words: ['muscle', 'fort', 'muscles', 'montre tes muscles', 'super héros', 'force'], motion: 'show_muscles' },
    { words: ['câlin', 'love you', 'calin', 'je t\'aime', 'bisou', 'affection'], motion: 'love_you' },
    { words: ['gratte la tête', 'gratte-toi', 'scratch', 'gratte'], motion: 'scratch_head' },
    { words: ['coucou cache', 'peekaboo', 'peek', 'coucou me voilà'], motion: 'peekaboo' },
    { words: ['écoute', 'écouter', 'j\'écoute', 'listening', 'attentif'], motion: 'listening_anim' },
    { words: ['enthousiaste', 'super', 'génial', 'ouais', 'enthusiastic'], motion: 'enthusiastic_g' },
    { words: ['réfléchis', 'pense', 'think', 'je réfléchis', 'hmm', 'voyons'], motion: 'think' },
    // Émotions corps
    { words: ['content', 'heureux', 'joyeux', 'happy', 'je suis content', 'super content'], motion: 'happy_anim' },
    { words: ['triste', 'sad', 'pleure', 'je suis triste', 'déprimé'], motion: 'sad_anim' },
    { words: ['ris', 'rire', 'laugh', 'haha', 'hihi', 'je ris', 'c\'est drôle'], motion: 'laugh_anim' },
    { words: ['peur', 'scared', 'effrayé', 'fear', 'j\'ai peur', 'terrifié'], motion: 'fear' },
    { words: ['confus', 'confused', 'perdu', 'je comprends pas', 'quoi', 'hein'], motion: 'confused_anim' },
    { words: ['timide', 'shy', 'gêné', 'je suis gêné', 'honte'], motion: 'shy_anim' },
    { words: ['excité', 'excited', 'je suis excité', 'trop bien', 'génial'], motion: 'excited_anim' },
    { words: ['colère', 'angry', 'fâché', 'en colère', 'je suis fâché', 'rage'], motion: 'angry_anim' },
    { words: ['déçu', 'disappointed', 'dommage', 'c\'est nul', 'pas content'], motion: 'disappointed' },
    { words: ['fier', 'proud', 'je suis fier', 'bravo moi', 'victoire'], motion: 'proud' },
    { words: ['fatigué', 'tired', 'je suis fatigué', 'repos', 'épuisé'], motion: 'relaxation' },
    // Danses / spectacle
    { words: ['danse', 'dance', 'bouge', 'on danse', 'fais la fête'], motion: 'funny_dancer' },
    { words: ['guitare', 'guitar', 'air guitare', 'rock', 'rock and roll'], motion: 'air_guitar' },
    { words: ['robot', 'danse robot', 'robot dance', 'comme un robot'], motion: 'robot_dance' },
    { words: ['zombie', 'mort vivant', 'zombie dance'], motion: 'zombie' },
    { words: ['hélicoptère', 'helicoptere', 'helicopter', 'tourne les bras'], motion: 'helicopter' },
    { words: ['kung fu', 'kungfu', 'karaté', 'arts martiaux', 'combat'], motion: 'kung_fu' },
    // Marche
    { words: ['avance', 'avancer', 'en avant', 'marche', 'vas-y', 'go'], motion: 'walk_forward' },
    { words: ['recule', 'reculer', 'en arrière', 'recule-toi', 'back'], motion: 'walk_backward' },
    { words: ['gauche', 'à gauche', 'va à gauche', 'left', 'vers la gauche'], motion: 'walk_left' },
    { words: ['droite', 'à droite', 'va à droite', 'right', 'vers la droite'], motion: 'walk_right' },
    { words: ['tourne à gauche', 'tourne gauche', 'turn left', 'pivote gauche'], motion: 'turn_left' },
    { words: ['tourne à droite', 'tourne droite', 'turn right', 'pivote droite'], motion: 'turn_right' },
    { words: ['stop', 'arrête', 'arrête-toi', 'halte', 'immobile', 'ne bouge plus', 'freeze'], motion: 'stop' },
    // LEDs / émotions lumineuses
    { words: ['lumière jaune', 'content lumière', 'led content', 'yeux jaunes'], emotion: 'happy' },
    { words: ['lumière bleue', 'triste lumière', 'led triste', 'yeux bleus'], emotion: 'sad' },
    { words: ['lumière rouge', 'colère lumière', 'led colère', 'yeux rouges'], emotion: 'angry' },
    { words: ['lumière blanche', 'neutre lumière', 'led neutre', 'yeux blancs'], emotion: 'neutral' },
    { words: ['lumière cyan', 'surpris lumière', 'led surpris', 'yeux cyan'], emotion: 'surprised' },
    { words: ['lumière violette', 'peur lumière', 'led peur', 'yeux violets'], emotion: 'scared' },
    { words: ['lumière orange', 'excité lumière', 'led excité', 'yeux oranges'], emotion: 'excited' },
    // Moteurs
    { words: ['relax', 'détends-toi', 'détends toi', 'repos moteurs', 'déstiffène', 'mou', 'soft'], relax: true },
    { words: ['stiffen', 'raidis-toi', 'raidis toi', 'active-toi', 'réveille-toi', 'dur', 'rigide'], stiffen: true },
];

var mediaRecorder = null;
var audioChunks = [];
var isRecording = false;
var currentMode = 'repeat';

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
    formData.append('mode', currentMode);
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
                if (cmd.motion)   sendPost({ motion: cmd.motion });
                if (cmd.emotion)  sendPost({ emotion: cmd.emotion });
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
