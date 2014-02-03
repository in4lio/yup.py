from __future__ import division

r"""
http://github.com/in4lio/yupp/
 __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \
\ \ \_\/  \_\/  \_\ \ \_\ \
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/
     \/_/      \/_/  \/_/

yup.py -- yupp in python
"""
COPYRIGHT   = 'Copyright (c) 2011, 2013, 2014'
AUTHORS     = 'Vitaly Kravtsov (in4lio@gmail.com)'
DESCRIPTION = 'yet another C preprocessor'
APP         = 'yup.py (yupp)'
VERSION     = '0.6a5'
"""
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

__version__ = VERSION

#   ---- cut here ----

#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *             T O D O             *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *
r"""
https://trello.com/b/531Gf0Iu
"""

#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *      PREPROCESSOR OPTIONS       *
#   *          (DEFAULTS)             *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

#   -----------------------------------
#   PP_SKIP_C_COMMENT
#   -----------------------------------
PP_SKIP_C_COMMENT_HELP = """
don't modify C comments
"""
PP_SKIP_C_COMMENT = True

#   -----------------------------------
#   PP_TRIM_APP_INDENT
#   -----------------------------------
PP_TRIM_APP_INDENT_HELP = """
use an application ($ _ ) indent as a base for all substituting lines,
delete spacing after ($set _ ), ($macro _ ) and ($! _ )
"""
PP_TRIM_APP_INDENT = True

#   -----------------------------------
#   PP_REDUCE_EMPTINESS
#   -----------------------------------
PP_REDUCE_EMPTINESS_HELP = """
reduce number of successive empty lines up to one
"""
PP_REDUCE_EMPTINESS = True


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *            D E B U G            *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *
#   depth - used for debug only.

ERR_SLICE = 64
APP_DELIMIT = ' <-- '

import inspect
import logging
import traceback
import tempfile
import os
import sys
sys.setrecursionlimit( 2 ** 20 )

#   ---------------------------------------------------------------------------
def callee():
    return inspect.getouterframes( inspect.currentframe())[ 1 ][ 1:4 ][ 2 ]

#   ---------------------------------------------------------------------------
def open_log( name, handler, _format ):
    l = logging.getLogger( name )
    handler.setFormatter( logging.Formatter( _format ))
    l.addHandler( handler )
    return l

#   -----------------------------------
#   Logging
#   -----------------------------------

LOG_LEVEL = logging.DEBUG

LOG_FORMAT = '* %(levelname)s * %(message)s'

log = open_log( 'log', logging.StreamHandler( sys.stdout ), LOG_FORMAT )
log.setLevel( LOG_LEVEL )

#   -----------------------------------
#   Trace parsing and evaluation
#   -----------------------------------

TR_NONE  = 0
TR_PARSE = 1
TR_EVAL  = 2
TR_PARSE_EVAL = TR_PARSE + TR_EVAL

#   -- default tracing stages
TR_STAGE = TR_NONE

#   -- write trace to (.trace) file
TR_TO_FILE = True

TR_FORMAT = '%(message)s'

if TR_TO_FILE:
    tr_fn = os.path.splitext( os.path.basename( sys.argv[ 0 ]))[ 0 ]
    try:
        tr_fn = os.path.join( tempfile.gettempdir(), tr_fn + '.trace' )
        h = logging.FileHandler( tr_fn, mode = 'w' )
    except ( OSError, NotImplementedError ):
#       -- e.g. permission denied
        TR_TO_FILE = False

if not TR_TO_FILE:
    h = logging.StreamHandler( sys.stdout )

trace = open_log( 'trace', h, TR_FORMAT )

#   ---------------------------------------------------------------------------
def set_trace( stage ):
    trace.setLevel( logging.INFO if stage else logging.WARNING )
#   -- used for preventing of trace.info() argument calculation
    trace.TRACE = trace.isEnabledFor( logging.INFO )

set_trace( TR_STAGE )
trace.deepest = 0

TR_INDENT = '.'
TR_DELIMIT = ' <--\n'
TR_EVAL_IN = ' E <--\n'
TR_EVAL_ENV = '<< '
TR_EVAL_OUT = ' E -->\n'
TR_SLICE = 64
TR_DEEPEST = 'deepest call - %d'

#   -----------------------------------
#   Traceback exceptions
#   -----------------------------------
TB_NONE   = 0
TB_PYTHON = 1
TB_ALL    = 2

TRACEBACK = TB_PYTHON

#   ---------------------------------------------------------------------------
def _ast_pretty( st ):
    """
    AST string beautifying.
    """
    WRAP = 100
    INDENT = '  '
    indent_l = len( INDENT )
    parenth = {}
    p = {}
    depth = 0
    for i, ch in enumerate( st ):
        if ch in ( ')', ']', '}' ):
            if depth:
                depth -= 1
#               -- opening bracket position
                parenth[ p[ depth ]] = ( i, depth )
#               -- closing bracket position
                parenth[ i ] = ( None, depth )
        else:
            if ch in ( '(', '[', '{' ):
                p[ depth ] = i
                depth += 1
    result = ''
    i = 0
    for b in sorted( parenth ):
        if i <= b:
            e, depth = parenth[ b ]
            if e is None:
#               -- closing bracket
                if i == b:
#                   -- ... only
                    result += INDENT * depth + st[ i : b + 1 ] + '\n'
                else:
                    result += INDENT * ( depth + 1 ) + st[ i : b ] + '\n' + INDENT * depth + st[ b ]  + '\n'
            else:
#               -- opening bracket
                if e - b + ( indent_l * depth ) < WRAP:
#                   -- don't prettify short node
                    b = e
                result += INDENT * depth + st[ i : b + 1 ] + '\n'
            i = b + 1
    result += st[ i: ]
    return result

#   ---------------------------------------------------------------------------
def trim_tailing_whitespace( text, reduce_emptiness = False ):
    """
    Trim tailing white space from each line and
    reduce number of successive empty lines up to one (depends on argument).
    """
#   -----------------------------------
    def _reduce( line ):
        empty = _reduce.empty
        _reduce.empty = not line
        return not empty or not _reduce.empty

#   ---------------
    content = [ x.rstrip() for x in text.splitlines()]
    if reduce_emptiness:
        _reduce.empty = False
        content = filter( _reduce, content )
    return '\n'.join( content ) + '\n'


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *              A S T              *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

#   ---------------------------------------------------------------------------
def _plain( st ):
    return ( '' if st is None else str( st ))

#   -----------------------------------
#   Based on 'str' AST notes
#   -----------------------------------

#   ---------------------------------------------------------------------------
class BASE_STR( str ):
    """
    AST: (abstract node) for strings.
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, str.__repr__( self ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and str.__eq__( self, other )

#   ---------------------------------------------------------------------------
class ATOM( BASE_STR ):
    """
    AST: ATOM( identifier ) <-- id
    """
#   ---------------
    def __eq__( self, other ):
        return isinstance( other, str ) and str.__eq__( self, other )

#   -----------------------------------
    def is_valid_c_id( self ):
        return ( self.find( '-' ) == -1 )

#   ---------------------------------------------------------------------------
class REMARK( BASE_STR ):
    """
    AST: REMARK( remark ) <-- '/*' ... '*/' | '//' ...
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class STR( BASE_STR ):
    """
    AST: STR( string ) <-- "'"..."'" | '"'...'"'
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class PLAIN( BASE_STR ):
    """
    AST: PLAIN( text ) <-- ...
    """
#   -----------------------------------
    def __new__( cls, val, indent = False, trim = False ):
        """
        indent:
            None  - plain text contains only TABs and SPACEs
            str   - the indent at the end of text (before next node) e.g. '\t  ' for 'foo\n\t  '
            False - no indent e.g. for 'foo  '
        """
        obj = BASE_STR.__new__( cls, val )
        obj.indent = indent
        obj.trim = trim
        return obj

#   -----------------------------------
    def __str__( self ):
        st = BASE_STR.__str__( self )

        if not PP_TRIM_APP_INDENT:
            return st

        if self.trim:
#           -- delete spacing after SET or MACRO
            return st.lstrip()

        return st

#   -----------------------------------
    def add_indent( self, indent ):
        if self.indent is not None:
            ln = self.splitlines( True )
            if ord( self[ -1 ]) in ps_EOL:
                ln.append( '' )
            return PLAIN( indent.join( ln )
            , ( indent + self.indent ) if isinstance( self.indent, str ) else self.indent, self.trim )
        else:
            return ( self )

#   -----------------------------------
#   Based on 'list' AST notes
#   -----------------------------------

#   ---------------------------------------------------------------------------
class BASE_LIST( list ):
    """
    AST: (abstract node) for lists.
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, list.__repr__( self ))

#   -----------------------------------
    def __str__( self ):
        return ''.join( map( _plain, self ))

#   ---------------------------------------------------------------------------
class LIST( BASE_LIST ):
    """
    AST: LIST([ form | EMBED( form )]) <-- '(' [ _ | *_ ] ')'
    """
#   ---------------
    pass

#   -----------------------------------
#   Any types based AST nodes
#   -----------------------------------

#   ---------------------------------------------------------------------------
class FLOAT( float ):
    """
    AST: FLOAT( number )
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, float.__repr__( self ))

#   ---------------------------------------------------------------------------
class INT( long ):
    """
    AST: INT( number )
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, long.__repr__( self ))

#   -----------------------------------
#   AST nodes without data
#   -----------------------------------

#   ---------------------------------------------------------------------------
class BASE_MARK( object ):
    """
    AST: (abstract node) for marks.
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s()' % ( self.__class__.__name__ )

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ )

