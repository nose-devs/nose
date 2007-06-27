<html>
  <head>
    <title>nose: %(title)s</title>
    <link rel="stylesheet" href="site.css" type="text/css"></link>
  </head>
  <body>
    
    <div id="menu">
      <p>This document covers nose version <b>%(version)s</b></p>
      <p>Last update: <b>%(date)s</b></p>
      %(menu)s
      %(sub_menu)s
    </div>
    
    <div id="main">
      <h1>%(title)s</h1>
      
      %(body)s

      <h2>Plugin Interface Methods</h2>

      <p>Plugin interface methods are described below, in alphabetical
	order. Methods that are <span class="method new"
	style="padding: 1px;">new</span> in
	this release are <span class="method new" style="padding: 1px;">highlighted</span>. 
	<span style="text-decoration: line-through; padding: 0px;">
	  Deprecated methods</span> are struck through. Methods that
	may be generators are labeled with the icon <img src="gen.png"
	alt="generative"/>. Methods that are chainable (that is, the
	results of calling the method on one plugin are passed as
	input to the next plugin) are labeled with the icon
	<img src="chain.png" alt="chainable" />.</p>

      %(methods)s

    </div>

    <div id="footer">
      Icons from tango project and gnome.
    </div>

  </body>
</html>
  
