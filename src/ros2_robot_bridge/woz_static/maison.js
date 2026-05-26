var groupsList = [
	["static/images/face/partage_sentiments.png", "Jeux symboliques avec médiateur"],
	["static/images/face/theatre_emotions.png", "QT partage ses sentiments"],
	["static/images/face/stars.png", "Renforcements positifs et encouragements"],
	["static/images/face/theatre_a_definir_3.png","QT clos la scéance"],
	["static/images/face/maison_debut_activite1.png", "QT ouvre la scéance"],
	["static/images/face/presentation2.png", "QT se présente pour la première fois"],
	["static/images/face/questionne.png", "QT et le jeu de mimes"],
	["static/images/face/mimes2.png", "Réactions pour le jeu de mimes"],
	["static/images/face/ghghgh.png", "QT et le travail manuel"],
	["static/images/face/manuel.png", "Réactions pour pour les travaux manuels"],	
	["static/images/face/wink.png", "QT et 1, 2, 3 soleil"],	
	["static/images/face/happy.png", "On raconte sa journée ?"],
]

var infoList = [
	["static/images/arrow/bleu1.png", ""],
	["static/images/arrow/bleu2.png", ""],
	["static/images/arrow/orange.png", ""],
	["static/images/arrow/hautplein.png", ""],
	["static/images/arrow/ah.png", ""],
	["static/images/arrow/vert1.png", ""],
	["static/images/arrow/rouge.png", ""],
	["static/images/arrow/vert2.png", ""],
	["static/images/arrow/peau.png", ""],
	["static/images/arrow/basgauche.png", ""],
	["static/images/arrow/jaune.png", ""],
	["static/images/arrow/gaucheplume.png", ""], 
]

var textList = [
	["", "Jeux symboliques avec médiateur"],
	["", "QT partage ses sentiments"],
	["", "Renforcements positifs et encouragements"],
	["","QT clos la scéance"],
	["", "QT  ouvre la scéance"],
	["", "QT se présente pour la première fois"],
	["", "QT et le jeu de mimes"],
	["", "Réactions pour le jeu de mimes"],
	["", "QT et le travail manuel"],
	["", "Réactions pour pour les travaux manuels"],
	["", "QT et 1, 2, 3 soleil"],
	["", "On raconte sa journée ?"]
]

