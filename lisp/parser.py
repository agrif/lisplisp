from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from pypy.rlib.parsing.parsing import ParseError, Rule

import os
import os.path

from .types import Cell, Symbol

BNF_RULES_FILE = os.path.join(os.path.dirname(__file__), 'grammar.txt')

try:
    with open(BNF_RULES_FILE, 'r') as f:
        t = f.read()
    regexs, rules, toAST = parse_ebnf(t)
except ParseError, e:
    print e.nice_error_message(filename=BNF_RULES_FILE, source=t)
    raise

parsefunc = make_parse_function(regexs, rules, eof=True)

def ast_to_types(ast):
    symbol = ast.symbol
    if symbol == 'valuelist':
        if len(ast.children) == 2:
            return Cell(ast_to_types(ast.children[0]), ast_to_types(ast.children[1]))
        elif len(ast.children) == 1:
            return Cell(ast_to_types(ast.children[0]))
        else:
            raise RuntimeError("too many children for 'valuelist' AST")
    elif symbol == 'SYMBOL':
        return Symbol(ast.additional_info)
    elif symbol == 'prefixed':
        if len(ast.children) == 2:
           prefix = ast.children[0].additional_info
           if prefix == "'":
               long_prefix = 'quote'
           elif prefix == "`":
               long_prefix = 'quasiquote'
           elif prefix == ",":
               long_prefix = 'unquote'
           elif prefix == ',@':
               long_prefix = 'unquote-splicing'
           else:
               raise RuntimeError("unknown prefix: " + prefix)
           return Cell(Symbol(long_prefix), Cell(ast_to_types(ast.children[1])))
        else:
           raise RuntimeError("too many children for 'prefixed' AST")
        return None
    elif symbol == 'cell':
        if len(ast.children) == 1:
            return Cell(ast_to_types(ast.children[0]))
        elif len(ast.children) == 2:
            return Cell(ast_to_types(ast.children[0]), ast_to_types(ast.children[1]))
        else:
            raise RuntimeError("too many children for 'cell' AST")
    elif symbol == 'nil':
        return None
    else:
        raise RuntimeError("unhandled AST")

def parse(code):
    t = parsefunc(code)
    ast = toAST().transform(t)
    return ast_to_types(ast)
