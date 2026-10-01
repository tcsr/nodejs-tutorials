"""Syntax highlighting for ReportLab code blocks (Pygments -> XPreformatted markup)."""
import re
from pygments import lex
from pygments.lexers import TypeScriptLexer, BashLexer, JsonLexer, DockerLexer
from pygments.token import (Keyword, Name, String, Comment, Number, Operator,
                            Literal, Generic)

# GitHub-light palette
STYLE = [
    (Comment,               ('#6e7781', 'i')),
    (Keyword.Type,          ('#953800', '')),
    (Keyword,               ('#cf222e', '')),
    (Name.Builtin,          ('#953800', '')),
    (Name.Function,         ('#8250df', '')),
    (Name.Class,            ('#953800', '')),
    (Name.Decorator,        ('#8250df', '')),
    (Name.Tag,              ('#116329', '')),
    (Name.Attribute,        ('#0550ae', '')),
    (Name.Variable,         ('#953800', '')),
    (Name.Constant,         ('#0550ae', '')),
    (String,                ('#0a3069', '')),
    (Number,                ('#0550ae', '')),
    (Literal,               ('#0550ae', '')),
    (Operator.Word,         ('#cf222e', '')),
    (Generic.Prompt,        ('#6e7781', '')),
]

_BASH_START = re.compile(
    r'^(#|\$ |npm |npx |curl |temporal |mkdir |cd |brew |node |docker |git |open |'
    r'[A-Z_]+=|src/|[\w.-]+/\s*$|tasks-api/|temporal-orders/)')


def detect(src: str):
    first = next((ln.strip() for ln in src.splitlines() if ln.strip()), '')
    if first.startswith('FROM '):
        return DockerLexer()
    if first.startswith('{') or first.startswith('"scripts"'):
        return JsonLexer()
    if first.startswith('//') or first.startswith('import ') or first.startswith('export '):
        return TypeScriptLexer()
    if _BASH_START.match(first):
        return BashLexer()
    return TypeScriptLexer()


def _style_for(ttype):
    for base, style in STYLE:
        if ttype in base:
            return style
    return None


def _esc(t: str) -> str:
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def highlight(src: str) -> str:
    """Return XPreformatted markup for src with colored tokens."""
    out = []
    for ttype, value in lex(src, detect(src)):
        text = _esc(value)
        st = _style_for(ttype)
        if not st or not value.strip():
            out.append(text)
            continue
        color, flag = st
        # apply per line so markup never spans a newline (keeps page splits clean)
        parts = text.split('\n')
        styled = []
        for part in parts:
            if part:
                part = f'<font color="{color}">{part}</font>'
                if flag == 'i':
                    part = f'<i>{part}</i>'
            styled.append(part)
        out.append('\n'.join(styled))
    result = ''.join(out)
    return result[:-1] if result.endswith('\n') and not src.endswith('\n') else result
