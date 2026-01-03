"""
GCSE History - Paper 2: All B Options (British Depth Studies)
=============================================================

Uploads all 4 British depth study options (B1, B2, B3, B4)

Structure for each:
- Level 2: No subsections (just the option itself)
- Level 3: Key topics (3 per option)
- Level 4: Numbered sections (1, 2, 3, 4)
- Level 5: Bullet points

Must run upload-history-structure.py FIRST!
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT_CODE = 'GCSE-History'

# All B options content
NEW_TOPICS = [
    # ========== OPTION B1: ANGLO-SAXON AND NORMAN ENGLAND ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptB1_KT1', 'title': 'Key topic 1: Anglo-Saxon England and the Norman Conquest, 1060–66', 'level': 3, 'parent': 'Paper2_OptB1'},
    {'code': 'Paper2_OptB1_KT2', 'title': 'Key topic 2: William I in power: securing the kingdom, 1066–87', 'level': 3, 'parent': 'Paper2_OptB1'},
    {'code': 'Paper2_OptB1_KT3', 'title': 'Key topic 3: Norman England, 1066–88', 'level': 3, 'parent': 'Paper2_OptB1'},
    
    # KT1 Topics
    {'code': 'Paper2_OptB1_KT1_T1', 'title': '1. Anglo-Saxon government, economy and society', 'level': 4, 'parent': 'Paper2_OptB1_KT1'},
    {'code': 'Paper2_OptB1_KT1_T2', 'title': '2. The last years of Edward the Confessor and the succession crisis', 'level': 4, 'parent': 'Paper2_OptB1_KT1'},
    {'code': 'Paper2_OptB1_KT1_T3', 'title': '3. The rival claimants for the throne', 'level': 4, 'parent': 'Paper2_OptB1_KT1'},
    {'code': 'Paper2_OptB1_KT1_T4', 'title': '4. The Norman invasion', 'level': 4, 'parent': 'Paper2_OptB1_KT1'},
    
    # KT1 T1 Bullets
    {'code': 'Paper2_OptB1_KT1_T1_B1', 'title': 'Monarchy and government. The power of the English monarchy. Earldoms, local government and the legal system', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T1'},
    {'code': 'Paper2_OptB1_KT1_T1_B2', 'title': 'The economy and social system. Towns and villages. The influence of the Church', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T1'},
    
    # KT1 T2 Bullets
    {'code': 'Paper2_OptB1_KT1_T2_B1', 'title': 'The significance and power of the house of Godwin. Harold Godwinson\'s succession as Earl of Wessex', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T2'},
    {'code': 'Paper2_OptB1_KT1_T2_B2', 'title': 'Harold Godwinson\'s embassy to Normandy. The reasons for the rising against Tostig and his exile. The death of Edward the Confessor', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T2'},
    
    # KT1 T3 Bullets
    {'code': 'Paper2_OptB1_KT1_T3_B1', 'title': 'The motives and claims of William of Normandy, Harald Hardrada and Edgar the Aethling', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T3'},
    {'code': 'Paper2_OptB1_KT1_T3_B2', 'title': 'Reasons for, and significance of, the outcome of the battles of Gate Fulford and Stamford Bridge', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T3'},
    {'code': 'Paper2_OptB1_KT1_T3_B3', 'title': 'The Witan and the coronation and reign of Harold Godwinson', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T3'},
    
    # KT1 T4 Bullets
    {'code': 'Paper2_OptB1_KT1_T4_B1', 'title': 'The Battle of Hastings', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T4'},
    {'code': 'Paper2_OptB1_KT1_T4_B2', 'title': 'Reasons for William\'s victory, including the leadership skills of Harold and William, Norman and English troops and tactics', 'level': 5, 'parent': 'Paper2_OptB1_KT1_T4'},
    
    # KT2 Topics
    {'code': 'Paper2_OptB1_KT2_T1', 'title': '1. Establishing control', 'level': 4, 'parent': 'Paper2_OptB1_KT2'},
    {'code': 'Paper2_OptB1_KT2_T2', 'title': '2. Anglo-Saxon resistance, 1068–71', 'level': 4, 'parent': 'Paper2_OptB1_KT2'},
    {'code': 'Paper2_OptB1_KT2_T3', 'title': '3. The legacy of resistance to 1087', 'level': 4, 'parent': 'Paper2_OptB1_KT2'},
    {'code': 'Paper2_OptB1_KT2_T4', 'title': '4. Revolt of the Earls, 1075', 'level': 4, 'parent': 'Paper2_OptB1_KT2'},
    
    # KT2 T1 Bullets
    {'code': 'Paper2_OptB1_KT2_T1_B1', 'title': 'The submission of the earls, 1066', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T1'},
    {'code': 'Paper2_OptB1_KT2_T1_B2', 'title': 'Reasons for the building of castles; their key features and importance', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T1'},
    {'code': 'Paper2_OptB1_KT2_T1_B3', 'title': 'Rewarding followers and establishing control on the borderlands through the use of earls. The Marcher earldoms', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T1'},
    
    # KT2 T2 Bullets
    {'code': 'Paper2_OptB1_KT2_T2_B1', 'title': 'Causes and outcomes of Anglo-Saxon resistance: the revolt of Earls Edwin and Morcar (1068); Edgar the Aethling and the rebellions in the North (1069); Hereward the Wake and rebellion at Ely (1070–71)', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T2'},
    
    # KT2 T3 Bullets
    {'code': 'Paper2_OptB1_KT2_T3_B1', 'title': 'The reasons for and features of Harrying of the North (1069–70). Its immediate and long-term impact, 1069–87', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T3'},
    {'code': 'Paper2_OptB1_KT2_T3_B2', 'title': 'Changes in landownership from Anglo-Saxon to Norman, 1066–87', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T3'},
    
    # KT2 T4 Bullets
    {'code': 'Paper2_OptB1_KT2_T4_B1', 'title': 'Reasons for and features of the revolt', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T4'},
    {'code': 'Paper2_OptB1_KT2_T4_B2', 'title': 'The defeat of the revolt and its effects', 'level': 5, 'parent': 'Paper2_OptB1_KT2_T4'},
    
    # KT3 Topics
    {'code': 'Paper2_OptB1_KT3_T1', 'title': '1. The feudal system and the Church', 'level': 4, 'parent': 'Paper2_OptB1_KT3'},
    {'code': 'Paper2_OptB1_KT3_T2', 'title': '2. Norman government', 'level': 4, 'parent': 'Paper2_OptB1_KT3'},
    {'code': 'Paper2_OptB1_KT3_T3', 'title': '3. The Norman aristocracy', 'level': 4, 'parent': 'Paper2_OptB1_KT3'},
    {'code': 'Paper2_OptB1_KT3_T4', 'title': '4. William I and the succession', 'level': 4, 'parent': 'Paper2_OptB1_KT3'},
    
    # KT3 T1 Bullets
    {'code': 'Paper2_OptB1_KT3_T1_B1', 'title': 'The feudal hierarchy. The role and importance of tenants-in-chief and knights. The nature of feudalism (landholding, homage, knight service, labour service); forfeiture', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T1'},
    {'code': 'Paper2_OptB1_KT3_T1_B2', 'title': 'The Church in England: its role in society and relationship to government, including the significance of Stigand and Lanfranc. The Normanisation and reform of the Church in the reign of William I', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T1'},
    {'code': 'Paper2_OptB1_KT3_T1_B3', 'title': 'The extent of change to Anglo-Saxon society and economy', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T1'},
    
    # KT3 T2 Bullets
    {'code': 'Paper2_OptB1_KT3_T2_B1', 'title': 'Changes to government after the Conquest. Centralised power and the limited use of earls under William I. The role of regents during William\'s absences', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T2'},
    {'code': 'Paper2_OptB1_KT3_T2_B2', 'title': 'The Domesday survey and Domesday Book and their significance for Norman government and finance', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T2'},
    {'code': 'Paper2_OptB1_KT3_T2_B3', 'title': 'The office of sheriff and the demesne. Introduction and significance of the \'forest\'', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T2'},
    
    # KT3 T3 Bullets
    {'code': 'Paper2_OptB1_KT3_T3_B1', 'title': 'The culture and language of the Norman aristocracy', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T3'},
    {'code': 'Paper2_OptB1_KT3_T3_B2', 'title': 'The career and significance of Bishop Odo', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T3'},
    
    # KT3 T4 Bullets
    {'code': 'Paper2_OptB1_KT3_T4_B1', 'title': 'Character and personality of William I and his relations with Robert, including Robert\'s revolt in Normandy (1077–80)', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T4'},
    {'code': 'Paper2_OptB1_KT3_T4_B2', 'title': 'William\'s death and the disputed succession. William Rufus and the defeat of Robert and Odo', 'level': 5, 'parent': 'Paper2_OptB1_KT3_T4'},
    
    # ========== OPTION B2: RICHARD I AND KING JOHN ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptB2_KT1', 'title': 'Key topic 1: Life and government in England, 1189–1216', 'level': 3, 'parent': 'Paper2_OptB2'},
    {'code': 'Paper2_OptB2_KT2', 'title': 'Key topic 2: Involvements overseas, 1189–1204', 'level': 3, 'parent': 'Paper2_OptB2'},
    {'code': 'Paper2_OptB2_KT3', 'title': 'Key topic 3: King John\'s downfall, 1205–16', 'level': 3, 'parent': 'Paper2_OptB2'},
    
    # KT1 Topics
    {'code': 'Paper2_OptB2_KT1_T1', 'title': '1. The feudal system', 'level': 4, 'parent': 'Paper2_OptB2_KT1'},
    {'code': 'Paper2_OptB2_KT1_T2', 'title': '2. Kingship and succession', 'level': 4, 'parent': 'Paper2_OptB2_KT1'},
    {'code': 'Paper2_OptB2_KT1_T3', 'title': '3. Royal government and finances', 'level': 4, 'parent': 'Paper2_OptB2_KT1'},
    {'code': 'Paper2_OptB2_KT1_T4', 'title': '4. English society', 'level': 4, 'parent': 'Paper2_OptB2_KT1'},
    
    # KT1 Bullets
    {'code': 'Paper2_OptB2_KT1_T1_B1', 'title': 'The feudal hierarchy and the nature of feudalism (landholding, homage, knight service, labour service); forfeiture', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T1'},
    {'code': 'Paper2_OptB2_KT1_T1_B2', 'title': 'The role and influence of the Church', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T1'},
    {'code': 'Paper2_OptB2_KT1_T2_B1', 'title': 'The nature of kingship: duties, rights, rituals', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T2'},
    {'code': 'Paper2_OptB2_KT1_T2_B2', 'title': 'Richard I as king: his claim to the throne; how power was secured; his character', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T2'},
    {'code': 'Paper2_OptB2_KT1_T2_B3', 'title': 'John as king: his claim to the throne; how power was secured and the murder of Prince Arthur; John\'s character', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T2'},
    {'code': 'Paper2_OptB2_KT1_T3_B1', 'title': 'How England was governed when Richard was absent, 1189–99, and during King John\'s continued presence in England, 1199–1216', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T3'},
    {'code': 'Paper2_OptB2_KT1_T3_B2', 'title': 'Royal revenues: the royal demesne and the role of sheriffs in collecting revenues; feudal incidents; scutage; taxes on moveables and income in 1207', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T3'},
    {'code': 'Paper2_OptB2_KT1_T4_B1', 'title': 'Countryside: the nature of agriculture and peasant life', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T4'},
    {'code': 'Paper2_OptB2_KT1_T4_B2', 'title': 'Towns: life in towns; their role in the economy', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T4'},
    {'code': 'Paper2_OptB2_KT1_T4_B3', 'title': 'Jews in Medieval England: legal status; role in moneylending; antisemitism; the causes and extent of the pogroms of 1189–90, including the significance of the coronation of Richard I; royal exploitation via taxes', 'level': 5, 'parent': 'Paper2_OptB2_KT1_T4'},
    
    # KT2 Topics
    {'code': 'Paper2_OptB2_KT2_T1', 'title': '1. The nature of crusading', 'level': 4, 'parent': 'Paper2_OptB2_KT2'},
    {'code': 'Paper2_OptB2_KT2_T2', 'title': '2. Richard and the Third Crusade', 'level': 4, 'parent': 'Paper2_OptB2_KT2'},
    {'code': 'Paper2_OptB2_KT2_T3', 'title': '3. Aftermath of the crusade', 'level': 4, 'parent': 'Paper2_OptB2_KT2'},
    {'code': 'Paper2_OptB2_KT2_T4', 'title': '4. Richard, John and the loss of Normandy', 'level': 4, 'parent': 'Paper2_OptB2_KT2'},
    
    # KT2 Bullets
    {'code': 'Paper2_OptB2_KT2_T1_B1', 'title': 'The concept of crusade and attitudes in England to the crusades', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T1'},
    {'code': 'Paper2_OptB2_KT2_T1_B2', 'title': 'The nature of the English crusading army: who they were, why they went', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T1'},
    {'code': 'Paper2_OptB2_KT2_T2_B1', 'title': 'The immediate causes of the Third Crusade; Richard\'s motives for involvement in the Third Crusade', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T2'},
    {'code': 'Paper2_OptB2_KT2_T2_B2', 'title': 'Richard\'s quarrel with Philip II; Richard\'s military victories at Acre and Arsuf', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T2'},
    {'code': 'Paper2_OptB2_KT2_T2_B3', 'title': 'The failure to recapture Jerusalem', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T2'},
    {'code': 'Paper2_OptB2_KT2_T3_B1', 'title': 'Richard\'s return from the Holy Land', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T3'},
    {'code': 'Paper2_OptB2_KT2_T3_B2', 'title': 'Richard\'s capture, the ransom and its burden on England', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T3'},
    {'code': 'Paper2_OptB2_KT2_T4_B1', 'title': 'The competing aims of Richard and John and Philip II in Normandy', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T4'},
    {'code': 'Paper2_OptB2_KT2_T4_B2', 'title': 'Richard and Chateau Gaillard: its cost and importance', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T4'},
    {'code': 'Paper2_OptB2_KT2_T4_B3', 'title': 'John and the fall of Chateau Gaillard; the loss of Normandy (1204)', 'level': 5, 'parent': 'Paper2_OptB2_KT2_T4'},
    
    # KT3 Topics
    {'code': 'Paper2_OptB2_KT3_T1', 'title': '1. The dispute with the Papacy', 'level': 4, 'parent': 'Paper2_OptB2_KT3'},
    {'code': 'Paper2_OptB2_KT3_T2', 'title': '2. Worsening relations with the barons', 'level': 4, 'parent': 'Paper2_OptB2_KT3'},
    {'code': 'Paper2_OptB2_KT3_T3', 'title': '3. Magna Carta and the First Barons\' War', 'level': 4, 'parent': 'Paper2_OptB2_KT3'},
    {'code': 'Paper2_OptB2_KT3_T4', 'title': '4. England in 1216', 'level': 4, 'parent': 'Paper2_OptB2_KT3'},
    
    # KT3 Bullets
    {'code': 'Paper2_OptB2_KT3_T1_B1', 'title': 'Causes of the dispute', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T1'},
    {'code': 'Paper2_OptB2_KT3_T1_B2', 'title': 'The Interdict and its impact on everyday life', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T1'},
    {'code': 'Paper2_OptB2_KT3_T1_B3', 'title': 'The significance of the reconciliation between John and Innocent III', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T1'},
    {'code': 'Paper2_OptB2_KT3_T2_B1', 'title': 'Growing financial impositions to raise money for war with France: taxation and \'fines\'; John\'s use of arbitrary power. The plot of 1212', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T2'},
    {'code': 'Paper2_OptB2_KT3_T2_B2', 'title': 'The impact of the failure to regain Normandy in 1214', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T2'},
    {'code': 'Paper2_OptB2_KT3_T2_B3', 'title': 'The rebellion of 1215: Northampton, Lincoln, the march on London', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T2'},
    {'code': 'Paper2_OptB2_KT3_T3_B1', 'title': 'Runnymede: the motives of John and the barons, and the main provisions of Magna Carta', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T3'},
    {'code': 'Paper2_OptB2_KT3_T3_B2', 'title': 'Reasons for the outbreak of the First Baron\'s War. The siege and taking of Rochester; the invasion of Prince Louis', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T3'},
    {'code': 'Paper2_OptB2_KT3_T4_B1', 'title': 'The condition of England at the time of John\'s death', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T4'},
    {'code': 'Paper2_OptB2_KT3_T4_B2', 'title': 'The problem of the succession', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T4'},
    {'code': 'Paper2_OptB2_KT3_T4_B3', 'title': 'The role of William Marshal as Protector', 'level': 5, 'parent': 'Paper2_OptB2_KT3_T4'},
    
    # ========== OPTION B3: HENRY VIII AND HIS MINISTERS ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptB3_KT1', 'title': 'Key topic 1: Henry VIII and Wolsey, 1509–29', 'level': 3, 'parent': 'Paper2_OptB3'},
    {'code': 'Paper2_OptB3_KT2', 'title': 'Key topic 2: Henry VIII and Cromwell, 1529–40', 'level': 3, 'parent': 'Paper2_OptB3'},
    {'code': 'Paper2_OptB3_KT3', 'title': 'Key topic 3: The Reformation and its impact, 1529–40', 'level': 3, 'parent': 'Paper2_OptB3'},
    
    # KT1 Topics with bullets
    {'code': 'Paper2_OptB3_KT1_T1', 'title': '1. Henry VIII, Renaissance Prince', 'level': 4, 'parent': 'Paper2_OptB3_KT1'},
    {'code': 'Paper2_OptB3_KT1_T1_B1', 'title': 'England in 1509: society and government. The young Henry and his accession to the throne', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T1'},
    {'code': 'Paper2_OptB3_KT1_T1_B2', 'title': 'Henry\'s character and views on sovereignty and monarchy. His personal style of government', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T1'},
    {'code': 'Paper2_OptB3_KT1_T1_B3', 'title': 'Strengths, weaknesses and aims as monarch', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T1'},
    
    {'code': 'Paper2_OptB3_KT1_T2', 'title': '2. The rise of Wolsey and his policies', 'level': 4, 'parent': 'Paper2_OptB3_KT1'},
    {'code': 'Paper2_OptB3_KT1_T2_B1', 'title': 'Reasons for Wolsey\'s rise to power. His personality, roles and wealth', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T2'},
    {'code': 'Paper2_OptB3_KT1_T2_B2', 'title': 'Wolsey\'s reforms: enclosures, finance and justice. The Eltham Ordinances', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T2'},
    {'code': 'Paper2_OptB3_KT1_T2_B3', 'title': 'Reasons for and reactions to the Amicable Grant', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T2'},
    
    {'code': 'Paper2_OptB3_KT1_T3', 'title': '3. Wolsey\'s foreign policy', 'level': 4, 'parent': 'Paper2_OptB3_KT1'},
    {'code': 'Paper2_OptB3_KT1_T3_B1', 'title': 'Aims of Wolsey\'s foreign policy', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T3'},
    {'code': 'Paper2_OptB3_KT1_T3_B2', 'title': 'Successes and failures, including relations with France and the Holy Roman Empire, the Treaty of London (1518), the \'Field of the Cloth of Gold\' (1520) and increasing difficulties in the 1520s', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T3'},
    
    {'code': 'Paper2_OptB3_KT1_T4', 'title': '4. Wolsey, Catherine, the succession and annulment', 'level': 4, 'parent': 'Paper2_OptB3_KT1'},
    {'code': 'Paper2_OptB3_KT1_T4_B1', 'title': 'Catherine of Aragon and the succession', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T4'},
    {'code': 'Paper2_OptB3_KT1_T4_B2', 'title': 'Henry\'s reasons for and attempts to gain an annulment. Opposition to the annulment, including the role of Pope Clement VII', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T4'},
    {'code': 'Paper2_OptB3_KT1_T4_B3', 'title': 'Reasons for Wolsey\'s fall from power, including the failure of the divorce proceedings in London and the influence of the Boleyns', 'level': 5, 'parent': 'Paper2_OptB3_KT1_T4'},
    
    # KT2 Topics with bullets
    {'code': 'Paper2_OptB3_KT2_T1', 'title': '1. Cromwell\'s rise to power, 1529–34', 'level': 4, 'parent': 'Paper2_OptB3_KT2'},
    {'code': 'Paper2_OptB3_KT2_T1_B1', 'title': 'Personality and early career, including service to Wolsey, election as MP and eventual membership of the Royal Council', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T1'},
    {'code': 'Paper2_OptB3_KT2_T1_B2', 'title': 'Handling of the king\'s annulment and influence over Henry. Role as the king\'s Chief Minister', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T1'},
    
    {'code': 'Paper2_OptB3_KT2_T2', 'title': '2. The king\'s marriages', 'level': 4, 'parent': 'Paper2_OptB3_KT2'},
    {'code': 'Paper2_OptB3_KT2_T2_B1', 'title': 'Reasons for the fall of Anne Boleyn, including the role of Cromwell', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T2'},
    {'code': 'Paper2_OptB3_KT2_T2_B2', 'title': 'Reasons for marriage to Jane Seymour; her influence, heir and death', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T2'},
    {'code': 'Paper2_OptB3_KT2_T2_B3', 'title': 'Reasons for marriage to Anne of Cleves', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T2'},
    
    {'code': 'Paper2_OptB3_KT2_T3', 'title': '3. Cromwell and government, 1534–40', 'level': 4, 'parent': 'Paper2_OptB3_KT2'},
    {'code': 'Paper2_OptB3_KT2_T3_B1', 'title': 'Reform of government and royal finance', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T3'},
    {'code': 'Paper2_OptB3_KT2_T3_B2', 'title': 'The management and use of parliament', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T3'},
    
    {'code': 'Paper2_OptB3_KT2_T4', 'title': '4. The fall of Cromwell', 'level': 4, 'parent': 'Paper2_OptB3_KT2'},
    {'code': 'Paper2_OptB3_KT2_T4_B1', 'title': 'Reasons for Cromwell\'s fall from power in 1540, including the influence of the Duke of Norfolk and the failure of the marriage to Anne of Cleves', 'level': 5, 'parent': 'Paper2_OptB3_KT2_T4'},
    
    # KT3 Topics with bullets
    {'code': 'Paper2_OptB3_KT3_T1', 'title': '1. The break with Rome', 'level': 4, 'parent': 'Paper2_OptB3_KT3'},
    {'code': 'Paper2_OptB3_KT3_T1_B1', 'title': 'Henry as \'Defender of the Faith\'. Reasons for Henry\'s campaign against the Pope and the Catholic Church, 1529–33', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T1'},
    {'code': 'Paper2_OptB3_KT3_T1_B2', 'title': 'The significance of the Act of Succession and the Act of Supremacy (1534) for the break with Rome. Cromwell\'s role in their enforcement, including the use of oaths and treason laws', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T1'},
    
    {'code': 'Paper2_OptB3_KT3_T2', 'title': '2. Opposition to, and impact of, Reformation, 1534–40', 'level': 4, 'parent': 'Paper2_OptB3_KT3'},
    {'code': 'Paper2_OptB3_KT3_T2_B1', 'title': 'Elizabeth Barton (the Nun of Kent) and John Fisher', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T2'},
    {'code': 'Paper2_OptB3_KT3_T2_B2', 'title': 'The significance of opposition from Thomas More', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T2'},
    {'code': 'Paper2_OptB3_KT3_T2_B3', 'title': 'Impact of the Reformation on the English Church, including the work of Thomas Cranmer and the influence of Thomas Cromwell', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T2'},
    
    {'code': 'Paper2_OptB3_KT3_T3', 'title': '3. The dissolution of the monasteries', 'level': 4, 'parent': 'Paper2_OptB3_KT3'},
    {'code': 'Paper2_OptB3_KT3_T3_B1', 'title': 'The role of religious houses in local communities', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T3'},
    {'code': 'Paper2_OptB3_KT3_T3_B2', 'title': 'Reasons for the dissolutions, including the findings of Cromwell\'s commissions of 1535', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T3'},
    {'code': 'Paper2_OptB3_KT3_T3_B3', 'title': 'The impact of the dissolutions. Beneficiaries and losers', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T3'},
    
    {'code': 'Paper2_OptB3_KT3_T4', 'title': '4. The Pilgrimage of Grace, 1536', 'level': 4, 'parent': 'Paper2_OptB3_KT3'},
    {'code': 'Paper2_OptB3_KT3_T4_B1', 'title': 'Reasons for the uprising', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T4'},
    {'code': 'Paper2_OptB3_KT3_T4_B2', 'title': 'Key events of the uprising, including rebellions in Lincolnshire and Yorkshire and the roles of Robert Aske and the Duke of Norfolk', 'level': 5, 'parent': 'Paper2_OptB3_KT3_T4'},
    
    # ========== OPTION B4: EARLY ELIZABETHAN ENGLAND ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptB4_KT1', 'title': 'Key topic 1: Queen, government and religion, 1558–69', 'level': 3, 'parent': 'Paper2_OptB4'},
    {'code': 'Paper2_OptB4_KT2', 'title': 'Key topic 2: Challenges to Elizabeth at home and abroad, 1569–88', 'level': 3, 'parent': 'Paper2_OptB4'},
    {'code': 'Paper2_OptB4_KT3', 'title': 'Key topic 3: Elizabethan society in the Age of Exploration, 1558–88', 'level': 3, 'parent': 'Paper2_OptB4'},
    
    # KT1 Topics with bullets
    {'code': 'Paper2_OptB4_KT1_T1', 'title': '1. The situation on Elizabeth\'s accession', 'level': 4, 'parent': 'Paper2_OptB4_KT1'},
    {'code': 'Paper2_OptB4_KT1_T1_B1', 'title': 'Elizabethan England in 1558: society and government', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T1'},
    {'code': 'Paper2_OptB4_KT1_T1_B2', 'title': 'Challenges at home and from abroad: financial weaknesses, religious divisions, the French threat', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T1'},
    {'code': 'Paper2_OptB4_KT1_T1_B3', 'title': 'The Virgin Queen: the problem of her legitimacy, gender, marriage. Her character and strengths', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T1'},
    
    {'code': 'Paper2_OptB4_KT1_T2', 'title': '2. The \'settlement\' of religion', 'level': 4, 'parent': 'Paper2_OptB4_KT1'},
    {'code': 'Paper2_OptB4_KT1_T2_B1', 'title': 'Elizabeth\'s religious settlement (1559): its features and impact', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T2'},
    {'code': 'Paper2_OptB4_KT1_T2_B2', 'title': 'The Church of England: its role in society', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T2'},
    
    {'code': 'Paper2_OptB4_KT1_T3', 'title': '3. Challenge to the religious settlement', 'level': 4, 'parent': 'Paper2_OptB4_KT1'},
    {'code': 'Paper2_OptB4_KT1_T3_B1', 'title': 'The nature and extent of the Puritan challenge', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T3'},
    {'code': 'Paper2_OptB4_KT1_T3_B2', 'title': 'The nature and extent of the Catholic challenge, including the role of the nobility, Papacy and foreign powers', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T3'},
    
    {'code': 'Paper2_OptB4_KT1_T4', 'title': '4. The problem of Mary, Queen of Scots', 'level': 4, 'parent': 'Paper2_OptB4_KT1'},
    {'code': 'Paper2_OptB4_KT1_T4_B1', 'title': 'Mary, Queen of Scots: her claim to the English throne', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T4'},
    {'code': 'Paper2_OptB4_KT1_T4_B2', 'title': 'Relations between Elizabeth and Mary, 1568–69', 'level': 5, 'parent': 'Paper2_OptB4_KT1_T4'},
    
    # KT2 Topics with bullets
    {'code': 'Paper2_OptB4_KT2_T1', 'title': '1. Plots and revolts at home', 'level': 4, 'parent': 'Paper2_OptB4_KT2'},
    {'code': 'Paper2_OptB4_KT2_T1_B1', 'title': 'The reasons for, and significance of, the Revolt of the Northern Earls, 1569–70', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T1'},
    {'code': 'Paper2_OptB4_KT2_T1_B2', 'title': 'The reasons for, and significance of, Mary Queen of Scots\' execution in 1587', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T1'},
    {'code': 'Paper2_OptB4_KT2_T1_B3', 'title': 'The features and significance of the Ridolfi, Throckmorton and Babington plots. Walsingham and the use of spies', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T1'},
    
    {'code': 'Paper2_OptB4_KT2_T2', 'title': '2. Relations with Spain', 'level': 4, 'parent': 'Paper2_OptB4_KT2'},
    {'code': 'Paper2_OptB4_KT2_T2_B1', 'title': 'Political, religious and commercial rivalry', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T2'},
    {'code': 'Paper2_OptB4_KT2_T2_B2', 'title': 'The significance of privateering and the activities of Drake', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T2'},
    
    {'code': 'Paper2_OptB4_KT2_T3', 'title': '3. Outbreak of war with Spain, 1585–88', 'level': 4, 'parent': 'Paper2_OptB4_KT2'},
    {'code': 'Paper2_OptB4_KT2_T3_B1', 'title': 'Reasons for deteriorating relations with Spain: English direct involvement in the Netherlands and the actions of Robert Dudley', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T3'},
    {'code': 'Paper2_OptB4_KT2_T3_B2', 'title': 'Drake and the raid on Cadiz: \'Singeing the King of Spain\'s beard\'', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T3'},
    
    {'code': 'Paper2_OptB4_KT2_T4', 'title': '4. The Armada', 'level': 4, 'parent': 'Paper2_OptB4_KT2'},
    {'code': 'Paper2_OptB4_KT2_T4_B1', 'title': 'Spanish invasion plans. Key events of the Spanish Armada', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T4'},
    {'code': 'Paper2_OptB4_KT2_T4_B2', 'title': 'The reasons for the English victory', 'level': 5, 'parent': 'Paper2_OptB4_KT2_T4'},
    
    # KT3 Topics with bullets
    {'code': 'Paper2_OptB4_KT3_T1', 'title': '1. Education and leisure', 'level': 4, 'parent': 'Paper2_OptB4_KT3'},
    {'code': 'Paper2_OptB4_KT3_T1_B1', 'title': 'Education in the home and schools', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T1'},
    {'code': 'Paper2_OptB4_KT3_T1_B2', 'title': 'Sport, pastimes and the theatre', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T1'},
    
    {'code': 'Paper2_OptB4_KT3_T2', 'title': '2. The \'problem\' of the poor', 'level': 4, 'parent': 'Paper2_OptB4_KT3'},
    {'code': 'Paper2_OptB4_KT3_T2_B1', 'title': 'The reasons for the increase in poverty and vagabondage during these years', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T2'},
    {'code': 'Paper2_OptB4_KT3_T2_B2', 'title': 'The changing attitudes and policies towards the poor', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T2'},
    
    {'code': 'Paper2_OptB4_KT3_T3', 'title': '3. Exploration and voyages of discovery', 'level': 4, 'parent': 'Paper2_OptB4_KT3'},
    {'code': 'Paper2_OptB4_KT3_T3_B1', 'title': 'Factors prompting exploration, including the impact of new technology on ships and sailing and the drive to expand trade', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T3'},
    {'code': 'Paper2_OptB4_KT3_T3_B2', 'title': 'The reasons for, and significance of, Drake\'s circumnavigation of the globe', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T3'},
    
    {'code': 'Paper2_OptB4_KT3_T4', 'title': '4. Attempted colonisation of Virginia', 'level': 4, 'parent': 'Paper2_OptB4_KT3'},
    {'code': 'Paper2_OptB4_KT3_T4_B1', 'title': 'Reasons for the attempted colonisation of Virginia, including the significance of Raleigh', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T4'},
    {'code': 'Paper2_OptB4_KT3_T4_B2', 'title': 'Reasons for the failure of the first settlement in Virginia', 'level': 5, 'parent': 'Paper2_OptB4_KT3_T4'},
]


def upload_b_options():
    """Add all B option detailed content."""
    print(f"\n[INFO] Adding Paper 2 B options content...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        # Delete old B option details (Level 3+) for ALL B options
        # Delete anything that starts with Paper2_OptB1_, Paper2_OptB2_, Paper2_OptB3_, or Paper2_OptB4_
        deleted_count = 0
        for t in existing_topics.data:
            code = t['topic_code']
            if (code.startswith('Paper2_OptB1_') or code.startswith('Paper2_OptB2_') or 
                code.startswith('Paper2_OptB3_') or code.startswith('Paper2_OptB4_')):
                supabase.table('staging_aqa_topics').delete().eq('id', t['id']).execute()
                deleted_count += 1
        
        print(f"[OK] Cleared {deleted_count} old B option details")
        
        # Insert new topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in NEW_TOPICS]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} new topics")
        
        # Link parents
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        for t in existing_topics.data:
            code_to_id[t['topic_code']] = t['id']
        
        linked = 0
        for topic in NEW_TOPICS:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
        
        print(f"[OK] Linked {linked} relationships")
        
        levels = defaultdict(int)
        for t in NEW_TOPICS:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print("[SUCCESS] PAPER 2: ALL B OPTIONS UPLOADED!")
        print("=" * 80)
        print("✅ B1: Anglo-Saxon and Norman England (COMPLETE with bullets)")
        print("✅ B2: Richard I and King John (COMPLETE with bullets)")
        print("✅ B3: Henry VIII and his ministers (COMPLETE with bullets)")
        print("✅ B4: Early Elizabethan England (COMPLETE with bullets)")
        print()
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} topics")
        print(f"\n   Total added: {len(NEW_TOPICS)}")
        print("=" * 80)
        
        return subject_id
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("GCSE HISTORY - PAPER 2 B OPTIONS")
    print("=" * 80)
    
    try:
        subject_id = upload_b_options()
        
        if subject_id:
            print("\n✅ COMPLETE! All 4 B options uploaded")
            print("\nNOTE: B1 & B2 have full content with bullets")
            print("B3 & B4 have structure only (add bullets as needed)")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

