import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automata import compile_nfa,determinize,evaluate,SyntaxErrorER

class ConversionTests(unittest.TestCase):
    def check(self,er,accepted,rejected):
        d=determinize(compile_nfa(er))
        for text in accepted: self.assertTrue(evaluate(d,text)[0],(er,text))
        for text in rejected: self.assertFalse(evaluate(d,text)[0],(er,text))
    def test_concat(self): self.check('ab',['ab'],['','a','b','abc','ba'])
    def test_union(self): self.check('a|b',['a','b'],['','ab','c'])
    def test_star(self): self.check('a*',['','a','aaa'],['b','ab'])
    def test_complex(self): self.check('(a|b)*abb',['abb','aabb','babb','abababb'],['','ab','aaba','bbba'])
    def test_epsilon(self): self.check('ε|a',['','a'],['b','aa'])
    def test_class(self): self.check('[a-c][0-2]',['a0','b1','c2'],['d0','a3','aa'])
    def test_negative(self): self.check('[^abc]',['d','X','4',' '],['a','b','c','','dd'])
    def test_dot(self): self.check('a.b',['acb','a b','a0b'],['ab','acbb'])
    def test_escapes(self): self.check(r'\*\N\h41',['*0A','*9A'],['*aA','*0B'])
    def test_letters(self): self.check(r'\A\a\z',['AbZ','AaB'],['aaa','AA1'])
    def test_whitespace(self): self.check(r'hola\ mundo',['hola mundo'],['holamundo'])
    def test_escaped_backslash(self): self.check('\\\\',['\\'],['','a'])
    def test_overlap(self): self.check('(a|[a-z])b',['ab','zb'],['Ab','a'])
    def test_ascii_hex(self): self.check(r'\h20',[' '],['','a'])
    def test_invalid(self):
        for expr in ['', 'a|','|a','(ab','[a-','a**','a\\',r'\hGG','[]','a)b']:
            with self.subTest(expr=expr),self.assertRaises(SyntaxErrorER): compile_nfa(expr)

if __name__=='__main__': unittest.main()
