from dataclasses import dataclass, field
from collections import deque

ASCII = frozenset(range(128))
EPS = 'ε'

class SyntaxErrorER(ValueError):
    pass

@dataclass(frozen=True)
class Token:
    kind: str
    label: str = ''
    chars: frozenset = frozenset()


def _literal(ch):
    code = ord(ch)
    if code >= 128:
        raise SyntaxErrorER('Solo se admiten caracteres ASCII (ε es la excepción sintáctica).')
    return Token('ATOM', ch if ch.isprintable() else f'\\h{code:02X}', frozenset({code}))


def tokenize(expr):
    result = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c == '\\':
            if i + 1 >= len(expr):
                raise SyntaxErrorER('Escape incompleto al final de la expresión.')
            x = expr[i+1]
            mapping = {'N': ('\\N', range(48,58)), 'A': ('\\A', range(65,91)),
                       'a': ('\\a', range(97,123)), 'z': ('\\z', list(range(65,91)) + list(range(97,123)))}
            if x == 'h':
                if i+3 >= len(expr):
                    raise SyntaxErrorER('\\h requiere dos dígitos hexadecimales.')
                try:
                    value = int(expr[i+2:i+4],16)
                except ValueError:
                    raise SyntaxErrorER('Código hexadecimal incorrecto.') from None
                if value > 127:
                    raise SyntaxErrorER('\\h solo admite códigos ASCII 00–7F.')
                result.append(Token('ATOM', f'\\h{value:02X}', frozenset({value})))
                i += 4
                continue
            if x in mapping:
                name, values = mapping[x]
                result.append(Token('ATOM',name,frozenset(values)))
            else:
                result.append(_literal(x))
            i+=2
            continue
        if c == '[':
            start = i
            i+=1
            negated = i < len(expr) and expr[i] == '^'
            if negated: i+=1
            vals = set()
            count = 0
            while i < len(expr) and expr[i] != ']':
                if expr[i] == '\\':
                    if i+1 >= len(expr): raise SyntaxErrorER('Escape incompleto en conjunto.')
                    ch = expr[i+1]; i+=2
                else:
                    ch = expr[i]; i+=1
                if ord(ch)>=128: raise SyntaxErrorER('Conjuntos limitados a ASCII.')
                if i < len(expr)-1 and expr[i]=='-' and expr[i+1]!=']':
                    i+=1
                    if expr[i]=='\\' and i+1<len(expr):
                        end=expr[i+1]; i+=2
                    else:
                        end=expr[i]; i+=1
                    if ord(end)>=128 or ord(end)<ord(ch):
                        raise SyntaxErrorER('Rango inválido en conjunto.')
                    vals.update(range(ord(ch),ord(end)+1))
                else:
                    vals.add(ord(ch))
                count+=1
            if i == len(expr): raise SyntaxErrorER('Falta cerrar el conjunto ].')
            if count == 0: raise SyntaxErrorER('Conjunto vacío no permitido.')
            i+=1
            chars = ASCII.difference(vals) if negated else frozenset(vals)
            result.append(Token('ATOM', expr[start:i], frozenset(chars)))
            continue
        if c in '()*|':
            result.append(Token(c)); i+=1; continue
        if c == EPS:
            result.append(Token('EPS', EPS)); i+=1; continue
        if c == '.':
            result.append(Token('ATOM','.',ASCII)); i+=1; continue
        result.append(_literal(c)); i+=1
    return result

class Parser:
    def __init__(self, tokens):
        self.tokens=tokens; self.i=0

    def peek(self):
        return self.tokens[self.i].kind if self.i<len(self.tokens) else None

    def pop(self):
        t=self.tokens[self.i]; self.i+=1; return t

    def parse(self):
        if not self.tokens: raise SyntaxErrorER('La expresión está vacía.')
        tree=self.union()
        if self.peek() is not None:
            raise SyntaxErrorER('Operador o paréntesis inesperado.')
        return tree

    def union(self):
        node=self.concat()
        while self.peek()=='|':
            self.pop(); node=('or',node,self.concat())
        return node

    def concat(self):
        if self.peek() not in ('ATOM','EPS','('):
            raise SyntaxErrorER('Se esperaba un símbolo, ε o un grupo.')
        node=self.repeat()
        while self.peek() in ('ATOM','EPS','('):
            node=('cat',node,self.repeat())
        return node

    def repeat(self):
        if self.peek()=='(':
            self.pop(); node=self.union()
            if self.peek()!=')': raise SyntaxErrorER('Paréntesis sin cerrar.')
            self.pop()
        else:
            node=('atom',self.pop())
        if self.peek()=='*':
            self.pop(); node=('star',node)
            if self.peek()=='*': raise SyntaxErrorER('Operador * repetido.')
        return node

@dataclass
class NFA:
    transitions: dict=field(default_factory=dict)
    start: int=0
    accept: int=0
    count: int=0
    symbols: list=field(default_factory=list)
    epsilon_explicit: bool=False
    symbol_order: list=field(default_factory=list)

    def new(self):
        q=self.count; self.count+=1; self.transitions[q]=[]; return q

    def edge(self,a,t,b):
        self.transitions[a].append((t,b))