var commandsList = [
	// ["", "Jeux symboliques avec médiateur"],
	["#C09BF5", [	["Et alors ?", "et_alors",0], 
					["Ça doit être dur pour lui", "c_dur",0],
					["Je comprends", "je_comprend",0],
					["C'est drôle", "c_drole",0],
					["Pourquoi il fait ça ?", "pourquoi_faire",0],
					["Comment il se sent ?", "se_sentir",0],
					["Tu peux m'expliquer ?", "m_expliquer",0],
					["Comment ça s'est passé ?", "comment_passe",0],
					["Tu es sûr ?", "tu_es_sur",0], 
					["Envie de jouer ?", "envie_de_jouer",0],
					["Réessayons !", "reessayons",0],
					["C'est trop difficile ?", "difficile",0]	]	], 
	// ["", "QT partage ses sentiments"],					
	["#5EEBF4", [	["QT surpris !", "surprise",0],
					["QT exprime la peur", "peur",0],
					["QT dégouté", "degout",0],
					["QT en colère !", "en_colere",0],
					["QT est heureux!", "bon_heur",0],
					["QT exprime sa tristesse", "_tristesse",0],
					["QT est fatigué", "_fatigue",0],
					["QT réfléchit !", "confusion",0] ]       ],
	// ["", "Renforcements positifs et encouragements"],				
	["#FFEE11", [	["Bravo", "bravo",0],
					["C'est bien", "cest_bien",0],
					["Tu as bien fait", "tu_es_fort",0],
					["On est fort", "nous_sommes_fort",0],
					["Je suis fier de toi", "fier_de_toi",0],
					["Merci", "merci",0],
					["Courage", "courage",0],
					["Ce n'est pas grave", "cest_pas_grave",0],
					["Respire et recommence", "respire",0],
					["Tu as l'air de t'amuser !", "amusement",0],
					["Quelle mine joyeuse !", "la_joie",0],
					["Tu t'appliques bien !", "applique",0]]	],
	// ["","QT clos la scéance"],
	["#56a0ff",	[	["Fin des activités ","terminee",0],
					["QT fatigué","qt_fatigue",0] ]	],
	//QT  ouvre la scéance				
	["#866d4f",	[	["Salut ","journee",0],
					["Etes vous prêts ?","on_est_prets",0],
					["Es tu prêt ?", "tu_es_pret",0],
					["Pourquoi tu ne veux pas ?","pourquoi_non",0],
					["On va s'amuser !","rassure_toi",0],
					["Je t'attend","previens_moi",0],
					["Choisir un jeu", "choix_activite",0],
					["On commence","on_commence",0] ]	],
	// QT se présente pour la première fois
	["#d0d0d0", [	["Je me présente", "_salut",0],
					["Quel est ton nom ?", "_comment_t_appeler",0],
					["Et tes parents ?", "_nom_parents",0],
					["Ce qu'on va faire", "_aujourdhui",0]  ]	],
	// QT et le jeu de mimes
	["#83a2fe", [	["Expliquer les règles", "regles_mime",0],
					["Le lion", "lion",0],
					["La girafe", "girafe",0],
					["Le zebre", "zebre",0],
					["Le singe", "singe",0],
					["L'éléphon", "elephon",0],
					["La tortue", "tortue",0],
					["Le serpent", "serpent",0],
					["Le chat", "chat",0],
					["Le chien", "chien",0],
					["Le chameau", "chameau",0],
					["La grenouille", "grenouille",0]		]	],
	// Réactions pour le jeu de mimes
	["#F2838C", [	["Quelle peur !", "quelle_peur",0],
					["Il est féroce !", "feroce",0],
					["C'est drôle", "drole",0],
					["Qu'il est mignon !", "mignon",0],
					["Bravo!", "_bravo",0],
					["Tu es fort !", "tres_fort",0],
					["Tu imites bien", "imites_bien",0],
					["Réflechis", "reflechis",0],
					["Un conseil à tes parents ?", "tes_parents",0],
					["Essaye encore", "essaye_encore",0],
					["Essaye un autre", "un_autre",0],
					["On reprend ?", "on_reprend",0]	]	],
	// QT et le travail manuel
	["#C0F971", [	["Pâte à modeler", "manuel_regles",0],	
					["Le ciel", "_ciel",0],
					["La table", "table",0],
					["Le salon", "salon",0],
					["Les animaux", "les_animaux",0],
					["La mer", "la_mer",0],
					["Construire un puzzle", "puzzle",0],
					["Construire une cabane", "cabane_regles",0],
					["Le sol","le_sol",0],
					["Les murs","les_murs",0],
					["Le toit", "le_toit",0],
					["La porte", "la_porte",0]	]	],
	//Réactions pour pour les travaux manuels"				
	["#5cd788", [	
					["Génial !", "genial",0],
					["C'est joli !", "c_joli",0],
					["C'est reussi !", "reussi",0],
					["Tu t'en sors bien !", "sors_bien",0],
					["Tu es rapide !", "rapide",0],
					["Fais de ton mieux", "fais_mieux",0],
					["Essayes encore", "recommencer",0],
					["Essayes un autre", "essaye_un_autre",0],
					["Sois patient","patience",0],
					["Puzzle : commencer","puzzle_debut",0],
					["C'est un bon début","bon_debut",0],
					["Observe bien les morceaux !", "observe_bien",0]	]	],
	//QT et 1, 2, 3 soleil				
	["#F98443", [	["Régles du jeu", "soleil_regles",0],
					["Lancer !", "lancer_soleil",0],
					["Bravo", "bravo",0],
					["J'ai gagné", "j_ai_gagne",0]	]	],
	//On raconte sa journée ?				
	["#F5D39B", [	["Comment ça va ?", "comment_ca_va",0],
					["Et ta journee ?", "et_ta_journee",0],
					["Envie de nous raconter ?", "raconter",0],
					["De belles choses à raconter ?", "de_belles_choses",0],
					["Quelque chose t'a inquieté ?", "inquietude",0],
					["Tu as joué avec tes amis ?", "tes_amis",0],
					["Et à l'école ?", "ecole_ennuie",0],
					["Vraiment ?", "really",0],
					["Pourquoi ?", "_pourquoi",0],
					["Et après ?", "et_apres",0],
					["Ah bon !", "ah_bon",0]	]	]
]


// icon position
var ellipseGroupList = [
	[14.9, 3.7],
	[10.2, 6],
	[5.2, 7.1],
	[-4.6, 7.1],
	[-10.4, 6],
	[-15.3, 3],
	[-14.9,	-4.2],
	[-10.2,	-6.5],
	[-2.9, -7.6],
	[2.5, -7.6],
	[10.2, -6.5],
	[14.9, -4.2]
]

// arrow position
var ellipseInfoList = [
	[19.8, 5],
	[14.7, 9.8],
	[7, 12.5],
	[-4.2, 12.5],
	[-12.5, 10.5],
	[-21, 5],
	[-19.8, -6],
	[-14.8, -9.5],
	[-3.1, -12.2],
	[5.2, -11.8],
	[13.3, -10.5],
	[19.8, -6]
]

	
	



// text position
var ellipseTextList = [
	[22.3, 9.0],
	[17.3, 13.8],
	[8, 17],
	[-4.7, 15.5],
	[-16.3, 11],
	[-26.5, 3.3],
	[-22.5, -8.8],
	[-13.5, -13],
	[-1.1, -15],
	[9.5, -12.3],
	[18.6, -9.7],
	[22.3, -6.8]
]

// button position
var ellipseCommandList = [
	[23.55, 4.4],
	[18.41, 10.05],
	[7.63, 12.67],
	[-7.63, 12.67],
	[-18.4, 10.04],
	[-23.55, 4.54],
	[-24.25, -3.4],
	[-19.21, -8.95],
	[-10.63, -12.67],
	[10.63, -12.67],
	[19.21, -8.95],
	[24.25, -3.4],
]
