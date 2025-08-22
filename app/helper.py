import re

def wrap_preeti_in_sentence(input_text):
    """
    Converts:
    Topic + です + Comment (gfd + です + l6Kk0fL)
    to:
    Topic + です + Comment
    (<font face="Preeti font  SDF">gfd</font> + です + <font face="Preeti font  SDF">l6Kk0fL</font>)
    Handles any number of parts dynamically.
    """
    match = re.search(r'\((.*?)\)', input_text)
    if not match:
        return f'<font="Preeti font SDF">{input_text}</font>'

    inner = match.group(1)
    # Split by '+'
    parts = [p.strip() for p in inner.split('+')]
    wrapped_parts = []
    for part in parts:
        # Heuristic: Preeti code is likely ASCII (not Japanese or Devanagari)
        # You can adjust this check as needed
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




def quiz_question_wrapper(text):
    """
    Wraps only the Preeti code (everything after the Japanese word) in a font tag, not the Japanese word (e.g., ‘です’).
    Example:
        ‘です’ sf] ;xL k|of]u 5fGg'xf]: :
    becomes:
        ‘です’ <font face="Preeti font SDF">sf] ;xL k|of]u 5fGg'xf]: :</font>
    """
    match = re.match(r"(‘.+?’)\s+(.+)", text)
    if match:
        jp = match.group(1)
        preeti = match.group(2)
        return f"{jp} <font face=\"Preeti font SDF\">{preeti}</font>"