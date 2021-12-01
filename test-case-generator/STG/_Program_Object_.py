# -*- coding: utf-8 -*-
# Copyright (C) 2015-2021 Martin Glueck All rights reserved
# Neugasse 2, A--2244 Spannberg, Austria. martin@mangari.org
# #*** <License> ************************************************************#
# This module is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this module. If not, see <http://www.gnu.org/licenses/>.
# #*** </License> ***********************************************************#
#
#++
# Name
#    STG._Program_Object_
#
# Purpose
#    Base class for all STG objects belonging to a program
#
#--

from   STG._Object_     import _STG_Object_, Once_Property
from STG.Parameter      import Parameter_Ref

class _Program_Object_ (_STG_Object_) :
    """Base class for all objects belonging to a program"""

    def __init__ (self, * args, ** kw) :
        super ().__init__ (* args, ** kw)
        self.children = []
    # end def __init__

    def _visit_element(self, program, xml, static, parent = None) :
        result = (parent or self).children
        for child in xml.getchildren () :
            _, tag = child.tag.split ("}")
            fct    = getattr (self, "_visit_%s" % (tag, ), None)
            if fct :
                fct (program, child, static)
            else :
                pass
                print ("Ignore child", child)
    # end def _parse_xml

    def _visit_Assign(self, program, xml, static) :
        self.children.append (Assign (program, xml, static, self))
    # end def _visit_Assign

    def _visit_ParameterBlock (self, program, xml, static) :
        self.children.append (Parameter_Block (program, xml, static, self))
    # end def _visit_ParameterBlock

    def _visit_Channel (self, program, xml, static) :
        ### right know I have no idea what a channel does )-;
        self._visit_element (program, xml, static)
    # end def _visit_Channel

    def _visit_ChannelIndependentBlock (self, program, xml, static) :
        ### right know I have no idea what a channel does )-;
        self._visit_element (program, xml, static)
    # end def _visit_ChannelIndependentBlock

    def _visit_choose (self, program, xml, static) :
        self.children.append (Choose (program, xml, static, self))
    # end def _visit_choose

    def _visit_ParameterRefRef (self, program, xml, static) :
        self.children.append \
            (static.Parameter_Ref (xml.get ("RefId"), self, program))
    # end def _visit_ParameterRefRef

    def _visit_ParameterSeparator (self, program, xml, static) :
        self.children.append \
            (Parameter_Separator (program, xml, static, self))
    # end def _visit_ParameterSeparator

    def _visit_when (self, program, xml, static) :
        self.children.append (When (program, xml, static, self))
    # end def _visit_when

    def _visit_ComObjectRefRef (self, program, xml, static) :
        self.children.append \
            ( static.get
                ( xml.get ( "RefId"), "ComObjectRef"
                , Com_Object_Ref
                , static = static, parent = self, program = program
                )
            )
    # end def _visit_ComObjectRefRef

    @property
    def pickle_cargo (self) :
        result              = super ().pickle_cargo
        result ["children"] = children = []
        for c in self.children :
            children.append ((c.__class__, c.pickle_cargo))
        return result
    # end def pickle_cargo
    @classmethod

    def From_Pickle (cls, program, state, parent = None) :
        children        = state.pop ("children", ())
        result          = super (_Program_Object_, cls).From_Pickle (state)
        if program is None :
            program                 = result
            program.parameter_refs  = dict ()
            program.com_object_refs = dict ()
        result.children             = []
        result.parent               = parent
        add                         = result.children.append
        for (ccls, cstate) in children :
            if ccls is Parameter_Ref :
                obj                 = Parameter_Ref.Table [cstate ["id"]]
                obj.parent          = result
                add (obj)
                program.parameter_refs [obj.id] = obj
            elif ccls is Com_Object_Ref :
                obj                 = Com_Object_Ref.Table [cstate ["id"]]
                obj.parent          = result
                add (obj)
                program.com_object_refs [obj.id] = obj
            else :
                ##print (ccls, state)
                add (ccls.From_Pickle (program, cstate, result))
        return result
    # end def From_Pickle

# end class _Program_Object_

