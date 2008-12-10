Generating HTML Coverage with nose
----------------------------------

.. Note ::

    HTML coverage requires Ned Batchelder's coverage.py module.

..
    >>> from nose.plugins.plugintest import run_buffered as run
    >>> import os
    >>> support = os.path.join(os.path.dirname(__file__), 'support')
    >>> cover_html_dir = os.path.join(support, 'cover')
    >>> from nose.plugins.cover import Coverage
    >>> run(argv=[__file__, '-v', '--with-coverage', '--cover-package=blah', 
    ...           '--cover-html', '--cover-html-dir=' + cover_html_dir, support, ], 
    ...     plugins=[Coverage()])
    test_covered.test_blah ... hi
    ok
    <BLANKLINE>
    Name    Stmts   Exec  Cover   Missing
    -------------------------------------
    blah        4      3    75%   6
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    OK
    >>> print open(os.path.join(cover_html_dir, 'index.html')).read()
    <html><head><title>Coverage Index</title></head><body><p>Covered: 3 lines<br/>
    Missed: 1 lines<br/>
    Skipped 3 lines<br/>
    Percent: 75 %<br/>
    <table><tr><td>File</td><td>Covered</td><td>Missed</td><td>Skipped</td><td>Percent</td></tr><tr><td><a href="blah.html">blah</a></td><td>3</td><td>1</td><td>3</td><td>75 %</td></tr></table></p></html
    >>> print open(os.path.join(cover_html_dir, 'blah.html')).read()
    <html>
    <head>
    <title>blah</title>
    </head>
    <body>
    blah
    <style>
    pre {float: left; margin: 0px 1em }
    .num pre { margin: 0px }
    .nocov {background-color: #faa}
    .cov {background-color: #cfc}
    div.coverage div { clear: both; height: 1em}
    </style>
    <div class="stats">
    Covered: 3 lines<br/>
    Missed: 1 lines<br/>
    Skipped 3 lines<br/>
    Percent: 75 %<br/>
    <BLANKLINE>
    </div>
    <div class="coverage">
    <div class="cov"><span class="num"><pre>1</pre></span><pre>def dostuff():</pre></div>
    <div class="cov"><span class="num"><pre>2</pre></span><pre>    print 'hi'</pre></div>
    <div class="skip"><span class="num"><pre>3</pre></span><pre></pre></div>
    <div class="skip"><span class="num"><pre>4</pre></span><pre></pre></div>
    <div class="cov"><span class="num"><pre>5</pre></span><pre>def notcov():</pre></div>
    <div class="nocov"><span class="num"><pre>6</pre></span><pre>    print 'not covered'</pre></div>
    <div class="skip"><span class="num"><pre>7</pre></span><pre></pre></div>
    </div>
    </body>
    </html>
    <BLANKLINE>
