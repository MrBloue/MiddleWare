#! /usr/bin/env python
# coding: utf-8
import random


                 
# state: ( {g: gesture, s: say, h: [head], la: [left_arm], ra: [right_arm], w: [x, y, z, ex, ey, ez]}, [(trigger, param, next_state)])
states = { 'begin': ( {}, [('time', 1, 'choice')]),

                'choice': ( {'g': '', 's': '', 'e':'' },
                                # à implementer le joystique plutard debut
                                [   ('woz', None, 'left'), ('woz', None, 'right'),('woz', None, 'upleft'),('woz', None, 'upright'),
                                    ('woz', None, 'up'), 
                                    ('woz', None, 'center'),
                                    ('woz', None, 'down'),('woz', None, 'right'),
                                    ('woz', None, 'downleft'),('woz', None, 'downright'),
                                    
                                    # comportement reactions
                                    ('woz', None, 'la_joie'),('woz', None, 'amusement'),('woz', None, 'la_colere'),('woz', None, 'la_motivation'),('woz', None, 'la_fatigue'),('woz', None, 'la_tristesse'),
                                    ('woz', None, 'la_fierte'),('woz', None, 'etonnement'),('woz', None, 'adulte_accord'),('woz', None, 'demande_adulte'),('woz', None, 'que_pense'),
                                    ('woz', None, 'monsieur'),('woz', None, 'madame'),('woz', None, 'bien'),('woz', None, 'cest_mieux'),
                                    ('woz', None, 'tu_mexplique'),('woz',None, 'important'),('woz', None, 'ensuite'),('woz', None, 'pk_pas_bien'),
                                    ('woz', None, 'tu_es_sur'),('woz', None, 'plus_simple'),('woz', None, 'plus_difficile'),
                                    ('woz', None, 'bien_mal'),('woz', None, 'pas_marche'),('woz', None, 'pourquoi'),('woz', None, 'ecrit'),('woz', None, 'senslettre'),('woz', None, 'fermelettre'),
                                    ('woz', None, 'endroitlettre'),('woz', None, 'bien_comme_toi'),('woz', None, 'triche'),('woz', None, 'facile'),('woz', None, 'pas_trop_vite'),
                                    ('woz', None, 'boum'),('woz', None, 'tu_relances'),('woz', None, 'je_bugue'),('woz', None, 'je_rouille'),
                                    ('woz', None, 'attends'),('woz', None, 'malade'),('woz', None, 'et_alors'),('woz', None, 'jai_progresse'),
                                    ('woz', None, 'cest_difficile'),('woz', None, 'fais_mon_mieux'),('woz', None, 'tas_gagne'),
                                                                            ('woz', None, 'ma_tablette'),('woz', None, 'pas_mal'),('woz', None, 'je_trouve_pas'),('woz', None, 'respire'),('woz', None, 'ecris_mal'),('woz', None, 'cest_pas_grave'),
                                    ('woz', None, 'reessayons'),('woz', None, 'fera_mieux'),('woz', None, 'courage'),('woz', None, 'rate'),('woz', None, 'difficile'),
                                    ('woz', None, 'pas_content_moi'),('woz', None, 'tu_mecoute'),('woz', None, 'on_essaye'),('woz', None, 'bravo'),
                                    ('woz', None, 'je_suis_fort'),('woz', None, 'cest_bien'),('woz', None, 'tu_es_fort'),('woz', None, 'nous_sommes_fort'),
                                    ('woz', None, 'fier_de_toi'),('woz', None, 'applique'),('woz', None, 'tu_perseveres'),
                                    ('woz', None, 'aie'),('woz', None, 'ahahah'),('woz', None, 'muscle'),('woz', None, 'merci'),('woz', None, 'repete'),('woz', None, 'oui'),
                                    ('woz', None, 'non'),('woz', None, 'sais_pas_toi'),('woz', None, 'et_toi'),
                                        
                                    # comportement de scenario
                                    ('woz', None, 'pression_lance'),('woz', None, 'pression_expli'),('woz', None, 'pression_complet'),('woz', None, 'archeo_lance'),('woz', None, 'archeo_expli'),('woz', None, 'archeo_complet'),
                                    ('woz', None, 'drapeau_lance'),('woz', None, 'drapeau_expli'),('woz', None, 'drapeau_complet'),('woz', None, 'alpha_lance'),('woz', None, 'alpha_expli'),
                                    ('woz', None, 'alpha_complet'),('woz', None, 'zoo_lance'),('woz', None, 'zoo_expli'),('woz', None, 'zoo_complet'),
                                    ('woz', None, 'chimi_lance'),('woz',None, 'chimi_expli'),('woz', None, 'tilt_lance'),('woz', None, 'tilt_expli'),
                                    ('woz', None, 'tilt_complet'),('woz', None, 'cowritter_lance'),('woz', None, 'cowritter_expli_class'),
                                    ('woz', None, 'cowritter_complet'),('woz', None, 'jus_lance'),('woz', None, 'jus_expli'),('woz', None, 'jus_complet'),('woz', None, 'poursuite_lance'),('woz', None, 'poursuite_expli'),
                                    ('woz', None, 'poursuite_complet'),('woz', None, 'tu_viens'),('woz', None, 'ton_nom'),('woz', None, 'ca_va'),('woz', None, 'bonjour'),
                                    ('woz', None, 'je_mappelle_qt'),('woz', None, 'tu_veux_maider'),('woz', None, 'tu_maides_encore'),('woz', None, 'adieu'),
                                    ('woz', None, 'adieu2'),('woz', None, 'pause'),('woz', None, 'change_jeu'),('woz', None, 'choisis_jeu'),
                                    ('woz', None, 'dernier_jeu'),('woz', None, 'cetait_bien'),('woz', None, 'tu_maide'),('woz', None, 'mes_progres'),('woz', None, 'bisou'),('woz', None, 'bcp_travaille'),('woz', None, 'il_est_lheure'),
                                    ('woz', None, 'arrete'),('woz', None, 'au_revoir'),
                                    # comportement theatre 
                                    ('woz', None, 'hello'),('woz', None, 'dontknow'),('woz', None, '_oui'),('woz', None, '_non'),('woz', None, 'suivi'),('woz', None, 'public'),
                                    ('woz', None, 'objetDroite'),('woz', None, 'objetGauche'),('woz', None, 'pense'),('woz', None, 'pense2'),('woz', None, 'neutral'),
                                    ('woz', None, 'really'),('woz', None, '_comment'),('woz', None, 'jaime'),('woz', None, 'happy'),
                                    ('woz', None, 'kisses'),('woz', None, 'excited'),('woz', None, 'thinking'),('woz', None, 'curious'),
                                    ('woz', None, 'fear'),('woz', None, 'confused'),('woz', None, 'bored'),
                                    # nuitrack
                                    # ('woz', None, 'human_0_appeared'),('woz', None, 'human_0_disappeared'),
                                    # ('woz', None, 'human_0_center'),('woz', None, 'human_0_left'),('woz', None, 'human_0_right'),
                                    # ('woz', None, 'human_0_center_1meter'),('woz', None, 'human_0_left_1meter'),('woz', None, 'human_0_right_1meter'),
                                    # ('woz', None, 'human_0_center_2meters'),('woz', None, 'human_0_left_2meters'),('woz', None, 'human_0_right_2meters'),
                                    
                                    
                                    ('woz', None, 'replique_1_1'),('woz', None, 'replique_2_1'),
                                    ('woz', None, 'replique_2_2'),('woz', None, 'replique_2_3'),('woz', None, 'replique_3_1'),('woz', None, 'replique_3_2'),('woz', None, 'replique_4_1'),
                                    ('woz', None,'replique_5_1'), ('woz', None,'replique_5_2'), ('woz', None,'replique_6_1'), ('woz',None,'reset_posture'), 
                                    # semi autonome
                                    ('woz', None,'human_0_center_1m'), ('woz', None,'human_0_left_1m'), ('woz',None,'human_0_left_2m'), ('woz',None,'human_0_right_2m'), 
                                    ('woz', None,'human_0_center_2m'),
                                    ('woz', None,'human_0_right_1m'),
                                    # maison
                                    ('woz', None, '_salut'),('woz', None, '_comment_t_appeler'),('woz',None,"_nom_parents"),('woz', None, '_aujourdhui'),('woz', None, 'journee'),('woz',None, 'on_est_prets'),
                                    ('woz', None, 'tu_es_pret'),('woz',None, 'pourquoi_non'),('woz',None, 'rassure_toi'),('woz',None, 'previens_moi'),('woz', None, 'on_commence'),('woz', None, 'choix_activite'),('woz',None, 'c_est_parti'),
                                    ('woz', None, 'terminee'), ('woz', None, 'qt_fatigue'),('woz', None, 'regles_mime'),('woz', None, 'lion'),('woz', None, 'girafe'),
                                    ('woz', None, 'gazelle'),('woz', None, 'zebre'),('woz', None, 'singe'),('woz', None, 'elephon'),('woz', None, 'guepard'),
                                    ('woz', None, 'tigre'),('woz', None, 'tortue'),('woz', None, 'panthere'), ('woz', None, 'serpent'),('woz', None, 'chat'), ('woz', None,'chien' ),('woz', None, 'papillon'),
                                    ('woz', None, 'chameau'),('woz', None, 'grenouille'), 
                                    ('woz', None, 'quelle_peur'),('woz', None, 'feroce'),('woz', None, 'drole'),('woz', None, 'mignon'),('woz', None, '_bravo'),('woz', None, 'tres_fort'),
                                    ('woz', None, 'imites_bien'),('woz', None, 'reflechis'),('woz', None, 'tes_parents'),('woz', None, 'essaye_encore'),('woz', None, 'un_autre'),('woz', None, 'on_reprend'),                                   
                                    ('woz', None, 'manuel_regles'),('woz', None, '_ciel'),('woz', None, 'table'),('woz', None, 'salon'),('woz', None, 'les_animaux'),('woz', None, 'la_mer'), ('woz', None, 'puzzle'),
                                    ('woz', None, 'cabane_regles'),('woz', None, 'le_sol'),('woz', None, 'les_murs'),('woz', None, 'le_toit'),('woz', None, 'la_porte'),('woz', None, 'genial'),('woz', None, 'c_joli'),
                                    ('woz', None, 'reussi'),('woz', None, 'sors_bien'),('woz', None, 'rapide'),('woz', None, 'fais_mieux'),('woz', None, 'recommencer'),('woz', None, 'essaye_un_autre'),('woz', None, 'patience'),
                                    ('woz', None, 'puzzle_debut'),('woz', None, 'bon_debut'),('woz', None, 'observe_bien'),
                                    ('woz', None, 'soleil_regles'),('woz', None, 'lancer_soleil'),('woz', None, 'j_ai_gagne'),
                                    ('woz', None, 'comment_ca_va'),('woz', None, 'et_ta_journee'),('woz', None, 'raconter'),('woz', None, 'de_belles_choses'),('woz', None, 'inquietude'),
                                    ('woz', None, 'tes_amis'),('woz', None, 'ecole_ennuie'),('woz', None, '_pourquoi'),('woz', None, 'et_apres'),('woz', None, 'ah_bon'),
                                    ('woz', None, 'envie_de_jouer'),('woz', None, 'c_dur'),('woz', None, 'je_comprend'),('woz', None, 'c_drole'),
                                    ('woz', None, 'pourquoi_faire'),('woz', None, 'se_sentir'),('woz', None, 'm_expliquer'),('woz', None, 'comment_passe'),
                                    ('woz', None, 'surprise'),('woz', None, 'peur'),('woz', None, 'degout'),('woz', None, 'en_colere'),
                                    ('woz', None, 'bon_heur'),('woz', None, '_tristesse'),('woz', None, '_fatigue'),('woz', None, 'confusion'),     
                                    ('woz', None, 'end')]),

           

                # à implementer le joystique plutard debut
                'up': ( {'h': [0.0,-20.0]}, [('time', 0.1, 'choice')]),
                'center': ( {'h': [0.0,0.0]}, [('time', 0.1, 'choice')]),
                # 'center': ( {'e':'', 'g':'QT/neutral','s':''}, [('time', 0.1, 'choice')]),
                'down': ( {'h': [0.0,+10.0]}, [('time', 0.1, 'choice')]),
                'right': ( {'h': [-20.0,0.0]}, [('time', 0.1, 'choice')]),
                'left': ( { 'h': [+20.0,0.0]}, [('time', 0.1, 'choice')]),
                'upright': ( { 'h': [-20.0,-20.0]}, [('time', 0.1, 'choice')]),
                'upleft': ( { 'h': [+20.0,-20.0]}, [('time', 0.1, 'choice')]),
                'downright': ( {'h': [-10.0,+10.0]}, [('time', 0.1, 'choice')]),
                'downleft': ( { 'h': [+10.0,+10.0]}, [('time', 0.1, 'choice')]),
                    #   # à implementer le joystique plutard fin 

                # QT_AVEC_AVEUGLE
                # AVEUGLE: Ramène-moi un verre d’eau !

                # QT : (en rigolant) Je ne suis plus ton serviteur ! (rire)
                'replique_1_1' : ({'e':'','g':'','s' : '\\vct=70\\je ne bougerai pas d\'un centimetre, Je  ne   suis   plu !  ton  serviteur ! #LAUGH01#'},[('time', 5, 'choice')]),

                # AVEUGLE: Allez QT J’ai super mal au pied.

                # QT : (lève la tête) Regarde ! (lève un bras) Il y a une araignée au plafond.
                # (baisse la tête et le bras) c’est passionnant ces bêtes-là ! 
                # J’aime beaucoup regarder les insectes, ils sont tellement poétiques…
                'replique_2_1' : ({'e':'','h' : [0.0, -20.0],'s' : '\\pau=2000\\,\\rspd=80\\,\\vct=70\\!Regaaaaarde !'},[('time', 2, 'replique_2_2')]),
                'replique_2_2' : ({'e':'','ra' : [80, 0, 0], 's' : '\\vct=70\\,\\rspd=80\\,\\vct=70\\Il y a une araignée au plafond.'},[('time', 5, 'replique_2_3')]),
                'replique_2_3' : ({'e':'','g':'' ,'s' : ' \\rspd=80\\C’est passionnant ces bêtes-là !\\pau=200\\,\\vct=70\\J’aime beaucoup regarder les insectes'},[('time', 2, 'replique2_4')]),
                'replique2_4'  : ({'e':'','ra' : [-80, 0, 0],'h': [0.0,0.0] ,'s' : ' \\rspd=80\\,\\pau=200\\,\\vct=70\\ ils sont tèèèllement poétiiiques'},[('time', 2, 'choice')]),
                # AVEUGLE: N’importe quoi, tu fais ton rebel maintenant ! Tu sais que je ne vois plus...

                # QT : Qu’est ce que tu racontes ? (visage fâché) Pas du tout ! ( secoue la tête)
                'replique_3_1' : ({ 'e' : 'QT/blowing_raspberry','g':'', 's' : '\\vct=70\\kèèè ce que tu racontes ?' }, [('time', 2, 'replique_3_2') ] ),
                'replique_3_2' : ({'e':'','g' : 'QT/imitation/head-right-left','s' : '\\vct=70\\Pas du tout !' },[('time', 1, 'choice') ]),

                # AVEUGLE: Tu comprends bien…

                # QT : On va à la plage ! (pointe du doigt à dx, visage enjoué)
                'replique_4_1' : ({'e' : 'QT/happy_blinking','ra' : [10, 0, 0], 's' : '\\vct=70\\On ! va ! à  la  plaaaaage !' }, [ ('time', 2, 'choice') ]),

                # AVEUGLE: Arrête et va ouvrir la porte il y a quelqu'un

                # QT :  AH ! (il regarde par terre) J’ai oublié de mettre de l'écran solaire ? (regarde ses bras, visage inquiet)
                'replique_5_1' : ({ 'e':'', 'h' : [0.0, +10.0], 's' : '\\vct=70\\Aaaaaaaaaah!' },[ ('time', 1, 'replique_5_2')] ),
                'replique_5_2' : ( {'e' : 'QT/surprise','la' : [0, 0, -20],'ra' : [0, 0, -20],'s' : '\\vct=70\\J’ai oublié de mettre de l\'écran solaire ?' }, [('time', 3, 'reset_posture') ]),

                # AVEUGLE : (ouvre la porte)

                # LIVREUR : Madame voici votre colis, vous avez bien un QT 2.0 dernière génération mobile?

                # QT :  Attends! Je t’apporte ton verre d’eau ! (sourire)
                'replique_6_1' : ({'e':'QT/showing_smile','g':'','s' : 'Attends!, Attends! ,Attends! , Attends! ,Attends!  Je t’apporte ton verre dooooo !' },[ ('time', 1, 'choice')] ),

                # Etat de reinitialisation de la posture
                'reset_posture' : ( {'e':'', 'g':'QT/neutral','s':'' }, [ ('time', 1, 'choice')]),

               
                'human_0_center_1m' : ({'e' : 'QT/breathing_exercise','g' : 'QT/disgusted','s' : 'Pas si près, je ne peux pas respirer.'},[('time', 6, 'choice')]),

               
                'human_0_left_1m' : ({'e' : 'QT/kiss','g' : 'QT/kiss','s' : '\\pau=300\\ J\'ai envie de te contempler. D\'ailleurs tu me fais rougir ! \\pau=1000\\ Dis-moi, est-ce que je te plais ?'},[('time', 6, 'choice')]),

                
                'human_0_right_1m' : ({'e' : 'QT/shy','g' : 'QT/shy','s' : 'Je n’ai pas d’ami\\pau=300\\Je n’ai pas d’ami\\pau=300\\ Je n’ai pas d’ami. Dis-moi, est-ce que je te plais ?'},[ ('time', 12, 'choice')]),

                'human_0_center_2m' : ({'e' : 'QT/talking','g' : 'QT/surprised','s' : '\\rspd=80\\ Je ne t\'entends pas très bien. Avance que je te vois.'},[('time', 6, 'choice')]),

               
                'human_0_left_2m' : ({'e' : 'QT/happy','g' : 'QT/happy','s' : 'C’est drole ! Tu me fais rire'},[('time', 6, 'choice')]),

                
                'human_0_right_2m' : ({'e' : 'QT/with_a_cold_sneezing','g' : 'QT/sad','s' : '#SNEEZE01# Pardon, je suis malade !'},[('time', 6, 'choice')]),


            
                
                #  Theatre
                'hello': ( {'e': 'QT/happy', 'g': 'QT/hi', 's': '\\pau=2000\\Salut!', 'h': [0,0]}, [('time', 1, 'choice')]),
                'dontknow': ( {'e': '', 'g': 'QT/touch-head', 's': '~\\pau=500\\Je ne sais pas'}, [('time', 1, 'choice')]),
                '_oui': ( {'e': '', 'g': 'QT/imitation/nodding-yes', 's': '~\\pau=500\\Oui!'}, [('time', 1, 'choice')]),
                '_non': ( {'e': '', 'g': 'QT/emotions/sad', 's': '~\\pau=500\\Non!'}, [('time', 1, 'choice')]),
                'suivi': ( {'e': 'QT/surprise', 'g': 'QT/imitation/head-right-left', 's': '\\pau=500\\'}, [('time', 1, 'choice')]),
                'public': ( {'e': 'QT/surprise', 'h': [0.0,0.0], 's': '\\pau=500\\'}, [('time', 1, 'choice')]),
                'objetDroite': ( {'e': 'QT/happy', 'h': [+10.0,0.0], 's': '\\pau=1000\\Ici!'}, [('time', 1, 'choice')]),
                'objetGauche': ( {'e': 'QT/happy', 'h': [-10.0,0.0], 's': '\\pau=1000\\Ici!'}, [('time', 1, 'choice')]),
                'pense': ( {'e': 'QT/confused', 'g': 'QT/imitation/hands-on-hip', 's': '\\pau=500\\'}, [('time', 1, 'choice')]),
                'pense2': ( {'e': 'QT/afraid', 'g': 'QT/touch-head-back', 's': '\\pau=500\\'}, [('time', 1, 'choice')]),
                'neutral': ( {'e': 'QT/neutral', 'g': 'QT/neutral', 's': '\\pau=500\\'}, [('time', 1, 'choice')]),
                'really': ( {'e': 'QT/dirty_face','g': 'QT/surprise', 's': '\\pau=2000\\Vraiment ?'}, [('time', 3, 'choice')]),
                '_comment': ( {'e':'QT/surpise','g': 'QT/touch-head', 's': '\\pau=2000\\Comment ?'}, [('time', 3, 'choice')]),
                'jaime': ( {'e':'QT/happy_blinking','g': 'QT/happy', 's': '\\pau=2000\\jème beaucoup !'}, [('time', 3, 'choice')]),
                'happy': ( {'e':'QT/happy_blinking','g': 'QT/happy', 's': '\\pau=500\\ Youpi !'}, [('time', 3, 'choice')]),

                'kisses': ( {'e':'QT/kiss','g': 'QT/kiss', 's' : ""}, [('time', 3, 'kisses1')]),
                'kisses1': ( {'e':'QT/one_eye_wink','g': 'QT/neutral', 's' : ""}, [('time', 3, 'kisses2')]),
                'kisses2': ( {'e':'QT/shy','h': [-10.0,+10.0], 's' : ""}, [('time', 3, 'choice')]),

                'excited': ( {'e':'QT/surprise','g': 'QT/neutral', 's' : ""}, [('time', 3, 'excited1')]),
                'excited1': ( {'e':'QT/happy','g': 'QT/neutral', 's' : ""}, [('time', 3, 'choice')]),

                'thinking': ( {'e':'QT/surprise','g': 'QT/bored', 's' : ""}, [('time', 3, 'choice')]),

                'curious': ( {'e':'QT/surprise','g': 'QT/neutral', 's' : ""}, [('time', 3, 'curious1')]),
                'curious1': ( {'e':'QT/showing_smile','g': 'QT/neutral', 's' : ""}, [('time', 3, 'choice')]),

                'fear': ( {'e':'QT/cry','g': 'QT/face', 's' : ""}, [('time', 3, 'choice')]),

                'confused': ( {'e':'QT/confused','g': 'QT/neutral', 's' : ""}, [('time', 3, 'choice')]),
                'bored': ( {'e':'QT/yawn','g': 'QT/bored', 's' : ""}, [('time', 3, 'choice')]),

                #comportement reactions
                'la_joie': ( {'e':'QT/happy', 'g':'QT/so', 's': random.choice(['Quelle mine joyeuse', 'Quel booo  sourire', 'Quel enthousiassme']) }, [('time', 1, 'choice')]),
                'amusement': ( {'e':'QT/happy', 'g':'QT/happy', 's': random.choice(["Ça a l'air de t'amuser!", "Tu as l'air de trouver que c'est drôle"]) }, [('time', 1, 'choice')]),
                'la_colere': ( {'e':'QT/confused', 'g':'QT/head_scratch', 's': random.choice(['child_name, Est-ce que tu es fâché?', "Tu es en colère?", "Tu as l'air en colère"]) }, [('time', 1, 'choice')]),
                'la_motivation': ( {'e':'QT/showing_smile', 'g':'QT/handclap', 's': random.choice(["Tu as l'air motivé", "child_name , tu es très motivé aujourd'hui"]) }, [('time', 1, 'choice')]),
                'la_fatigue': ( {'e':'QT/yawn', 'g':'QT/yawn', 's': "Je suis désolé. #YAWN01# je suis fatigué." }, [('time', 1, 'choice')]),
                'la_tristesse': ( {'e':'QT/sad', 'g':'QT/thanks', 's': random.choice(["child_name ,Est-ce que tu es triste?" , "Tu as de la\sel=alt=p-20\  peine?", "Quelque chose te rend triste?"]) }, [('time', 1, 'choice')]),
                'la_fierte': ( {'e':'QT/showing_smile', 'g':'QT/yes', 's': random.choice(["Tu es fier de ton travail ?	", "Tu as l'air fier de ton travail"]) }, [('time', 1, 'choice')]),
                'etonnement': ( {'e':'', 'g':'QT/curious', 's': random.choice(["Tu as l'air étonné", "Tu es étonné,"]) }, [('time', 1, 'choice')]),
                
                'adulte_accord': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': " adult_name ,tu es d'accord?" }, [('time', 1, 'choice')]),
                'demande_adulte': ( {'e':'QT/talking', 'g':'QT/angry', 's':"Demandons à adult_name " }, [('time', 1, 'choice')]),
                'que_pense': ( {'e':'QT/talking', 'g':'QT/challenge', 's':random.choice([" adult_name ,  qu'en penses-tu ?" , "Qu'est-ce que tu en pense adult_name ?"]) }, [('time', 1, 'choice')]),
                'monsieur': ( {'e':'', 'g':'', 's': "Monsieur!" }, [('time', 1, 'choice')]),
                'madame': ( {'e':'', 'g':'', 's': "Madame!" }, [('time', 1, 'choice')]),

                'bien': ( {'e':'QT/showing_smile', 'g':'', 's': random.choice(["C'est comme ça qu'il faut faire?", "Est-ce que c'est bien?"]) }, [('time', 1, 'choice')]),
                'cest_mieux': ( {'e':'', 'g':'QT/bored', 's': random.choice(["Est-ce que je m'améliore?", "Je fais mieux kavant?"]) }, [('time', 1, 'choice')]),
                'tu_mexplique': ( {'e':'QT/curious', 'g':'QT/confused', 's': random.choice(["tu m'expliques?", "Tu peux m'expliquer un peu?", "Olala. c'est difficile! Tu peux m'expliquer?"]) }, [('time', 1, 'choice')]),
                'important': ( {'e':'QT/talking', 'g':'QT/challenge', 's': random.choice(["Qu'est-ce qu'on a fait qui est le plus important?", "C'est quoi le plus important dans ce qu'on a fait,"]) }, [('time', 1, 'choice')]),
                'ensuite': ( {'e':'QT/showing_smile', 'g':'QT/angry', 's': random.choice(["Que fait-on maintenant pour que j'apprenne mieux à écrire", "Quel jeu pourrait le pluss m'aider tu penses"]) }, [('time', 1, 'choice')]),
                'pk_pas_bien': ( {'e':'QT/sad', 'g':'QT/so', 's': random.choice(["Pourquoi c'est pas bien,", "Pourquoi, je ne fais pas comme il faut?", "Ah bon? Qu'est-ce qui ne va pas?"]) }, [('time', 1, 'choice')]),
                'tu_es_sur': ( {'e':'QT/confused', 'g':'QT/head_scratch', 's': random.choice(["Tu es sûr?", "Tu es sûr de toi?", "Je ne suis pas sûr"]) }, [('time', 1, 'choice')]),
                'plus_simple': ( {'e':'QT/talking', 'g':'', 's': "C'était quoi le plus simple pour toi " }, [('time', 1, 'choice')]),
                'plus_difficile': ( {'e':'QT/talking', 'g':'', 's': "C'était quoi le plus difficile pour toi " }, [('time', 1, 'choice')]),
                'bien_mal': ( {'e':'QT/talking', 'g':'', 's': "Qu'est-ce que je fais mal \sel=alt=p-50\ \Rspd=80\ et \sel=alt=p-50\ bien?" }, [('time', 1, 'choice')]),
                'pas_marche': ( {'e':'QT/sad', 'g':'QT/thanks', 's': "Pourquoi ça n'a pas marché?" }, [('time', 1, 'choice')]),
                'pourquoi': ( {'e':'', 'g':'', 's': random.choice(["Pourquoi?", "Pour quelle raison?"]) }, [('time', 1, 'choice')]),
                
                'ecrit': ( {'e':'', 'g':'QT/test', 's': "" }, [('time', 1, 'choice')]),
                'senslettre': ( {'e':'QT/talking', 'g':'', 's':"Est-ce que je fais mes lettres en tournant dans le bon sens?" }, [('time', 1, 'choice')]),
                'fermelettre': ( {'e':'QT/talking', 'g':'',  's': random.choice([ "Est-ce que mes lettres sont bien fermés?", "Est-ce que j'ai bien fermés mes lettres?", "Mes lettres sont fermés comme il faut?"]) }, [('time', 1, 'choice')]),
                'endroitlettre': ( {'e':'QT/talking', 'g':'', 's': random.choice([ "Est-ce que je débute mes lettres où il faut?", "Est-ce qu'il y a des lettres que je ne commence pas au bon endroit?"])}, [('time', 1, 'choice')]),
                'bien_comme_toi': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Mon mot \sel=alt=p-20\ \Rspd=80\ ressemble \Rspd=100\ à ce que tu as écrit?", "Est-ce que j'écris aussi bien que toi?", "J'écris bien comme toi?", "Mon mot est aussi beau que le tien?"]) }, [('time', 1, 'choice')]),

                'triche': ( {'e':'QT/one_eye_wink', 'g':'QT/angry', 's': "Mais tu triche," }, [('time', 1, 'choice')]),
                'facile': ( {'e':'QT/confused', 'g':'QT/challenge', 's':"Est-ce que c'est trop facile?" }, [('time', 1, 'choice')]),
                'pas_trop_vite': ( {'e':'QT/talking', 'g':'',  's': random.choice([ "attention, ne va pas trop vite", "child_name , ne va pas trop vite"]) }, [('time', 1, 'choice')]),
                'boum': ( {'e':'', 'g':'QT/happy', 's':"Boum!"}, [('time', 1, 'choice')]),

                'tu_relances': ( {'e':'', 'g':'QT/challenge', 's': random.choice([ "Tu peux relancer le jeu?", "Peux-tu relancer l'activité ?"])}, [('time', 1, 'choice')]),
                'je_bugue': ( {'e':'QT/confused', 'g':'QT/thanks', 's': random.choice(["Ça n'a pas bien marché", "J'ai eu un bug"]) }, [('time', 1, 'choice')]),
                'fatigue': ( {'e':'QT/yawn', 'g':'QT/yawn', 's': "Je suis désolé. #YAWN01# je suis fatigué." }, [('time', 1, 'choice')]),
                'je_rouille': ( {'e':'QT/with_a_cold', 'g':'QT/grandpa', 's':"aïe Aïe, je suis un peu rouillé aujourd'hui" }, [('time', 1, 'choice')]),
                'attends': ( {'e':'', 'g':'',  's': random.choice([ "tu patiente un petit moment?", "Attends un peu, je ne suis pas prêt", "Attends une seconde"]) }, [('time', 1, 'choice')]),
                'malade': ( {'e':'QT/with_a_cold_cleaning_nose', 'g':'QT/sneezing', 's':"je suis malade #SNEEZE01#"}, [('time', 1, 'choice')]),

                'et_alors': ( {'e':'QT/confused', 'g':'QT/so_what', 's':random.choice([ "Oui, et alors?", "Qu'est-ce que ça fait?", "Et alors?"]) }, [('time', 1, 'choice')]),
                'jai_progresse': ( {'e':'QT/happy', 'g':'QT/happy',  's': random.choice([ "J'ai beaucoup progressé", "J'ai fait beaucoup de progrès!", "Je me débrouille beaucoup mieux qu'avant."]) }, [('time', 1, 'choice')]),
                'cest_difficile': ( {'e':'QT/afraidshort', 'g':'QT/ohno', 's':random.choice(["Ce n'est pas si facile!", "Oui mais c'est dur", "C'est quand même difficile!"])}, [('time', 1, 'choice')]),
                'fais_mon_mieux': ( {'e':'QT/talking', 'g':'QT/angry', 's': random.choice(["mais tu sais je fais comme je peux, je fais beaucoup d'efforts", "Je fais de mon mieux", "Je fais de gros effort"])}, [('time', 1, 'choice')]),
                'tas_gagne': ( {'e':'', 'g':'QT/challenge', 's': "Bon.Tu as gagné. On s'y remet?" }, [('time', 1, 'choice')]),
                'ma_tablette': ( {'e':'QT/surprise', 'g':'QT/angry', 's': random.choice([ "Mais! Ma tablette!","Mais où est ma tablette?", "Je ne trouve plus ma tablette!"]) }, [('time', 1, 'choice')]),
                'pas_mal': ( {'e':'QT/showing_smile', 'g':'QT/bored', 's':random.choice([ "Je trouve que je me suis pas si mal débrouillé ", "Ce n'est pas si mal même si on peut faire mieux"])  }, [('time', 1, 'choice')]),
                'je_trouve_pas': ( {'e':'', 'g':'QT/no',  's': random.choice([ "Ah bon? Je ne trouve pas", "Je ne suis pas vraiment d'accord", "Je ne suis pas du même avis que toi"]) }, [('time', 1, 'choice')]),
                
                'respire': ( {'e':'QT/calmig_down_exercise_nose', 'g':'', 's': random.choice(["Respire un peu, et réessaye", "ce n'est pas grave, reprends ton souffle, et on repart"]) }, [('time', 1, 'choice')]),
                'ecris_mal': ( {'e':'QT/sad', 'g':'QT/thanks', 's': random.choice(["j'écris vraiment très mal", "Olala, mon écriture n'est pas terrible", "J'ai mal écrit"]) }, [('time', 1, 'choice')]),
                'cest_pas_grave': ( {'e':'', 'g':'QT/so_what', 's': random.choice(["~C'est pas grave, ça arrive", "~child_name , Ce n'est pas grave"]) }, [('time', 1, 'choice')]),
                'reessayons': ( {'e':'QT/showing_smile', 'g':'QT/show_tablet', 's': random.choice(["encore une fois?", "On essaye encore?"]) }, [('time', 1, 'choice')]),
                'fera_mieux': ( {'e':'QT/showing_smile', 'g':'QT/fera_mieux', 's': random.choice(["Nous n'avons pas réussi, mais nous ferons mieux la prochaine fois!", "On va faire mieux quand on reéessayera!"]) }, [('time', 1, 'choice')]),
                'courage': ( {'e':'QT/showing_smile', 'g':'QT/strong', 's': random.choice(["Courage, child_name , nous allons y arriver", "Allez, nous allons faire mieux", "Ne nous décourageons pas"]) }, [('time', 1, 'choice')]),
                'rate': ( {'e':'QT/confused', 'g':'QT/sad', 's': random.choice(["Mince, nous avons raté", "Oh non, nous n'avons pas été très fort", "Nous n'avons pas très bien réussi"]) }, [('time', 1, 'choice')]),
                'difficile': ( {'e':'QT/confused', 'g':'QT/challenge', 's': "Est-ce que c'est trop difficile?" }, [('time', 1, 'choice')]),
                'pas_content_moi': ( {'e':'QT/sad', 'g':'', 's':  random.choice(["Je ne suis pas content de moi", "Ce n'est pas beau ce que j'ai fait", "ça ne me plait pas ce que j'ai fait"])}, [('time', 1, 'choice')]),
                'tu_mecoute': ( {'e':'', 'g':'', 's': random.choice(["Tu ne m'écoutes \\sel=alt=p+100\\ \\Rspd=130\\ plus \\pau=120\\ \\sel=alt=p-50\\  \\Rspd=70\\ child_name ?", "Hey! child_name ?", "child_name ?", "child_name, tu m'écoutes?"]) }, [('time', 1, 'choice')]),
                'on_essaye': ( {'e':'', 'g':'QT/yes', 's': "Ok, alors on essaye plus tard" }, [('time', 1, 'choice')]),
                
                'bravo': ( {'e':'QT/happy', 'g':'QT/happy', 's': random.choice(["Felicitations !", "Bravo! ", "Bien joué  child_name", "Félicitations child_name"]) }, [('time', 0.1, 'choice')]),
                'je_suis_fort': ( {'e':'QT/one_eye_wink', 'g':'QT/hips', 's': random.choice(["je suis trop fort", "je suis très fier de moi!", "J'ai trop bien réussi!"]) }, [('time', 1, 'choice')]),
                'cest_bien': ( {'e':'QT/showing_smile', 'g':'QT/happy', 's': random.choice(["Super!", "C'est bien !", "C'est chouette!"]) }, [('time', 1, 'choice')]),
                'tu_es_fort': ( {'e':'QT/happy', 'g':'QT/handclap', 's': random.choice(["trop fort?", "Tu as trop bien réussi child_name ", "Tu as trop bien fait!"]) }, [('time', 1, 'choice')]),
                'nous_sommes_fort': ( {'e':'QT/happy', 'g':'QT/happy', 's': random.choice(["On est trop forts", "On est super forts!", "On a trop bien réussi!"]) }, [('time', 1, 'choice')]),
                'fier_de_toi': ( {'e':'QT/happy', 'g':'', 's':"Je suis fier de toi!"}, [('time', 1, 'choice')]),
                'applique': ( {'e':'QT/one_eye_wink', 'g':'QT/thanks', 's': random.choice(["tu travaille très bien","tu t'appliques très bien!", "tu est bien appliqué"]) }, [('time', 1, 'choice')]),
                'tu_perseveres': ( {'e':'QT/happy', 'g':'', 's':random.choice(["Tu n'as pas \pau=5\ \sel=alt=p+50\ abandonné! Bravo!", "Tu as tenu bon, C'est bien !","Tu \sel=alt=p+50\ persévères, Super!"])}, [('time', 1, 'choice')]),

                'aie': ( {'e':'QT/afraidshort', 'g':'QT/protect', 's': random.choice(["Aie!","Ouilleu", "aoutch, ça fait mal!"]) }, [('time', 1, 'choice')]),
                'ahahah': ( {'e':'QT/happy', 'g':'QT/laugh', 's':random.choice(["#LAUGH02# C'est rigolo","Ça me fais rire!", "C'est drôle!"])}, [('time', 1, 'choice')]),
                'muscle': ( {'e':'QT/one_eye_wink', 'g':'QT/strong', 's':"Oui mais moi, tu sais, j'ai des muscles en plastique"}, [('time', 1, 'choice')]),

                'merci': ( {'e':'QT/showing_smile', 'g':'QT/thanks', 's':  random.choice(["merci","Merci beaucoup", "Je te remercie", "merci, child_name"])}, [('time', 1, 'choice')]),
                'repete': ( {'e':'QT/talking', 'g':'', 's': random.choice([ "child_name , est-ce que tu peux répèter?","Peux-tu répéter?","Comment?", "Je n'ai pas entendu?"]) }, [('time', 1, 'choice')]),
                'oui': ( {'e':'', 'g':'QT/thanks', 's':"Oui"}, [('time', 6, 'choice')]),
                'non': ( {'e':'', 'g':'QT/no', 's': "Non" }, [('time', 7, 'choice')]),
                'sais_pas_toi': ( {'e':'', 'g':'QT/so_what', 's':random.choice(["Aucune idee ! ,Et toi?","Je ne sais pas. et toi?","Je sais pas trop. et toi?"])}, [('time', 1, 'choice')]),
                'et_toi': ( {'e':'', 'g':'', 's':"Et toi?"}, [('time', 3, 'choice')]),
                
                #comportement de scenario 
                'pression_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Clique sur le jeu qui s'appelle sous-marin", "Démarre le jeu sous-marin"]) }, [('time', 1, 'choice')]),
                'pression_expli': ( {'e':'QT/talkinglong', 'g':'QT/bored', 's': "Je navigue en sous-marin. Appuie ton stylo plus ou moins fort pour m'aider à piloter. Attention aux obstacles. Tu peux aller chercher les étoiles en bonus." }, [('time', 1, 'choice')]),
                'pression_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored_long', 's': "Rappelle-toi, c'est la pression sur le stylo qui pilote. Plus tu appuies fort, plus mon sous-marin descend. Si tu lâches le stylo, mon sous-marin s'arrête. Évite les pics et les rochers." }, [('time', 1, 'choice')]),
                'archeo_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Lance le jeu archéologue", "Clique sur le jeu qui s'appelle archéologue"]) }, [('time', 1, 'choice')]),
                'archeo_expli': ( {'e':'QT/talking', 'g':'QT/bored', 's': "Dans ce jeu, j'ai enterré un trésor dans le sol. Appuie le stylo sur la tablette. Déplace-le pour creuser dans le sol et trouver le trésor" }, [('time', 1, 'choice')]),
                'archeo_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored_long', 's': "Attention ! \pau=80\ Si tu appuie trop fort, tu risque de casser le trésor. Une fois que tu as trouvé tout, n'oublie pas de valider." }, [('time', 1, 'choice')]),
                
                'drapeau_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Lance le jeu drapeau", "Clique sur le jeu qui s'appelle drapeau"]) }, [('time', 1, 'choice')]),
                'drapeau_expli': ( {'e':'QT/talking', 'g':'QT/bored', 's':"Je dois livrer ce drapeau, \pau=30\ mais  je ne sais pas à quel pays \pau=50\ il appartient. Tu peux me recopier son nom pour que je puisse le livrer?" }, [('time', 1, 'choice')]),
                'drapeau_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored_long', 's':"Il faut bien suivre l'example, et écrire dessus pour qu'on puisse livrer. Sinon notre colis risque d'être refusé. " }, [('time', 1, 'choice')]),
                'alpha_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice([ "Lance le jeu alphabet.", "Clique sur le jeu qui s'appelle alphabet."])  }, [('time', 1, 'choice')]),
                'alpha_expli': ( {'e':'QT/talking', 'g':'QT/bored',  's': "Choisis un chiffre, ou une lettre, et montre-moi comment bien l'écrire." }, [('time', 1, 'choice')]),
                'alpha_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored', 's': "Attention ! \pau=80\ Il faut bien que tu me montre en repassant sur le modèle. Plus on suit le modèle, plus le trait est vert, et plus on gagne de points." }, [('time', 1, 'choice')]),
                
                'zoo_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Lance le jeu zoo", "Clique sur le jeu qui s'appelle zoo"]) }, [('time', 1, 'choice')]),
                'zoo_expli': ( {'e':'QT/talking', 'g':'QT/bored', 's': "Tu peux me montrer comment bien colorier un \sel=alt\ dessin sur la tablette? \pau=50\ On perd des points \sel=alt\ si on dépasse ou si on se trompe de couleurs." }, [('time', 1, 'choice')]),
                'zoo_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored_long', 's': "il faut bien tout colorier. Si tu n'as pas le temps de finir, tu peux sauvegarder en cliquant sur la croix. On terminera une prochaine fois."}, [('time', 1, 'choice')]),
                
                'chimi_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Lance le jeu chimiste", "Clique sur le jeu qui s'appelle chimiste"]) }, [('time', 1, 'choice')]),
                'chimi_expli': ( {'e':'QT/talking', 'g':'QT/bored', 's': "Copie le mot avec les bonnes couleurs avec moi. Quand tu lève le stylo, la couleur change." }, [('time', 1, 'choice')]),
                
                'tilt_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Lance le jeu hélicoptère", "Clique sur le jeu qui s'appelle hélicoptère"]) }, [('time', 1, 'choice')]),
                'tilt_expli': ( {'e':'QT/talking', 'g':'QT/bored', 's':"Je conduis un hélicoptère dans le jeu, et tu dois m'aider à piloter en plaçant ton stylo dans le cercle. Aide-moi à livrer les boîtes." }, [('time', 1, 'choice')]),
                'tilt_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored_long', 's': "\sel=alt=p-70\Rappelle-toi \pau=130\  Je vais dans la direction vers laquelle tu places ton stylo. On doit prendre \pau=50\ et livrer les boites. Une flèche rouge nous dit \pau=50\ où on doit aller. Si tu lâches le stylo, la boîte tombe." }, [('time', 1, 'choice')]),
                
                'cowritter_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's':  random.choice(["Démarre le jeu qui s'appelle Apprenti", "Clique sur Apprenti"]) }, [('time', 1, 'choice')]),
                'cowritter_expli_class': ( {'e':'QT/talkinglongrepeat', 'g':'QT/bored', 's': "Tu m'entraîne à écrire. Dans ce jeu, mon surnom est le robot de proust. Tu me montre comment bien corriger mes erreurs!" }, [('time', 1, 'choice')]),
                'cowritter_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored_long', 's': "\sel=alt=p-70\Rappelle-toi \pau=130\ Tu m'apprends à écrire. Mieux tu me montre, mieux j'apprends. À la fin on verra ma note." }, [('time', 1, 'choice')]),
                
                'jus_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Clique sur le jeu qui s'appelle jus", "jouons au jeu qui s'appelle jus"]) }, [('time', 1, 'choice')]),
                'jus_expli': ( {'e':'QT/talking', 'g':'QT/bored', 's': "Aide mon avatar à faire un jus. Laisse ta main gauche appuyée sur le bouton jaune pour allumer la lumière. Avec tes doigts, suit les étapes qui sont indiqué dans le cadre gris." }, [('time', 1, 'choice')]),
                'jus_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored', 's': "Attention ! \pau=80\ Il faut cliquer sur tout les fruits indiqués en même temps. Pour couper le fruit, il faut cliquer sur le fruit et le couteau en même temps, et glisser le couteau vers le fruit. Pour presser le jus, glisse tous les fruit en même temps vers le pressoir." }, [('time', 1, 'choice')]),

                'poursuite_lance': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's':  random.choice(["Clique sur le jeu Poursuite","Lances le jeu qui s'appelle Poursuite"]) }, [('time', 1, 'choice')]),
                'poursuite_expli': ( {'e':'QT/talkinglong', 'g':'QT/bored', 's':"J'ai faim. Suis le chemin avec ton stylo et ramasse tous les fruits pour moi."}, [('time', 1, 'choice')]),
                'poursuite_complet': ( {'e':'QT/talkinglong', 'g':'QT/bored_long',  's': "\sel=alt=p-50\Rappelle-toi \pau=100\ il faut bien rester sur le chemin bleu pour ne pas perdre des ballons. Tu peux prendre ton temps." }, [('time', 1, 'choice')]),
                
                'tu_viens': ( {'e':'QT/one_eye_wink', 'g':'QT/come', 's':random.choice([ "child_name c'est l'heure de mon cours, non?", "child_name tu viens m'aider à améliorer mon écriture?", "child_name je suis impatient d'écrire, tu viens?","child_name tu peux venir pour qu'on fasse mon cours?"])}, [('time', 1, 'choice')]),
                'ton_nom': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice([ "Clique sur ton nom pour commencer", "Avant qu'on commence, tu dois cliquer sur ton nom"])}, [('time', 1, 'choice')]),
                'ca_va': ( {'e':'QT/showing_smile', 'g':'', 's': random.choice(["Comment vas-tu?", "Ça va?", "Tu vas bien?" ]) }, [('time', 1, 'choice')]),
                'bonjour': ( {'e':'QT/showing_smile', 'g':'QT/hi', 's': random.choice(["Bonjour, child_name" , "Coucou? child_name" ]) }, [('time', 1, 'choice')]),
                
                'je_mappelle_qt': ( {'e':'QT/talkinglongadapted', 'g':'QT/hi', 's':"Bonjour, je m'appelle kyuti. Et toi, comment tu t'appelles?" }, [('time', 1, 'choice')]),
                'tu_veux_maider': ( {'e':'QT/talkinglongrepeat', 'g':'QT/begin',  's':"Je suis content de te rencontrer. J'ai besoin de ton aide pour mieux écrire, car je ne suis pas très fort. Est-ce que tu es d'accord pour m'aider? On s'améliorera ensemble!" }, [('time', 1, 'choice')]),
                'tu_maides_encore': ( {'e':'QT/talkinglong', 'g':'QT/rappel', 's':"Comme je ne sais pas très bien écrire, tu avais décidé de m'aider pour qu'on devienne meilleurs ensemble. On continue?"}, [('time', 1, 'choice')]),
                'adieu': ( {'e':'QT/dernieradieu', 'g':'QT/adieu', 's':"On a terminé notre dernière séance. Merci beaucoup. J'ai fais beaucoup de progrès, et je me suis bien amusé. J'espère que toi aussi. " }, [('time', 1, 'choice')]),
                'adieu2': ( {'e':'QT/showing_smile', 'g':'QT/hi',  's': "Au revoir child_name ! Bon courage pour la suite!" }, [('time', 1, 'choice')]),
                
                'pause': ( {'e':'QT/talking', 'g':'QT/bored', 's':random.choice(["Après un niveau, on s'arrête \pau=20\ et on \Rspd=70\ réfléchit \Rspd=80\ ensemble.", "On fait un niveau, et on s'arrête pour que tu m'expliques."])}, [('time', 1, 'choice')]),
                'change_jeu': ( {'e':'QT/talking', 'g':'QT/show_tablet', 's': random.choice(["Tu veux qu'on fasse un autre \sel=alt=p-30\jeu?", "Tu as envie de changer de jeu?", "On passe à la prochaine activité?"])}, [('time', 1, 'choice')]),
                'choisis_jeu': ( {'e':'QT/talking', 'g':'QT/show_tablet',  's': random.choice([ "Je te laisse choisir la prochaine activité sur la tablette.", "À toi de choisir dans les jeux sur la tablette.", "Parmi les jeux qu'on a sur notre \Rspd=100\ tablette,\Rspd=80\ lequel tu veux faire ensuite?"]) }, [('time', 1, 'choice')]),
                
                'dernier_jeu': ( {'e':'QT/showing_smile', 'g':'', 's':random.choice(["Ce sera notre dernière activité.", "Plus qu'une partie et on arrête.", "C'est le dernier jeu."])}, [('time', 1, 'choice')]),
                'cetait_bien': ( {'e':'QT/happy', 'g':'QT/handclap', 's': random.choice(["C'était une super séance, child_name", "nous avons bien travaillé aujourd'hui"])}, [('time', 1, 'choice')]),
                'tu_maide': ( {'e':'QT/happy', 'g':'QT/thanks', 's':random.choice([ "child_name , Merci pour ton aidé", "Merci child_name tu m'aides beaucoup!", "tu m'as beaucoup aidé "]) }, [('time', 1, 'choice')]),
                'mes_progres': ( {'e':'QT/happy', 'g':'QT/hips',  's': random.choice([ "Tu as vu comment j'écrivais et comment j'ai progressé?", "Tu as vu comme je me suis amélioré en écriture?", "Tu as vu mes progrès?"]) }, [('time', 1, 'choice')]),
                'bisou': ( {'e':'QT/kiss2', 'g':'QT/kiss', 's':"Je peux t'envoyer un bisou?"}, [('time', 8, 'choice')]),
                'bcp_travaille': ( {'e':'', 'g':'QT/strong', 's': random.choice(["Nous avons beaucoup travaillé aujourd'hui,", "Nous avons travaillé dur", "Nous avons beaucoup travaillé ensemble"])}, [('time', 1, 'choice')]),
                'il_est_lheure': ( {'e':'', 'g':'QT/bored',  's': random.choice([ "Il est l'heure, on doit s'arrêter", "C'est l'heure à laquelle on doit finir"]) }, [('time', 1, 'choice')]),
                'arrete': ( {'e':'', 'g':'QT/bored', 's':random.choice(["child_name , On s'arrête pour aujourd'hui", "On arrête là cette séance"])}, [('time', 1, 'choice')]),
                'au_revoir': ( {'e':'QT/showing_smile', 'g':'QT/hi', 's': random.choice(["À bientôt!", "À la prochaine!", "Au revoir,child_name !"])}, [('time', 1, 'choice')]),  
                
                # maison 
                       # premiere utimisation 
                '_salut': ( {'e':'QT/happy', 'g':'QT/hi', 's': random.choice(["Salut ! Je m’appelle kyouti, enchanté de te rencontrer","Salut ! Je m’appelle kyouti, ravi de faire ta connaissance."])}, [('time', 1, 'choice')]),  
                '_comment_t_appeler': ( {'e':'', 'g':'QT/imitation/hands-on-hip', 's': random.choice(["~Comment tu t'appel ?","~Quel est ton prénom ? "])}, [('time', 1, 'choice')]),  
                '_nom_parents' : ( {'e':'', 'g':'', 's': "~Comment s’appellent tes parents ?"}, [('time', 1, 'choice')]),  
                '_aujourdhui': ( {'e':'', 'g':'QT/show_tablet', 's': "~ On va commencer par faire connaissance et puis on jouera ensemble régulièrement ! Tu pourras me dire ce que tu penses et ce que tu ressens, avec des mots, des dessins ou par le jeu. D’accord ? \\pau=1000\\ C’est parti ! "}, [('time', 11, 'choice')]),  
                    # debut chaque utilisation 
                'journee': ( {'e':'QT/happy_blinking', 'g':'', 's': "Salut?\\pau=200\\ comment allez-vous  \\pau=800\\ Comment s’est passée votre journée  "}, [('time', 1, 'choice')]),
                'on_est_prets': ( {'e':'QT/showing_smile', 'g':'QT/challenge', 's': "Nous allons jouer ensemble. Vous êtes prêts ?"}, [('time', 1, 'choice')]),
                'tu_es_pret': ( {'e':'QT/showing_smile', 'g':'QT/challenge', 's': "child_name, tu es prêt ?"}, [('time', 1, 'choice')]),
                'pourquoi_non': ( {'e':'QT/talking', 'g':'QT/angry', 's': "Pourquoi ? Tu n’aimes pas jouer ? "}, [('time', 1, 'choice')]),
                'rassure_toi': ( {'e':'QT/happy_blinking', 'g':'QT/come', 's': random.choice(["Rassure-toi, on va bien s’amuser ! ", "Tu vas voir, ça va être génial ! "])}, [('time', 1, 'choice')]),
                'previens_moi': ( {'e':'', 'g':'QT/show_QT', 's': "~Tu me dis quand tu seras prêt, je t’attends ! "}, [('time', 1, 'choice')]),
                'choix_activite': ( {'e':'QT/talking', 'g':'QT/swipe_right', 's': random.choice([" À quoi tu as envie qu'on joue ensemble aujourd’hui? Tu peux choisir un jeux","À quoi on va jouer ?"])}, [('time', 5, 'choix_jeu')]),
                'choix_jeu': ( {'e':'QT/talking', 'g':'QT/strong', 's': "Jeu de mimes ?, construire une cabane ? ou fabriquer des choses avec nos mains "}, [('time', 1, 'choice')]),    
                'on_commence': ( {'e':'QT/surprise', 'g':'QT/one-arm-up', 's': random.choice([" Très bien, on commence !", "Super, c’est parti ! "])}, [('time', 1, 'choice')]),
                    # fin des activités
                'terminee': ( {'e':'', 'g':'QT/bye', 's': random.choice(["~On a terminé pour aujourd’hui. J’espère que tu t’es bien amusé. J’ai hâte de jouer à nouveau avec toi ! À bientôt ! ",
                                                                   "~C’est fini pour aujourd’hui. Je suis très content d’avoir joué avec toi. J’espère te revoir très vite ! ",
                                                                   "~On a bien joué aujourd’hui ! A une prochaine ! "])}, [('time', 1, 'choice')]),    
                'qt_fatigue':( {'e':'QT/yawn', 'g':'QT/yawn', 's': "\\pau=1000\\  #YAWN01#"}, [('time', 1, 'choice')]),
                # Activités cognitives 
                    # 1-Jeu des mimes ==>> à completer 
                'regles_mime': ( {'e':'', 'g':'QT/bored', 's': "~Amusons-nous avec le jeu de mime ! Je vais te décrire un animal et je voudrais que tu le mimes; si tu veux, tu peux nous montrer comment il se comporte, comment il bouge, nous faire entendre ses cris. Nous serons tes spectateurs ! "}, [('time', 8, 'choice')]),    
                    # liste des animaux à mimer ==> à completer et à revoir  
                'lion': ( {'e':'QT/talkinglongadapted', 'g':'QT/strong', 's': "il a quatre pattes,\\pau=300\\  il a une krinière,\\pau=300\\il est féroce, il est fort\\pau=300\\   il est le roi de la savane,\\pau=600\\  "}, [('time', 2, 'lion1')]),   
                'lion1': ( {'e':'QT/talkinglongadapted', 'g':'QT/stretch', 's': "\\pau=900\\Entre en piste le Lion !  À toi de jouer !  "}, [('time', 1, 'choice')]),   
                
                'girafe': ( {'e':'', 'g':'QT/bored', 's': "~elle a quatre pattes,\\pau=300\\ elle vit dans la savane\\pau=300\\, elle a un cou trés long\\pau=300\\   elle peut atteindre des délicieuses feuilles, les plus hautes"}, [('time', 2, 'girafe1')]), 
                'girafe1': ( {'e':'', 'g':'QT/stretch', 's': "~et voicii, la girafe  ! À toi de jouer !  "}, [('time', 1, 'choice')]), 

                'gazelle': ( {'e':'', 'g':'QT/bored', 's': "~elle a quatre pattes,\\pau=300\\ elle cours tres vite\\pau=300\\, personne ne peut la ratrapper\\pau=300\\  \\pau=600\\  "}, [('time', 2, 'gazelle1')]),   
                'gazelle1': ( {'e':'', 'g':'QT/stretch', 's': "~et voicii en piste , la gazelle  !   À toi de jouer ! "}, [('time', 1, 'choice')]),   

                'zebre': ( {'e':'', 'g':'QT/bored', 's': "~Il vit dans la savane \\pau=300\\ Il a quatre pattes \\pau=300\\ Il a des rayures noires et blanches \\pau=300\\ Quelle robe élégante !"}, [('time', 2, 'zebre1')]),  
                'zebre1': ( {'e':'', 'g':'QT/stretch', 's': "~Entre en piste le zèbre ! à toi de jouer !"}, [('time', 1, 'choice')]),  

                'singe': ( {'e':'', 'g':'QT/monkey', 's': "~Il peut grimper dans les plus hauts arbres \\pau=300\\ Il peut aussi sauter d’une branche à l’autre \\pau=300\\il est drôle, mais il peut être espiègle, attention !\\pau=300\\ Parmi les animaux, c'est lui qui nous ressemble le plus !"}, [('time', 11, 'singe1')]),  
                'singe1': ( {'e':'', 'g':'QT/stretch', 's': "~Entre en piste le singe ! à toi de jouer !"}, [('time', 1, 'choice')]),  

                'elephon': ( {'e':'', 'g':'QT/bored', 's': "~Il a quatre pattes,\\pau=300\\ il est grand et puissant!\\pau=300\\Il a une trompe,\\pau=300\\ il est le plus sage de tous!"}, [('time', 2, 'elephon1')]),
                'elephon1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\ Entre en piste l’éléphant! à toi de jouer !"}, [('time', 1, 'choice')]),

                'guepard': ( {'e':'', 'g':'QT/bored', 's': "~Il vit dans la savane,\\pau=300\\Il a quatre pattes,\\pau=300\\ il a une cape tachetée\\pau=300\\ Il court si vite que personne ne peut le battre!"}, [('time', 2, 'guepard1')]),
                'guepard1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\Entre en piste le guépard! à toi de jouer !"}, [('time', 1, 'choice')]),

                'tigre': ( {'e':'', 'g':'QT/strong', 's': "~Il vit dans la savane,\\pau=300\\ il a quatre pattes\\pau=300\\, il est féroce!\\pau=300\\il a une cape rayée !"}, [('time', 2, 'tigre1')]),
                'tigre1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\ Entre en piste la tigre! à toi de jouer ! "}, [('time', 1, 'choice')]),

                'tortue': ( {'e':'', 'g':'QT/bored', 's': "~Elle aime la salade\\pau=300\\ Elle prend toujours son temps, elle est très lente!\\pau=300\\ Elle porte sa maison sur son dos  ! "}, [('time', 2, 'tortue1')]),
                'tortue1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\Entre en piste la tortue ! à toi de jouer ! "}, [('time', 1, 'choice')]),

                'panthere': ( {'e':'', 'g':'QT/bored', 's': "~Elle ressemble à un gros chat, et miaule plus fort que lui ! \\pau=300\\Quel beau manteau noir "}, [('time', 2, 'panthere1')]),
                'panthere1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\ Entre en piste la panthère ! à toi de jouer !"}, [('time', 1, 'choice')]),

                'serpent': ( {'e':'', 'g':'QT/bored', 's': "~Il se deplace en rampant,\\pau=300\\ Il ne fait pas de bruit,\\pau=300\\ attention! il peut se tordre! Il fait peur quand il siffle ! "}, [('time', 2, 'serpent1')]),
                'serpent1': ( {'e':'QT/talking', 'g':'QT/stretch', 's': "\\pau=600\\ Entre en piste le serpent ! à toi de jouer !"}, [('time', 1, 'choice')]),

                'chat': ( {'e':'', 'g':'QT/bored', 's': "~Il aime rester à la maison mais aussi sortir et explorer,\\pau=300\\Il a des moustache\\pau=300\\ Il aime les câlins et ronronne ,\\pau=300\\ Il miaule pour demander de l’attention "}, [('time', 2, 'chat1')]),
                'chat1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\ Entre en piste le chat ! à toi de jouer !"}, [('time', 1, 'choice')]),

                'chien': ( {'e':'', 'g':'QT/bored', 's': "~C’est le meilleur ami de l’homme ! \\pau=300\\Il aboie pour garder les maisons \\pau=300\\  Il aime jouer et se balader ! "}, [('time', 1, 'chien1')]),
                'chien1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\ Entre en piste le chien ! à toi de jouer ! "}, [('time', 1, 'choice')]),

                'papillon': ( {'e':'', 'g':'QT/bored', 's': "~Avant il n’était pas comme maintenant, c’était une chenille ,\\pau=300\\ regardez combien il a de couleurs sur ses ailes !\\pau=300\\ « Il aime les fleurs et le printemps "}, [('time', 2, 'papillon1')]),
                'papillon1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\ Entre en piste le papillon ! à toi de jouer !"}, [('time', 1, 'choice')]),

                'chameau': ( {'e':'', 'g':'QT/bored', 's': "~Il a quatre pattes,\\pau=300\\ Il vit dans le désert. \\pau=300\\ Il a deux bosses pour garder l’eau "}, [('time', 2, 'chameau1')]),
                'chameau1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\ Entre en piste le chameau ! à toi de jouer !"}, [('time', 1, 'choice')]),

                'grenouille': ( {'e':'', 'g':'QT/bored', 's': "~Va-t-elle se transformer en prince? \\pau=300\\ Elle se protège de la pluie en sautant dans l’eau. \\pau=300\\ Elle est verte, elle attrape les insectes avec sa langue"}, [('time', 2, 'grenouille1')]),
                'grenouille1': ( {'e':'', 'g':'QT/stretch', 's': "~\\pau=600\\Entre en piste la grenouille ! à toi de jouer !"}, [('time', 1, 'choice')]),

                    # feliciter et/ou encourager , commenter ...
                'quelle_peur': ( {'e':'QT/afraidshort', 'g':'QT/fera_mieux', 's': " Oh! quelle peur!  "}, [('time', 1, 'choice')]),
                'feroce': ( {'e':'QT/afraid', 'g':'QT/yes', 's': " Il a l’air féroce!  "}, [('time', 1, 'choice')]),
                'drole': ( {'e':'QT/one_eye_wink', 'g':'QT/laugh', 's': "C’est drôle !   "}, [('time', 1, 'choice')]),
                'mignon': ( {'e':'QT/shy', 'g':'QT/kiss', 's': " Qu’il est mignon !"}, [('time', 1, 'choice')]),

                '_bravo': ( {'e':'QT/happy', 'g':'QT/happy', 's':random.choice([ " Bravo !  ", "Très bien !", "Génial !"])}, [('time', 1, 'choice')]),
                'tres_fort': ( {'e':'QT/happy', 'g':'QT/handclap', 's': " « Tu es très fort child_name !"}, [('time', 1, 'choice')]),
                'imites_bien': ( {'e':'QT/surprise', 'g':'QT/handclap', 's': random.choice(["Tu l’imites trés bien !", "Quelle bonne imitation !", "On devine tout de suite !"])}, [('time', 1, 'choice')]),
                
                'reflechis': ( {'e':'', 'g':'QT/neutral', 's': "~Prends ton temps, réfléchis  "}, [('time', 1, 'choice')]),
                'tes_parents': ( {'e':'', 'g':'QT/neutral', 's': "~Demande un conseil à tes parents ! "}, [('time', 1, 'choice')]),
                'essaye_encore': ( {'e':'', 'g':'QT/challenge', 's': "~Essaye encore une fois, tu peux réussir  "}, [('time', 1, 'choice')]),
                'un_autre': ( {'e':'QT/confused', 'g':'QT/confused', 's': "  Celui là est difficile c’est vrai, essaye un autre  "}, [('time', 1, 'choice')]),
                'on_reprend': ( {'e':'', 'g':'QT/challenge', 's': random.choice(["~On reprend ?", "~On peut reprendre ?"])}, [('time', 1, 'choice')]),
     
                    
                    # 2- travail manuel : patte a modeler
                'manuel_regles':( {'e':'', 'g':'QT/bored', 's': "~Maintenant je te propose des objets \\pau=300\\et avec l’aide de tes parents, tu vas essayer de les créer en pâte à modeler !"}, [('time', 1, 'choice')]),    
                        # montrer soleil, lune etoile 
                '_ciel':( {'e':'QT/happy', 'g':'QT/so', 's': "Aujourd’hui nous réalisons le ciel. "}, [('time', 1, '_ciel1')]), 
                '_ciel1':( {'e':'', 'g':'QT/show_tablet', 's': "~On va créer un soleil, une lune, et une étoile. allez , A toi l’artiste ! "}, [('time', 1, 'choice')]), 
                        # montrer un plat une tasse,une fourchette,une cuillère,un couteau,un verre   
                'table':( {'e':'QT/happy', 'g':'QT/so', 's': "Aujourd’hui on met la table. "}, [('time', 1, 'table1')]), 
                'table1':( {'e':'', 'g':'QT/show_tablet', 's': "~On va créer un plat,\\pau=300\\  une tasse,\\pau=300\\  une cuillere \\pau=300\\ et un verre. A toi l’artiste ! "}, [('time', 1, 'choice')]), 
                        # montrer un pelouche, un ballon ...
                'salon':( {'e':'QT/happy', 'g':'QT/challenge', 's': "Aujourd’hui nous embellissons ta chambre."}, [('time', 1, 'salon1')]), 
                'salon1':( {'e':'', 'g':'QT/show_tablet', 's': "~on va créer un pelouche, un ballon, un petit train. A toi l’artiste !"}, [('time', 1, 'choice')]), 
                        # montrer une chat, chien, lapin ...        
                'les_animaux':( {'e':'', 'g':'QT/challenge', 's': "~Aujourd’hui nous créons nos amis à quatre pattes ."}, [('time', 1, 'les_animaux1')]), 
                'les_animaux1':( {'e':'', 'g':'QT/show_tablet', 's': "~On va creer un chat, un hamster et un lapin . A toi l’artiste !"}, [('time', 1, 'choice')]), 
                        # montrer un petit bateau, un chateau de sable et un poisson ...        
                'la_mer':( {'e':'QT/happy', 'g':'QT/challenge', 's': "Aujourd’hui nous allons à la mer ."}, [('time', 1, 'la_mer1')]), 
                'la_mer1':( {'e':'', 'g':'QT/show_tablet', 's': "~On va créer un petit bateau, un chateau de sable et un poisson. A toi l’artiste ! "}, [('time', 1, 'choice')]), 

                        # 2- travail manuel : faire un puzzle
                'puzzle':( {'e':'QT/happy', 'g':'QT/show_tablet', 's': "~Maintenant on fait un peuzeul ensemble !\\pau=300\\ Tu vas assembler les différentes pièces pour reconstituer le dessin "}, [('time', 1, 'choice')]),     
                    # 2- travail manuel : construire une cabane
                'cabane_regles':( {'e':'', 'g':'QT/show_tablet', 's': "~Maintenant nous allons essayer de construire une cabane. Avec l’aide de tes parents, utilise ce que tu as autour de toi pour créer un petit espace. Par exemple des legos, des chaises, des coussins, des draps, des matelas, des cartons… "}, [('time', 14, 'choice')]),     
                'le_sol':( {'e':'', 'g':'QT/so', 's': "~On commence par quoi ? On fait le sol! ?"}, [('time', 1, 'choice')]),     
                'les_murs':( {'e':'', 'g':'', 's': "~Maintenant nous pouvons construire les murs  "}, [('time', 1, 'choice')]),     
                'le_toit':( {'e':'', 'g':'', 's': "~Il est temps de construire le toit "}, [('time', 1, 'choice')]),     
                'la_porte':( {'e':'', 'g':'', 's': "~Et maintenant nous fermons la cabane avec une porte "}, [('time', 2, 'choice')]),     
                    # feliciter et/ou encourager , commenter ...
                'genial':( {'e':'QT/happy', 'g':'QT/happy', 's': random.choice(["Bravo !", "Très bien !", "Génial !"])}, [('time', 1, 'choice')]),     
                'c_joli':( {'e':'QT/happy', 'g':'QT/kiss', 's': "C’est joli ! "}, [('time', 1, 'choice')]),     
                'reussi':( {'e':'QT/happy', 'g':'QT/handclap', 's': "C’est vraiment réussi ! "}, [('time', 1, 'choice')]),
                'sors_bien':( {'e':'', 'g':'QT/yes', 's': random.choice(["~Tu t’en sors bien ! ", "~C’est ingénieux ! "])}, [('time', 1, 'choice')]),     
                'rapide':( {'e':'QT/surprise', 'g':'', 's': "Tu es rapide !"}, [('time', 1, 'choice')]),     
                     
                'fais_mieux':( {'e':'', 'g':'', 's': "~Fais de ton mieux  "}, [('time', 1, 'choice')]),     
                'recommencer':( {'e':'', 'g':'QT/challenge', 's': random.choice(["~Essayes encore une fois, tu peux réussir ", "~Recommence, prends ton temps "])}, [('time', 1, 'choice')]),     
                'essaye_un_autre':( {'e':'', 'g':'QT/confused', 's': "~Celui là est difficile, c’est vrai, essaye un autre !"}, [('time', 6, 'choice')]),     
                'patience':( {'e':'', 'g':'', 's': "~Sois patient, tu vas y arriver "}, [('time', 1, 'choice')]),     
                'puzzle_debut':( {'e':'', 'g':'QT/so', 's': "~Tu peux commencer par trier les morceaux par couleur, ou, selon les motifs par exemple "}, [('time', 1, 'choice')]),     
                'bon_debut':( {'e':'QT/happy', 'g':'', 's': "C’est un bon début, continue !"}, [('time', 1, 'choice')]),     
                'observe_bien':( {'e':'', 'g':'', 's': "~Observe bien l’image et les morceaux"}, [('time', 1, 'choice')]),     

                    # 2- travail manuel : 1,2,3 soleil
                'soleil_regles':( {'e':'', 'g':'QT/show_tablet', 's': "~On va jouer à un deux trois soleil ! Essaie de t’approcher de moi lorsque je ferme les yeux. Quand j’ouvrirai les yeux et que je dirai 'soleil', tu devras t’arrêter. Il faut être concentré et rapide ! Si tu réussis à avancer pendant que j’ai les yeux fermés, tu auras gagné.  Prêt à me rejoindre ?"}, [('time', 20, 'choice')]),
                'lancer_soleil':( {'e':'QT/calming_down', 'g':'QT/peekaboo', 's': "\\pau=1000\\ Un\\pau=800\\, deux \\pau=800\\, trois \\pau=2000\\ Soleil!"}, [('time', 1, 'choice')]),
                'j_ai_gagne':( {'e':'QT/happy', 'g':'QT/happy', 's': "\\pau=300\\J'ai gagné !"}, [('time', 1, 'choice')]),         

                 # Activités sociales
                    #S ous-catégorie : Raconter la journée/semaine aux parents 
                'comment_ca_va':( {'e':'', 'g':'', 's': "~Comment ça va? "}, [('time', 1, 'choice')]),
                'et_ta_journee':( {'e':'', 'g':'', 's': "~Comment s’est passée ta journée ? "}, [('time', 1, 'choice')]),
                'raconter':( {'e':'', 'g':'QT/show_left', 's': "~Tu veux me raconter ce que tu as fait ? Je suis curieux ! "}, [('time', 1, 'choice')]),
                'de_belles_choses':( {'e':'QT/showing_smile', 'g':'QT/show_right', 's': "Est ce qu'il s'est passé quelque chose de rigolo ? "}, [('time', 1, 'choice')]),
                'inquietude':( {'e':'QT/with_a_cold', 'g':'', 's': "Il s’est passé quelque chose qui t’a embêté ? "}, [('time', 1, 'choice')]),
                'tes_amis':( {'e':'', 'g':'', 's': random.choice(["~Tu as joué avec tes copains ? ", "~Tu t’es amusé avec tes copains ? "])}, [('time', 1, 'choice')]),
                
                'ecole_ennuie':( {'e':'', 'g':'QT/sad', 's': "~Tu ne t’es pas \\pau=50\\ ennuyé à l’école ?"}, [('time', 1, 'choice')]),
                '_pourquoi':( {'e':'', 'g':'', 's': "~Pourquoi ? "}, [('time', 1, 'choice')]),
                'et_apres':( {'e':'', 'g':'', 's': "~Et après ? "}, [('time', 1, 'choice')]),
                'ah_bon':( {'e':'', 'g':'', 's': "~Ah bon !"}, [('time', 1, 'choice')]),


                # Activités émotionnelles
                    #  Sous-catégorie : jeu symbolique/jeu avec médiateur
                'envie_de_jouer':( {'e':'', 'g':'QT/show_tablet', 's': "~As-tu envie de t’amuser avec ces jeux ? Tu peux dessiner, jouer avec des poupées, nous raconter des histoires… Tu peux choisir ce que tu veux! "}, [('time', 12, 'choice')]),
                'c_dur':( {'e':'', 'g':'', 's': "~Ça doit être dur pour lui"}, [('time', 1, 'choice')]),
                'je_comprend':( {'e':'', 'g':'QT/yes', 's': "~Je comprends !"}, [('time', 1, 'choice')]),
                'c_drole':( {'e':'QT/puffing_the_chredo_eeks', 'g':'QT/laugh', 's': "C’est drôle!"}, [('time', 1, 'choice')]),
                'pourquoi_faire':( {'e':'', 'g':'', 's': "~Pourquoi il fait ça?"}, [('time', 1, 'choice')]),
                'se_sentir':( {'e':'', 'g':'', 's': "~Comment il se sent ?"}, [('time', 1, 'choice')]),
                'm_expliquer':( {'e':'', 'g':'', 's': "~Tu peux m’expliquer? Je t'écoute!"}, [('time', 1, 'choice')]),
                'comment_passe':( {'e':'', 'g':'', 's': "~Comment ça s’est passé?"}, [('time', 1, 'choice')]),

                    #  Psychodrame    
                'surprise':( {'e':'QT/surprise', 'g':'QT/curious', 's': random.choice(["C’est incroyable!", "Incroyable!"])}, [('time', 1, 'choice')]),
                'peur':( {'e':'QT/afraid', 'g':'fera_mieux', 's': random.choice(["Oh! Quelle peur!", "Oh! J'ai eu peur!"])}, [('time', 1, 'choice')]),
                'degout':( {'e':'QT/disgusted', 'g':'QT/yawn', 's': "\\pau=500\\Ooh! non! "}, [('time', 1, 'choice')]),
                'en_colere':( {'e':'QT/confused', 'g':'QT/head_scratch', 's': "Je suis en colère!"}, [('time', 1, 'choice')]),
                'bon_heur':( {'e':'QT/happy_blinking', 'g':'QT/happy', 's': "\\pau=500\\ Youpi !"}, [('time', 1, 'choice')]),
                '_tristesse':( {'e':'QT/sad', 'g':'QT/thanks', 's': "\\pau=500\\Oh, quelle tristesse!"}, [('time', 1, 'choice')]),
                '_fatigue':( {'e':'QT/yawn', 'g':'QT/thanks', 's': "#YAWN01# Je suis fatigué"}, [('time', 1, 'choice')]),
                'confusion':( {'e':'QT/confused', 'g':'QT/touch-head-back', 's': random.choice(["Je ne comprends pas!", "J'ai du mal à comprendre!"])}, [('time', 1, 'choice')]),
    

                # Posture shortcuts (theatre.js buttons)
                'standup': ( {'g': 'Stand', 'spd': 0.8}, [('time', 0.01, 'choice')]),
                'LSD':     ( {'g': 'Sit',   'spd': 0.8}, [('time', 0.01, 'choice')]),
                'LSU':     ( {'g': 'Stand', 'spd': 0.8}, [('time', 0.01, 'choice')]),

                'end': ((), [('time', 0.1, 'end')]) }
