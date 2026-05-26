
var groupsList = [
	["static/images/face/theatre_identifie_sentiments.png", "QT identifie les sentiments"],
	["static/images/face/theatre_emotions.png", "QT exprime des émotions"],
	["static/images/face/theatre_parle_et_reagit.png", "QT parle et réagit"],
	
	// ["",""],
	// ["static/images/face/reacjeux2.png", "QT commente les jeux"],
	// ["static/images/face/ouch.png", "QT bugue et est malade"],
	// ["static/images/face/ghghgh.png", "QT encourage et réagit à un échec"],
	// ["static/images/face/defend2.png", "Humour"],
	["static/images/face/ah.png", "QT dans son environnement"],
	["static/images/face/stars.png", "QT félicite et applaudit"],	
	["static/images/face/theatre_qt_et_aveugle.png", "QT et l'aveugle"],
	["static/images/face/happy.png", "QT taquine et plaisante"],	
]

var infoList = [
	["static/images/arrow/bleu1.png", ""],

	["static/images/arrow/bleu2.png", ""],
	["static/images/arrow/orange.png", ""],
	
	["static/images/arrow/peau.png", ""],
	["static/images/arrow/basgauche.png", ""],
	["static/images/arrow/jaune.png", ""],
	["static/images/arrow/gaucheplume.png", ""],  
	// ["static/images/arrow/vert2.png", ""],
	["", ""],
	// ["static/images/arrow/ah.png", ""],
	["", ""],
	// ["static/images/arrow/vert1.png", ""],
	["", ""],
	// ["static/images/arrow/rouge.png", ""],
	["", ""],
	
	["", ""],
	
]

var textList = [
	["", "QT identifie les sentiments"],
	["", "QT exprime des émotions"],
	["", "QT parle et réagit"],
	
	// ["", ""],
	// ["", ""],
	// ["",""],
	// ["", "QT écrit"],
	// ["", "QT commente les jeux"],
	// ["", "QT bugue et est malade"],
	
	// ["", "QT encourage et réagit à un échec"],
	["", "QT dans son environnement"],
	["", "QT félicite et applaudit"],
	["", "QT et l'aveugle"],
	["", "QT taquine et plaisante"],
	// ["", "Humour"],
	["", ""],
	["", ""],
	["", ""],
	["", ""],
	["", ""],
]

var commandsList = [

["#C09BF5", [	["La joie", "la_joie",0],
				["L'amusement", "amusement",0],
				["La colère", "la_colere",],
				["La motivation", "la_motivation",0],
				["La fatigue", "la_fatigue",0],
				["La tristesse", "la_tristesse",0],
				["La fierté", "la_fierte",0],
				["L'etonnement", "etonnement",0]	]	],	
		
["#5EEBF4",	[	["Ennuyé", "bored",0],
				["Confus", "confused",0],
				["Craintif", "fear",0],
				["Curieux", "curious",0],
				["Pensif", "thinking",0],
				["Excité","excited",0],
				["Heureux","happy",0],
				["Face au publique","public",0],
				["Neutre","neutral",0]]		],					

["#83A2FE",	[	["Salut", "hello",0],
				["Je ne sais pas", "dontknow",0],
				["Oui", "_oui",0],
				["Non", "_non",0],
				["Vraiment !", "really",0],
				["Comment !","_comment",0],
				["J'aime","jaime",0],
				["Bisous","kisses",0],]	],	

				
["#C4BAD2",	[	["L'objet est à gauche", "objetDroite",0],
				["L'objet est à droite", "objetGauche",0],
				["Suivre des yeux", "suivi",0],
				["Penser", "pense",0],
				["Réflichir", "pense2",0],
				["Debout","standup",0],
				["LSD", "LSD",0],
				["LSU", "LSU",0],
				["END", "end",0], ]	],
				
					
["#FFEE11", [	["Bravo", "bravo",0],
				["Je suis fort", "je_suis_fort",0],
				["C'est bien", "cest_bien",0],
				["Tu as bien fait", "tu_es_fort",0],
				["On est fort", "nous_sommes_fort",0],
				["Je suis fier de toi","fier_de_toi",0],
				["Tu t'appliques","applique",0],
				["Tu persévères","tu_perseveres",0]	]	],					
	
["#F98443", [	["replique 1", "replique_1_1",0],
				["replique 2", "replique_2_1",0],
				// ["replique_2_2", "replique_2_2",0],
				// ["replique_2_3", "replique_2_3",0],
				["replique 3", "replique_3_1",0],

				// ["replique_5_2", "replique_5_2",0],
				["replique 4", "replique_4_1",0],
				["replique 5", "replique_5_1",0],
				["replique 6", "replique_6_1",0],
				["posture initiale", "reset_posture",0]
					]	],
				
["#F5D39B", [	["Merci", "merci",0],
				["Comment ?", "repete",0],
				["Oui", "oui",0],
				["Non", "non",0],
				["Je sais pas, et toi?","sais_pas_toi",0],
				["Et toi?","et_toi",0]	]	]	,				
				
				
				["white",	[	["Humour","humour",0] ]		],
				["red",			[	["","",0] ]		],
				["white",		[	["","",0] ]		],
				["gray",		[	["","",0] ]		],
				["black",		[	["","",0] ]		],
			]
			
// icon position
var ellipseGroupList = [
	[14.9, 3.7],
	[10.2, 6],
	[5.2, 7.1],
	// [-5.2, 7.1],
	// [-10.2, 6],
	// [-14.9, 3.7],
	// [-14.9,	-4.2],
	// [-10.2,	-6.5],
	[-5.2, -7.6],
	[5.2, -7.6],
	[10.2, -6.5],
	[14.9, -4.2],
]

// arrow position
var ellipseInfoList = [
	[19.8, 5],
	[14.7, 9.8],
	[7, 12.5],
	
	// [-7.2, 12],
	// [-11.5, 10.5],
	// [-19.8, 6],
	// [-19.8, -6],
	
	[-6.3, -12.2],
	[7.2, -11.8],
	[13.3, -10.5],
	[19.8, -6],
	// [-14.8, -9.5],
	["", ""],
	["", ""],
	["", ""],
	["", ""],
	["", ""],
]

// text position
var ellipseTextList = [
	[22.3, 9.0],
	[15.3, 12.8],
	[0, 14],
	
	// [-7.7, 11.5],
	// [-15.8, 12],
	// [-25, 4.3],
	// [-22.5, -8.8],
	[-1.1, -15],
	[10.5, -12.3],
	[20.6, -9.7],
	[22.3, -6.8],
	// [-14, -11.7],
	["", ""],
	["", ""],
	["", ""],
	["", ""],
	["", ""],
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