class Parameter_Block (_Program_Object_) :
    """A set of parameter group logically together."""

    Macro            = "block"
    Value_Attributes = ("id", "raw_name", "raw_text")
    Ref_Attributes   = ( ("ref", Parameter_Ref), )
    ref              = None

    def __init__ (self, program, xml, static, parent) :
        super ().__init__ ()
        self.parent    = parent
        self.xml       = xml
        self.static    = static
        self.id        = xml.get ("Id")
        self.raw_name  = xml.get ("Name")
        self.raw_text  = xml.get ("Text")
        ref_id         = xml.get ("ParamRefId")
        if ref_id is not None :
            self.ref   = static.Parameter_Ref (ref_id, self, program)
        if self.Debug :
            print ("%sPB %s [%s] [%s]" % (self.head_indent, self.id, self.name, self.text))
        self._visit_element (program, xml, static)
    # end def __init__

    @Once_Property
    def text (self) :
        if self.raw_text :
            return Language.Translation (self.id, "Text", self.raw_text)
        return self.ref.parameter.text or self.name
    # end def text

    @Once_Property
    def name (self) :
        if self.raw_name :
            return Language.Translation (self.id, "Name", self.raw_name)
        return self.ref.parameter.name
    # end def name

    def __str__ (self) :
        return "PB [%s] %s/%s" % (self.id, self.text, self.name)
    # end def __str__

# end class Parameter_Block

class Choose (_Program_Object_) :
    """Select one of multiple possible childrens"""

    Macro            = "choose"
    Value_Attributes = ("id", )
    Ref_Attributes   = ( ("ref", Parameter_Ref), )

    def __init__ (self, program, xml, static, parent) :
        super ().__init__ ()
        self.xml    = xml
        self.parent = parent
        self.id     = str (id (self)) ### choose does not have a unique id
        self.ref    = static.Parameter_Ref \
            (xml.get ("ParamRefId"), self, program)
        if self.Debug :
            print ("%sCH %s" % (self.head_indent, self.ref.id))
        self._visit_element (program, xml, static)
    # end def __init__

    @Once_Property
    def text (self) :
        return "? %s" % (self.ref.text, )
    # end def text

# end class Choose

class When (_Program_Object_) :
    """XXX"""

    Macro            = "when"
    Value_Attributes = ("id", "test")

    def __init__ (self, program, xml, static, choose) :
        super ().__init__ ()
        self.xml     = xml
        self.static  = static
        self.choose  = self.parent = choose
        self.test    = int (xml.get ("test", "-1"))
        self.id      = "%s-%s" % (choose.id, self.test)
        if self.Debug :
            print ( "%sWH %s %s %s"
                  % ( self.head_indent, choose.ref.id, self.test
                    , self.test_as_text
                    )
                  )
        self._visit_element (program, xml, static)
    # end def __init__

    @Once_Property
    def choose (self) :
        return self.parent
    # end def choose

    @Once_Property
    def test_as_text (self) :
        return self.choose.ref.parameter.type.value_as_text (self.test)
    # end def test_as_text

    @Once_Property
    def text (self) :
        test = self.test
        return "== %s (%s)" % (test, self.choose.ref.type.value_as_text (test))
    # end def text

# end class When

class Assign (_Program_Object_) :
    """Assign an value to a different parameter"""
    
    Macro            = "assign"
    Value_Attributes = ("id", "value")
    Ref_Attributes   = ( ("target_parameter_ref", Parameter_Ref)
                       , ("source_param_ref",     Parameter_Ref)
                       )
    source_param_ref = None
    
    def __init__ (self, program, xml, static, parent) :
        super ().__init__ ()
        self.xml     = xml
        self.static  = static
        self.parent  = parent
        self.value   = int (xml.get ("Value", "-1"))
        self.target_parameter_ref = static.Parameter_Ref \
            (xml.get ("TargetParamRefRef"), self, program)
        src_ref = xml.get ("SourceParamRefRef", None)
        if src_ref is not None :
            self.source_param_ref = static.Parameter_Ref \
            (src_ref, self, program)
        self.id      = "%s-A-%s" % (parent.id, self.target_parameter_ref.id)
        if self.Debug :
            print ( "%sWH %s %s %s"
                  % ( self.head_indent, choose.ref.id, self.test
                    , self.test_as_text
                    )
                  )
    # end def __init__

    @Once_Property
    def parameter (self) :
        return self.target_parameter_ref.parameter
    # end def parameter
    
# end class Assign



from STG.Com_Object     import Com_Object_Ref
### __END__ STG._Program_Object_
