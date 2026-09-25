# Contexte projet — ros2_robot_bridge / Lutin WOZ

Ce fichier résume les choix architecturaux, l'état des branches, et les décisions
non-évidentes du projet. Il est destiné à bootstrapper rapidement une session IA
(web ou CLI) sans avoir à relire tout l'historique git.

---

## Environnement de déploiement

- **Machine de développement :** Ubuntu 24.04, ROS2 Jazzy, `~/Lutin/mw_ws`
- **Déploiement cible :** Raspberry Pi 4 (`rasplutin@10.42.0.1`, mot de passe `lutinlutin`)
  - Workspace Pi : `~/mw_ws/MiddleWare`
  - Déploiement par git bundle (air-gapped) :
    ```bash
    git bundle create /tmp/mw_update.bundle <pi_head>..HEAD
    sshpass -p lutinlutin scp /tmp/mw_update.bundle rasplutin@10.42.0.1:~/
    sshpass -p lutinlutin ssh rasplutin@10.42.0.1 \
      "cd ~/mw_ws/MiddleWare && git fetch ~/mw_update.bundle && git merge FETCH_HEAD \
       && colcon build --packages-select ros2_robot_bridge"
    ```
  - Dernier commit déployé sur le Pi : `8f02ac3`
- **Build local :** `colcon build --packages-select ros2_robot_bridge`
  - Toujours sourcer `/opt/ros/jazzy/setup.bash` d'abord (ne pas sourcer `~/ros2_jazzy` — ABI mismatch)

---

## Architecture générale

```
Navigateur → woz_node.py (Flask) → _RobotSlot → qi / roslibpy → Robot
                                                     ↑
                              connexion directe, BYPASSE le pipeline ROS2

Pipeline ROS2 (indépendant du WOZ) :
/robot_cmd → command_dispatcher → nao_bridge   → NAO/Pepper (qi)
                                → qt_bridge    → QTrobot (roslibpy)
```

**Point critique :** `woz_node.py` ne publie PAS sur `/robot_cmd`. Il gère ses
propres connexions robot via des objets `_RobotSlot`. Les deux chemins (WOZ et
pipeline ROS) sont complètement indépendants — ils partagent le vocabulaire de
gestes mais pas le code d'exécution.

---

## Robots supportés

