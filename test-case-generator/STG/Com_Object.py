# -*- coding: utf-8 -*-
# Copyright (C) 2015-2021 Martin Glueck All rights reserved
# Neugasse 2, A--2244 Spannberg, Austria. martin@mangari.org
# #*** <License> ************************************************************#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this module. If not, see <http://www.gnu.org/licenses/>.
# #*** </License> ***********************************************************#
#
#++
# Name
#    STG.Com_Object
#
# Purpose
#    Classes related to COM objects
#
#--

from   STG._Object_     import _STG_Object_, Once_Property
from   STG.Datapoint    import Datapoint
from   STG.Language     import Language

class Com_Object (_STG_Object_) :
    """A com object"""

    Table                   = dict ()
    Value_Attributes        = ( "id", "flags", "number", "size"
                              , "raw_text", "raw_ftext"
                              )

    Flag_Attributes         = dict \
        ( ReadFlag          = "read"
        , ReadOnInitFlag    = "read_in_init"
        , WriteFlag         = "write"
        , CommunicationFlag = "communuication"
        , TransmitFlag      = "transmit"
        , UpdateFlag        = "update"
        )

    def __init__ (self, xml, static) :
        super ().__init__ ()
        self.xml       = xml
        self.raw_text  = xml.get ("Text")
        self.raw_ftext = xml.get ("FunctionText")
        self.id        = xml.get ("Id")
        self.flags     = dict ()
        for xml_attr, flag in self.Flag_Attributes.items () :
            self.flags [flag]   = xml.get (xml_attr, "Disabled") == "Enabled"
        self.flags ["priority"] = xml.get ("Priority")
        self.number             = int (xml.get ("Number"))
        self.datapoint          = xml.get ("DatapointType")
        if self.datapoint :
            self.datapoint      = Datapoint.Get (self.datapoint)
            self.size           = self.datapoint.size
        else :
            size                = xml.get ("ObjectSize")
            if size :
                number, text    = size.split (" ")
                if "Byte" in text :
                    size        = int (number) * 8
                elif "Bit" in text :
                    size        = int (number)
            self.size           = size
    # end def __init__

    @Once_Property
    def text (self) :
        return Language.Translation (self.id, "Text", self.raw_text)
    # end def text

    @Once_Property
    def function_text (self) :
        return Language.Translation \
            (self.id, "FunctionText", self.raw_ftext)
    # end def function_text

    def as_string (self, f, com = True) :
        return "%3d: %s %s %s %s %s %s" % \
            ( self.number
            , "C" if (f ["communuication"] and com) else "-"
            , "R" if  f ["read"          ]          else "-"
            , "W" if  f ["write"         ]          else "-"
            , "T" if  f ["transmit"      ]          else "-"
            , "U" if  f ["update"        ]          else "-"
            , f ["priority"]
            )
    # end def as_string

    def __str__ (self) :
        return "[O] %s %s" % (self.function_text, self.as_string (self.flags))
    # end def __str__

# end class Com_Object

class Com_Object_Ref (_STG_Object_) :
    """A reference to a com object."""

    Table                   = dict ()
    Value_Attributes        = ("id", "size", "flags")
    Ref_Attributes          = ( ("object", Com_Object)
                              , ("datapoint", Datapoint)
                              )
    Macro                  = "com_object_ref"
    Flags2BitMask          = dict \
        ( read             = 0x08
        , write            = 0x10
        , communuication   = 0x04
        , transmit         = 0x40
        , update           = 0x80
        )
    Prio2Value             = dict \
        ( { None           : 0b11}
        , Low              = 0b11
        , High             = 0b10
        , Alert            = 0b01
        , System           = 0b00
        )
    Type_Map = \
        {   1 :  0
        ,   2 :  1
        ,   3 :  2
        ,   4 :  3
        ,   5 :  4
        ,   6 :  5
        ,   7 :  6
        ,   8 :  7
        ,  16 :  8
        ,  24 :  9
        ,  32 : 10
        ,  48 : 11
        ,  64 : 12
        ,  80 : 13
        , 112 : 14
        , 120 : 15
        }

    def __init__ (self, program, xml, static, parent) :
        super ().__init__ ()
        self.id            = xml.get ("Id")
        assert self.id not in program.com_object_refs
        program.com_object_refs [self.id] = self
        self.xml           = xml
        self.parent        = parent
        self.object        = static.get \
            (xml.get ("RefId"), "ComObject", Com_Object, static = static)
        self.flags         = dict (self.object.flags)
        for xml_attr, flag in self.object.Flag_Attributes.items () :
            value          = xml.get (xml_attr)
            if value != None :
                self.flags [flag] =  value == "Enabled"
        if self.Debug :
            print ( "%sCR %s [%s] {%s}"
                  % ( self.head_indent, self.id, self.function_text, self.text
                    )
                  )
    # end def __init__

    def _flags_as_bin (self, flags, com = True) :
        result = 0
        for name, mask in self.Flags2BitMask.items () :
            value = flags [name]
            if name == "communuication" : value = value and com
            if value :
                result |= mask
        result |= self.Prio2Value [flags ["priority"]]
        return result
    # end def _flags_as_bin

    def flags_as_bin (self) :
        return self._flags_as_bin (self.flags, False)
    # end def flags_as_bin

    @Once_Property
    def function_text (self) :
        return Language.Translation \
            (self.id, "FunctionText", self.object.function_text)
    # end def function_text

    @Once_Property
    def text (self) :
        return Language.Translation \
            (self.id, "Text", self.object.text)
    # end def text

    def __str__ (self) :
        return "[R] %s %s" % (self.function_text, self.as_string (self.flags))
    # end def __str__

    def __getattr__ (self, name) :
        return getattr (self.object, name)
    # end def __getattr__

# end class Com_Object_Ref

### __END__ STG.Com_Object
