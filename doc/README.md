![screenshot](pic/logo.png)

### WHAT IS IT?

**yupp** is a lexical preprocessor which implements the macro language
with Lisp-like Polish notation syntax in fully parenthesized form.
**yupp** is intended to transform C programs before they are compiled.
It can also be useful for more general purposes, if you would like
to use the preprocessor with Python 2 just install [yupp package](../../../tree/master/python).

**yupp** allows to generate a well-formatted readable text. Special
attention is paid to providing complete diagnostic information and
navigational capabilities.

Embedding of the preprocessor expressions into the source code occurs
by using _an application form_, e.g. `($e)`.

There is a small example with comments: ["A glance at the yupp"](glance.md).

### SYNTAX

Main syntactic categories of the macro language are: **list**, **application**
and **lambda expression**.

**List** is a sequence of expressions separated by blanks and enclosed
in parentheses.

    <list> ::= '(' { <expression> } ')'

e.g. `(0.5 "string" atom)`

**Application** is an applying a function to arguments, it syntactically
differs from a list in presence of the dollar sign after the open
parenthesis.

    <application> ::= '($' <function> { <argument> } ')'

e.g. `($add 2 3)`

**Lambda expression** is an anonymous function, it consists of a sequence of parameters
and a function body.

    <lambda> ::= <param> { <param> } <expression>
    <param>  ::= '\' <name> [ ':' <default> ] '.'

e.g. `\p.($sub p 1)`

Syntactic forms can be nested within each other but, as mentioned above,
only _an application_ can be embedded into the source code directly.