| Robot | Protocole WOZ | Protocole bridge ROS |
|-------|--------------|---------------------|
| NAO v5/v6 | `qi.Session` → port 9559 | idem |
| Pepper v1/v1.8 | `qi.Session` → port 9559 | idem |
| Pepper v2 | ⚠️ non supporté dans WOZ (besoin tcps://) | `tcps://` + cert |
| QTrobot QT1/QT2 | `roslibpy.Ros` → port 9090 | idem |

---

## _RobotSlot (woz_node.py)

Classe centrale du WOZ. Une instance par robot connecté depuis le navigateur.

- `_connect()` : branche sur `robot_type`
  - `qtrobot` → `_connect_qt()` (roslibpy WebSocket)
  - sinon → `qi.Session` NAOqi
- `_do_speak()` : publie sur speech/say (QT) ou ALTextToSpeech.say() (NAO)
- `_do_move()` : résout via `QT_MOTION_MAP` / gestes custom (QT) ou behaviors/gestures NAOqi
- `_do_display()` : émotion → `/qt_robot/emotion/show` (QT) ou `ALLeds.fadeRGB()` (NAO)
- `exec_cmd()` : guard `if not self.connected: return` — commandes ignorées si pas connecté
- `relax` / `stiffen` / `volume` : ignorés silencieusement pour QTrobot

---

## Branches git

```
main          ← branche stable (non modifiée récemment)
hotfixing     ← branche de travail principale ACTUELLE
  └── QTrobot WOZ support (2493eb7) ← dernier commit
screenshots   ← branche avec les changements UI récents (non mergée dans hotfixing)
  ├── Remove Scénarios/Réactions tabs, rename Maison→Jeux (5681ca1)
  └── Allow WOZ access without a connected robot / offline mode (011afac)
```

**Divergence hotfixing / screenshots :**
- `hotfixing` a le support QTrobot WOZ mais les anciens onglets (5 tabs)
- `screenshots` a les nouveaux onglets (Jeux/Macros/Vocal) et le mode offline, mais pas le QTrobot WOZ
- Ces deux branches doivent être mergées

---

## Interface WOZ — onglets (état hotfixing)

| Onglet | Route | Contenu |
|--------|-------|---------|
| Scénario et Jeux | `/r/<rid>/scenarios` | Boutons de scénarios |
| Réactions | `/r/<rid>/reactions` | Boutons émotions/feedbacks rapides |
| Maison | `/r/<rid>/maison` | Activités alternatives + joysticks |
| Macros | `/r/<rid>/macros` | Boutons rapides + programmation par blocs |
| Vocal | `/r/<rid>/vocal` | Reconnaissance vocale → parole robot |

**Sur la branche `screenshots` :** les 3 premiers onglets ont été réduits à un seul
**Jeux** (`/r/<rid>/jeux`), et un mode démo sans robot ("Continuer sans robot") a été ajouté.

---

## Joysticks (woz.js)

Deux joysticks sur chaque page :
- **Joy3** (tête) : `JoyStick` — position `fixed` bottom-left, suit le scroll. Envoie `head` commands.
- **Joy2** (marche) : `JoyStick2` — walk forward/backward/turn. Dead zone horizontale élargie (÷4 au lieu de ÷10) pour faciliter la marche droite. Vitesse proportionnelle à la magnitude Y × `wozSpeedMult` (widget 🏃, 5 niveaux 0.2–1.0, persisté en localStorage).

---

## Programmation par blocs (blocks.js / Macros tab)

- Éditeur drag-and-drop dans l'onglet Macros (niveau de complexité 3)
- Blocs : actions (parler, geste, émotion, LED, pause), contrôle (Répéter N fois, Si/Sinon)
- Drag opéré sur la poignée `.blk-grip` uniquement (pas sur le bloc entier) pour éviter le conflit avec les drop zones imbriquées
- Exécution côté serveur dans `_exec_blocks()` (threading), arrêt via `threading.Event`
- Bug corrigé : `stop.set()` était appelé en fin de `_exec_blocks()` récursif, faisant sortir Répéter après 1 itération. Fix : `stop.set()` uniquement dans le wrapper `_run()` de `run_program()` via `finally`
- Programmes sauvegardés en localStorage (`woz_blocks_saved`)

---

## Décisions de design non-évidentes

### Pourquoi WOZ bypasse le pipeline ROS ?
Le WOZ a besoin de réponses immédiates (l'opérateur clique, le robot réagit en <200ms).
Passer par `/robot_cmd` → `command_dispatcher` → bridge ajoute une latence et des
points de défaillance. Le WOZ est une interface temps-réel, pas une API générique.

### Pourquoi `_RobotSlot` au lieu de réutiliser `nao_bridge.py` ?
`nao_bridge.py` est un nœud ROS2 avec son propre cycle de vie. Le WOZ tourne dans
un thread Flask dans le même processus que `woz_node.py`. Instancier un second nœud
ROS2 dans le même processus n'est pas supporté proprement. La duplication est
intentionnelle.

### Pourquoi roslibpy bloque dans `_connect_qt()` ?
`roslibpy.Ros.run()` est bloquant par design (event loop WebSocket). Il tourne dans
son propre thread daemon. `on_ready()` est appelé une fois connecté — c'est là que
`connected = True` est mis et les topics pré-advertised.

### Pourquoi QT_MOTION_MAP dans qt_bridge.py et pas dans woz_node.py ?
La table existe déjà dans `qt_bridge.py` pour le pipeline ROS. `woz_node.py` l'importe
(`from ros2_robot_bridge.qt_bridge import QT_MOTION_MAP, ...`) pour éviter la
duplication. Import au module level, protégé par `_HAS_QT_MAPS`.

### Pourquoi le volume ne fonctionne pas sur QTrobot via WOZ ?
QTrobot n'expose pas de contrôle de volume audio via rosbridge. La commande `volume`
est silencieusement ignorée (`if not is_qt:` dans `_do_exec`).

---

## Limitations connues

- **Pepper v2 (NAOqi 2.9)** : le WOZ utilise `tcp://` hardcodé (port 9559). Pepper v2
  utilise un gateway TLS (`tcps://`). La connexion échouera.
- **Stripping TTS** : les balises de prosodie QT (`\sel=alt=p-70\` etc.) sont toujours
  supprimées même sur un QTrobot (dans `_STRIP_RE`). À corriger si QTrobot utilisé en prod.
- **Pas de keepalive WOZ** : `nao_bridge.py` a un timer keepalive toutes les 60s
  (`ALTextToSpeech.getLanguage()`). `_RobotSlot` n'en a pas — connexions longues peuvent
  expirer silencieusement.
- **Pas de reconnect WOZ** : si la connexion qi drop, `_RobotSlot` passe en erreur
  sans retenter. Déconnecter et reconnecter depuis `/robots`.

---

## Fichiers clés

| Fichier | Rôle |
|---------|------|
| `woz_node.py` | Nœud Flask WOZ + `_RobotSlot` (connexions directes robot) |
| `qt_bridge.py` | Bridge ROS QTrobot + tables `QT_MOTION_MAP`, `QT_CUSTOM_GESTURES` |
| `nao_bridge.py` | Bridge ROS NAO/Pepper + tables `BEHAVIORS`, `GESTURES` |
| `nao_behavior_tables.py` | Tables de gestes NAO (importées par woz_node et nao_bridge) |
| `woz_states.py` | Machine à états WOZ (comportements par bouton) |
| `woz_static/woz.js` | Logique UI, joysticks, widgets volume/speed |
| `woz_static/blocks.js` | Éditeur de programmation par blocs |
| `woz_static/macros.js` | Boutons macros + éditeur homebrew |
