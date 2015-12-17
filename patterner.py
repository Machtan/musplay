# encoding: utf-8
# Created by Jakob Lautrup Nysom @ Thursday October 29th 2015
import sys
import os
import re


def reg(pat):
    return re.compile(pat, re.X) # Verbose: whitespace is ignored


_BRACE = re.compile(r"(?:\\\\)* (?<!\\) (\{ ([0-9]+,?(?:[0-9]+)?)? \})", re.X)
def escape_braces(string):
    parts = []
    start = 0
    for match in _BRACE.finditer(string):
        parts.append(string[start : match.start()])
        parts.append("{{{}}}".format(match.group()))
        start = match.end()
    
    if start == 0:
        return string
    
    if start != len(string):
        parts.append(string[start:])
        
    return "".join(parts)
        
    
class Patterner():
    """A simple pattern combiner for easier regex combination.
    any previously defined pattern will be mapped into new patterns.
    Ex:
    p = Patterner()
    p.REGNUM = r"[0-9]+ (?:_[0-9]+)*"
    p.SIGN = r"\+ | \-"
    p.EXPONENT = r"e{SIGN}? {REGNUM}"
    """
    def __init__(self):
        self._dict = dict()
    
    def __getattr__(self, key):
        return self._dict[key]
    
    def __setattr__(self, key, val):
        if key.startswith("_"):
            super().__setattr__(key, val)
        else:
            pat = escape_braces("(?:{})".format(val))
            self._dict[key] = pat.format(**self._dict)
    

def main(args=sys.argv[1:]):
    p = Patterner()
    p.REGNUM = r"[0-9]+ (?:_[0-9]+)*"
    p.SIGN = r"\+ | \-"
    p.EXPONENT = r"e{SIGN}? {REGNUM}"
    p.INTEGER = r"(?P<integer>{SIGN}? {REGNUM})"
    p.FLOAT = r"""(?P<float>
    {SIGN}? {REGNUM} 
    (?:{SIGN}? {REGNUM}\.{REGNUM}{EXPONENT}? | {EXPONENT}))"""
    p.NUMBER = r"({FLOAT} | {INTEGER})"

    p.BARE = r"(?P<bare> (?: [a-zA-Z0-9] | _ | -)+ )"

    _ESCAPED = ["b", "t", "n", "f", "r",'"', "\\", "u[0-9]{4}", "U[0-9]{8}"]
    p.ESCAPED = "|".join(r"\\" + pattern for pattern in _ESCAPED)
    p.BASIC = r"(?P<basic>\"(?:{ESCAPED}|[^\"])*\")"


    INTEGER = reg(p.INTEGER)
    FLOAT = reg(p.FLOAT)
    BASIC = reg(p.BASIC)
    BARE = reg(p.BARE)


if __name__ == "__main__":
    main()


