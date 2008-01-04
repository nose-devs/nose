<html>
  <head>
    <title>nose: a discovery-based unittest extension</title>
    <link rel="stylesheet" href="doc/site.css" type="text/css"></link>
  </head>
  <body>

    
    <div id="menu">
      <h2><a href="/mrl/projects/nose/nose-%(version)s.tar.gz">Download</a></h2>
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
          <a href="doc/">API docs</a> <span class="new">NEW</a>
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
        <li>
          <a href="http://peak.telecommunity.com/DevCenter/setuptools">
            setuptools</a>
        </li>
      </ul>
    </div>
    <div id="main">
      <h1>nose: a discovery-based unittest extension.</h1>

      <p class="note">
	This document refers to nose version %(version)s.
	<a href="/mrl/projects/nose/0.9.3/">Documention for version
	0.9.3</a> is available <a href="/mrl/projects/nose/0.9.3/">here</a>.
      </p>	

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

      <p>However, <b>please note</b> that without setuptools
	installed, you will not be able to use 3rd-party nose plugins.
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

      <p><a href="doc/writing_plugins.html">Write
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
    <script src="http://www.google-analytics.com/urchin.js" 
	    type="text/javascript">
    </script>
    <script type="text/javascript">
      _uacct = "UA-2236166-1";
      urchinTracker();
    </script>
  </body>
</html>
