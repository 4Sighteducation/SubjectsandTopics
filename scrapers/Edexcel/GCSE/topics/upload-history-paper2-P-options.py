"""
GCSE History - Paper 2: P Options (Period Studies)
==================================================

Uploads Period study options (P1, P2, P4)

Structure: Same as B options
- Level 3: Key topics (3 per option)
- Level 4: Numbered sections
- Level 5: Bullet points
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

NEW_TOPICS = [
    # ========== OPTION P1: SPAIN AND THE 'NEW WORLD' ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptP1_KT1', 'title': 'Key topic 1: Spain reaches the Americas, c1490–1512', 'level': 3, 'parent': 'Paper2_OptP1'},
    {'code': 'Paper2_OptP1_KT2', 'title': 'Key topic 2: The conquistadors, 1513–c1528', 'level': 3, 'parent': 'Paper2_OptP1'},
    {'code': 'Paper2_OptP1_KT3', 'title': 'Key topic 3: The Spanish Empire c1528–c1555', 'level': 3, 'parent': 'Paper2_OptP1'},
    
    # KT1 Topics
    {'code': 'Paper2_OptP1_KT1_T1', 'title': '1. Spanish exploration', 'level': 4, 'parent': 'Paper2_OptP1_KT1'},
    {'code': 'Paper2_OptP1_KT1_T2', 'title': '2. Columbus reaches the Americas', 'level': 4, 'parent': 'Paper2_OptP1_KT1'},
    {'code': 'Paper2_OptP1_KT1_T3', 'title': '3. Spanish claims in the Caribbean', 'level': 4, 'parent': 'Paper2_OptP1_KT1'},
    
    # KT1 T1 Bullets
    {'code': 'Paper2_OptP1_KT1_T1_B1', 'title': 'Spain c1490: the crusading spirit and foreign ambitions', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T1'},
    {'code': 'Paper2_OptP1_KT1_T1_B2', 'title': 'Columbus\'s attempts to gain sponsorship. The role of Queen Isabella: her desire to spread Christianity and sponsorship of Columbus', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T1'},
    {'code': 'Paper2_OptP1_KT1_T1_B3', 'title': 'Columbus\'s first voyage of 1492 and the problems encountered', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T1'},
    
    # KT1 T2 Bullets
    {'code': 'Paper2_OptP1_KT1_T2_B1', 'title': 'Columbus\'s actions: exploration of the Bahamas and the Caribbean. The foundation of La Navidad', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T2'},
    {'code': 'Paper2_OptP1_KT1_T2_B2', 'title': 'The impact of contact with Indigenous peoples: the discovery of gold, relations with the Tainos and Caribs', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T2'},
    {'code': 'Paper2_OptP1_KT1_T2_B3', 'title': 'The impact of rivalry with Portugal, and the Treaty of Tordesillas (1494)', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T2'},
    
    # KT1 T3 Bullets
    {'code': 'Paper2_OptP1_KT1_T3_B1', 'title': 'Columbus\'s later voyages and his role as governor in the Spanish settlement. The significance of the establishment of the Spanish colony at Santo Domingo (1496)', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T3'},
    {'code': 'Paper2_OptP1_KT1_T3_B2', 'title': 'The effects of Spanish settlement: treatment of Indigenous peoples, effects of smallpox', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T3'},
    {'code': 'Paper2_OptP1_KT1_T3_B3', 'title': 'Development of an imperial policy in relation to the Caribbean: the regulation of further exploration, the establishment of a monopoly on trade, the extension of Spanish authority and the use of slavery. The role of Catholic missionaries', 'level': 5, 'parent': 'Paper2_OptP1_KT1_T3'},
    
    # KT2 Topics
    {'code': 'Paper2_OptP1_KT2_T1', 'title': '1. The start of an empire', 'level': 4, 'parent': 'Paper2_OptP1_KT2'},
    {'code': 'Paper2_OptP1_KT2_T2', 'title': '2. The conquest of Mexico', 'level': 4, 'parent': 'Paper2_OptP1_KT2'},
    {'code': 'Paper2_OptP1_KT2_T3', 'title': '3. Impact of Spain in the Americas', 'level': 4, 'parent': 'Paper2_OptP1_KT2'},
    
    # KT2 T1 Bullets
    {'code': 'Paper2_OptP1_KT2_T1_B1', 'title': 'Balboa\'s claim of Spanish authority over the Pacific (1513)', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T1'},
    {'code': 'Paper2_OptP1_KT2_T1_B2', 'title': 'The conquest of Cuba', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T1'},
    {'code': 'Paper2_OptP1_KT2_T1_B3', 'title': 'The voyage of Magellan and Spanish claim to the Philippines', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T1'},
    
    # KT2 T2 Bullets
    {'code': 'Paper2_OptP1_KT2_T2_B1', 'title': 'Cortes\'s expedition to Mexico in 1519', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T2'},
    {'code': 'Paper2_OptP1_KT2_T2_B2', 'title': 'Key events of the Spanish conquest of Mexico; the role of Montezuma, the war between Aztecs and Tlaxcalans', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T2'},
    {'code': 'Paper2_OptP1_KT2_T2_B3', 'title': 'The capture of Tenochtitlan and the Aztec surrender', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T2'},
    
    # KT2 T3 Bullets
    {'code': 'Paper2_OptP1_KT2_T3_B1', 'title': 'Cortes\'s actions as Governor and Captain-General of New Spain (1523–28)', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T3'},
    {'code': 'Paper2_OptP1_KT2_T3_B2', 'title': 'The consequences of the Spanish invasion for the Aztecs', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T3'},
    {'code': 'Paper2_OptP1_KT2_T3_B3', 'title': 'The founding and significance of a Spanish base at Panama', 'level': 5, 'parent': 'Paper2_OptP1_KT2_T3'},
    
    # KT3 Topics
    {'code': 'Paper2_OptP1_KT3_T1', 'title': '1. Pizarro and the conquest of the Incas', 'level': 4, 'parent': 'Paper2_OptP1_KT3'},
    {'code': 'Paper2_OptP1_KT3_T2', 'title': '2. Expansion of empire', 'level': 4, 'parent': 'Paper2_OptP1_KT3'},
    {'code': 'Paper2_OptP1_KT3_T3', 'title': '3. Impact of the \'New World\' on Spain', 'level': 4, 'parent': 'Paper2_OptP1_KT3'},
    
    # KT3 T1 Bullets
    {'code': 'Paper2_OptP1_KT3_T1_B1', 'title': 'Contact with the Incas (1528); the significance of the death of Huayna Capac', 'level': 5, 'parent': 'Paper2_OptP1_KT3_T1'},
    {'code': 'Paper2_OptP1_KT3_T1_B2', 'title': 'The voyage of Pizarro (1530), and the significance of the war between Atahuallpa and Huascar', 'level': 5, 'parent': 'Paper2_OptP1_KT3_T1'},
    {'code': 'Paper2_OptP1_KT3_T1_B3', 'title': 'Key events of the Spanish conquest of Peru: the Battle of Cajamarca and the capture of Atahuallpa, the revolt of the Incas, the siege of Cuzco (1536–37). The impact of the conquest', 'level': 5, 'parent': 'Paper2_OptP1_KT3_T1'},
    
    # KT3 T2 Bullets
    {'code': 'Paper2_OptP1_KT3_T2_B1', 'title': 'The role of the viceroys and encomiendas in the Spanish Empire. The role of Las Casas and the significance of the New Laws (1542)', 'level': 5, 'parent': 'Paper2_OptP1_KT3_T2'},
    {'code': 'Paper2_OptP1_KT3_T2_B2', 'title': 'The significance of the discovery of silver in Bolivia and in Mexico. The foundation of La Paz (1548)', 'level': 5, 'parent': 'Paper2_OptP1_KT3_T2'},
    
    # KT3 T3 Bullets
    {'code': 'Paper2_OptP1_KT3_T3_B1', 'title': 'The importance of gold and silver for the Spanish economy and to support Spain\'s European empire', 'level': 5, 'parent': 'Paper2_OptP1_KT3_T3'},
    {'code': 'Paper2_OptP1_KT3_T3_B2', 'title': 'The government of the Spanish Empire: the role of the House of Trade and Council of the Indies', 'level': 5, 'parent': 'Paper2_OptP1_KT3_T3'},
    
    # ========== OPTION P2: BRITISH AMERICA ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptP2_KT1', 'title': 'Key topic 1: British settlement in North America, 1713–41', 'level': 3, 'parent': 'Paper2_OptP2'},
    {'code': 'Paper2_OptP2_KT2', 'title': 'Key topic 2: A disrupted society, 1742–64', 'level': 3, 'parent': 'Paper2_OptP2'},
    {'code': 'Paper2_OptP2_KT3', 'title': 'Key topic 3: The loss of an empire, 1765–83', 'level': 3, 'parent': 'Paper2_OptP2'},
    
    # KT1 Topics
    {'code': 'Paper2_OptP2_KT1_T1', 'title': '1. Developments in colonial society', 'level': 4, 'parent': 'Paper2_OptP2_KT1'},
    {'code': 'Paper2_OptP2_KT1_T2', 'title': '2. Slavery in North America', 'level': 4, 'parent': 'Paper2_OptP2_KT1'},
    {'code': 'Paper2_OptP2_KT1_T3', 'title': '3. Problems within the colonies', 'level': 4, 'parent': 'Paper2_OptP2_KT1'},
    
    # KT1 T1 Bullets
    {'code': 'Paper2_OptP2_KT1_T1_B1', 'title': 'The impact of expansion and immigration on society: the pattern of settlement and tensions among social groups', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T1'},
    {'code': 'Paper2_OptP2_KT1_T1_B2', 'title': 'Economic developments: trade with Britain and with the West Indies, the importance of tobacco, the impact of piracy, including the activities of \'Black Sam\' Bellamy and Edward Teach (\'Blackbeard\')', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T1'},
    {'code': 'Paper2_OptP2_KT1_T1_B3', 'title': 'The suppression of piracy in American waters: King George I\'s Proclamation and the Piracy Act (1717), the work of Governor Spotswood', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T1'},
    
    # KT1 T2 Bullets
    {'code': 'Paper2_OptP2_KT1_T2_B1', 'title': 'The transatlantic slave trade and \'Atlantic trade triangle\'', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T2'},
    {'code': 'Paper2_OptP2_KT1_T2_B2', 'title': 'The impact of slavery on the development of tobacco and rice plantations', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T2'},
    {'code': 'Paper2_OptP2_KT1_T2_B3', 'title': 'The impact of slavery on colonial society; the position of enslaved people within society and the treatment of fugitives within the colonies', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T2'},
    
    # KT1 T3 Bullets
    {'code': 'Paper2_OptP2_KT1_T3_B1', 'title': 'Slave revolts in the Carolinas: the Stono Rebellion (1739); the significance of Spain\'s decision to protect runaways in Florida', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T3'},
    {'code': 'Paper2_OptP2_KT1_T3_B2', 'title': 'The New York Conspiracy (1741)', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T3'},
    {'code': 'Paper2_OptP2_KT1_T3_B3', 'title': 'Smuggling, attempts to collect customs revenue and to control the fur trade', 'level': 5, 'parent': 'Paper2_OptP2_KT1_T3'},
    
    # KT2 Topics
    {'code': 'Paper2_OptP2_KT2_T1', 'title': '1. The impact of cultural developments', 'level': 4, 'parent': 'Paper2_OptP2_KT2'},
    {'code': 'Paper2_OptP2_KT2_T2', 'title': '2. War in the colonies', 'level': 4, 'parent': 'Paper2_OptP2_KT2'},
    {'code': 'Paper2_OptP2_KT2_T3', 'title': '3. The aftermath of the French and Indian war', 'level': 4, 'parent': 'Paper2_OptP2_KT2'},
    
    # KT2 T1 Bullets
    {'code': 'Paper2_OptP2_KT2_T1_B1', 'title': 'Religious revivals, including the Great Awakening and revivalist preachers', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T1'},
    {'code': 'Paper2_OptP2_KT2_T1_B2', 'title': 'The significance of Benjamin Franklin as a writer, philanthropist and intellectual', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T1'},
    {'code': 'Paper2_OptP2_KT2_T1_B3', 'title': 'The Enlightenment: the emphasis on education; the growth of newspapers and public libraries', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T1'},
    
    # KT2 T2 Bullets
    {'code': 'Paper2_OptP2_KT2_T2_B1', 'title': 'Relations with the French and with Indigenous peoples during and after King George\'s War (1744–48)', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T2'},
    {'code': 'Paper2_OptP2_KT2_T2_B2', 'title': 'The significance of the Treaty of Paris (1763) and the Proclamation Act (1763)', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T2'},
    {'code': 'Paper2_OptP2_KT2_T2_B3', 'title': 'The French and Indian War (1754–63) in North America and the role of Wolfe in Canada', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T2'},
    
    # KT2 T3 Bullets
    {'code': 'Paper2_OptP2_KT2_T3_B1', 'title': 'The impact of the war on American colonists\' relations with Britain', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T3'},
    {'code': 'Paper2_OptP2_KT2_T3_B2', 'title': 'Opposition to the Sugar Act (1764)', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T3'},
    {'code': 'Paper2_OptP2_KT2_T3_B3', 'title': 'Relations with Indigenous peoples, including Pontiac\'s Rebellion (1763–64). The Paxton Boys: their actions and impact', 'level': 5, 'parent': 'Paper2_OptP2_KT2_T3'},
    
    # KT3 Topics
    {'code': 'Paper2_OptP2_KT3_T1', 'title': '1. American colonist relations with Britain: growing opposition, 1765-75', 'level': 4, 'parent': 'Paper2_OptP2_KT3'},
    {'code': 'Paper2_OptP2_KT3_T2', 'title': '2. The War of Independence 1775-83', 'level': 4, 'parent': 'Paper2_OptP2_KT3'},
    {'code': 'Paper2_OptP2_KT3_T3', 'title': '3. Consequences of the war in America', 'level': 4, 'parent': 'Paper2_OptP2_KT3'},
    
    # KT3 T1 Bullets
    {'code': 'Paper2_OptP2_KT3_T1_B1', 'title': 'Opposition to British policies: the Stamp Act, the Sons of Liberty and the Boston Massacre (1770)', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T1'},
    {'code': 'Paper2_OptP2_KT3_T1_B2', 'title': 'The significance of the First and Second Continental Congresses, 1774–75', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T1'},
    {'code': 'Paper2_OptP2_KT3_T1_B3', 'title': 'British and American relations: the Boston Tea Party (1773) and the Intolerable Acts (1774)', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T1'},
    
    # KT3 T2 Bullets
    {'code': 'Paper2_OptP2_KT3_T2_B1', 'title': 'The influence of Thomas Paine\'s \'Common Sense\'. The significance of the Declaration of Independence. The role of Thomas Jefferson', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T2'},
    {'code': 'Paper2_OptP2_KT3_T2_B2', 'title': 'Key American victories: Saratoga (1777) and Yorktown (1781). The significance of Washington\'s role, British mistakes, and French and Spanish involvement in the war', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T2'},
    {'code': 'Paper2_OptP2_KT3_T2_B3', 'title': 'The Peace of Paris (1783), including the role of Franklin', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T2'},
    
    # KT3 T3 Bullets
    {'code': 'Paper2_OptP2_KT3_T3_B1', 'title': 'The significance of American independence for slavery', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T3'},
    {'code': 'Paper2_OptP2_KT3_T3_B2', 'title': 'The consequences of the war for Indigenous peoples', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T3'},
    {'code': 'Paper2_OptP2_KT3_T3_B3', 'title': 'The impact of the war on Loyalists, including their resettlement in Nova Scotia and Niagara', 'level': 5, 'parent': 'Paper2_OptP2_KT3_T3'},
    
    # ========== OPTION P3: THE AMERICAN WEST ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptP3_KT1', 'title': 'Key topic 1: The early settlement of the West, c1835–c1862', 'level': 3, 'parent': 'Paper2_OptP3'},
    {'code': 'Paper2_OptP3_KT2', 'title': 'Key topic 2: Development of the Plains, c1862–c1876', 'level': 3, 'parent': 'Paper2_OptP3'},
    {'code': 'Paper2_OptP3_KT3', 'title': 'Key topic 3: Later developments in the West, c1876–c1895', 'level': 3, 'parent': 'Paper2_OptP3'},
    
    # KT1 Topics (structure only for now - add bullets if needed)
    {'code': 'Paper2_OptP3_KT1_T1', 'title': '1. Indigenous peoples of the Plains: their beliefs and ways of life', 'level': 4, 'parent': 'Paper2_OptP3_KT1'},
    {'code': 'Paper2_OptP3_KT1_T2', 'title': '2. Migration and early settlement', 'level': 4, 'parent': 'Paper2_OptP3_KT1'},
    {'code': 'Paper2_OptP3_KT1_T3', 'title': '3. Conflict and tension', 'level': 4, 'parent': 'Paper2_OptP3_KT1'},
    
    # KT2 Topics
    {'code': 'Paper2_OptP3_KT2_T1', 'title': '1. The development of settlement in the West', 'level': 4, 'parent': 'Paper2_OptP3_KT2'},
    {'code': 'Paper2_OptP3_KT2_T2', 'title': '2. Ranching and the cattle industry', 'level': 4, 'parent': 'Paper2_OptP3_KT2'},
    {'code': 'Paper2_OptP3_KT2_T3', 'title': '3. Changes in the ways of life of Indigenous peoples of the Plains', 'level': 4, 'parent': 'Paper2_OptP3_KT2'},
    
    # KT3 Topics
    {'code': 'Paper2_OptP3_KT3_T1', 'title': '1. Changes in farming, the cattle industry and settlement', 'level': 4, 'parent': 'Paper2_OptP3_KT3'},
    {'code': 'Paper2_OptP3_KT3_T2', 'title': '2. Conflict and tension', 'level': 4, 'parent': 'Paper2_OptP3_KT3'},
    {'code': 'Paper2_OptP3_KT3_T3', 'title': '3. Indigenous peoples of the Plains: the destruction of their ways of life', 'level': 4, 'parent': 'Paper2_OptP3_KT3'},
    
    # ========== OPTION P4: COLD WAR ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptP4_KT1', 'title': 'Key topic 1: The origins of the Cold War, 1941–58', 'level': 3, 'parent': 'Paper2_OptP4'},
    {'code': 'Paper2_OptP4_KT2', 'title': 'Key topic 2: Cold War crises, 1958–70', 'level': 3, 'parent': 'Paper2_OptP4'},
    {'code': 'Paper2_OptP4_KT3', 'title': 'Key topic 3: The end of the Cold War, 1970–91', 'level': 3, 'parent': 'Paper2_OptP4'},
    
    # KT1 Topics (structure only for now)
    {'code': 'Paper2_OptP4_KT1_T1', 'title': '1. Early tension between East and West', 'level': 4, 'parent': 'Paper2_OptP4_KT1'},
    {'code': 'Paper2_OptP4_KT1_T2', 'title': '2. The development of the Cold War', 'level': 4, 'parent': 'Paper2_OptP4_KT1'},
    {'code': 'Paper2_OptP4_KT1_T3', 'title': '3. The Cold War intensifies', 'level': 4, 'parent': 'Paper2_OptP4_KT1'},
    
    # KT2 Topics
    {'code': 'Paper2_OptP4_KT2_T1', 'title': '1. Increased tension between East and West', 'level': 4, 'parent': 'Paper2_OptP4_KT2'},
    {'code': 'Paper2_OptP4_KT2_T2', 'title': '2. Cold War crises', 'level': 4, 'parent': 'Paper2_OptP4_KT2'},
    {'code': 'Paper2_OptP4_KT2_T3', 'title': '3. Reaction to crisis', 'level': 4, 'parent': 'Paper2_OptP4_KT2'},
    
    # KT3 Topics
    {'code': 'Paper2_OptP4_KT3_T1', 'title': '1. Attempts to reduce superpower tensions in the 1970s', 'level': 4, 'parent': 'Paper2_OptP4_KT3'},
    {'code': 'Paper2_OptP4_KT3_T2', 'title': '2. The end of détente and the \'Second Cold War\'', 'level': 4, 'parent': 'Paper2_OptP4_KT3'},
    {'code': 'Paper2_OptP4_KT3_T3', 'title': '3. The collapse of Soviet control of Eastern Europe, 1985-91', 'level': 4, 'parent': 'Paper2_OptP4_KT3'},
    
    # ========== OPTION P5: CONFLICT IN THE MIDDLE EAST ==========
    
    # Level 3: Key topics
    {'code': 'Paper2_OptP5_KT1', 'title': 'Key topic 1: The birth of the state of Israel, 1945–63', 'level': 3, 'parent': 'Paper2_OptP5'},
    {'code': 'Paper2_OptP5_KT2', 'title': 'Key topic 2: The escalating conflict, 1964–73', 'level': 3, 'parent': 'Paper2_OptP5'},
    {'code': 'Paper2_OptP5_KT3', 'title': 'Key topic 3: Attempts at a solution, 1974–95', 'level': 3, 'parent': 'Paper2_OptP5'},
    
    # KT1 Topics (structure only for now)
    {'code': 'Paper2_OptP5_KT1_T1', 'title': '1. The British withdrawal and the creation of Israel', 'level': 4, 'parent': 'Paper2_OptP5_KT1'},
    {'code': 'Paper2_OptP5_KT1_T2', 'title': '2. Aftermath of the 1948–49 war', 'level': 4, 'parent': 'Paper2_OptP5_KT1'},
    {'code': 'Paper2_OptP5_KT1_T3', 'title': '3. Increased tension, 1955–63', 'level': 4, 'parent': 'Paper2_OptP5_KT1'},
    
    # KT2 Topics
    {'code': 'Paper2_OptP5_KT2_T1', 'title': '1. The Six Day War, 1967', 'level': 4, 'parent': 'Paper2_OptP5_KT2'},
    {'code': 'Paper2_OptP5_KT2_T2', 'title': '2. Aftermath of the 1967 war', 'level': 4, 'parent': 'Paper2_OptP5_KT2'},
    {'code': 'Paper2_OptP5_KT2_T3', 'title': '3. Israel and Egypt, 1967–73', 'level': 4, 'parent': 'Paper2_OptP5_KT2'},
    
    # KT3 Topics
    {'code': 'Paper2_OptP5_KT3_T1', 'title': '1. Diplomatic negotiations', 'level': 4, 'parent': 'Paper2_OptP5_KT3'},
    {'code': 'Paper2_OptP5_KT3_T2', 'title': '2. The Palestinian issue', 'level': 4, 'parent': 'Paper2_OptP5_KT3'},
    {'code': 'Paper2_OptP5_KT3_T3', 'title': '3. Attempts at a solution', 'level': 4, 'parent': 'Paper2_OptP5_KT3'},
]


def upload_p_options():
    """Add all P option detailed content."""
    print(f"\n[INFO] Adding Paper 2 P options content...")
    
    try:
        subject_result = supabase.table('staging_aqa_subjects').select('id').eq('subject_code', SUBJECT_CODE).eq('qualification_type', 'GCSE').eq('exam_board', 'Edexcel').execute()
        
        if not subject_result.data:
            print("[ERROR] History subject not found!")
            return None
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        existing_topics = supabase.table('staging_aqa_topics').select('*').eq('subject_id', subject_id).execute()
        
        # Delete old P option details (Level 3+)
        deleted_count = 0
        for t in existing_topics.data:
            code = t['topic_code']
            if (code.startswith('Paper2_OptP1_') or code.startswith('Paper2_OptP2_') or 
                code.startswith('Paper2_OptP3_') or code.startswith('Paper2_OptP4_') or 
                code.startswith('Paper2_OptP5_')):
                supabase.table('staging_aqa_topics').delete().eq('id', t['id']).execute()
                deleted_count += 1
        
        print("[OK] Cleared old P option details")
        
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
        print("[SUCCESS] PAPER 2: ALL P OPTIONS UPLOADED!")
        print("=" * 80)
        print("✅ P1: Spain and the 'New World' (COMPLETE with bullets)")
        print("✅ P2: British America (COMPLETE with bullets)")
        print("✅ P3: The American West (structure only)")
        print("✅ P4: Superpower relations and the Cold War (structure only)")
        print("✅ P5: Conflict in the Middle East (structure only)")
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
    print("GCSE HISTORY - PAPER 2 P OPTIONS")
    print("=" * 80)
    
    try:
        subject_id = upload_p_options()
        
        if subject_id:
            print("\n✅ COMPLETE! All P options uploaded")
            print("\nNOTE: P1 & P2 have full content with bullets")
            print("P3 & P4 have structure only (add bullets if needed)")
        else:
            print("\n❌ FAILED")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

