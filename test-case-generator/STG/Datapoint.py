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
#    STG.Datapoint
#
# Purpose
#    The EIB datapoint types
#
#--

from   Once_Property        import Once_Property
from   STG._Object_         import _STG_Object_
from   STG.Language         import Language 

class _Format_ :
    """Base class for datapoint type formats"""

    Table      = dict ()
    Attributes = ("id", "bit_start")

    def __init__ (self, id, bit_start, register = True) :
        self.id        = id
        self.bit_start = bit_start
        if register :
            assert id not in self.Table
            self.Table [id] = self
    # end def __init__

    def clone (self, bit_start) :
        attrs = dict \
            ((an, getattr (self, an)) for an in self.Attributes)
        attrs.pop ("bit_start")
        return self.__class__ \
            (bit_start = bit_start, register = False, ** attrs)
    # end def clone

    def __call__ (self, value) :
        mask = (2 ** self.size - 1)
        return str ((value >> self.bit_start) & mask)
    # end def __call__

# end class _Format_

class Bit (_Format_) :
    """Text values for a specific bit of an datapoint"""

    size       = 1
    Attributes = _Format_.Attributes + ("on", "off")

    def __init__ (self, id, bit_start, off, on, ** kw) :
        super ().__init__ (id, bit_start, ** kw)
        self.on      = on
        self.off     = off
    # end def __init__

    @Once_Property
    def mask (self) :
        return 2 ** self.bit_start
    # end def mask

    def __str__ (self) :
        return "%04X (%s, %s)" % (self.mask, self.off, self.on)
    # end def __str__

    def __call__ (self, value) :
        print (self.mask, value, self.on, self.off)
        return self.on if value & self.mask else self.off
    # end def __call__

# end class Bit

class _Number_ (_Format_) :
    """Base class for numbers."""

    Attributes = _Format_.Attributes + \
        ("name", "size", "unit", "coeffecient", "min_value", "max_value")

    def __init__ ( self, id, bit_start
                 , name
                 , size
                 , unit
                 , coeffecient
                 , min_value
                 , max_value
                 , ** kw) :
        super ().__init__ (id, bit_start, ** kw)
        self.name        = name
        self.size        = int  (str (size))
        self.unit        = unit
        self.coeffecient = eval (str (coeffecient) or "1")
        self.min_value   = eval (str (min_value) or self._default_min_value)
        self.max_value   = eval (str (max_value) or self._default_max_value)
        self.mask        = (2 ** self.size) - 1
    # end def __init__

    def __str__ (self) :
        parts = []
        mask  = self.mask << self.bit_start
        for a in "unit", "coeffecient" :
            v = getattr (self, a)
            if v :
                parts.append (str (v))
        return "%s[%04X %d-%d, %s]" % \
               ( self.Kind, mask
               , self.min_value, self.max_value
               , ", ".join (parts)
               )
    # end def __str__

# end class _Number_

class Unsigned_Integer (_Number_) :
    """A part of the data type should be interpreter as unsigned int value."""

    Kind = "UI"

    @property
    def _default_min_value (self) :
        return "0"
    # end def _default_min_value

    @property
    def _default_max_value (self) :
        return str ((2 ** self.size) - 1)
    # end def _default_max_value

# end class Unsigned_Integer

class Signed_Integer (_Number_) :
    """A part of the data type should be interpreter as signed int value."""

    Kind = "SI"

    @property
    def _default_min_value (self) :
        return str (-(2 ** (self.size - 1)))
    # end def _default_min_value

    @property
    def _default_max_value (self) :
        return str ( (2 ** (self.size - 1)) - 1)
    # end def _default_max_value

# end class Signed_Integer

class Float (_Number_) :
    """A float value"""

    Kind = "F"

    @property
    def _default_min_value (self) :
        return "-0"
    # end def _default_min_value

    @property
    def _default_max_value (self) :
        return "+0"
    # end def _default_max_value

# end class Float

class String (_Format_) :
    """A string encoding"""

    Attributes = _Format_.Attributes + ("size", "encoding")

    def __init__ (self, id, bit_start, size, encoding, ** kw) :
        super ().__init__ (id, bit_start, ** kw)
        self.size     = int (str (size))
        self.encoding = encoding
    # end def __init__

    @Once_Property
    def characters (self) :
        return self.size // 8
    # end def characters

    def __str__ (self) :
        return "String (%d/%s)" % (self.characters, self.encoding)
    # end def __str__

# end class String