The following examples show various syntactic constructs of the macro
language. Try them using [yupp Web Console](http://yup-py.appspot.com/).

    ($! this is a comment, won't be saved in the generated text )

Binding of the atom (identifier) with the value – `($set )`:

    ($set a 'A')

The atom binding with the list:

    ($set abc (a 'B' 'C' 'D' 'E'))

Binding of the atom with the lambda is a function definition:

    ($set inc \val.($add val 1))

Application of the number is subscripting:

    ($2 miss miss HIT miss)

    HIT

Getting the specific element of the list:

    ($0 abc)

    'A'

Application of the list is "for each" loop:

    ($(0 1 2) \i.($inc i))

    123

Embedding of one list into another – `*list`:

    ($set mark (5 4 *(3 2) 1))

Infix expression in Python – `{ }`:

    ($set four { 2 + 2 })

Infix expression straight into the source code:

    foo = (${} sqrt(four) * 5.0);

    foo = 10.0;

Conditional expression – `consequent ? condition | alternative`:

    ($set fact \n.($ 1 ? { n == 0 } | { ($fact { n - 1 }) * n }))
    ($fact 10)

    3628800

Enclosing of the source code into the application:

    ($abc \ch.($code putchar(($ch));))

    putchar('A'); putchar('B'); putchar('C'); putchar('D'); putchar('E');

The source code enclosing with square brackets – `[ ]`:

    ($mark \i.[($i), ])

    5, 4, 3, 2, 1,

The function parameter with default value – `\p:val.`:

    ($set if \cond.\then:[].\else:[].($ then ? cond | else ))

The named argument:

    ($if { four != 4 } \else OK )

    OK

The macro definition:

    ($macro GRADE ( PAIRS )
        ($set GRADE-name  ($ (($PAIRS)) \p.($0 p)))
        ($set GRADE-value ($ (($PAIRS)) \p.($1 p)))
        ($set each-GRADE  ($range ($len (($PAIRS)) )))
    )

The quote – ``(` )``:

    ($GRADE
        (`
            ( A 5 )
            ( B 4 )
            ( C 3 )
            ( D 2 )
            ( E 1 )
        )
    )

Enclosing of the source code into the loop
with reverse square brackets – `]<EOL> <EOL>[`:

    ($each-GRADE \i.]
        int ($i GRADE-name) = ($i GRADE-value);

    [ )

    int A = 5;
    int B = 4;
    int C = 3;
    int D = 2;
    int E = 1;

The source code enclosing with double comma – `,,`:

    ($import stdlib)
    ($hex ($BB,,11000000,,11111111,,11101110))

    0xc0ffee

The string substitution:

    ($ "Give ($0) ($p)." \p ($0 mark) me )

    "Give me 5."

The string evaluation – `($$ )`:

    ($ ($$'($($func) ($0) ($1))' \func (`mul) 5 5))

    25

The iterator (modifier), NOT applicable into a loop
or conditional expression, **experimental**:

    ($set i 0)
    ($emit i inc) ($emit i inc) ($emit i dec) ($emit i)

    0 1 2 1

The iterator (modifier) of the list:

    ($set l ($range 5 25 5))
    ($emit l) ($emit l) ($emit l) ($emit l)

    5 10 15 20

The late bound parameter – `\p.. &p`:

    ($ \func.\val.($func val) \p.($q p) regular)
    ($ \p..\func.\val.($func val) ($q &p) late_bound)

    "regular"
    "late_bound"

The variable argument list – `\... __va_args__`, **experimental**:

    ($ \p1.\p2.\...($__va_args__) 1 2 v a _ a r g s)

    va_args

    ($ \val.\...($ ($lazy __va_args__) \func.[($func val) ])
        9.0
        \n.($sqrt n)
        \n.{ 2 * n }
        \n.($pow n 2)
    )

    3.0 18.0 81.0

Getting names of parameters from the list – `\(p).`:

    ($set p (c d))
    ($ \(p).{ c - d } 100 500)
    ($set p (d c))
    ($ \(p).{ c - d } 100 500)

    -400
    400

The atom binding in the expression – `($let )`:

    ($let (p2 p4) (\x.($mul x x) \x.($p2 ($p2 x))) ($p2 ($p4 2)))

    256

Any functions from _"string"_, _"operator"_ and _"math"_ modules of Python
Standard Library can be used in preprocessor expressions –
[Built-in Functions](builtin.md).

The special `($import )` form is provided to include macros and functions
from [yupp Standard Library](../../../blob/master/lib/README.md) or other libraries.

### USAGE

**yupp** is written in Python, the main file is _"yup.py"_. Source files
for preprocessing are passed to **yupp** as command-line arguments.

To learn more about the preprocessor parameters, please get help on
the command-line interface:

    python yup.py -h

The files generated by the preprocessor are getting other extensions
that could come from the original, e.g. _".c"_ for _".yu-c"_.
In failing to translate the preprocessor expressions into a plain text
the evaluation result will be saved as _".ast"_ file.

### EXAMPLE

    >cd yupp
    >more "./eg/hello.yu-c"

```cpp
($set greeting "Hello world!\n")

($set name   (  Co       F              Zu           ))
($set type   (  float    double         float        ))
($set val    (  { pi }   (`acos( -1 ))  { 355/113 }  ))
($set format (  "%.2f"   "%.10f"        "%.6f"       ))

($set each-Pi ($range ($len name)))

#include <math.h>
#include <stdio.h>

int main( void )
{
    ($each-Pi \i.]
        ($i type) ($i name) = ($i val);

    [ )
    printf( ($greeting) );

    ($each-Pi \i.]
        ($set n ($i name))
        printf( ($"($0) = ($1)\n" ($n) ($unq ($i format))), ($n) );

    [ )
    return ( 0 );
}
```

    >python yup.py -q "./eg/hello.yu-c"

    >more "./eg/hello.c"

```cpp
#include <math.h>
#include <stdio.h>

int main( void )
{
    float Co = 3.14159265359;
    double F = acos( -1 );
    float Zu = 3.14159292035;

    printf( "Hello world!\n" );

    printf( "Co = %.2f\n", Co );
    printf( "F = %.10f\n", F );
    printf( "Zu = %.6f\n", Zu );

    return ( 0 );
}
```

[Further examples...](https://github.com/in4lio/yupp/tree/master/eg)

### MACROS IN PYTHON

The easiest way to integrate the preprocessor into Python 2 – to install
the corresponding package:

    pip install yupp

You have to use **pip**, and may need to specify `--pre` key to install
the beta version.

After that you will be able to apply macro expressions in the source
code in Python, starting the script with:

    # coding: yupp

Preprocessor options for all files in a directory can be specified into
_".yuconfig"_ file, individual options for the file in _"file.yuconfig"_.

Nothing hinders to translate any file types using the package:

    python -c "from yupp import pp; pp.translate( 'file.yu-c' )"

[Read more...](../../../tree/master/python)

### SUBLIME TEXT

The folder [_"sublime_text"_](../../../tree/master/sublime_text) contains
configuration files for comfortable
usage of the preprocessor in Sublime Text 2 editor. In addition there is
a plugin for quick navigation between the generated text and its origin.

### VIM

Switching between the generated text and its origin in VIM editor is
[under development](https://github.com/in4lio/vim-yupp/).

### TESTKIT

**yupp** is currently in beta stage. The file called _"test_yup.py"_ contains
a number of _smoke_ tests.

The preprocessor still needs testing and optimization. Also you may run
into problems with completing of the eval-apply cycle when used recursion
or experimental features.

### WEB

- [yupp Wiki](https://github.com/in4lio/yupp/wiki/)
- [yupp Blog](http://yup-py.blogspot.com/)
- [yupp Web Console](http://yup-py.appspot.com/)

### PROJECTS

- [LEGO Mindstorms EV3 Debian C library](https://github.com/in4lio/ev3dev-c/)
- [predict – an embedded application framework](https://github.com/in4lio/predict/)

### GIT

Enter in the following on your command-line to clone **yupp** repository:

    git clone https://github.com/in4lio/yupp.git

### CONTACT

Please feel free to contact me at in4lio+yupp@gmail.com if you have
any questions about the preprocessor.