#   ---------------------------------------------------------------------------
class LATE_BOUNDED( BASE_MARK ):
    """
    AST: LATE_BOUNDED <-- '&' id
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class COMMENT( BASE_MARK ):
    """
    AST: COMMENT <-- '($!' ... ')'
    """
#   ---------------
    pass

#   -----------------------------------
#   Caption AST nodes
#   -----------------------------------

#   ---------------------------------------------------------------------------
class BASE_CAP( object ):
    """
    AST: (abstract node) for captions.
    """
#   -----------------------------------
    def __init__( self, ast ):
        self.ast = ast

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, repr( self.ast ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.ast == other.ast )

#   ---------------------------------------------------------------------------
class EVAL( BASE_CAP ):
    """
    AST: EVAL( APPLY ) <-- '($$' ... ')'
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class INFIX( BASE_CAP ):
    """
    AST: INFIX( exp ) <-- '{' ... '}'
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class EMBED( BASE_CAP ):
    """
    AST: EMBED( form ) <-- '*' _
    """
#   ---------------
    pass

#   -----------------------------------
#   Structural AST notes
#   -----------------------------------

#   ---------------------------------------------------------------------------
class TEXT( object ):
    """
    AST: TEXT([ SET | MACRO | APPLY | STR | REMARK | PLAIN ], number, number ) <-- ']' ... '['
    """
#   -----------------------------------
    def __init__( self, ast, pth_sq = 0, pth = 0 ):
        self.ast = ast
        self.depth_pth_sq = pth_sq
        self.depth_pth = pth

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %d, %d)' % ( self.__class__.__name__, repr( self.ast ), self.depth_pth_sq, self.depth_pth )

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.ast == other.ast )

#   ---------------------------------------------------------------------------
class VAR( object ):
    """
    AST: VAR( LATE_BOUNDED | [ ATOM ], ATOM ) <-- id '::' id | '&' id | id
    """
#   -----------------------------------
    def __init__( self, reg, atom ):
        self.reg = reg
        self.atom = atom

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.reg ), repr( self.atom ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.reg == other.reg ) and ( self.atom == other.atom )

#   ---------------------------------------------------------------------------
class APPLY( object ):
    """
    AST: APPLY( form, [ form ], [( ATOM, form )]) <-- '($' ... ')'
    """
#   -----------------------------------
    def __init__( self, fn, args, named ):
        self.fn = fn
        self.args = args
        self.named = named

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.fn ), repr( self.args ), repr( self.named ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.fn == other.fn ) and ( self.args == other.args )
        and ( self.named == other.named ))

#   ---------------------------------------------------------------------------
class SET( object ):
    """
    AST: SET( ATOM | [ ATOM ], form ) <-- '($set' ... ')'
    """
#   -----------------------------------
    def __init__( self, lval, ast ):
        self.lval = lval
        self.ast = ast

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.lval ), repr( self.ast ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.lval == other.lval ) and ( self.ast == other.ast )

#   ---------------------------------------------------------------------------
class MACRO( object ):
    """
    AST: MACRO( ATOM, [ ATOM ], str ) <-- '($macro' ... ')'
    """
#   -----------------------------------
    def __init__( self, name, pars, text ):
        self.name = name
        self.pars = pars
        self.text = text

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.name ), repr( self.pars ), repr( self.text ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.name == other.name ) and ( self.pars == other.pars )
        and ( self.text == other.text ))

#   ---------------------------------------------------------------------------
class EMIT( object ):
    """
    AST: EMIT( ATOM, form ) <-- '($emit' ... ')'
    """
#   -----------------------------------
    def __init__( self, var, ast ):
        self.var = var
        self.ast = ast

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.var ), repr( self.ast ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.var == other.var ) and ( self.ast == other.ast )

#   ---------------------------------------------------------------------------
class LAMBDA( object ):
    """
    AST: LAMBDA([([ ATOM ], ATOM, form )], TEXT | APPLY | LIST | INFIX) <-- [ '\\' _ '..' ] '\\' _ ':' _ '.' '(' ... ')'
    """
#   -----------------------------------
    def __init__( self, bound, l_form ):
        self.bound = bound
        self.l_form = l_form

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.bound ), repr( self.l_form ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.bound == other.bound ) and ( self.l_form == other.l_form )

#   ---------------------------------------------------------------------------
class COND( object ):
    """
    AST: COND( former, former, form ) <-- _ '?' _ '|' _
    """
#   -----------------------------------
    def __init__( self, cond, leg_1, leg_0 ):
        self.cond = cond
        self.leg_1 = leg_1
        self.leg_0 = leg_0

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.cond ), repr( self.leg_1 ), repr( self.leg_0 ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.cond == other.cond ) and ( self.leg_1 == other.leg_1 )
        and ( self.leg_0 == other.leg_0 ))


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *            P A R S E            *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

DIRECTORY = []

#   -----------------------------------
#   Terminal symbols
#   -----------------------------------

import re
from ast import literal_eval

#   ---------------------------------------------------------------------------
def ps_term( _ ):
    """
    ANY ::= [ '\n', '\r', '\t', '\x20'..'\xFF' ];
    string ::= '"' { CHAR YIELD | char_code }0... '"';
    char ::= '\'' { CHAR YIELD | char_code }0... '\'';
    CHAR ::= ANY - EOL - [ '\\', '\t' ];
    char_code ::= '\\n' | '\\r' | '\\t' | '\\\\'
        | '\\' { [ '0'..'7' ] }1..4
        | '\\x' { [ '0'..'9', 'A'..'F', 'a'..'f' ] }1..4;
    EMBED ::= '*';
    """
#   ---------------
    pass

#   ---- EOL
ps_EOL = frozenset([ ord( '\n' ), ord( '\r' )])
#   ---- SPACE | TAB
ps_SPACE = frozenset([ ord( ' ' ), ord( '\t' )])
#   ---- any Roman letter | _
ps_LETTER = frozenset( range( ord( 'a' ), ord( 'z' ) + 1 ) + range( ord( 'A' ), ord( 'Z' ) + 1 ) + [ ord( '_' )])
#   ---- any figure
ps_FIGURE = frozenset( range( ord( '0' ), ord( '9' ) + 1 ) + [ ord( '-' )])
#   ---- any printable character
ps_ANY = frozenset([ ord( '\n' ), ord( '\r' ), ord( '\t' )] + range( ord( ' ' ), 256 ))
#   ---- code mark
ps_CODE = '($code'
l_CODE = len( ps_CODE )
#   ---- code double comma mark
ps_DUALCOMMA = ',,'
l_DUALCOMMA = len( ps_DUALCOMMA )
#   ---- code end mark
ps_DUALSEMI = ';;'
l_DUALSEMI = len( ps_DUALSEMI )
#   ---- infix mark
ps_INFIX = '(${}'
l_INFIX = len( ps_INFIX )
#   ---- set mark
ps_SET = '($set'
l_SET = len( ps_SET )
#   ---- set tag
ps_SET_T = '\\set'
l_SET_T = len( ps_SET_T )
#   ---- import mark
ps_IMPORT = '($import'
l_IMPORT = len( ps_IMPORT )
#   ---- import tag
ps_IMPORT_T = '\\import'
l_IMPORT_T = len( ps_IMPORT_T )
#   ---- quoted mark
ps_QUOTED = '($quoted'
l_QUOTED = len( ps_QUOTED )
#   ---- backquote mark
ps_BQUOTE = '(`'
l_BQUOTE = len( ps_BQUOTE )
#   ---- macro mark
ps_MACRO = '($macro'
l_MACRO = len( ps_MACRO )
#   ---- comment mark
ps_COMMENT = '($!'
l_COMMENT = len( ps_COMMENT )
#   ---- emit mark
ps_EMIT = '($emit'
l_EMIT = len( ps_EMIT )
#   ---- emit tag
ps_EMIT_T = '\\emit'
l_EMIT_T = len( ps_EMIT_T )
#   ---- embed character
ps_EMBED = '*'
#   ---- hexadecimal number
re_HEX = re.compile( r'^[+-]? *0[xX][0-9a-fA-F]+' )
#   ---- octal number
re_OCT = re.compile( r'^[+-]? *0[0-7]+' )
#   ---- decimal number
re_DEC = re.compile( r'^[+-]? *[0-9]+[lL]?' )
#   ---- float
re_FLOAT = re.compile( r'^[+-]? *(?:\d+(?:\.\d+))(?:[eE][+-]?\d+)?' )
#   ---- string literal
re_STR = re.compile( r'^"(?:\\.|[^\\"])*"' )
#   ---- character literal
re_CHR = re.compile( r"^'(?:\\.|[^\\'])*'" )

#   -----------------------------------
#   Grammar rules
#   -----------------------------------

#   ---------------------------------------------------------------------------
def _ord( sou, pos = 0 ):
    return ( ord( sou[ pos ]) if pos < len( sou ) else None )

#   ---------------------------------------------------------------------------
def _while_in( sou, pool ):
    i = 0
    while _ord( sou, i ) in pool:
        i += 1

    return ( sou[ i: ], sou[ :i ] or None )

#   ---------------------------------------------------------------------------
def _unq( st ):
    try:
        return literal_eval( st )
    except:                                                                                                            #pylint: disable=W0702
        return ( st )

#   ---------------------------------------------------------------------------
def _import_source( lib ):
#   TODO: look for libraries into specified directories
    lpath = lib
    if not os.path.isfile( lpath ):
#       -- input file directory
        lpath = os.path.join( yushell.dirname, lib )
        if not os.path.isfile( lpath ):
#           -- yupp lib directory
            if '__file__' in globals():
                lpath = os.path.join( os.path.dirname( os.path.realpath( __file__ )), 'lib', lib )
            else:
#               -- specially for Web Console
                lpath = os.path.join( './lib', lib )
#           -- specified directory
            for dirname in DIRECTORY:
                if os.path.isfile( lpath ):
                    break
                lpath = os.path.join( dirname, lib )
    try:
        f = open( lpath, 'r' )
        try:
            sou = f.read().replace( '\r\n', '\n' )
        finally:
            f.close()
    except:
        e_type, e, tb = sys.exc_info()
        raise e_type, 'ps_import: %s' % ( e ), tb

    return sou

#   ---------------------------------------------------------------------------
def trace__ps_( name, sou, depth ):
    if depth > trace.deepest:
        trace.deepest = depth
    if trace.TRACE:
        trace.info( TR_INDENT * depth + name + TR_DELIMIT + repr( sou[ :TR_SLICE ]))

#   ---------------------------------------------------------------------------
def echo__ps_( fn ):
    def wrapped( sou, depth = 0 ):
        trace__ps_( fn.__name__, sou, depth )
        return fn( sou, depth )

    return wrapped

#   ---------------------------------------------------------------------------
def yuparse( sou ):
    """
    source ::= text EOF;
    """
#   ---------------
    if not sou:
        return TEXT([])

    try:
        text = ps_text( sou, 0 )
        while sou:
            ( sou, ast ) = text.next()

        return ast

    except:                                                                                                            #pylint: disable=W0702
        e_type, e, tb = sys.exc_info()
#   ---- python exception
        arg = e.args[ 0 ] if e.args else None
        if not isinstance( arg, str ) or not arg.startswith( 'ps_' ) and not arg.startswith( 'python' ):
            raise e_type, 'python: %s: %s' % ( e, repr( sou[ :ERR_SLICE ])), tb

#   ---- raised exception
        else:
            raise e_type, e, tb

#   ---------------------------------------------------------------------------
def ps_text( sou, depth = 0 ):
    """
    text ::= ($set (depth_pth_sq depth_pth) 0) {
          set
        | import
        | macro
        | comment
        | application
        | quoted
        | remark
        | YIELD
        | plain
    }0...;
    """
#   ---------------
    ast = []
    depth_pth_sq = depth_pth = 0
    _plain_ret = ''
    while True:
        trace__ps_( 'ps_text', sou, depth )
#   ---- set
        ( sou, leg ) = ps_set( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- import
        ( sou, leg ) = ps_import( sou, depth + 1 )
        if leg is not None:
            if isinstance( leg, TEXT ):
                ast.extend( leg.ast )
            else:
                ast.append( leg )
            continue
#   ---- macro
        ( sou, leg ) = ps_macro( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- comment
        ( sou, leg ) = ps_comment( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- application
        ( sou, leg ) = ps_application( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- quoted
        ( sou, leg ) = ps_quoted( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- remark
        if PP_SKIP_C_COMMENT:
            ( sou, leg ) = ps_remark( sou, depth + 1 )
            if leg is not None:
                ast.append( leg )
                continue
#   ---- YIELD
        yield ( sou, TEXT( ast, depth_pth_sq, depth_pth ))

#   ---- plain
        if sou == _plain_ret and ast:
            ast.pop()
        else:
            plain = ps_plain( sou, depth_pth_sq, depth_pth, None if ast else '', depth + 1 )

        ( sou, leg, depth_pth_sq, depth_pth ) = plain.next()
        ast.append( leg )
        _plain_ret = sou

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_set( sou, depth = 0 ):
    """
    set ::= '($set' ( '(' { atom }1... ')' | atom ) form { '\\set' } ')';
    """
#   ---------------
#   ---- ($set
    if sou[ :l_SET ] != ps_SET:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_SET: ], depth + 1 )
#   ---- (
    if sou[ :1 ] == '(':
#   ---- gap
        ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
        lval = []
        while True:
#   ---- atom
            ( sou, leg ) = ps_atom( sou, depth + 1 )
            if leg is None:
                raise SyntaxError( '%s: name expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

            lval.append( leg )
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- )
            if sou[ :1 ] == ')':
                sou = sou[ 1: ]
                break
    else:
#   ---- atom
        ( sou, leg ) = ps_atom( sou, depth + 1 )
        if leg is None:
            raise SyntaxError( '%s: name expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

        lval = leg
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- form
    ( sou, leg ) = ps_form( sou, depth + 1 )
    if leg is None:
        raise SyntaxError( '%s: form expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- { \set }
    if sou[ :l_SET_T ] == ps_SET_T:
        ( sou, _ ) = ps_gap( sou[ l_SET_T: ], depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

    return ( sou[ 1: ], SET( lval, leg ))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_import( sou, depth = 0 ):
    """
    import ::=  '($import' quoted { '\\import' } ')';
    """
#   ---------------
#   ---- ($import
    if sou[ :l_IMPORT ] != ps_IMPORT:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_IMPORT: ], depth + 1 )
#   ---- quoted
    ( sou, leg ) = ps_quoted( sou, depth + 1 )
    if leg is None:
        raise SyntaxError( '%s: quoted expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- \import
    if sou[ :l_IMPORT_T ] == ps_IMPORT_T:
        ( sou, _ ) = ps_gap( sou[ l_IMPORT_T: ], depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

    return ( sou[ 1: ], yuparse( _import_source( _unq( leg ))))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_macro( sou, depth = 0 ):
    """
    macro ::= '($macro' atom '(' { atom }0... ')' plain ')';
    """
#   ---------------
#   ---- ($macro
    if sou[ :l_MACRO ] != ps_MACRO:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_MACRO: ], depth + 1 )
#   ---- atom
    ( sou, name ) = ps_atom( sou, depth + 1 )
    if name is None:
        raise SyntaxError( '%s: name expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- (
    if sou[ :1 ] != '(':
        raise SyntaxError( '%s: "(" expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
    pars = []
#   ---- )
    while sou[ :1 ] != ')':
#   ---- atom
        ( sou, leg ) = ps_atom( sou, depth + 1 )
        if leg is None:
            raise SyntaxError( '%s: name expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

        pars.append( leg )
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )

    sou = sou[ 1: ]
    if sou[ :1 ] == ')':
        return ( sou[ 1: ], MACRO( name, pars, '' ))

    plain = ps_plain( sou, 0, 0, None, depth + 1 )
    while True:
#   ---- plain
        ( sou, leg, _, depth_pth ) = plain.next()
#   ---- ) & ($eq depth_pth 0)
        if ( sou[ :1 ] == ')' ) and ( depth_pth == 0 ):
            return ( sou[ 1: ], MACRO( name, pars, str( leg )))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_emit( sou, depth = 0 ):
    """
    emit ::= '($emit' variable { form } { '\\emit' } ')';
    """
#   ---------------
#   ---- ($emit
    if sou[ :l_EMIT ] != ps_EMIT:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_EMIT: ], depth + 1 )
#   ---- variable
    ( sou, leg ) = ps_variable( sou, depth + 1 )
    if leg is None:
        raise SyntaxError( '%s: variable expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

    var = leg
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- { form }
    ( sou, leg ) = ps_form( sou, depth + 1 )
    if leg is not None:
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- { \emit }
    if sou[ :l_EMIT_T ] == ps_EMIT_T:
        ( sou, _ ) = ps_gap( sou[ l_EMIT_T: ], depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

    return ( sou[ 1: ], EMIT( var, leg ))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_application( sou, depth = 0 ):
    """
    application ::= '($' function ($set fn ::function::text) { argument }0... { tag } ')';
    argument ::= { name ! '.' | EMBED } form;
    tag ::= name & ($eq fn ::name::atom::text);
    name ::= '\\' atom GAP;
    """
#   ---------------
#   ---- ($
    if sou[ :2 ] != '($':
        return ( sou, None )

#   ---- ($quoted
    if sou[ :l_QUOTED ] == ps_QUOTED:
        return ( sou, None )

#   ---- ($code
    if sou[ :l_CODE ] == ps_CODE:
        return ps_code( sou, depth + 1 )

#   ---- ($emit
    if sou[ :l_EMIT ] == ps_EMIT:
        return ps_emit( sou, depth + 1 )

#   ---- (${}
    if sou[ :l_INFIX ] == ps_INFIX:
        return ps_infix( sou, depth + 1 )

    sou = sou[ 2: ]
#   ---- $
    _eval = sou[ :1 ] == '$'
    if _eval:
        sou = sou[ 1: ]
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- function
    ( sou, func ) = ps_function( sou, depth + 1 )
    if func is None:
        raise SyntaxError( '%s: function expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

#   ---- ($set fn ::function::text)
    fn = ( func.atom if isinstance( func, VAR ) else None )
    named = []
    args = []
#   ---- {
    while True:
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- name -- \
        name = None
        if sou[ :1 ] == '\\':
#   ---- name -- atom
            ( look, name ) = ps_atom( sou[ 1: ], depth + 1 )
            if name is not None:
#   ---- name -- gap
                ( look, _ ) = ps_gap( look, depth + 1 )
#   ---- '.'
                if look[ :1 ] == '.':
#                   -- lambda
                    name = None
                else:
                    sou = look

        if name is not None:
#   ---- ($eq fn ::name::atom::text)
            if fn != name:
#   ---- argument -- name
#   ---- gap
                ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- argument -- form
                ( sou, form ) = ps_form( sou, depth + 1 )
                if form is None:
                    raise SyntaxError( '%s: form expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

                named.append(( name, form ))
            else:
#   ---- }0... tag -- name
                break
        else:
#   ---- argument -- EMBED
            embed = sou[ :1 ] == ps_EMBED
            if embed:
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- argument -- form
            ( sou, form ) = ps_form( sou, depth + 1 )
            if form is not None:
                args.append( EMBED( form ) if embed else form )
            else:
#   ---- }0...
                if embed:
                    raise SyntaxError( '%s: unexpected "*": %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

                break
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

    return ( sou[ 1: ], EVAL( APPLY( func, args, named )) if _eval else APPLY( func, args, named ))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_remark( sou, depth = 0 ):
    """
    remark ::=
          '//' { ANY YIELD }0... >> EOL <<
        | '/*' { ANY YIELD }0... '*/';
    """
#   ---------------
#   ---- //
    if sou[ :2 ] == '//':
        i = 2
        l = len( sou )
        while i < l:
#   ---- EOL
            if ord( sou[ i ]) in ps_EOL:
#               -- leave EOL
                break
            i += 1
        return ( sou[ i: ], REMARK( sou[ :i ]))

#   ---- /*
    elif sou[ :2 ] == '/*':
        i = 2
        l = len( sou ) - 1
        while i < l:
#   ---- */
            if sou[ i:( i + 2 )] == '*/':
                return ( sou[( i + 2 ): ], REMARK( sou[ :( i + 2 )]))

            i += 1

        raise SyntaxError( '%s: unclosed comment: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

    return ( sou, None )

#   ---------------------------------------------------------------------------
def ps_plain( sou, pth_sq, pth, indent, depth = 0 ):
    """
    plain ::= { ANY
        ($switch ::prev::text
            "[" ($inc depth_pth_sq)
            "]" ($dec depth_pth_sq)
            "(" ($inc depth_pth)
            ")" ($dec depth_pth)
        )
        YIELD }1...;
    """
#   ---------------
    depth_pth_sq = pth_sq
    depth_pth = pth
    i = 0
    while True:
        trace__ps_( 'ps_plain', sou[ i: ], depth )

        symbol = _ord( sou, i )
#   ---- ANY
        if symbol is None:
            raise EOFError( '%s: unexpected EOF:' % ( callee()))

        if symbol not in ps_ANY:
            raise SyntaxError( '%s: forbidden character: %s' % ( callee(), repr( sou[ i:( ERR_SLICE + i )])))

#   ---- ($switch ...
        if symbol == ord( '[' ):
            depth_pth_sq += 1
        elif symbol == ord( ']' ):
            if depth_pth_sq:
                depth_pth_sq -= 1
        elif symbol == ord( '(' ):
            depth_pth += 1
        elif symbol == ord( ')' ):
            if depth_pth:
                depth_pth -= 1
#       -- calculate indent
        if symbol in ps_EOL:
            indent = ''
        elif symbol in ps_SPACE:
            if isinstance( indent, str ):
                indent += sou[ i ]
        else:
            indent = False
        i += 1
#   ---- YIELD
        yield ( sou[ i: ], PLAIN( sou[ :i ], indent ), depth_pth_sq, depth_pth )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_function( sou, depth = 0 ):
    """
    function ::= form;
    """
#   ---------------
#   ---- form
    ( sou, leg ) = ps_form( sou, depth + 1 )
    return ( sou, leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_variable( sou, depth = 0 ):
    """
    variable ::= { region '::' }0... atom | '&' late-bounded;
    region ::= atom;
    late-bounded ::= atom;
    """
#   ---------------
#   ---- &
    if sou[ :1 ] == '&':
#   ---- atom
        ( sou, leg ) = ps_atom( sou[ 1: ], depth + 1 )
        if leg is not None:
            return ( sou, VAR( LATE_BOUNDED(), leg ))

        raise SyntaxError( '%s: late-bounded expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

    else:
#   ---- atom
        ( sou, leg ) = ps_atom( sou, depth + 1 )
        if leg is None:
            return ( sou, None )

        region = []
#   ---- ::
        while sou[ :2 ] == '::':
            region.append( leg )
#   ---- atom
            ( sou, leg ) = ps_atom( sou[ 2: ], depth + 1 )
            if leg is None:
                raise SyntaxError( '%s: atom expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

        return ( sou, VAR( region, leg ))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_lambda( sou, depth = 0 ):
    """
    lambda ::= ( { bound }1... | l-bound ) l-form;
    bound ::=  { late '..' }0... name { ':' default } '.' | '\\...';
    late ::= name;
    default :: = form;
    l-bound ::= '\\' '(' variable ')' '.';
    """
#   ---------------
#   ---- \
    if sou[ :1 ] == '\\':
#   ---- (
        if sou[ 1:2 ] == '(':
#   ---- gap
            ( sou, _ ) = ps_gap( sou[ 2: ], depth + 1 )
#   ---- variable
            ( sou, bound ) = ps_variable( sou, depth + 1 )
            if bound is None:
                raise SyntaxError( '%s: variable expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- )
            if sou[ :2 ] != ').':
                raise SyntaxError( '%s: ")." expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

#   ---- gap
            ( sou, _ ) = ps_gap( sou[ 2: ], depth + 1 )
        else:
#   ---- bound
            bound = []
            late = []
            while sou[ :1 ] == '\\':
#   ---- ...
                if sou[ 1:4 ] == '...':
                    if late:
                        raise SyntaxError( '%s: late bound with refuge: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

                    bound.append(( [], ATOM( '...' ), None ))
#   ---- gap
                    ( sou, _ ) = ps_gap( sou[ 4: ], depth + 1 )
                    continue

#   ---- name -- atom
                ( sou, leg ) = ps_atom( sou[ 1: ], depth + 1 )
                if leg is None:
                    raise SyntaxError( '%s: name expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))
#   ---- :
                if sou[ :1 ] == ':':
#   ---- form
                    ( sou, form ) = ps_form( sou[ 1: ], depth + 1 )
                    if form is None:
                        raise SyntaxError( '%s: form expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))
                else:
                    form = None
#   ---- .
                if sou[ :1 ] != '.':
                    raise SyntaxError( '%s: "." expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))
#   ---- ..
                if sou[ :2 ] == '..':
                    late.append( leg )
#   ---- gap
                    ( sou, _ ) = ps_gap( sou[ 2: ], depth + 1 )
                    continue

                bound.append(( late, leg, form ))
                late = []
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )

#   ---- l-form
        ( sou, leg ) = ps_l_form( sou, depth + 1 )
        if leg is None:
            raise SyntaxError( '%s: l-form expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

        return ( sou, LAMBDA( bound, leg ))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_value( sou, depth = 0 ):
    """
    value ::=
          quoted
        | number;
    """
#   ---------------
    ( sou, leg ) = ps_quoted( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

    ( sou, leg ) = ps_number( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_form( sou, depth = 0 ):
    """
    form ::= former { '?' cond { '|' form } };
    cond ::= former;
    """
#   ---------------
#   ---- former
    ( sou, leg ) = ps_former( sou, depth + 1 )
    if leg is not None:
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- ?
        if sou[ :1 ] == '?':
#   ---- gap
            ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- cond
            ( sou, cond ) = ps_former( sou, depth + 1 )
            if cond is None:
                raise SyntaxError( '%s: former expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

            form = None
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- |
            if sou[ :1 ] == '|':
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- form
                ( sou, form ) = ps_form( sou, depth + 1 )
                if form is None:
                    raise SyntaxError( '%s: form expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

            return ( sou, COND( cond, leg, form ))

    return ( sou, leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_former( sou, depth = 0 ):
    """
    former ::=
          variable
        | lambda
        | value
        | l-form;
    """
#   ---------------
#   ---- variable
    ( sou, leg ) = ps_variable( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- lambda
    ( sou, leg ) = ps_lambda( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- value
    ( sou, leg ) = ps_value( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- l-form
    ( sou, leg ) = ps_l_form( sou, depth + 1 )

    return ( sou, leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_l_form( sou, depth = 0 ):
    """
    l-form ::=
          code
        | infix
        | application
        | list;
    """
#   ---------------
#   ---- code
    ( sou, leg ) = ps_code( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- infix
    ( sou, leg ) = ps_infix( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- application
    ( sou, leg ) = ps_application( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- list
    ( sou, leg ) = ps_list( sou, depth + 1 )

    return ( sou, leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_code( sou, depth = 0 ):                                                                                         #pylint: disable=R0911,R0912
    """
    code ::=
          ']' EOL text EOL '['
        | ']' text '[' >> { tag } ')' <<
        | '[' text ']' & ($eq depth_pth_sq 0)
        | ',,' text ( ';;' | >> ( ',,' | { tag } ')' & ($eq depth_pth 0) ) << )
        | '($code' text ')' & ($eq depth_pth 0);
    """
#   ---------------
#   ---- ]
    if sou[ :1 ] == ']':
#   ---- EOL
        ( rest, _ ) = ps_space( sou[ 1: ], depth + 1 )
        ( rest, eol ) = ps_eol( rest, depth + 1 )
        if eol:
            text = ps_text( rest, depth + 1 )
            while True:
#   ---- text
                ( rest, leg ) = text.next()
#   ---- EOL
                ( rest, eol ) = ps_eol( rest, depth + 1 )
                if eol:
                    ( rest, _ ) = ps_space( rest, depth + 1 )
#   ---- [
                    if rest[ :1 ] == '[':
                        return ( rest[ 1: ], leg )

#                   HACK: Highlighting in editor (Textastic) problem (unclosed [ in string) workaround
#                   +
                    if rest[ :2 ] == '\\[':
                        return ( rest[ 2: ], leg )
#                   .
        else:
            text = ps_text( sou[ 1: ], depth + 1 )
            while True:
#   ---- text
                ( rest, leg ) = text.next()
#   ---- [ >>
#               HACK: Highlighting problem workaround
#               -
#               if rest[ :1 ] == '[':
#   ---- gap
#                   ( look, _ ) = ps_gap( rest[ 1: ], depth + 1 )
#               +
                pos = ( 1 if rest[ :1 ] == '[' else 2 if rest[ :2 ] == '\\[' else 0 )
                if pos:
#   ---- gap
                    ( look, _ ) = ps_gap( rest[ pos: ], depth + 1 )
#               .
#   ---- \
                    if look[ :1 ] == '\\':
#   ---- atom
                        ( look, name ) = ps_atom( look[ 1: ], depth + 1 )
                        if name is None:
                            continue
#   ---- gap
                    ( look, _ ) = ps_gap( look, depth + 1 )
#   ---- ) <<
                    if look[ :1 ] == ')':
#                       HACK: Highlighting problem workaround
#                       -
#                       return ( rest[ 1: ], leg )
#                       +
                        return ( rest[ pos: ], leg )
#                       .

#   ---- [
    elif sou[ :1 ] == '[':
        text = ps_text( sou[ 1: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ] & ($eq depth_pth_sq 0)
            if ( rest[ :1 ] == ']' ) and ( leg.depth_pth_sq == 0 ):
                return ( rest[ 1: ], leg )

#   ---- ($code
    elif sou[ :l_CODE ] == ps_CODE:
        text = ps_text( sou[ l_CODE: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ) & ($eq depth_pth 0)
            if ( rest[ :1 ] == ')' ) and ( leg.depth_pth == 0 ):
                return ( rest[ 1: ], leg )

#   ---- ,,
    elif sou[ :l_DUALCOMMA ] == ps_DUALCOMMA:
#       -- (syntactic sugar) e.g. ($f,,code,,code) equals to ($f [code] [code])
        text = ps_text( sou[ l_DUALCOMMA: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ;;
            if rest[ :l_DUALSEMI ] == ps_DUALSEMI:
                return ( rest[ l_DUALSEMI: ], leg )

#   ---- >>
            look = rest
#   ---- ,, <<
            if look[ :l_DUALCOMMA ] == ps_DUALCOMMA:
                return ( rest, leg )
#   ---- \
            elif look[ :1 ] == '\\':
#   ---- atom
                ( look, name ) = ps_atom( look[ 1: ], depth + 1 )
                if name is None:
                    continue
#   ---- gap
                ( look, _ ) = ps_gap( look, depth + 1 )
#   ---- ) & ($eq depth_pth 0) <<
            if ( look[ :1 ] == ')' )  and ( leg.depth_pth == 0 ):
                return ( rest, leg )

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_list( sou, depth = 0 ):
    """
    list ::= '(' { { EMBED } form }0... ')';
    """
#   ---------------
#   ---- (
    if sou[ :1 ] == '(':
#   ---- gap
        ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
        lst = []
#   ---- )
        while sou[ :1 ] != ')':
#   ---- EMBED
            embed = sou[ :1 ] == ps_EMBED
            if embed:
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- form
            ( sou, leg ) = ps_form( sou, depth + 1 )
            if leg is None:
                raise SyntaxError( '%s: form expected: %s' % ( callee(), repr( sou[ :ERR_SLICE ])))

            lst.append( EMBED( leg ) if embed else leg )
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )

        return( sou[ 1: ], LIST( lst ))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_infix( sou, depth = 0 ):
    """
    infix ::=
          '{' exp { op_logic_or exp } '}'
        | '(${}' exp { op_logic_or exp } ')' & ($eq depth_pth 0);

    exp ::= subexp { op_logic_and subexp };
    subexp ::= simple { op_relation simple };
    simple ::= { '+' | '-' } ( term { ( op_like_add | op_like_or ) term }0... );
    term ::= multiplier { ( op_like_mult | op_like_and ) multiplier }0...;
    multiplier ::= { '!' } ( variable | value | application | '(' exp ')' );
    op_logic_or ::= '||';
    op_logic_and ::= '&&';
    op_relation ::= '==' | '!=' | '<=' | '<' | '>=' | '>';
    op_like_add ::= '+' | '-';
    op_like_or ::= '|' | '^';
    op_like_mult ::= '*' | '/' | '\\';
    op_like_and ::= '&' | '<<' | '>>';
    """
#   ---------------
#   -- infix has been released as a python expression
#   ---- {
    if sou[ :1 ] == '{':
        text = ps_text( sou[ 1: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- }
            if rest[ :1 ] == '}':
                return ( rest[ 1: ], INFIX( leg ))

#   ---- (${}
    elif sou[ :l_INFIX ] == ps_INFIX:
        text = ps_text( sou[ l_INFIX: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ) & ($eq depth_pth 0)
            if ( rest[ :1 ] == ')' ) and ( leg.depth_pth == 0 ):
                return ( rest[ 1: ], INFIX( leg ))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_atom( sou, depth = 0 ):
    """
    atom ::= LETTER { LETTER | FIGURE }0...;
    """
#   ---------------
    i = 0
    if _ord( sou, 0 ) in ps_LETTER:
        i = 1
        while _ord( sou, i ) in ( ps_LETTER | ps_FIGURE ):
            i += 1

    return ( sou[ i: ], ATOM( sou[ :i ]) if i else None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_space( sou, depth = 0 ):
    """
    SPACE ::= [ '\t', ' ' ];
    """
#   ---------------
    return _while_in( sou, ps_SPACE )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_eol( sou, depth = 0 ):
    """
    EOL ::= [ '\n', '\r' ];
    """
#   ---------------
    if _ord( sou, 0 ) in ps_EOL:
        return ( sou[ 1: ], sou[ :1 ])

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_gap( sou, depth = 0 ):
    """
    GAP ::= EOL + SPACE;
    """
#   ---------------
    return _while_in( sou, ps_SPACE | ps_EOL )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_quoted( sou, depth = 0 ):
    """
    quoted ::=
          string
        | char
        | ( '($quoted' | '(`' ) plain ')' & ($eq depth_pth 0);
    """
#   ---------------
#   ---- str
    mch = re_STR.match( sou )
    if mch:
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], STR( leg ))

#   ---- chr
    mch = re_CHR.match( sou )
    if mch:
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], STR( leg ))

#   ---- (` | ($quoted
    pos = ( l_BQUOTE if sou[ :l_BQUOTE ] == ps_BQUOTE else l_QUOTED if sou[ :l_QUOTED ] == ps_QUOTED else 0 )
    if pos:
        sou = sou[ pos: ]
        if sou[ :1 ] == ')':
            return ( sou[ 1: ], STR( '' ))

        plain = ps_plain( sou, 0, 0, None, depth + 1 )
        while True:
#   ---- plain
            ( sou, leg, _, depth_pth ) = plain.next()
#   ---- ) & ($eq depth_pth 0)
            if ( sou[ :1 ] == ')' ) and ( depth_pth == 0 ):
                return ( sou[ 1: ], STR( str( leg )))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_comment( sou, depth = 0 ):
    """
    comment ::= '($!' plain ')' & ($eq depth_pth 0);
    """
#   ---------------
#   ---- ($!
    if sou[ :l_COMMENT ] == ps_COMMENT:
        sou = sou[ l_COMMENT: ]
        if sou[ :1 ] == ')':
            return ( sou[ 1: ], COMMENT())

        plain = ps_plain( sou, 0, 0, None, depth + 1 )
        while True:
#   ---- plain
            ( sou, _leg, _, depth_pth ) = plain.next()
#   ---- ) & ($eq depth_pth 0)
            if ( sou[ :1 ] == ')' ) and ( depth_pth == 0 ):
                return ( sou[ 1: ], COMMENT())

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_number( sou, depth = 0 ):
    """
    number ::=
          float
        | hex
        | oct
        | dec;
    """
#   ---------------
#   ---- float
    mch = re_FLOAT.match( sou )
    if mch:
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], FLOAT( leg ))

#   ---- hex
    mch = re_HEX.match( sou )
    if mch:
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], INT( leg, 16 ))

#   ---- oct
    mch = re_OCT.match( sou )
    if mch :
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], INT( leg, 8 ))

#   ---- dec
    mch = re_DEC.match( sou )
    if mch:
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], INT( leg, 10 ))

    return ( sou, None )


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *             E V A L             *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

import copy
from textwrap import dedent
from ast import NodeVisitor
from ast import parse

#   -----------------------------------
#   AST extension
#   -----------------------------------

#   ---------------------------------------------------------------------------
class BOUND( BASE_MARK ):
    """
    Mark of bounded and unassigned variable.
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class LAMBDA_CLOSURE( object ):
    """
    AST: (abstract node) for lambda and macro closures.
    """