def compile_nfa(expr):
    tokens=tokenize(expr)
    root=Parser(tokens).parse()
    n=NFA()
    n.epsilon_explicit=any(t.kind=='EPS' for t in tokens)
    n.symbol_order=[]
    for t in tokens:
        if t.kind in ('ATOM','EPS') and t.label not in n.symbol_order:
            n.symbol_order.append(t.label)
    for t in tokens:
        if t.kind=='ATOM' and t not in n.symbols: n.symbols.append(t)
    def build(node):
        kind=node[0]
        if kind=='atom':
            a=n.new(); b=n.new(); t=node[1]
            n.edge(a, None if t.kind=='EPS' else t,b)
            return a,b
        if kind=='cat':
            a,b=build(node[1]); c,d=build(node[2]); n.edge(b,None,c); return a,d
        if kind=='or':
            a=n.new(); b,c=build(node[1]); d,e=build(node[2]); z=n.new()
            n.edge(a,None,b); n.edge(a,None,d); n.edge(c,None,z); n.edge(e,None,z)
            return a,z
        if kind=='star':
            a=n.new(); b,c=build(node[1]); z=n.new()
            n.edge(a,None,b); n.edge(a,None,z); n.edge(c,None,b); n.edge(c,None,z)
            return a,z
        raise AssertionError(kind)
    n.start,n.accept=build(root)
    order=[n.start]+[x for x in range(n.count) if x!=n.start]
    remap={old:i for i,old in enumerate(order)}
    n.transitions={remap[k]:[(t,remap[v]) for t,v in values] for k,values in n.transitions.items()}
    n.accept=remap[n.accept]; n.start=0
    return n

def closure(n,states):
    found=set(states); pending=list(states)
    while pending:
        s=pending.pop()
        for token,dest in n.transitions[s]:
            if token is None and dest not in found:
                found.add(dest); pending.append(dest)
    return frozenset(found)


def _ascii_label(chars):
    if len(chars)==128: return '.'
    if len(chars)==1:
        v=next(iter(chars)); return chr(v) if 32<=v<=126 and chr(v) not in '|\\' else f'\\h{v:02X}'
    intervals=[]; vals=sorted(chars); first=prev=vals[0]
    for v in vals[1:]:
        if v==prev+1: prev=v
        else:
            intervals.append((first,prev)); first=prev=v
    intervals.append((first,prev))
    def printable(v):
        ch=chr(v)
        return ch if 33<=v<=126 and ch not in '[]\\-' else f'\\h{v:02X}'
    return '['+''.join(printable(a) if a==b else f'{printable(a)}-{printable(b)}' for a,b in intervals)+']'

@dataclass
class DFA:
    states: list
    transitions: dict
    finals: set
    alphabet: list

    def step(self,state,char):
        code=ord(char)
        for idx,(_,chars) in enumerate(self.alphabet):
            if code in chars:
                return self.transitions.get((state,idx))
        return None


def determinize(n):
    groups={}
    for code in range(128):
        signature=tuple(code in t.chars for t in n.symbols)
        if any(signature): groups.setdefault(signature,set()).add(code)
    classes=[]
    for signature,values in groups.items():
        chars=frozenset(values)
        original=next((t.label for t in n.symbols if t.chars==chars),None)
        classes.append((original if original is not None else _ascii_label(chars),chars))
    classes.sort(key=lambda pair:min(i for i,t in enumerate(n.symbols) if pair[1]&t.chars))
    start=closure(n,{n.start}); states=[start]; ids={start:0}; trans={}; finals=set(); pending=deque([start])
    while pending:
        current=pending.popleft(); cid=ids[current]
        if n.accept in current: finals.add(cid)
        for index,(_,chars) in enumerate(classes):
            representative=next(iter(chars))
            moves={dst for q in current for t,dst in n.transitions[q] if t is not None and representative in t.chars}
            if not moves: continue
            target=closure(n,moves)
            if target not in ids:
                ids[target]=len(states); states.append(target); pending.append(target)
            trans[(cid,index)]=ids[target]
    return DFA(states,trans,finals,classes)


def _format_set(names): return '{'+','.join(names)+'}'

def describe_nfa(n):
    lines=['AFND', 'Q='+_format_set(f'q{i}' for i in range(n.count))]
    symbols=list(n.symbol_order)
    if EPS not in symbols: symbols.append(EPS)
    lines+=['Σ='+_format_set(symbols), 'Inicial=q0', f'F={{q{n.accept}}}']
    for src in range(n.count):
        grouped={}
        for t,dst in n.transitions[src]:
            grouped.setdefault(EPS if t is None else t.label,set()).add(dst)
        for label,dests in grouped.items():
            lines.append(f'q{src}|{label}|'+_format_set(f'q{x}' for x in sorted(dests)))
    return '\n'.join(lines)

def describe_dfa(d):
    lines=['AFD', 'Q='+_format_set(f'Q{i}' for i in range(len(d.states))),
           'Σ='+_format_set(label for label,_ in d.alphabet), 'Inicial=Q0',
           'F='+_format_set(f'Q{i}' for i in sorted(d.finals))]
    for src in range(len(d.states)):
        for ix,(label,_) in enumerate(d.alphabet):
            if (src,ix) in d.transitions:
                lines.append(f'Q{src}|{label}|Q{d.transitions[src,ix]}')
    return '\n'.join(lines)

def evaluate(d,text):
    state=0; trace=[]
    for char in text:
        target=d.step(state,char)
        symbol=char if 32<=ord(char)<=126 else f'\\h{ord(char):02X}'
        trace.append(f'Q{state}|{symbol}|'+(f'Q{target}' if target is not None else '∅'))
        if target is None:
            return False,trace
        state=target
    return state in d.finals, trace
