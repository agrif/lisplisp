from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from pypy.rlib.parsing.parsing import ParseError, Rule

import os
import os.path

from .types import Cell, Symbol, String, Integer, Float

BNF_RULES_FILE = os.path.join(os.path.dirname(__file__), 'grammar.txt')

try:
    with open(BNF_RULES_FILE, 'r') as f:
        t = f.read()
    regexs, rules, toAST = parse_ebnf(t)
except ParseError, e:
    print e.nice_error_message(filename=BNF_RULES_FILE, source=t)
    raise

parsefunc = make_parse_function(regexs, rules, eof=True)

string_escape_table = {
    r'\\' : '\\',
    r'\"' : '\"',
    r'\a' : '\a',
    r'\b' : '\b',
    r'\f' : '\f',
    r'\n' : '\n',
    r'\r' : '\r',
    r'\t' : '\t',
    r'\v' : '\v',
}

def parse_string(s):
    result = ""
    i = 1
    while i < len(s) - 1:
        done = False
        if s[i] == '\\':
            key = '\\' + s[i + 1]
            if key in string_escape_table:
                result += string_escape_table[key]
                i += len(key)
                done = True
            if key == r'\x':
                for j in range(256):
                    test_escape = r'\x%x%x' % (j // 16, j % 16)
                    if s[i:].startswith(test_escape):
                        result += chr(j)
                        i += 4
                        done = True
        if not done:
            result += s[i]
            i += 1
    return result

def ast_to_types(ast):
    symbol = ast.symbol
    if symbol == 'valuelist':
        if len(ast.children) == 2:
            return Cell(ast_to_types(ast.children[0]), ast_to_types(ast.children[1]))
        elif len(ast.children) == 1:
            return Cell(ast_to_types(ast.children[0]))
        else:
            raise RuntimeError("too many children for 'valuelist' AST")
    elif symbol == 'INTEGER':
        return Integer(int(ast.additional_info))
    elif symbol == 'FLOAT':
        return Float(float(ast.additional_info))
    elif symbol == 'SYMBOL':
        return Symbol(ast.additional_info)
    elif symbol == 'STRING':
        parsed_string = parse_string(ast.additional_info)
        return String(parsed_string)
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
