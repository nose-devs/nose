"""Attribute selector plugin.

Simple syntax (-a, --attr) examples:
  * nosetests -a status=stable
    => only test cases with attribute "status" having value "stable"

  * nosetests -a priority=2,status=stable
    => both attributes must match

  * nosetests -a priority=2 -a slow
    => either attribute must match
    
  * nosetests -a tags=http
    => attribute list "tags" must contain value "http" (see test_foobar()
       below for definition)

  * nosetests -a slow
    => attribute "slow" must be defined and its value cannot equal to False
       (False, [], "", etc...)

  * nosetests -a !slow
    => attribute "slow" must NOT be defined or its value must be equal to False

Eval expression syntax (-A, --eval-attr) examples:
  * nosetests -A "not slow"
  * nosetests -A "(priority > 5) and not slow"

"""
import os
import re
import sys
import textwrap

from nose.plugins.base import Plugin
from nose.util import tolist

compat_24 = sys.version_info >= (2, 4)

class ContextHelper:
    """Returns default values for dictionary lookups."""
    def __init__(self, obj):
        self.obj = obj
        
    def __getitem__(self, name):
        return self.obj.get(name, False)

class AttributeSelector(Plugin):
    """Selects test cases to be run based on their attributes.
    """

    def __init__(self):
        Plugin.__init__(self)
        self.attribs = []
    
    def addOptions(self, parser, env=os.environ):
        """Add command-line options for this plugin."""

        parser.add_option("-a", "--attr",
                          dest="attr", action="append",
                          default=env.get('NOSE_ATTR'),
                          help="Run only tests that have attributes "
                          "specified by ATTR [NOSE_ATTR]")
        # disable in < 2.4: eval can't take needed args
        if compat_24:
            parser.add_option("-A", "--eval-attr",
                              dest="eval_attr", metavar="EXPR", action="append",
                              default=env.get('NOSE_EVAL_ATTR'),
                              help="Run only tests for whose attributes "
                              "the Python expression EXPR evaluates "
                              "to True [NOSE_EVAL_ATTR]")

    def configure(self, options, config):
        """Configure the plugin and system, based on selected options.

        attr and eval_attr may each be lists.

        self.attribs will be a list of lists of tuples. In that list, each
        list is a group of attributes, all of which must match for the rule to
        match.
        """
        self.attribs = []
        
        # handle python eval-expression parameter
        if compat_24 and options.eval_attr:
            eval_attr = tolist(options.eval_attr)
            for attr in eval_attr:
                # "<python expression>"
                # -> eval(expr) in attribute context must be True
                def eval_in_context(expr, attribs):
                    return eval(expr, None, ContextHelper(attribs))
                self.attribs.append([(attr, eval_in_context)])

        # attribute requirements are a comma separated list of
        # 'key=value' pairs
        if options.attr:
            std_attr = tolist(options.attr)
            for attr in std_attr:
                # all attributes within an attribute group must match
                attr_group = []
                for attrib in attr.split(","):
                    # don't die on trailing comma
                    if not attrib:
                        continue
                    items = attrib.split("=", 1)
                    if len(items) > 1:
                        # "name=value"
                        # -> 'str(obj.name) == value' must be True
                        key, value = items
                    else:
                        key = items[0]
                        if key[0] == "!":
                            # "!name"
                            # 'bool(obj.name)' must be False
                            key = key[1:]
                            value = False
                        else:
                            # "name"
                            # -> 'bool(obj.name)' must be True
                            value = True
                    attr_group.append((key, value))
                self.attribs.append(attr_group)
        if self.attribs:
            self.enabled = True
            
    def validateAttrib(self, attribs):
        # TODO: is there a need for case-sensitive value comparison?

        # within each group, all must match for the group to match
        # if any group matches, then the attribute set as a whole
        # has matched
        any = False
        for group in self.attribs:
            match = True
            for key, value in group:
                obj_value = attribs.get(key)
                if callable(value):
                    if not value(key, attribs):
                        match = False
                        break
                elif value is True:
                    # value must exist and be True
                    if not bool(obj_value):
                        match = False
                        break
                elif value is False:
                    # value must not exist or be False
                    if bool(obj_value):
                        match = False
                        break
                elif type(obj_value) in (list, tuple):
                    # value must be found in the list attribute
                    if not value in [str(x).lower() for x in obj_value]:
                        match = False
                        break
                else:
                    # value must match, convert to string and compare
                    if (value != obj_value
                        and str(value).lower() != str(obj_value).lower()):
                        match = False
                        break
            any = any or match
        if any:
            # not True because we don't want to FORCE the selection of the
            # item, only say that it is acceptable
            return None
        return False
        
    def wantFunction(self, function):
        return self.validateAttrib(function.__dict__)
        
    def wantMethod(self, method):
        # start with class attributes...
        cls = method.im_class
        attribs = cls.__dict__.copy()
        # method attributes override class attributes
        attribs.update(method.__dict__)
        return self.validateAttrib(attribs)
