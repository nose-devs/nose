"""
Lists builtin plugins
"""
plugins = []
builtins = (
    ('nose.plugins.attrib', 'AttributeSelector'),
    ('nose.plugins.capture', 'Capture'),
    ('nose.plugins.cover', 'Coverage'),
    ('nose.plugins.debug', 'Pdb'),
    ('nose.plugins.deprecated', 'Deprecated'),
    ('nose.plugins.doctests', 'Doctest'),
    ## ('nose.plugins.isolation', 'Isolation'),
    ('nose.plugins.failuredetail', 'FailureDetail'),
    ('nose.plugins.prof', 'Profile'),
    ('nose.plugins.skip', 'Skip'),
    ('nose.plugins.testid', 'TestId')
    )

for module, cls in builtins:
    try:
        plugmod = __import__(module, globals(), locals(), [cls])
    except ImportError:
        continue
    plug = getattr(plugmod, cls)
    plugins.append(plug)
    globals()[cls] = plug
