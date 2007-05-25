<html>
  <head>
    <title>nose: a discovery-based unittest extension</title>
    <style>
      body {
      margin 0px;
      padding: 10px 40px;
      font: x-small Georgia,Serif;
      font-size/* */:/**/small;
      font-size: /**/small;
      }
      a:link {
      color:#58a;
      text-decoration:none;
      }
      a:visited {
      color:#969;
      text-decoration:none;
      }
      a:hover {
      color:#c60;
      text-decoration:underline;
      }

      #menu {
      padding-left 1em;
      padding-right: 1em;
      padding-bottom: 10px;
      margin-left: 20px;
      min-width: 200px;
      width: 20%%;
      border-left: 1px solid #ddd;
      border-bottom: 1px solid #ddd;
      background-color: #fff;
      float: right;
      }
      
      #main {
      margin: 0px;
      padding: 0px;
      padding-right: 20px;
      width: 70%%;
      float: left;
      }      

      h1 {
      font-size: 140%%;
      margin-top: 0;
      }

      .section h1 {
      font-size: 120%%;
      }

      .section h2 {
      font-size: 105%%;
      }
      
      pre.literal-block {
      font: small;
      background: #ddd;
      }

      #menu ul {
      margin: 0 1em .25em;
      padding: 0;
      list-style:none;
      }

      #menu h2 {
      font-size: 100%%;
      color: #999;
      margin: 0 .5em;
      padding: 0;
      }
      
      #menu ul li {
      margin: 0px;
      padding: 0px 0px 0px 15px;
      text-indent:-15px;
      /* line-height:1.5em; */
      }
      
      #menu p, #menu ol li {
      font-size: 90%%;
      color:#666;
      /* line-height:1.5em; */
      margin: 0 1em .5em;
      }

      #menu ul li {
      font-size: 90%%;
      color:#666;
      }
      
      #menu dd {
      margin: 0;
      padding:0 0 .25em 15px;
      }

      #news {
      border: 1px solid #999;
      background-color: #eef;
      /* wouldn't it be nice if this worked */
      background-image: url(flake.svg);
      padding: 4px;
      padding-right: 8px;
      }

      #news h2 {
      margin-top: 0px;
      font-size: 105%%;
      }

      #news li p {
        margin-left: 1.5em;
      }

      #news li p.first {
        margin-left: 0;
        font-weight: bold;
      }
      
      #news p {
      margin-bottom: 0px;
      }

      p.note {
      background: #fed;
      border: 1px solid black;
      padding: 6px;
      }
    </style>
  </head>
  <body>

    
    <div id="menu">
      <h2><a href="nose-%(version)s.tar.gz">Download</a></h2>
      <p>Current version: %(version)s <br />(%(date)s)</p>
            
      <h2>Install</h2>
      <p>Current version: <br /><tt>easy_install nose==%(version)s</tt></p>
      <p>Unstable (trunk): <br /><tt>easy_install nose==dev</tt></p>

      <h2>Read</h2>
      <ul>
        <li>
          <a href="http://code.google.com/p/python-nose/w/list">
            Wiki
          </a>
        </li>
        <li>
          <a href="doc/">API docs</a>
        </li>
        <li>
          <a href="http://ivory.idyll.org/articles/nose-intro.html">
            An Extended Introduction to the nose Unit Testing Framework
          </a>
          <br />Titus Brown's excellent article provides a great overview of
          nose and its uses.
        </li>
        <li><a href="#usage">nosetests usage</a>
          <br />How to use the command-line test runner.
        </li>
      </ul>

      <h2><a href="http://groups.google.com/group/nose-announce">
          Announcement list</a></h2>
      <p>Sign up to receive email announcements
        of new releases</p>

      <h2><a href="http://code.google.com/p/python-nose/">Tracker</a></h2>
      <p>Report bugs, request features, wik the wiki, browse source.</p>

      <h2>Get the code</h2>
      <p><tt>svn co http://python-nose.googlecode.com/svn/trunk/ nose</tt></p>
      
      <h2>Other links</h2>
      <ul>
        <li><a href="/mrl/">My blog</a></li>
        <li>
          <a href="http://codespeak.net/py/current/doc/test.html">py.test</a>
        </li>
        <li><a href="http://www.turbogears.com/testgears/">testgears</a></li>
        <li>
          <a href="http://peak.telecommunity.com/DevCenter/setuptools">
            setuptools</a>
        </li>
      </ul>
    </div>
    <div id="main">
      <h1>nose: a discovery-based unittest extension.</h1>

      <p>nose provides an alternate test discovery and running process for
        unittest, one that is intended to mimic the behavior of py.test as much
        as is reasonably possible without resorting to too much magic.
      </p>
      
      <div id="news">
        <h2>News</h2>
        %(news)s
        <p>See the <a href="#changelog">changelog</a> for details.</p>
      </div>

      <h2>Install</h2>

      <p class="note">
        On most UNIX-like systems, you'll probably need to run these commands
        as root or using sudo.
      </p>

      <p>Install nose using setuptools:
        <pre>easy_install nose</pre>
      </p>

      <p>Or, if you don't have setuptools installed, use the download link at
      right to download the source package, and install in the normal fashion:
      Ungzip and untar the source package, cd to the new directory, and:

        <pre>python setup.py install</pre>
      </p>

      <p>If you have an older version of setuptools installed, you may see an
        error like this:
        
        <blockquote>
          <tt>The required version of setuptools (>=0.6c5) is not available, and
          can't be installed while this script is running. Please install
          a more recent version first.</tt>
        </blockquote>
        
        In that case, you'll need to update your setuptools install first,
        either by running:

        <pre>easy_install -U setuptools</pre>

        or:

        <pre>python ez_setup.py</pre>
      </p>
        
      %(body)s
      
      <h2><a name="commands"></a>nosetests setuptools command</h2>

      %(commands)s
      
      <h2><a name="usage"></a>nosetests usage</h2>

      %(usage)s
      
      <h2>Bug reports</h2>

      <p>Please report bugs and make feature
      requests <a href="http://code.google.com/p/python-nose/">here</a>.</p>
      
      <h2>Hack</h2>

      <p><a href="http://code.google.com/p/python-nose/wiki/WritingPlugins">Write
          plugins!</a> It's easy and fun.</p>
      
      <p>Get the code:
        <pre>svn checkout http://python-nose.googlecode.com/svn/trunk/ nose</pre>
      </p>

      <p><a href="mailto:jpellerin+nose@gmail.com">Patches are
          welcome</a>. I'd suggest grabbing a copy
          of <a href="http://svk.elixus.org/">svk</a> so that you can have
          local version control and submit full patches against an up-to-date
          tree easily.
      </p>
      
      <p>Thanks to Google for providing the Google code hosting service.</p>
      
      <h2><a name="changelog"></a>Changelog</h2>
      %(changelog)s

      %(coda)s
      
    </div>
    
  </body>
</html>