#   -----------------------------------
    def __init__( self, l_form, env, late = None, default = None ):
        self.l_form = l_form
        self.env = env
        self.env.parent = None
        self.late = late or {}
        self.default = default or {}

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s, %s)' % ( self.__class__.__name__, repr( self.l_form ), repr( self.env )
        , repr( self.late ), repr( self.default ))


#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.l_form == other.l_form ) and ( self.env == other.env )
        and ( self.late == other.late ) and ( self.default == other.default ))

#   ---------------------------------------------------------------------------
class L_CLOSURE( LAMBDA_CLOSURE ):
    """
    AST: L_CLOSURE( form, ENV, { var: [( late: BOUND )]}, { var: form }) <-- LAMBDA | late
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class M_CLOSURE( LAMBDA_CLOSURE ):
    """
    AST: M_CLOSURE( text, ENV( { par: BOUND } )) <-- MACRO( name, pars, text )
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class INFIX_CLOSURE( object ):
    """
    AST: INFIX_CLOSURE( tree, ENV ) <-- INFIX
    """
#   -----------------------------------
    def __init__( self, tree, env, text ):
        self.tree = tree
        self.env = env
        self.text = text

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.text ), repr( self.env ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.tree == other.tree ) and ( self.env == other.env ))

#   ---------------------------------------------------------------------------
class COND_CLOSURE( object ):
    """
    AST: COND_CLOSURE( former, former, form ) <-- COND
    """
