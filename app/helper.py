import re

def wrap_preeti_in_sentence(input_text):
    """
    Converts:
    Topic + です + Comment (gfd + です + l6Kk0fL)
    to:
    Topic + です + Comment
    (<font face="Preeti font  SDF">gfd</font> + です + <font face="Preeti font  SDF">l6Kk0fL</font>)
    Handles any number of parts dynamically.
    If the text is Japanese only, returns as-is.
    """
    # If Japanese only (Hiragana, Katakana, Kanji), return as-is
    if re.fullmatch(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\s。、・ー「」（）]+', input_text):
        return input_text

    match = re.search(r'\((.*?)\)', input_text)
    if not match:
        return f'<font="Preeti font  SDF">{input_text}</font>'

    inner = match.group(1)
    # Split by '+'
    parts = [p.strip() for p in inner.split('+')]
    wrapped_parts = []
    for part in parts:
        # Heuristic: Preeti code is likely ASCII (not Japanese or Devanagari)
        if re.fullmatch(r'[A-Za-z0-9]+', part):
            wrapped_parts.append(f'<font="Preeti font  SDF">{part}</font>')
        else:
            wrapped_parts.append(part)
    new_inner = ' + '.join(wrapped_parts)
    before_paren = input_text.split('(')[0].strip()
    return f"{before_paren}\n({new_inner})"



def wrap_preeti_before_parenthesis(text):
    """
    Wraps the part before the first '(' in a font tag.
    Example: dfof (Love) -> <font="Preeti font  SDF">dfof</font> (Love)
    """
    match = re.match(r'^([^\(]+)\((.*)\)$', text.strip())
    if match:
        preeti = match.group(1).strip()
        rest = match.group(2).strip()
        return f'<font="Preeti font SDF">{preeti}</font> ({rest})'
    return text



# def quiz_question_wrapper(text):
#     """
#     Wraps Preeti code (ASCII) in a font tag, whether inside quotes or after.
#     Example:
#         'です' sf] ;xL k|of]u 5fGg'xf]: :
#         -> 'です' <font face="Preeti font SDF">sf] ;xL k|of]u 5fGg'xf]: :</font>
#         'cf' sf] ;xL cIf/ 5fGg'xf];
#         -> <font face="Preeti font SDF">'cf' sf] ;xL cIf/ 5fGg'xf];</font>
#     """
#     match = re.match(r"('.+?')\s+(.+)", text)
#     if match:
#         jp = match.group(1)
#         preeti = match.group(2)
#         # Check if the quoted part contains ASCII characters (Preeti code)
#         jp_is_preeti = re.search(r"[A-Za-z0-9]", jp)
#         # Check if the rest is Preeti code
#         preeti_is_preeti = re.fullmatch(r"[A-Za-z0-9\s;\[\]\|\/:5]+", preeti)
        
#         if jp_is_preeti and preeti_is_preeti:
#             # Both parts contain Preeti, wrap the whole thing
#             return f'<font face="Preeti font SDF">{jp} {preeti}</font>'
#         elif preeti_is_preeti:
#             # Only the rest is Preeti, wrap only that part
#             return f'{jp} <font face="Preeti font SDF">{preeti}</font>'
#         else:
#             return text
    
#     # If the whole text is Preeti code (ASCII), wrap it
#     if re.fullmatch(r"['''A-Za-z0-9\s;:\[\]\|\/5]+", text):
#         return f'<font face="Preeti font SDF">{text}</font>'
#     return text


def quiz_question_wrapper(text):
    """
    Wraps Preeti code (ASCII) in a font tag, whether inside quotes or after.
    - If the quoted part contains English letters/digits, wrap the whole line.
    - If the quoted part is Japanese (no English letters/digits), wrap only the part after the quotes.
    """
    # Match quoted part and optional rest
    match = re.match(r"('.*?')\s*(.*)", text)
    # If the whole text appears to be Preeti code (ASCII), wrap it
    if re.search(r"[A-Za-z0-9]", text) and not re.search(r"[ひらがなカタカナ一-龯]", text):
        return f'<font="Preeti font  SDF">{text}</font>'
    
    if match:
        quoted = match.group(1)
        rest = match.group(2)
        
        # Check the content inside the quotes (excluding the quote marks themselves)
        quoted_content = quoted[1:-1]  # Remove the surrounding quotes
        
        # If quoted content has any English letter or digit, wrap whole line
        if re.search(r"[A-Za-z0-9]", quoted_content):
            return f'<font="Preeti font  SDF">{text}</font>'
        else:
            # Only wrap the rest if it exists and looks like Preeti code
            if rest and rest.strip():
                return f'{quoted} <font="Preeti font  SDF">{rest}</font>'
            else:
                return text
    
    
    
    return text