class Enumeration (_Format_) :
    """Range of a datapoint is used as an enumeation"""

    Attributes = _Format_.Attributes + ("size", "enums")

    def __init__ (self, id, bit_start, size, ** kw) :
        enums = kw.pop ("enums", ())
        super ().__init__ (id, bit_start, ** kw)
        self.size  = int (str (size))
        self.enums = list (enums)
    # end def __init__

    def add_enum (self, value, text) :
        self.enums.append ((value, text))
    # end def add_enum

    @Once_Property
    def mask (self) :
        return 2 ** self.size - 1
    # end def mask

    def __str__ (self) :
        mask = self.mask << self.bit_start
        return "EN(%04X, %s)" % (mask, ", ".join (str (e) for e in self.enums))
    # end def __str__

# end class Enumeration

class Datapoint (_STG_Object_) :
    """A EIB datapoint"""

    Value_Attributes = ("id", "name", "size", "text")
    Table            = dict ()

    def __init__ (self, id, name, size, text) :
        self.id         = id
        self.name       = name
        self.size       = size
        self.text       = text
        self.formats    = []
        assert id not in self.Table, id
        self.Table [id] = self
    # end def __init__

    def parse_format (self, format) :
        bit_number = 0
        for c in format.iterchildren () :
            if not isinstance (c.tag, str) :
                continue
            tag = c.tag.split ("}", 1) [1].lower ()
            cid = c.get ("Id")
            if tag == "bit" :
                fmt = Bit (cid, bit_number, c.get ("Cleared"), c.get ("Set"))
            elif tag == "reftype" :
                fmt = _Format_.Table [c.get ("RefId")]
                if fmt :
                    fmt = fmt.clone (bit_number)
            elif (  (tag == "unsignedinteger")
                 or (tag == "signedinteger")
                 or (tag == "float")
                 ) :
                if   tag == "unsignedinteger" : cls = Unsigned_Integer
                elif tag == "signedinteger"   : cls = Signed_Integer
                else                          : cls = Float

                fmt = cls \
                    ( cid, bit_number
                    , name        = c.get ("Name")
                    , size        = c.get ("Width")
                    , unit        = c.get ("Unit")
                    , coeffecient = c.get ("Coefficient",  "")
                    , min_value   = c.get ("MinInclusive", "")
                    , max_value   = c.get ("MaxInclusive", "")
                    )
            elif tag == "string" :
                fmt = String \
                    (cid, bit_number, c.get ("Width"), c.get ("Encoding"))
            elif tag == "enumeration" :
                fmt = Enumeration (cid, bit_number, c.get ("Width"))
                for e in c.getchildren () :
                    fmt.add_enum (e.get ("Value"), e.get ("Text"))
            elif tag == "reserved" :
                bit_number += int (c.get ("Width"))
                continue
            else :
                print (self.id, tag)
                aa
                fmt = None
                _Format_.Table [cid] = fmt
            self.formats.append (fmt)
            bit_number += getattr (fmt, "size", 1) ### XXX
        # txt = "%s, %s" % (self.name, ", ".join (str (f) for f in self.formats))
        # print (txt.encode ("latin1", "replace").decode ("latin1"))
    # end def parse_format

    @classmethod
    def From_Master (cls, xml) :
        Language.add (xml)
        for dp in cls.xpath (xml, "//E:DatapointType") :
            size = int (dp.get ("SizeInBit"))
            for dps in cls.xpath \
                (dp, "E:DatapointSubtypes/E:DatapointSubtype") :
                id = dps.get ("Id")
                obj = cls \
                    ( id, dps.get ("Name"), size
                    , Language.Translation (id, "Name", dps.get ("Name"))
                    )
                fmt = cls.xpath (dps, "E:Format")
                if fmt :
                    obj.parse_format (fmt [0])
    # end def From_Master

    @classmethod
    def Get (cls, id) :
        id = id.split (" ") [-1]
        return cls.Table [id]
    # end def Get

# end class Datapoint

if __name__ == "__main__" :
    import sys
    # code snippet, to be included in 'sitecustomize.py'
    def info (type, value, tb) :
       if hasattr(sys, 'ps1') or not sys.stderr.isatty () :
          # we are in interactive mode or we don't have a tty-like
          # device, so we call the default hook
          sys.__excepthook__(type, value, tb)
       else:
          import traceback, pdb
          # we are NOT in interactive mode, print the exception...
          traceback.print_exception (type, value, tb)
          print ()
          # ...then start the debugger in post-mortem mode.
          pdb.pm ()
    # end def info
    sys.excepthook = info

    master = Datapoint.Parse (sys.argv [1])
    Datapoint.From_Master    (master)
### __END__ STG.Datapoint