#   -----------------------------------
    def __init__( self, cond, leg_1, leg_0 ):
        self.cond = cond
        self.leg_1 = leg_1
        self.leg_0 = leg_0

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.cond ), repr( self.leg_1 ), repr( self.leg_0 ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.cond == other.cond ) and ( self.leg_1 == other.leg_1 )
        and ( self.leg_0 == other.leg_0 ))

#   ---------------------------------------------------------------------------
class SET_CLOSURE( object ):
    """
    AST: SET_CLOSURE( form, ENV ) <-- SET
    """
#   -----------------------------------
    def __init__( self, form, env ):
        self.form = form
        self.env = env
        self.env.parent = None

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.form ), repr( self.env ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.form == other.form ) and ( self.env == other.env ))

#   ---------------------------------------------------------------------------
class BUILDIN( object ):
    """
    AST: BUILDIN( ATOM, fn )
    """
#   -----------------------------------
    def __init__( self, atom, fn = None ):
        self.atom = atom
        self.fn = fn

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, repr( self.atom ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.atom == other.atom )

#   ---------------------------------------------------------------------------
class T( BASE_LIST ):
    """
    AST: T([ form ]) <-- TEXT
    """
#   -----------------------------------
    def __init__( self, val, indent = '' ):
        BASE_LIST.__init__( self, val )
        self.indent = indent

