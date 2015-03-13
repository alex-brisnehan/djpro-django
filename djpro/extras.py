# -*- coding: utf-8 -*-
import re

# default unicode character mapping ( you may not see some chars, leave as is )
char_map = {u'À': 'A', u'Á': 'A', u'Â': 'A', u'Ã': 'A', u'Ä': 'A', u'Å': 'A', u'Æ': 'AE', u'Ā': 'A', u'Ą': 'A', u'Ă': 'A', u'Ç': 'C', u'Ć': 'C', u'Č': 'C', u'Ĉ': 'C', u'Ċ': 'C', u'Ď': 'D', u'Đ': 'D', u'È': 'E', u'É': 'E', u'Ê': 'E', u'Ë': 'E', u'Ē': 'E', u'Ę': 'E', u'Ě': 'E', u'Ĕ': 'E', u'Ė': 'E', u'Ĝ': 'G', u'Ğ': 'G', u'Ġ': 'G', u'Ģ': 'G', u'Ĥ': 'H', u'Ħ': 'H', u'Ì': 'I', u'Í': 'I', u'Î': 'I', u'Ï': 'I', u'Ī': 'I', u'Ĩ': 'I', u'Ĭ': 'I', u'Į': 'I', u'İ': 'I', u'Ĳ': 'IJ', u'Ĵ': 'J', u'Ķ': 'K', u'Ľ': 'L', u'Ĺ': 'L', u'Ļ': 'L', u'Ŀ': 'L', u'Ł': 'L', u'Ñ': 'N', u'Ń': 'N', u'Ň': 'N', u'Ņ': 'N', u'Ŋ': 'N', u'Ò': 'O', u'Ó': 'O', u'Ô': 'O', u'Õ': 'O', u'Ö': 'O', u'Ø': 'O', u'Ō': 'O', u'Ő': 'O', u'Ŏ': 'O', u'Œ': 'OE', u'Ŕ': 'R', u'Ř': 'R', u'Ŗ': 'R', u'Ś': 'S', u'Ş': 'S', u'Ŝ': 'S', u'Ș': 'S', u'Š': 'S', u'Ť': 'T', u'Ţ': 'T', u'Ŧ': 'T', u'Ț': 'T', u'Ù': 'U', u'Ú': 'U', u'Û': 'U', u'Ü': 'U', u'Ū': 'U', u'Ů': 'U', u'Ű': 'U', u'Ŭ': 'U', u'Ũ': 'U', u'Ų': 'U', u'Ŵ': 'W', u'Ŷ': 'Y', u'Ÿ': 'Y', u'Ý': 'Y', u'Ź': 'Z', u'Ż': 'Z', u'Ž': 'Z', u'à': 'a', u'á': 'a', u'â': 'a', u'ã': 'a', u'ä': 'a', u'ā': 'a', u'ą': 'a', u'ă': 'a', u'å': 'a', u'æ': 'ae', u'ç': 'c', u'ć': 'c', u'č': 'c', u'ĉ': 'c', u'ċ': 'c', u'ď': 'd', u'đ': 'd', u'è': 'e', u'é': 'e', u'ê': 'e', u'ë': 'e', u'ē': 'e', u'ę': 'e', u'ě': 'e', u'ĕ': 'e', u'ė': 'e', u'ƒ': 'f', u'ĝ': 'g', u'ğ': 'g', u'ġ': 'g', u'ģ': 'g', u'ĥ': 'h', u'ħ': 'h', u'ì': 'i', u'í': 'i', u'î': 'i', u'ï': 'i', u'ī': 'i', u'ĩ': 'i', u'ĭ': 'i', u'į': 'i', u'ı': 'i', u'ĳ': 'ij', u'ĵ': 'j', u'ķ': 'k', u'ĸ': 'k', u'ł': 'l', u'ľ': 'l', u'ĺ': 'l', u'ļ': 'l', u'ŀ': 'l', u'ñ': 'n', u'ń': 'n', u'ň': 'n', u'ņ': 'n', u'ŉ': 'n', u'ŋ': 'n', u'ò': 'o', u'ó': 'o', u'ô': 'o', u'õ': 'o', u'ö': 'o', u'ø': 'o', u'ō': 'o', u'ő': 'o', u'ŏ': 'o', u'œ': 'oe', u'ŕ': 'r', u'ř': 'r', u'ŗ': 'r', u'ś': 's', u'š': 's', u'ť': 't', u'ù': 'u', u'ú': 'u', u'û': 'u', u'ü': 'u', u'ū': 'u', u'ů': 'u', u'ű': 'u', u'ŭ': 'u', u'ũ': 'u', u'ų': 'u', u'ŵ': 'w', u'ÿ': 'y', u'ý': 'y', u'ŷ': 'y', u'ż': 'z', u'ź': 'z', u'ž': 'z', u'ß': 'B', u'ſ': 'f', u'Α': 'A', u'Β': 'B', u'Δ': 'D', u'Ε': 'E', u'Ζ': 'Z', u'Η': 'H',  u'Ι': 'I', u'Κ': 'K', u'Μ': 'M', u'Ν': 'N', u'Ο': 'O', u'Ρ': 'P', u'Σ': 'E', u'Τ': 'T', u'Υ': 'Y', u'Χ': 'X', u'α': 'a', u'β': 'b', u'γ': 'y', u'δ': 'd', u'ε': 'e',  u'η': 'n', u'ι': 'i', u'κ': 'k', u'μ': 'u', u'ν': 'v', u'ο': 'o', u'ρ': 'p', u'τ': 't', u'υ': 'u', u'χ': 'x', u'А': 'A', u'Б': 'B', u'В': 'B', u'Е': 'E', u'Ё': 'E', u'Ж': 'X', u'З': 'E', u'И': 'N', u'Й': 'N', u'К': 'K', u'М': 'M', u'Н': 'H', u'О': 'O', u'Р': 'P', u'С': 'C', u'Т': 'T', u'У': 'Y', u'Х': 'X', u'Э': 'E', u'Я': 'R', u'а': 'A', u'б': 'B', u'в': 'b', u'е': 'E', u'ё': 'E', u'ж': 'x', u'з': 'e', u'и': 'n', u'й': 'n', u'к': 'K', u'м': 'M', u'н': 'N', u'о': 'O', u'р': 'p', u'с': 'c', u'т': 'T', u'у': 'y', u'х': 'x', u'э': 'E', u'я': 'r', u'Ъ': 'b', u'ъ': 'b', u'Ь': 'b', u'ь': 'b', u'ð': 'd', u'Ð': 'D', u'þ': 'p', u'Þ': 'P', u'“': '"', u'”': '"', u"‘": "'", u"’": "'", u'¡': '!', u'¿': '?' }

def replace_char(m):
    char = m.group()
    if char_map.has_key(char):
        return char_map[char]
    else:
        return char
        
def ugam(value, overwrite_char_map={}):
    """
    Ugly American. 
    For the violently monologuist. 
    
    Orgionally based on High Fidelity slugify except that 
    ß → B and Þ → P instead of the phonetic mapping. This
    will piss off any German and Icelandic speakers, but 
    that’s the price you pay for being an ulgy american.
    
    Examples :
    
    >>> ugam("C'est déjà l'été.")
    "C'est deja l'ete."
    """
    
    # overwrite chararcter mapping
    char_map.update(overwrite_char_map)

    # try to replace chars
    value = re.sub(r'[^a-zA-Z0-9\s\-]{1}', replace_char, value)
    
    return value


def sans_the(text):
    """
    To allow title sorting.
    
    >>> sans_the("The Title")
    'Title, The'
    >>> sans_the(u"a title")
    u'title, a'
    """
    test = text.lower()
    if test[0:2] == 'a ':
        return text[2:] + ', ' + text[0:1]
    if test[0:3] == 'an ':
        return text[3:] + ', ' + text[0:2]
    if test[0:4] == 'the ':
        return text[4:] + ', ' + text[0:3]
    return text
