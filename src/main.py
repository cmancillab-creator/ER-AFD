#!/usr/bin/env python3
import sys
from automata import compile_nfa,determinize,describe_nfa,describe_dfa,evaluate,SyntaxErrorER

def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    if len(argv)!=2:
        print('Uso: er-afd <ER> <cadena>\nEjemplo: er-afd "(a|b)*abb" "aabb"',file=sys.stderr)
        return 2
    try:
        nfa=compile_nfa(argv[0]); dfa=determinize(nfa)
    except SyntaxErrorER as exc:
        print(f'Error de expresión regular: {exc}',file=sys.stderr)
        return 2
    print(describe_nfa(nfa))
    print()
    print(describe_dfa(dfa))
    print('\nANÁLISIS DE ENTRADA')
    accepted,trace=evaluate(dfa,argv[1])
    for line in trace: print(line)
    print('Cadena aceptada' if accepted else 'Cadena rechazada')
    return 1 if accepted else 0

if __name__=='__main__':
    sys.exit(main())
