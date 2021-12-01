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
#    STG.Parameter_Block
#
# Purpose
#    A parameter block is represented as a `page`
#
#--

from   Once_Property            import Once_Property
from   STG._Object_             import _STG_Object_
from   STG.Language             import Language
from   collections              import OrderedDict

class Absolute_Segment (_STG_Object_) :
    """A absolute located code segment"""

    Value_Attributes = ("id", "address", "size", "data", "mask")
    Table            = dict ()

    def __init__ (self, xml, static) :
        super ().__init__ ()
        self.xml     = xml
        self.id      = xml.get ("Id")
        self.address = int (xml.get ("Address"))
        self.size    = int (xml.get ("Size"))
        self.data    = self.get (xml, "E:Data", default = None)
        self.mask    = self.get (xml, "E:Mask", default = None)
    # end def __init__

# end class Absolute_Segment

class Parameter_Type (_STG_Object_) :
    """A parameter type"""

    Table             = dict ()
    Value_Attributes  = ("id", "Macro", "size", "choices", "min", "max")

    choices           = dict ()
    min = max = Macro = None

    def __init__ (self, xml, static) :
        super ().__init__ ()
        self.xml    = xml
        self.id     = xml.get ("Id")
        type        = xml.getchildren () [0]
        tag         = type.tag.split ("}") [-1]
        if   tag == "TypeNumber" :
            self.Macro = "input"
            self.size  = int (type.get ("SizeInBit", "0"))
            self.min   = int (type.get ("minInclusive", "0"))
            self.max   = int (type.get ("maxInclusive", "0"))
        elif tag == "TypeRestriction" :
            self.Macro = "select"
            self.size  = int (type.get ("SizeInBit", "0"))
            self._setup_choices (type)
        else :
            self.size = 0
    # end def __init__

    def _setup_choices (self, xml) :
        choices = []
        for idx, c in enumerate (xml.getchildren ()) :
            text = Language.Translation \
                (c.get ("Id"), "Text", c.get ("Text"))
            choices.append \
                ( ( int (c.get ("DisplayOrder", str (idx)))
                  , int (c.get ("Value")), text
                  )
                )
        choices.sort ()
        self.choices = OrderedDict ((v, t) for (_, v, t) in choices)
    # end def _setup_choices

    def value_as_text (self, value) :
        if value in self.choices :
            return self.choices [value]
        return str (value)
    # end def value_as_text

# end class Parameter_Type

class Parameter (_STG_Object_) :
    """A parameter of a eib device"""

    Table            = dict ()
    Value_Attributes = ( "id", "value", "access", "name", "raw_text", "raw_name"
                       , "address", "offset", "bit_offset", "size", "mask"
                       )
    Ref_Attributes   = ( ("type",   Parameter_Type)
                       , ("memory", Absolute_Segment)
                       )
    address          = offset = size = bit_offset = mask = 0
    memory           = None
    value            = None

    def __init__ (self, xml, static) :
        super ().__init__ ()
        self.xml      = xml
        self.id       = xml.get ("Id")
        self.raw_text = xml.get ("Text")
        self.raw_name = xml.get ("Name")
        self.type     = static.Parameter_Type (xml.get ("ParameterType"))
        if self.type.size :
            self.value   = int    (xml.get ("Value") or "-1")
        self.access  = xml.get    ("Access", "ReadWrite")
        mem          = self.get (xml, "E:Memory", default = None)
        if mem is None :
            parent   = xml.getparent ()
            tag      = parent.tag.split ("}") [1]
            if tag == "Union" :
                mem  = self.get (parent, "E:Memory")
        if mem is not None :
            self.memory     = static.Memory (mem.get ("CodeSegment"))
            self.offset          = \
                int (mem.get ("Offset")) + int (xml.get ("Offset", "0"))
            self.address    = self.memory.address + self.offset
            self.bit_offset =  \
                int (mem.get ("BitOffset")) + int (xml.get ("BitOffset", "0"))
            self.size       = self.type.size
            self.mask       = ((2 ** self.size) - 1) << self.bit_offset
    # end def __init__

    @Once_Property
    def text(self) :
        return Language.Translation (self.id, "Text", self.raw_text)
    # end def text

    @Once_Property
    def name (self) :
        return self.raw_name
    # end def name

# end class Parameter

class Parameter_Ref (_STG_Object_) :
    """A reference to a parameter"""

    Table            = dict ()
    Value_Attributes = ("id", "value")
    Ref_Attributes   = (("parameter", Parameter), )

    Macro            = "parameter_ref"

    def __init__ (self, program, xml, static, parent) :
        super ().__init__ ()
        self.xml       = xml
        self.id        = xml.get ("Id")
        self.parent    = parent
        self.parameter = static.Parameter (xml.get ("RefId"))
        self.value     = xml.get ("Value", self.undefined)
        if self.value == self.undefined :
            self.value = self.parameter.value
        else :
            self.value = int (self.value)
        if self.Debug :
            print ( "%sPR %s [%s] {%s} %s"
                  % ( self.head_indent, self.id, self.name, self.text
                    , self.parameter.access
                    )
                  )
        assert self.id not in program.parameter_refs
        program.parameter_refs [self.id] = self
    # end def __init__

    @Once_Property
    def type (self) :
        return self.parameter.type
    # end def type

    @Once_Property
    def name (self) :
        return self.parameter.name
    # end def name

    @Once_Property
    def text (self) :
        return self.parameter.text
    # end def text

    @Once_Property
    def access (self) :
        return self.parameter.access
    # end def access

    @Once_Property
    def value_as_text (self) :
        return self.type.value_as_text (self.value)
    # end def value_as_text

# end class Parameter_Ref

### Parameter_Block moved into _Program_Object_

class Parameter_Separator (_STG_Object_) :
    """A empty line in the editor"""

    Macro = "seperator"
    
    def __init__ (self, program, xml, static, parent) :
        self.id     = xml.get ("Id")
        self.parent = parent
        self.text   = ""
        if self.Debug :
            print ("%sPS %s" % (self.head_indent, self.id, ))
    # end def __init__

    @classmethod
    def From_Pickle (cls, program, state, parent) :
        result        = super (Parameter_Separator, cls).From_Pickle (state)
        result.parent = parent
        return result
    # end def From_Pickle

    @Once_Property
    def text (self) :
        return "-----"
    # end def text

# end class Parameter_Separator

### Choose, When, Assign moved into _Program_Object_
### __END__ STG.Parameter