#   ---------------------------------------------------------------------------
class TRIM( BASE_CAP ):
    """
    AST: TRIM( form, indent )
    """
#   -----------------------------------
    def __init__( self, ast, indent ):
        BASE_CAP.__init__( self, ast )
        self.indent = indent if indent else ''

#   -----------------------------------
    def trim( self, plain ):
        if not plain or not PP_TRIM_APP_INDENT:
            return plain

        return self.indent.join( dedent( plain ).splitlines( True ))

#   -----------------------------------
    def __str__( self ):
        return self.trim( _plain( self.ast ))

#   -----------------------------------
#   Environment
#   -----------------------------------

#   ---- name of variable argument list
__va_args__ = ATOM( '__va_args__' )

#   ---------------------------------------------------------------------------
class NOT_FOUND( object ):
    """
    Mark of negative result.
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class ENV( dict ):
    """
    Environment.
    AST: ENV( ENV, [( var, value )])
    """
#   -----------------------------------
    def __init__( self, parent = None, local = None ):
        dict.__init__( self )
        self.parent = parent
        self.order = []
        if local:
            for key, value in local:
                self.__setitem__( key, value )

#   -----------------------------------
    def __setitem__( self, key, value ):
        if key in self.order:
            self.order.remove( key )
        self.order.append( key )

        dict.__setitem__( self, key, value )

#   -----------------------------------
    def __getitem__( self, key ):
        return dict.__getitem__( self, key )

#   -----------------------------------
    def __contains__( self, key ):
        return dict.__contains__( self, key )

#   -----------------------------------
    def __delitem__( self, key ):
        self.order.remove( key )
        dict.__delitem__( self, key )

#   -----------------------------------
    def eval_local( self, env, depth ):
        result = True
        for key in self.order:
            val = yueval( self.__getitem__( key ), env, depth )
            if result and not _is_term( val ):
                result = False
            dict.__setitem__( self, key, val )
        return result

#   -----------------------------------
    def xlocal( self ):
        for key in list( self.order ):
            yield key, self.__getitem__( key )

#   -----------------------------------
#   TODO: region
    def lookup( self, reg, var ):                                                                                      #pylint: disable=W0613
        env = self
        while env is not None:
            if env.__contains__( var ):
                return env.__getitem__( var )

            env = env.parent

        return NOT_FOUND

#   -----------------------------------
#   TODO: region
    def update( self, reg, var, value ):                                                                               #pylint: disable=W0613
        env = self
        while env is not None:
            if env.__contains__( var ):
                dict.__setitem__( env, var, value )
                return var

            env = env.parent

        return NOT_FOUND

#   -----------------------------------
    def unassigned( self ):
        for key in self.order:
            if isinstance( self.__getitem__( key ), BOUND ):
                return key

        return NOT_FOUND

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, dict.__repr__( self ), repr( self.parent ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( dict.__eq__( self, other ))
        and ( self.parent == other.parent ) and ( self.order == other.order ))

#   -----------------------------------
    def __deepcopy__( self, memodict ):
        return ENV( copy.deepcopy( self.parent, memodict )
        , [( key, copy.deepcopy( self.__getitem__( key ), memodict )) for key in self.order ])

#   -----------------------------------
#   -- debug message
    def _keylist( self ):
        result = []
        env = self
        while env is not None:
            for key, value in env.items():
                result.append( str( key ) if isinstance( value, BOUND ) else key.upper())
            env = env.parent
        return '%s(%s)' % ( self.__class__.__name__, ' '.join( result ))

#   ---------------------------------------------------------------------------
class INFIX_VISITOR( NodeVisitor ):
    """
    Get identifiers from python expression.
    """
#   -----------------------------------
    def __init__( self ):
        self.names = set()

#   -----------------------------------
    def visit_Name( self, node ):
        self.names.add( node.id )

#   ---------------------------------------------------------------------------
class LAZY( BASE_CAP ):
    """
    AST: LAZY( form ) <-- '($lazy' ... ')'
    """
#   -----------------------------------
    def __str__( self ):
        return _plain( self.ast )

#   ---------------------------------------------------------------------------
class SKIPREST( BASE_MARK ):
    """
    Skip the rest of text.
    """
#   ---------------
    pass

#   -----------------------------------
#   Build-in functions and consts
#   -----------------------------------

import string, operator, math, datetime                                                                                #pylint: disable=W0402

#   ---------------------------------------------------------------------------
def yushell( input_file = None, output_file = None ):
    if input_file:
        yushell.input = os.path.basename( input_file )
        yushell.dirname = os.path.dirname( input_file )
        yushell.module = os.path.splitext( yushell.input )[ 0 ].replace( '-', '_' ).upper()
    else:
        yushell.input = '<stdin>'
        yushell.dirname = ''
        yushell.module = 'UNTITLED'
    yushell.output = os.path.basename( output_file ) if output_file else '<stdout>'

yushell()

_title_template = r"""/*  %(output)s was generated by %(app)s %(version)s
    out of %(input)s at %(time)s
 */"""

buildin = dict()
buildin.update( vars( string ))
buildin.update( vars( operator ))
buildin.update( vars( math ))
buildin.update({
                                                                                                                       #pylint: disable=W0142
    '__FILE__': lambda : '"%s"' % yushell.input,
    '__OUTPUT_FILE__': lambda : '"%s"' % yushell.output,
    '__MODULE_NAME__': lambda : ATOM( yushell.module ),
    '__TITLE__': lambda : PLAIN( _title_template % {
      'app': APP, 'version': VERSION
    , 'input': yushell.input, 'output': yushell.output
    , 'time': datetime.datetime.now().strftime( '%Y-%m-%d %H:%M' )
    }),
    'skip': SKIPREST(),
    'car': lambda l : LIST( l[ :1 ]),
    'cdr': lambda l : LIST( l[ 1: ]),
    'dec': lambda val : ( val - 1 ),
    'getslice': lambda seq, *l : LIST( operator.getitem( seq, slice( *l ))),
    'hex': hex,
    'inc': lambda val : ( val + 1 ),
    'islist': lambda l : isinstance( l, list ),
    'lazy': lambda val : LIST( LAZY( x ) for x in val ) if isinstance( val, list ) else LAZY( val ),
    'len': len,
    'list': lambda *l : LIST( l ),
    'print': lambda *l : sys.stdout.write( ' '.join(( _unq( x ) if isinstance( x, STR ) else str( x )) for x in l )),
    'reduce': reduce,
    'reversed': lambda l : LIST( reversed( l )),
    'q': lambda val : '"%s"' % str( val ),
    'range': lambda *l : LIST( range( *l )),
    'repr': repr,
    'str': str,
    'sum': sum,
    'unq': _unq
})

#   ---------------------------------------------------------------------------
def _plain_back( st ):
    return ( '()' if st == [] else str( st ))

#   ---------------------------------------------------------------------------
def _is_term( node ):                                                                                                  #pylint: disable=R0911
    """
    Check node is term.
    """
#   ---------------
    if node is None:
        return True

#   ---- TRIM
    if isinstance( node, TRIM ):
        return _is_term( node.ast )

#   ---- list
    if isinstance( node, list ):
        for i in node:
            if not _is_term( i ):
                return False

        return True

#   ---- LAZY
    if isinstance( node, LAZY ):
        return True

#   ---- str based | int | float | long
    if isinstance( node, str ) or isinstance( node, int ) or isinstance( node, long ) or isinstance( node, float ):
        return True

    return False

#   ---------------------------------------------------------------------------
def _list_to_bound( node ):
    """
    Check and convert list of atoms to list of parameters.
    """
#   ---------------
    if isinstance( node, list ):
        bound = []
        for i in node:
            if not isinstance( i, ATOM ):
                return NOT_FOUND

            bound.append(( [], i, None ))

        return bound

    return NOT_FOUND

#   ---------------------------------------------------------------------------
def _list_eval_1( args, env, depth = 0 ):
    """
    Evaluate first argument into the list.
    """
#   ---------------
                                                                                                                       #pylint: disable=E1103
    if not args:
        return ( None, [])

    arg = yueval( args[ 0 ], env, depth + 1 )
#   ---- EMBED
    if isinstance( arg, EMBED ):
        if isinstance( arg.ast, list ):
            if arg.ast:
                return ( arg.ast[ 0 ], arg.ast[ 1: ] + args[ 1: ])

            return _list_eval_1( args[ 1: ], env, depth + 1 )

#   ---- EMBED -- VAR | APPLY
        if isinstance( arg.ast, VAR ) or isinstance( arg.ast, APPLY ):
#           -- unreducible
            return ( NOT_FOUND, args )

        return ( arg.ast, args[ 1: ])

    return ( arg, args[ 1: ])

#   ---------------------------------------------------------------------------
def trace__eval_in_( node, env, depth ):
    if trace.TRACE:
        trace.info( TR_INDENT * depth + TR_EVAL_IN + _ast_pretty( repr( node )))
        trace.info( TR_EVAL_ENV + _ast_pretty( repr( env )))

#   ---------------------------------------------------------------------------
def trace__eval_out_( node, depth ):
    if trace.TRACE:
        trace.info( TR_INDENT * depth + TR_EVAL_OUT + _ast_pretty( repr( node )))

#   ---------------------------------------------------------------------------
def echo__eval_( fn ):
    def wrapped( node, env = ENV(), depth = 0 ):
        if depth > trace.deepest:
            trace.deepest = depth
        trace__eval_in_( node, env, depth )
        result = fn( node, env, depth )
        trace__eval_out_( result, depth )
        return result

    return wrapped

#   ---------------------------------------------------------------------------
@echo__eval_
def yueval( node, env = ENV(), depth = 0 ):                                                                            #pylint: disable=R0915,R0912,R0911,R0914
    """
    AST reduction.
    """
#   -----------------------------------
    def _callee():
        return 'yueval'

#   ---------------
#   TODO: region
                                                                                                                       #pylint: disable=E1103
    try:
        tr = False
        while True:
            if tr:
#               -- trace eliminated tail recursion
                trace__eval_in_( node, env, depth )
            else:
                tr = True
#   ---- TEXT --> T
            if isinstance( node, TEXT ):
                node = T( node.ast )
                # fall through -- yueval( node )
#   ---- T
            elif isinstance( node, T ):
                t = T([], node.indent )
                for i, x in enumerate( node ):
                    nx = i + 1
                    x_apply = isinstance( x, APPLY )
#   ---- T -- PLAIN
                    if isinstance( x, PLAIN ):
                        if x.indent is None:
#                           -- prior value
                            x_indent = node.indent
                        else:
#                           -- plain's value
                            x_indent = x.indent
                    else:
                        x_indent = False
#   ---- T -- COMMENT
                    if isinstance( x, COMMENT ):
                        if isinstance( node.indent, str ) and ( nx < len( node )) and isinstance( node[ nx ], PLAIN ):
#                           -- delete spacing
                            node[ nx ].trim = True
#                       -- skip
                        continue

                    x = yueval( x, env, depth + 1 )
                    if x is None:
#                       -- skip
                        continue

#   ---- T -- SKIPREST
                    if isinstance( x, SKIPREST ):
                        break

#   ---- T -- ENV
                    if isinstance( x, ENV ):
                        if nx < len( node ):
                            if isinstance( node.indent, str ) and isinstance( node[ nx ], PLAIN ):
#                               -- delete spacing
                                node[ nx ].trim = True
                            del node[ :nx ]
#                           -- !? extend
                            t.append( yueval( SET_CLOSURE( node, x ), env, depth + 1 ))
                        else:
#                           -- item is ignored
                            log.warn( 'useless assign: %s', repr( node )[ :ERR_SLICE ])
                        break

#   ---- T -- EMBED --> T
                    if isinstance( x, EMBED ):
                        if isinstance( x.ast, T ):
#                           -- add the indent of an application to each line of the substituting text
                            if node.indent:
                                for ii, xx in enumerate( x.ast ):
                                    if isinstance( xx, PLAIN ):
                                        x.ast[ ii ] = xx.add_indent( node.indent )
#                           -- insert an embedded AST into the head of the list of the rest and evaluate them together
#                           -- so complicated because ($macro) can contain ($set)
                            del node[ :nx ]
                            node[ 0:0 ] = x.ast
                            tail = yueval( node, env, depth + 1 )

                            if isinstance( tail, list ):
                                t.extend( tail )
                            else:
                                t.append( tail )
                            break

                        else:
                            x = x.ast
#                   -- indent mimicry
                    t.append( TRIM( x, node.indent ) if x_apply else x )
                    node.indent = x_indent

                if _is_term( t ):
                    return _plain( t )

#               -- unreducible
                return t

#   ---- APPLY
            elif isinstance( node, APPLY ):
                node.fn = yueval( node.fn, env, depth + 1 )
                node.args = yueval( node.args, env, depth + 1 )

#   ---- APPLY -- BUILDIN
                if isinstance( node.fn, BUILDIN ):
                    if node.named:
                        raise SyntaxError( '%s: unexpected named argument of buildin function: %s' % ( _callee()
                        , repr( node )[ :ERR_SLICE ]))

#   ---- APPLY -- BUILDIN -- function
                    if callable( node.fn.fn ):
                        if _is_term( node.args ):
#   TODO: check arguments count
                            val = node.fn.fn( *node.args )
                            return int( val ) if isinstance( val, bool ) else val

#   ---- APPLY -- BUILDIN -- lazy | repr
                        if node.fn.atom in [ 'lazy', 'repr' ] \
                        and len( node.args ) == 1 and not isinstance( node.args[ 0 ], VAR ):
#                           -- argument is substituted
                            return node.fn.fn( node.args[ 0 ])

#   ---- APPLY -- BUILDIN -- reduce
                        if node.fn.atom in [ 'reduce' ] \
                        and len( node.args ) > 1 and isinstance( node.args[ 0 ], BUILDIN ) \
                        and _is_term( node.args[ 1: ]):
                            return node.fn.fn( node.args[ 0 ].fn, *node.args[ 1: ] )

#                       -- unreducible
                        return node

#   ---- APPLY -- BUILDIN -- const
                    if node.args:
                        raise TypeError( '%s: no arguments of constant expected: %s' % ( _callee()
                        , repr( node )[ :ERR_SLICE ]))

                    return node.fn.fn

#   ---- APPLY -- int | float | long (subscripting)
                elif isinstance( node.fn, int ) or isinstance( node.fn, long ) or isinstance( node.fn, float ):
                    if node.named:
                        raise SyntaxError( '%s: unexpected named argument of index function: %s' % ( _callee()
                        , repr( node )[ :ERR_SLICE ]))

                    if node.args:
                        if _is_term( node.args ):
                            pos = int( node.fn )
#                           -- (syntactic sugar) if only one argument and it's a list - apply operation to it
                            if len( node.args ) == 1 and isinstance( node.args[ 0 ], list ):
                                return node.args[ 0 ][ pos ] if pos < len( node.args[ 0 ]) else None
                            else:
                                return node.args[ pos ] if pos < len( node.args ) else None

#                       -- unreducible
                        return node

                    return node.fn

#   ---- APPLY -- TEXT
                elif isinstance( node.fn, TEXT ):
                    if node.args or node.named:
                        raise TypeError( '%s: no arguments of text expected: %s' % ( _callee()
                        , repr( node )[ :ERR_SLICE ]))

                    node = node.fn
                    # fall through -- yueval( node )

#   ---- APPLY -- L_CLOSURE -- e.g. APPLY( form, arg0, arg1 )
#                           --> yueval( apply( yueval( apply( yueval( form ) yueval( arg0 ))) yueval( arg1 )))
#   ---- APPLY -- M_CLOSURE
                elif isinstance( node.fn, LAMBDA_CLOSURE ):
#                   -- apply named arguments
                    if node.named:
                        var, val = node.named.pop( 0 )
                        if var in node.fn.env:
                            if not isinstance( node.fn.env[ var ], BOUND ):
                                log.warn( 'parameter "%s" already has value: %s', str( var )
                                , repr( node )[ :ERR_SLICE ])
                            val = yueval( val, env, depth + 1 )
                        else:
                            raise TypeError( '%s: function has no parameter "%s": %s' % ( _callee(), str( var )
                            , repr( node )[ :ERR_SLICE ]))

#                   -- apply anonymous arguments
                    elif node.args:
                        var = node.fn.env.unassigned()
                        if var is NOT_FOUND:
#                           -- no parameters
                            log.warn( 'unused argument(s) %s: %s', repr( node.args ), repr( node )[ :ERR_SLICE ])
                            return yueval( node.fn, env, depth + 1 )

                        if var == __va_args__:
#   TODO: handle if refuge is not the last parameter...
                            val = LIST( node.args )
                            node.args = []
                        else:
                            val, node.args = _list_eval_1( node.args, env, depth + 1 )

#                       -- unreducible -- EMBED
                        if val is NOT_FOUND:
                            return node

#                   -- no arguments
                    else:
                        var = node.fn.env.unassigned()
#                       -- no parameters
                        if var is NOT_FOUND:
                            return yueval( node.fn, env, depth + 1 )

#                       -- no default
                        if var not in node.fn.default:
#                           -- result is LAMBDA_CLOSURE (BOUND)
                            return node.fn

#                       -- apply default
                        val = yueval( node.fn.default[ var ], env, depth + 1 )
#                   -- late bounded -- second yueval()
                    if var in node.fn.late:
                        val = yueval( L_CLOSURE( val, ENV( None, node.fn.late[ var ])), env, depth + 1 )
                    node.fn.env[ var ] = val
#                   -- have no more arguments and default
                    if not node.named and not node.args and node.fn.env.unassigned() not in node.fn.default:
                        node = node.fn
                    # fall through -- yueval( node ) -- apply next argument

#   ---- APPLY -- LAZY
                elif isinstance( node.fn, LAZY ):
                    node.fn = node.fn.ast
                    # fall through -- yueval( node )

#   ---- APPLY -- str
                elif isinstance( node.fn, str ):
#                   -- have no arguments
                    if not node.named and not node.args:
                        return node.fn

#                   -- format string
                    term = True
                    for i, ( var, val ) in enumerate( node.named ):
                        val = yueval( val, env, depth + 1 )
                        node.named[ i ] = ( var, val )
                        term = term and _is_term( val )
                    if not term or not _is_term( node.args ):
#                       -- unreducible
                        return node

                    for i, val in enumerate( node.args ):
                        node.fn = node.fn.replace( '($' + str( i ) + ')', _plain( val ))
                    for var, val in node.named:
                        node.fn = node.fn.replace( '($' + str( var ) + ')', _plain( val ))
                    return STR( node.fn )

#   ---- APPLY -- list ("for each" loop)
                elif isinstance( node.fn, list ):
                    if node.named:
                        raise SyntaxError( '%s: unexpected named argument of foreach function: %s' % ( _callee()
                        , repr( node )[ :ERR_SLICE ]))

#                   -- !? is it right without
#                   if not _is_term( node.fn ):
#                       -- unreducible
#                       return node

                    lst = LIST()
                    for x in node.fn:
                        for arg in node.args:
                            fn = copy.deepcopy( arg )
                            x = yueval( APPLY( fn, [ x ], []), env, depth + 1 )
                        lst.append( x )
                    return lst

#   ---- APPLY -- SKIPREST
                elif isinstance( node.fn, SKIPREST ):
                    return node.fn

#   ---- APPLY -- None
                elif node.fn is None:
                    return None

#   ---- APPLY -- ...
                else:
#                   -- unreducible
                    return node

#   ---- VAR
            elif isinstance( node, VAR ):
                val = env.lookup( node.reg, node.atom )
                if val is NOT_FOUND:
#   ---- VAR -- LATE_BOUNDED
                    if isinstance( node.reg, LATE_BOUNDED ):
#                       -- unreducible
                        return node

                    if not node.reg:
#   ---- VAR -- BUILDIN
                        if node.atom in buildin:
                            return BUILDIN( node.atom, buildin[ node.atom ])

#                       -- if not valid C identifier mark as LATE_BOUNDED
                        if not node.atom.is_valid_c_id():
                            node.reg = LATE_BOUNDED()
#                           -- unreducible
                            return node

                        return node.atom

                    raise TypeError( '%s: undefined variable "%s": %s' % ( _callee(), str( node.atom )
                    , repr( node )[ :ERR_SLICE ]))

#   ---- VAR -- BOUND
                if isinstance( val, BOUND ):
#                   -- unreducible
                    return node

                return copy.deepcopy( val )

#   ---- LAMBDA --> L_CLOSURE
            elif isinstance( node, LAMBDA ):
#   ---- LAMBDA -- VAR
                if isinstance( node.bound, VAR ):
                    val = env.lookup( node.bound.reg, node.bound.atom )
                    if isinstance( val, BOUND ):
#                       -- unreducible
                        return node

                    node.bound = _list_to_bound( val )
                    if node.bound is NOT_FOUND:
                        raise TypeError( '%s: illegal parameters list: %s' % ( _callee(), repr( node )[ :ERR_SLICE ]))

#   ---- LAMBDA -- VAR | list
                d_late = {}
                d_default = {}
                env_l = ENV()
#               -- convert to L_CLOSURE
                for late, var, default in node.bound:
                    if late:
                        d_late[ var ] = [( key, BOUND()) for key in late ]
                    if default is not None:
                        d_default[ var ] = yueval( default, env, depth + 1 )
                    if var == ATOM( '...' ):
                        var = __va_args__
                    env_l[ var ] = BOUND()
#               -- eval L_CLOSURE
                node = L_CLOSURE( node.l_form, env_l, d_late, d_default )
                # fall through -- yueval( node )

#   ---- L_CLOSURE
            elif isinstance( node, L_CLOSURE ):
                node.env.parent = env
                if node.env.unassigned() is not NOT_FOUND:
                    node.l_form = yueval( node.l_form, node.env, depth + 1 )
#                   -- unreducible
                    return node

                env = node.env
                node = node.l_form
                # fall through -- yueval( node )

#   ---- SET --> ENV
            elif isinstance( node, SET ):
                env_l = ENV( env )
                if isinstance( node.lval, ATOM ):
                    env_l[ node.lval ] = BOUND()
                else:
                    for i, var in enumerate( node.lval ):
                        env_l[ var ] = BOUND()
#               -- circular reference
                val = yueval( node.ast, env_l, depth + 1 )
                if isinstance( node.lval, ATOM ):
                    env_l[ node.lval ] = val
                else:
                    if isinstance( val, list ):
                        for i, var in enumerate( node.lval ):
                            if len( val ) > i:
                                env_l[ var ] = val[ i ]
                            else:
                                log.warn( 'there is nothing to assign to "%s": %s', str( var )
                                , repr( node )[ :ERR_SLICE ])
                                env_l[ var ] = None
                    else:
                        for var in node.lval:
                            env_l[ var ] = val
                return env_l

#   ---- SET_CLOSURE
            elif isinstance( node, SET_CLOSURE ):
                node.env.parent = env
                node.form = yueval( node.form, node.env, depth + 1 )
                if _is_term( node.form ):
                    return node.form

#               -- unreducible
                return node

#   ---- MACRO --> ENV( None, ( name, M_CLOSURE( text, ENV( None, [( par, BOUND )]))))
            elif isinstance( node, MACRO ):
                return ENV( None, [( node.name, M_CLOSURE( node.text, ENV( None
                , zip( node.pars, [ BOUND()] * len( node.pars )))))])

#   ---- M_CLOSURE --> EVAL
            elif isinstance( node, M_CLOSURE ):
                if not node.env.eval_local( env, depth + 1 ):
#                   -- unreducible
                    return node

                for var, val in node.env.xlocal():
                    node.l_form = node.l_form.replace( '($' + str( var ) + ')', _plain_back( val ))
                node = EVAL( node.l_form )
                # fall through -- yueval( node )

#   ---- EVAL --> EMBED
            elif isinstance( node, EVAL ):
                node.ast = yueval( node.ast, env, depth + 1 )
                if not isinstance( node.ast, str ):
#                   -- unreducible
                    return node

                if isinstance( node.ast, STR ):
                    node.ast = _unq( node.ast ).strip()
#                   -- (syntactic sugar) enclose string into ($ )
                    if not node.ast.startswith( '($' ):
                        node.ast = '($' + node.ast + ')'

                node = yuparse( node.ast )
                if not node.ast:
                    return None

                if ( any( isinstance( x, SET ) for x in node.ast )):
                    return EMBED( T( node.ast ))

#               -- !? e.g. ($ \p.($...))
                node = T( node.ast ) if len( node.ast ) > 1 else node.ast[ 0 ]
                # fall through -- yueval( node )

#   ---- COND --> COND_CLOSURE
            elif isinstance( node, COND ):
                node.cond = yueval( node.cond, env, depth + 1 )
                if not _is_term( node.cond ):
#                   -- unreducible
                    return COND_CLOSURE( node.cond, node.leg_1, node.leg_0 )

                node = node.leg_1 if node.cond else node.leg_0
                # fall through -- yueval( node )

#   ---- COND_CLOSURE
            elif isinstance( node, COND_CLOSURE ):
                node.cond = yueval( node.cond, env, depth + 1 )
                if not _is_term( node.cond ):
#                   -- !? potential problem of infinite recursion...
                    node.leg_1 = yueval( node.leg_1, env, depth + 1 )
                    node.leg_0 = yueval( node.leg_0, env, depth + 1 )
#                   -- unreducible
                    return node

                node = yueval( node.leg_1 if node.cond else node.leg_0, env, depth + 1 )
                # fall through -- yueval( node )

#   ---- INFIX --> INFIX_CLOSURE
            elif isinstance( node, INFIX ):
                node.ast = yueval( node.ast, env, depth + 1 )
                if not isinstance( node.ast, str ):
#                   -- unreducible
                    return node

                infix_visitor = INFIX_VISITOR()
                tree = parse( node.ast.lstrip(), mode = 'eval' )
                infix_visitor.visit( tree )

                env_l = ENV()
                for name in infix_visitor.names:
                    val = env.lookup( [], name )
                    if val is not NOT_FOUND:
                        env_l[ ATOM( name )] = VAR( [], ATOM( name ))

                node = INFIX_CLOSURE( tree, env_l, node.ast )
                # fall through -- yueval( node )

#   ---- INFIX_CLOSURE
            elif isinstance( node, INFIX_CLOSURE ):

                if not node.env.eval_local( env, depth + 1 ):
#                   -- unreducible
                    return node

                code = compile( node.tree, '', 'eval' )
                                                                                                                       #pylint: disable=W0142
                return eval( code, dict( globals(), **buildin ), node.env )

#   ---- EMIT
            elif isinstance( node, EMIT ):
                val = env.lookup( node.var.reg, node.var.atom )
                if val is NOT_FOUND:
                    raise TypeError( '%s: undefined variable "%s": %s' % ( _callee(), str( node.var.atom )
                    , repr( node )[ :ERR_SLICE ]))

#   ---- EMIT -- VAR -- BOUND
                if isinstance( val, BOUND ):
#                   -- unreducible
                    return node

                if isinstance( val, list ):
                    if len( val ):
                        result = val[ 0 ]
                        del val[ 0 ]
                    else:
                        result = None
                else:
                    result = val

                if node.ast:
                    val = yueval( APPLY( node.ast, [ val ], []), env, depth + 1 )
                    env.update( node.var.reg, node.var.atom, val )
                return result

#   ---- LIST | list
            elif isinstance( node, list ):
                lst = LIST()
                for i, x in enumerate( node ):
                    x = yueval( x, env, depth + 1 )
                    if x is None:
                        continue
#   ---- LIST -- EMBED
                    if isinstance( x, EMBED ):
                        if isinstance( x.ast, list ):
                            lst.extend( x.ast )
                        else:
#   ---- LIST -- EMBED -- VAR | APPLY
                            if isinstance( x.ast, VAR ) or isinstance( x.ast, APPLY ):
#                               -- unreducible
                                lst.append( x )
                            else:
                                lst.append( x.ast )
                    else:
                        lst.append( x )
                return lst

#   ---- EMBED | TRIM
            elif isinstance( node, EMBED ) or isinstance( node, TRIM ):
                node.ast = yueval( node.ast, env, depth + 1 )
                return node

#   ---- INT
#   ---- FLOAT
#   ---- STR
#   ---- REMARK
#   ---- PLAIN
            else:
                return node

    except:                                                                                                            #pylint: disable=W0702
        e_type, e, tb = sys.exc_info()
#   ---- python or recursive exception
        arg = e.args[ 0 ] if e.args else None
        if ( not isinstance( arg, str )
        or not arg.startswith( 'yueval' ) and not arg.startswith( 'python' ) and not arg.startswith( 'ps_' )):
            if isinstance( arg, str ) and arg.startswith( 'maximum recursion depth' ):
                raise e_type, 'yueval: %s' % e, tb
            else:
#               -- this 'raise' expr. could be cause of new exception when maximum recursion depth is exceeded
                raise e_type, 'python: %s: %s' % ( e, repr( node )[ :ERR_SLICE ]), tb

#   ---- raised exception
        else:
            raise e_type, e, tb

#   ---------------------------------------------------------------------------
def _ast_readable( node ):
    """
    Represent AST as readable text.
    """
#   ---- SET_CLOSURE
    if isinstance( node, SET_CLOSURE ):
#       -- node.env will be included into children
        return _ast_readable( node.form )

#   ---- TRIM
    elif isinstance( node, TRIM ):
        return node.trim( _ast_readable( node.ast ))

#   ---- PLAIN
    elif isinstance( node, PLAIN ):
        return str( node )

#   ---- list
    elif isinstance( node, list ):
        return ''.join( _ast_readable( x ) for x in node )

#   ---- str
    elif isinstance( node, str ):
        return node

    return _ast_pretty( repr( node ))

#   ---- cut here ----

#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *           S H E L L             *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

TITLE = r""" __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \  %(description)s
\ \ \_\/  \_\/  \_\ \ \_\ \  %(app)s %(version)s
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/   %(copyright)s
     \/_/      \/_/  \/_/    %(authors)s
