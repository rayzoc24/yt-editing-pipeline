import re

# Direct conversational mappings for common Hindi words
COMMON_HINGLISH_DICT = {
    # Pronouns & Basics
    "मैं": "main", "मुझे": "mujhe", "मुझको": "mujhko", "मेरा": "mera", "मेरी": "meri", "मेरे": "mere",
    "हम": "hum", "हमें": "humein", "हमारा": "hamara", "हमारी": "hamari", "हमारे": "hamare",
    "तू": "tu", "तुझे": "tujhe", "तेरा": "tera", "तेरी": "teri", "तेरे": "tere",
    "तुम": "tum", "तुम्हें": "tumhein", "तुम्हारा": "tumhara", "तुम्हारी": "tumhari", "तुम्हारे": "tumhare",
    "आप": "aap", "आपको": "aapko", "आपका": "aapka", "आपकी": "aapki", "आपके": "aapke",
    "यह": "yeh", "ये": "yeh", "वह": "woh", "वो": "woh", "इस": "is", "इसको": "isko", "इसका": "iska",
    "इसकी": "iski", "इसके": "iske", "उस": "us", "उसको": "usko", "उसका": "uska", "उसकी": "uski", "उसके": "uske",
    "इन": "in", "इनका": "inka", "इनकी": "inki", "इनके": "inke", "उन": "un", "उनका": "unka", "उनकी": "unki", "उनके": "unke",
    "कौन": "kaun", "क्या": "kya", "क्यों": "kyon", "क्यूँ": "kyun", "कैसे": "kaise", "कब": "kab", "कहाँ": "kahan", "कहा": "kaha",
    "यहाँ": "yahan", "वहाँ": "wahan", "जहाँ": "jahan", "कहीं": "kahin", "कभी": "kabhi",

    # Conjunctions & Particles
    "और": "aur", "या": "ya", "लेकिन": "lekin", "पर": "par", "मगर": "magar", "किंतु": "kintu",
    "क्योंकि": "kyunki", "ताकि": "taaki", "अगर": "agar", "यदि": "yadi", "तो": "toh",
    "भी": "bhi", "ही": "hi", "तक": "tak", "भर": "bhar", "सिर्फ": "sirf", "बस": "bas",

    # Common Prepositions / Postpositions
    "में": "mein", "से": "se", "को": "ko", "का": "ka", "की": "ki", "के": "ke",
    "पर": "par", "पे": "pe", "लिए": "liye", "साथ": "saath", "बिना": "bina", "पास": "paas",

    # Auxiliaries & Be-verbs
    "है": "hai", "हैं": "hain", "हूँ": "hoon", "हो": "ho",
    "था": "tha", "थी": "thi", "थे": "the", "थीं": "theen",
    "होगा": "hoga", "होगी": "hogi", "होंगे": "honge", "होना": "hona",

    # Negations & Affirmations
    "नहीं": "nahi", "ना": "na", "हाँ": "haan", "जी": "jee", "अच्छा": "achha", "सही": "sahi", "गलत": "galat",

    # Common Action Verbs
    "कर": "kar", "करना": "karna", "करता": "karta", "करती": "karti", "करते": "karte",
    "किया": "kiya", "की": "ki", "किए": "kiye", "करेंगे": "karenge", "करेगा": "karega", "करेगी": "karegi", "करो": "karo", "कीजिये": "kijiye",
    "हो": "ho", "होता": "hota", "होती": "hoti", "होते": "hote", "हुआ": "hua", "हुई": "hui", "हुए": "hue",
    "जा": "jaa", "जाना": "jaana", "जाता": "jaata", "जाती": "jaati", "जाते": "jaate", "गया": "gaya", "गई": "gayi", "गए": "gaye",
    "आ": "aa", "आना": "aana", "आता": "aata", "आती": "aati", "आते": "aate", "आया": "aaya", "आई": "aayi", "आए": "aaye",
    "देख": "dekh", "देखना": "dekhna", "देखो": "dekho", "देखा": "dekha", "देखेंगे": "dekhenge",
    "बोल": "bol", "बोलना": "bolna", "बोलो": "bolo", "बोला": "bola", "बता": "bata", "बताओ": "batao", "बताया": "bataya",
    "सुन": "sun", "सुनना": "sunna", "सुनो": "suno", "सुना": "suna",
    "समझ": "samajh", "समझना": "samajhna", "समझा": "samjha", "समझे": "samjhe",
    "दे": "de", "देना": "dena", "दो": "do", "दिया": "diya", "दी": "dee", "दिए": "diye",
    "ले": "le", "लेना": "lena", "लो": "lo", "लिया": "liya", "ली": "lee", "लिए": "liye",
    "सक": "sak", "सकता": "sakta", "सकती": "sakti", "सकते": "sakte", "सका": "saka",
    "चाहिए": "chahiye", "चाहता": "chahta", "चाहती": "chahti", "चाहते": "chahte",
    "रहा": "raha", "रही": "rahi", "रहे": "rahe",

    # Slang & Content Creator Words
    "भाई": "bhai", "यार": "yaar", "दोस्त": "dost", "दोस्तों": "dosto",
    "लोग": "log", "लोगों": "logon", "सब": "sab", "कुछ": "kuch", "सबकुछ": "sabkuch",
    "बहुत": "bohot", "बोहोत": "bohot", "ज्यादा": "zyada", "ज़्यादा": "zyada", "कम": "kam",
    "एकदम": "ekdum", "बिल्कुल": "bilkul", "पक्का": "pakka", "सच": "sach", "सचमें": "sachme",
    "मस्त": "mast", "बढ़िया": "badhiya", "ज़बरदस्त": "zabardast", "जबरदस्त": "zabardast", "खतरनाक": "khatarnak",
    "गाड़ी": "gaadi", "घर": "ghar", "पैसा": "paisa", "पैसे": "paise", "काम": "kaam", "बात": "baat", "चीज": "cheez",
    "आज": "aaj", "कल": "kal", "पहला": "pehla", "पहली": "pehli", "पहले": "pehle", "बाद": "baad", "अभी": "abhi",
    "सिंगल": "single", "गर्लफ्रेंड": "girlfriend", "बॉयफ्रेंड": "boyfriend", "वीडियो": "video",
    "गेम": "game", "गेमिंग": "gaming", "रोस्ट": "roast", "चैनल": "channel",
    "डॉलर": "dollar", "जीटीए": "GTA", "कार": "car", "बाइक": "bike", "फोन": "phone"
}

VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ऑ': 'o', 'ऍ': 'e', 'ॲ': 'a'
}

MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ॉ': 'o', 'ॅ': 'e', 'ॊ': 'o', 'ॆ': 'e'
}

CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'd', 'ढ़': 'dh', 'फ़': 'f'
}

SPECIAL = {'ँ': 'n', 'ं': 'n', 'ः': 'h'}

def is_devanagari(text):
    """Returns True if the text contains any Devanagari characters."""
    return any('\u0900' <= char <= '\u097F' for char in text)

PUNCT_REGEX = r"[.,!?;:\'\"/\\()\[\]{}—\-_।॥\s]+"

def transliterate_word(word):
    """
    Transliterates a single Devanagari word into natural conversational Hinglish.
    Preserves trailing and leading punctuation (converting Hindi danda । to period .).
    """
    # Replace Hindi danda with period
    word = word.replace("।", ".").replace("॥", ".")

    prefix = ""
    suffix = ""
    clean = word

    m_pre = re.match(r"^([^a-zA-Z0-9\u0900-\u097F]+)(.*)$", clean)
    if m_pre:
        prefix = m_pre.group(1)
        clean = m_pre.group(2)

    m_suf = re.search(r"^(.*?)([^a-zA-Z0-9\u0900-\u097F]+)$", clean)
    if m_suf:
        clean = m_suf.group(1)
        suffix = m_suf.group(2)

    if not clean:
        return word

    # 1. Direct dictionary match
    if clean in COMMON_HINGLISH_DICT:
        return prefix + COMMON_HINGLISH_DICT[clean] + suffix

    # If it has no devanagari, return as is
    if not is_devanagari(clean):
        return word

    # 2. Phonetic Character-by-Character transliteration
    res = []
    i = 0
    n = len(clean)

    while i < n:
        ch = clean[i]

        # Handle nukta (e.g. ड़, ज़, फ़)
        if i + 1 < n and clean[i+1] == '़':
            nukta_char = ch + '़'
            if nukta_char in CONSONANTS:
                ch = nukta_char
                i += 1

        if ch in VOWELS:
            res.append(VOWELS[ch])
        elif ch in CONSONANTS:
            c_sound = CONSONANTS[ch]
            # Next character check
            if i + 1 < n and clean[i+1] == '्':  # Halant
                res.append(c_sound)
                i += 1
            elif i + 1 < n and clean[i+1] in MATRAS:  # Explicit vowel matra
                res.append(c_sound + MATRAS[clean[i+1]])
                i += 1
            elif i + 1 == n or (i + 1 < n and clean[i+1] in SPECIAL):  # Word-final consonant (Hindi schwa deletion)
                res.append(c_sound)
            else:
                # Medial consonant has inherent 'a'
                res.append(c_sound + 'a')
        elif ch in MATRAS:
            res.append(MATRAS[ch])
        elif ch in SPECIAL:
            res.append(SPECIAL[ch])
        else:
            res.append(ch)
        i += 1

    translit = "".join(res)
    
    # Conversational polish:
    # 'ee' at the end of words is commonly written as 'i' (e.g., naheen -> nahi, bhee -> bhi)
    if translit.endswith("ee"):
        translit = translit[:-2] + "i"
    # 'aa' at the end of common verb stems is often single 'a'
    if translit.endswith("aa") and len(translit) > 3:
        translit = translit[:-1]

    return prefix + translit + suffix

def devanagari_to_hinglish(text):
    """
    Converts mixed Hindi/Devanagari text into natural Hinglish (Roman script).
    English words remain untouched.
    """
    if not text or not is_devanagari(text):
        return text

    words = text.split()
    converted = [transliterate_word(w) for w in words]
    return " ".join(converted)
