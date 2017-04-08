Markdown version of README still under development...


    yet another lexical preprocessor
     __    __    _____ _____
    /\ \  /\ \  /\  _  \  _  \
    \ \ \_\/  \_\/  \_\ \ \_\ \
     \ \__  /\____/\  __/\  __/
      \/_/\_\/___/\ \_\/\ \_\/
         \/_/      \/_/  \/_/

    ($($\y:u.\m.\...(m y($\C.\p.(r)e p)($\ro.(ce)s)))so r)

### WHAT IS IT?

**yupp** is a lexical preprocessor which implements the macro language
with Lisp-like Polish notation syntax in fully parenthesized form.
**yupp** is intended to transform C programs before they are compiled.
It can also be useful for more general purposes, if you would like
to use the preprocessor with Python 2 just install "yupp" package.

**yupp** allows to generate a readable, well-formatted text. Special
attention is paid to providing complete diagnostic information and
navigational capabilities.

Embedding of the preprocessor expressions into the source code occurs
by using an _application_ form, e.g. `($e)`.

A small example with comments:
    https://github.com/in4lio/yupp/blob/master/doc/glance.md

    ___        ___________________________________
    ___ SYNTAX ___________________________________

    Main syntactic categories of the macro language are: list, application
    and lambda expression.

    List is a sequence of expressions separated by blanks and enclosed
    in parentheses.

    <list> ::= '(' { <expression> } ')'

    e.g. (0.5 "string" atom)

    Application is an applying a function to arguments, it syntactically
    differs from a list in presence of the dollar sign after the open
    parenthesis.

    <application> ::= '($' <function> { <argument> } ')'

    ($add 2 3)

    Lambda is an anonymous function, it consists of a sequence of parameters
    and a function body.

    <lambda> ::= <param> { <param> } <expression>
    <param>  ::= '\' <name> [ ':' <default> ] '.'

    \p.($sub p 1)

    Syntactic forms can be nested within each other but, as mentioned above,
    only an application can be embedded into the source code directly.

    The following examples show various syntactic constructs of the macro
    language. Try them using yupp Web Console (http://yup-py.appspot.com/).

    ($! this is a comment, won't be saved in the generated text )

    ($! binding of the atom (identifier) with the value )

        ($set a 'A')

    ($! the atom binding with the list )

        ($set abc (a 'B' 'C' 'D' 'E'))

    ($! binding of the atom with the lambda is a function definition )

        ($set inc \val.($add val 1))

    ($! application of the number is subscripting )

        ($2 miss miss HIT miss)

    HIT

    ($! getting the specific element of the list )

        ($0 abc)

    'A'

    ($! application of the list is "for each" loop )

        ($(0 1 2) \i.($inc i))

    123

    ($! embedding of one list into another – *list )

        ($set mark (5 4 *(3 2) 1))

    ($! infix expression on Python – { } )

        ($set four { 2 + 2 })

    ($! infix expression straight into the source code )

        foo = (${} sqrt(four) * 5.0);

    foo = 10.0;

    ($! conditional expression – consequent ? condition | alternative )

        ($set fact \n.($ 1 ? { n == 0 } | { ($fact { n - 1 }) * n }))
        ($fact 10)

    3628800

    ($! enclosing of the source code into the application )

        ($abc \ch.($code putchar(($ch));))

    putchar('A'); putchar('B'); putchar('C'); putchar('D'); putchar('E');

    ($! the source code enclosing with square brackets – [ ] )

        ($mark \i.[($i), ])

    5, 4, 3, 2, 1,

    ($! the function parameter with default value – \p:val. )

        ($set if \cond.\then:[].\else:[].($ then ? cond | else ))

    ($! the named argument )

        ($if { four != 4 } \else OK )

    OK

    ($! the macro definition )

        ($macro GRADE ( PAIRS )
            ($set GRADE-name  ($ (($PAIRS)) \p.($0 p)))
            ($set GRADE-value ($ (($PAIRS)) \p.($1 p)))
            ($set each-GRADE  ($range ($len (($PAIRS)) )))
        )

    ($! the quote – (` ) )

        ($GRADE
            (`
                ( A 5 )
                ( B 4 )
                ( C 3 )
                ( D 2 )
                ( E 1 )
            )
        )

    ($! enclosing of the source code into the loop
        with reverse square brackets – ]<EOL> <EOL>[ )

        ($each-GRADE \i.]
            int ($i GRADE-name) = ($i GRADE-value);

        [ )

    int A = 5;
    int B = 4;
    int C = 3;
    int D = 2;
    int E = 1;

    ($! the source code enclosing with double comma – ,, )

        ($import stdlib)
        ($hex ($BB,,11000000,,11111111,,11101110))

    0xc0ffee

    ($! the string substitution )

        ($ "Give ($0) ($p)." \p ($0 mark) me )

    "Give me 5."

    ($! the string evaluation – ($$ ) )

        ($ ($$'($($func) ($0) ($1))' \func (`mul) 5 5))

    25

    ($! the iterator (modifier) – experimental!
        NOT applicable into a loop or conditional expression )

        ($set i 0)
        ($emit i inc) ($emit i inc) ($emit i dec) ($emit i)

    0 1 2 1

    ($! the iterator (modifier) of the list )

        ($set l ($range 5 25 5))
        ($emit l) ($emit l) ($emit l) ($emit l)

    5 10 15 20

    ($! the late bound parameter – \p.. &p )

        ($ \func.\val.($func val) \p.($q p) regular)
        ($ \p..\func.\val.($func val) ($q &p) late_bound)

    "regular"
    "late_bound"

    ($! the variable argument list – \... __va_args__ – experimental! )

        ($ \p1.\p2.\...($__va_args__) 1 2 v a _ a r g s)

    va_args

        ($ \val.\...($ ($lazy __va_args__) \func.[($func val) ])
            9.0
            \n.($sqrt n)
            \n.{ 2 * n }
            \n.($pow n 2)
        )

    3.0 18.0 81.0

    ($! getting names of parameters from the list – \(p). )

        ($set p (c d))
        ($ \(p).{ c - d } 100 500)
        ($set p (d c))
        ($ \(p).{ c - d } 100 500)

    -400
    400

    Any functions from "string", "operator" and "math" modules of Python
    Standard Library can be used in preprocessor expressions
    (https://github.com/in4lio/yupp/blob/master/doc/builtin.md).

    The special ($import ) form is provided to include macros and functions
    from yupp Standard Library or other libraries
    (https://github.com/in4lio/yupp/blob/master/lib/README.md).

    ___       ____________________________________
    ___ USAGE ____________________________________

    yupp is written in Python, the main file is "yup.py". Source files
    for preprocessing are passed to "yup.py" as command-line arguments.

    To learn more about the preprocessor parameters, please get help on
    the command-line interface:

        python yup.py -h

    The files generated by the preprocessor are getting other extensions
    that could come from the original, e.g. ".c" for ".yu-c".
    In failing to translate the preprocessor expressions into a plain text
    the evaluation result will be saved as ".ast" file.

    ___         __________________________________
    ___ EXAMPLE __________________________________

    >cd yupp
    >more "./eg/hello.yu-c"

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

    >python yup.py -q "./eg/hello.yu-c"

    >more "./eg/hello.c"

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

    Further examples:

        https://github.com/in4lio/yupp/tree/master/eg

    ___                   ________________________
    ___ MACROS IN PYTHON  ________________________

    The easiest way to integrate the preprocessor into Python 2 - to install
    the corresponding package:

        pip install yupp

    You have to use "pip", and may need to specify "--pre" key to install
    the beta version.

    After that you will be able to apply macro expressions in the source
    code on Python, starting the script with:

        # coding: yupp

    Preprocessor options for all files in a directory can be specified into
    ".yuconfig" file, individual options for the file in "file.yuconfig".

    Nothing hinders to translate any file types using the package:

        python -c "from yupp import pp; pp.translate( 'file.yu-c' )"

    Read more:

        https://github.com/in4lio/yupp/tree/master/python

    ___              _____________________________
    ___ SUBLIME TEXT _____________________________

    The folder "sublime_text" contains configuration files for comfortable
    usage of the preprocessor in Sublime Text 2 editor. In addition there is
    a plugin for quick navigation between the generated text and its origin.

    ___     ______________________________________
    ___ VIM ______________________________________

    Switching between the generated text and its origin in VIM editor:

        https://github.com/in4lio/vim-yupp (under development)

    ___         __________________________________
    ___ TESTKIT __________________________________

    yupp is currently in beta stage. The file called "test_yup.py" contains
    a number of smoke tests.

    The preprocessor still needs testing and optimization. Also you may run
    into problems with completing of the eval-apply cycle when used recursion
    or experimental features.

    ___     ______________________________________
    ___ WEB ______________________________________

    o   The project on GitHub:
        https://github.com/in4lio/yupp/
        https://github.com/in4lio/yupp/wiki/

    o   yupp Blog:
        http://yup-py.blogspot.com/

    o   yupp Web Console:
        http://yup-py.appspot.com/

    ___          _________________________________
    ___ PROJECTS _________________________________

    o   LEGO Mindstorms EV3 Debian C library:
        https://github.com/in4lio/ev3dev-c/

    o   predict – an embedded application framework:
        https://github.com/in4lio/predict/

    ___     ______________________________________
    ___ GIT ______________________________________

    Enter in the following on your command-line to clone yupp repository:

        git clone https://github.com/in4lio/yupp.git

    ___         __________________________________
    ___ CONTACT __________________________________

    Please feel free to contact me at in4lio+yupp@gmail.com if you have
    any questions about the preprocessor.