""" % { 'description' : DESCRIPTION, 'copyright': COPYRIGHT, 'authors': AUTHORS, 'app': APP, 'version': VERSION }

PROMPT  = '[yupp]# '
PP_I    = '<--'
PP_O    = '-->'
PP_FILE = '[%s]'
OK      = '* OK *'
FAIL    = '* FAIL * %s * %s'
___     = '.' * 79

E_YU    = '.yu'
re_e_yu = re.compile( r'\.yu(?:-([^\.]+))?$', flags = re.I )
E_C     = '.c'
E_BAK   = '.bak'
E_AST   = '.ast'

QUIET_HELP = """
don't show the usual greeting, version message and processed file
"""
QUIET = False

TYPE_FILE_HELP = """
show content of output file
"""
TYPE_FILE = False

LOG_LEVEL_SCALE = 10

SYSTEM_EXIT_HELP = 'Also, arguments can be passed through the response file e.g. yup.py @FILE .' \
' The preprocessor exit status is a negative number of unsuccessfully processed files' \
' or an error of command line arguments (2) or a program execution error (1)' \
' or zero in case of successful execution.'

#   ---------------------------------------------------------------------------
def shell_argparse():
    from argparse import ArgumentParser

    argp = ArgumentParser(
      description = 'yupp, %(description)s' % { 'description': DESCRIPTION }
    , version = '%(app)s %(version)s' % { 'app': APP, 'version': VERSION }
    , epilog = SYSTEM_EXIT_HELP
    )
#   -- an input text (used by Web Console)
    argp.add_argument( '-i', '--input', metavar = 'TEXT', type = str, dest = 'text', default = ''
    , help = "an input text (used by Web Console)" )
#   -- a source of input text (used by Web Console)
    argp.add_argument( '--input-source', metavar = 'NAME', type = str, dest = 'text_source', default = ''
    , help = "a source of input text (used by Web Console)" )
#   -- input files
    argp.add_argument( 'files', metavar = 'FILE', type = str, nargs = '*', help = "an input file" )
#   -- an import directory
    argp.add_argument( '-d', action = 'append', metavar = 'DIR', dest = 'directory', default = DIRECTORY
    , help = "an import directory" )
#   -- echo options
    argp.add_argument( '-q', '--quiet', action = 'store_true', dest = 'quiet', default = QUIET
    , help = QUIET_HELP )
    argp.add_argument( '--type-file', action = 'store_true', dest = 'type_file', default = TYPE_FILE
    , help = TYPE_FILE_HELP )
#   -- debug options
    argp.add_argument( '-l', '--log', metavar = 'LEVEL', type = int, dest = 'log_level'
    , default = ( LOG_LEVEL // LOG_LEVEL_SCALE ), choices = range( 1, 6 )
    , help = "set logging level: 1 - DEBUG 2 - INFO 3 - WARNING 4 - ERROR 5 - CRITICAL" )
    argp.add_argument( '-t', '--trace', metavar = 'STAGE', type = int, dest = 'tr_stage'
    , default = TR_STAGE, choices = range( 0, 4 )
    , help = "set tracing stages: 0 - NONE 1 - PARSE 2 - EVAL 3 - BOTH" )
    argp.add_argument( '-b', '--traceback', metavar = 'TYPE', type = int, dest = 'traceback'
    , default = TRACEBACK, choices = range( 0, 3 )
    , help = "set exceptions traceback: 0 - NONE 1 - PYTHON 2 - ALL" )
#   -- preprocessor options
    argp.add_argument( '--pp-skip-c-comment', action = 'store_true', dest = 'pp_skip_c_comment'
    , help = PP_SKIP_C_COMMENT_HELP )
    argp.add_argument( '--pp-no-skip-c-comment', action = 'store_false', dest = 'pp_skip_c_comment' )
    argp.add_argument( '--pp-trim-app-indent', action = 'store_true', dest = 'pp_trim_app_indent'
    , help = PP_TRIM_APP_INDENT_HELP )
    argp.add_argument( '--pp-no-trim-app-indent', action = 'store_false', dest = 'pp_trim_app_indent' )
    argp.add_argument( '--pp-reduce-emptiness', action = 'store_true', dest = 'pp_reduce_emptiness'
    , help = PP_REDUCE_EMPTINESS_HELP )
    argp.add_argument( '--pp-no-reduce-emptiness', action = 'store_false', dest = 'pp_reduce_emptiness' )

    argp.set_defaults( pp_skip_c_comment = PP_SKIP_C_COMMENT, pp_trim_app_indent = PP_TRIM_APP_INDENT
    , pp_reduce_emptiness = PP_REDUCE_EMPTINESS )

    if ( len( sys.argv ) == 2 ) and sys.argv[ 1 ].startswith( '@' ):
#       -- get arguments from response file
        try:
            with open( sys.argv[ 1 ][ 1: ], 'r' ) as f:
                return argp.parse_args( f.read().split())

        except IOError as e:
#           -- file operation failure
            print FAIL % ( type( e ).__name__, e )
            sys.exit( 2 )

    return argp.parse_args()
    return argp.parse_args([ '-h' ])                                                                                   #pylint: disable=W0101

#   ---------------------------------------------------------------------------
def shell_input():
    try:
        return raw_input( PROMPT )

    except ( EOFError, ValueError ):
#       -- e.g. run into environment without terminal input
        return ''

#   ---------------------------------------------------------------------------
def shell_backup( fn ):
    if os.path.isfile( fn ):
        fn_bak = fn + E_BAK
        if os.path.isfile( fn_bak ):
            os.remove( fn_bak )
        os.rename( fn, fn_bak )

#   ---------------------------------------------------------------------------
def shell_savetofile( fn, text ):
    f = open( fn, 'wb' )
    try:
        f.write( text )
    finally:
        f.close()

#   ---------------------------------------------------------------------------
def _output_fn( fn ):
    fn_o, e = os.path.splitext( fn )
    if e == E_C:
#   ---- .c --> .yu.c
        return fn_o + E_YU + E_C

    e_yu = re_e_yu.search( e )
    if e_yu is None:
#   ---- * --> *.c
        return fn + E_C

    if e_yu.group( 1 ):
#   ---- .yu-* --> .*
        return fn_o + '.' + e_yu.group( 1 )

    if fn_o.endswith( E_C ):
#   ---- .c.yu --> .c
        return fn_o

#   ---- .yu --> .c
    return fn_o + E_C

#   ---------------------------------------------------------------------------
def _pp_file( fn ):
    result = False
    try:
#       -- input file reading
        f = open( fn, 'r' )
        try:
            text = f.read()
        finally:
            f.close()
        if not QUIET:
            print PP_I, PP_FILE % fn
#       -- output file naming
        fn_o = _output_fn( fn )
#       -- preprocessing
        yushell( fn, fn_o )
        result, plain = _pp( text )
        print
        if result:
            if TYPE_FILE:
                print plain
            if not QUIET:
                print PP_O, PP_FILE % fn_o
#           -- output file backup
            shell_backup( fn_o )
#           -- output file writing
            shell_savetofile( fn_o, plain )
            if not QUIET:
                print OK
        else:
            if plain:
#           -- AST in plain
                fn_o = os.path.splitext( fn_o )[ 0 ] + E_AST
                if TYPE_FILE:
                    print plain
                if not QUIET:
                    print PP_O, PP_FILE % fn_o
#               -- output file writing
                shell_savetofile( fn_o, plain )

    except IOError as e:
#       -- e.g. file operation failure
        print FAIL % ( type( e ).__name__, e )

    return result

#   ---------------------------------------------------------------------------
def _pp_test( text, echo = True ):
    if not text or text.isspace():
#       -- empty text - quit REPL
        return False

    if echo:
        print PP_I, text
    yushell()
    result, plain = _pp( text )
    print
    print PP_O, plain
    if result:
        print OK
#   -- continue REPL
    return True

#   ---------------------------------------------------------------------------
def _pp_text( text, text_source = None ):
    yushell( text_source )
    result, plain = _pp( text )
    print
    print plain
    if result:
        print OK

#   ---------------------------------------------------------------------------
def _pp( text ):                                                                                                       #pylint: disable=R0915
    """
    return yueval( yuparse( text ))
    (also tracing and logging)
    """
#   ---------------
    set_trace( TR_STAGE & TR_PARSE )
    TR2F = trace.TRACE and TR_TO_FILE
    LOG = not trace.TRACE or TR_TO_FILE
#   -- parse
    try:
        if TR2F:
            trace.info( text )
        trace.deepest = 0
        ast = yuparse( text.replace( '\r\n', '\n' ))

        if trace.TRACE:
            trace.info( repr( ast ))
            trace.info( TR_DEEPEST, trace.deepest )
    except:                                                                                                            #pylint: disable=W0702
        e_type, e, tb = sys.exc_info()
        msg = '\n'
        arg = e.args[ 0 ] if e.args else None
        if (( TRACEBACK == TB_ALL ) or
            ( TRACEBACK == TB_PYTHON ) and isinstance( arg, str ) and arg.startswith( 'python' )):
#           -- enabled traceback
            msg += ''.join( traceback.format_tb( tb ))
        msg += ''.join( traceback.format_exception_only( e_type, e ))
        if TR2F:
            trace.info( msg )
        if LOG:
            log.error( msg )
        if trace.TRACE:
            trace.info( TR_DEEPEST, trace.deepest )
        if TR2F:
            trace.info( ___ )
        return False, ''

#   -- eval
    set_trace( TR_STAGE & TR_EVAL )
    TR2F = trace.TRACE and TR_TO_FILE
    LOG = not trace.TRACE or TR_TO_FILE
    try:
        trace.deepest = 0
        plain = yueval( ast )

        result = isinstance( plain, str )
        if result:
            plain = trim_tailing_whitespace( plain, PP_REDUCE_EMPTINESS )
        else:
            plain = _ast_readable( plain )
        if trace.TRACE:
            trace.info( plain )
            trace.info( TR_DEEPEST, trace.deepest )
    except:                                                                                                            #pylint: disable=W0702
        e_type, e, tb = sys.exc_info()
        msg = '\n'
        arg = e.args[ 0 ] if e.args else None
        if (( TRACEBACK == TB_ALL ) or
            ( TRACEBACK == TB_PYTHON ) and isinstance( arg, str ) and arg.startswith( 'python' )):
#           -- enabled traceback
            msg += ''.join( traceback.format_tb( tb ))
        msg += ''.join( traceback.format_exception_only( e_type, e ))
        if TR2F:
            trace.info( msg )
        if LOG:
            log.error( msg )
        if trace.TRACE:
            trace.info( TR_DEEPEST, trace.deepest )
        if TR2F:
            trace.info( ___ )
        return False, ''

    if TR2F:
        trace.info( ___ )

    return ( result, plain )

#   ---------------------------------------------------------------------------
if __name__ == '__main__':
#   -- options
    shell = shell_argparse()

    QUIET = shell.quiet
    TYPE_FILE = shell.type_file
    LOG_LEVEL = shell.log_level * LOG_LEVEL_SCALE
    log.setLevel( LOG_LEVEL )
    TR_STAGE = shell.tr_stage
    set_trace( TR_STAGE )
    TRACEBACK = shell.traceback
    PP_SKIP_C_COMMENT = shell.pp_skip_c_comment
    PP_TRIM_APP_INDENT = shell.pp_trim_app_indent
    PP_REDUCE_EMPTINESS = shell.pp_reduce_emptiness
    DIRECTORY = shell.directory

    if not QUIET:
        print TITLE
#       -- startup testing
        _pp_test( r"""($($\y:u.\m.\...(m y($\C.\p.(r)e p)($\ro.(ce)s)))so r)""" )
        _pp_test( r"""
""" )

    if shell.text:
#       -- input text preprocessing
        _pp_text( shell.text, shell.text_source )

    if shell.files:
        f_failed = 0
#       -- input files preprocessing
        for path in shell.files:
            if not _pp_file( path ):
                f_failed -= 1
#       -- sys.exit() redefined in Web Console
        sys.exit( f_failed )

    else:
#       -- Read-Eval-Print Loop
        while _pp_test( shell_input(), False ):
            pass

#   -- EOF
