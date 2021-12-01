# -*- coding: utf-8 -*-
# Copyright (C) 2015-2021 Martin Glueck All rights reserved
# Neugasse 2, A--2244 Spannberg, Austria. martin@mangari.org
# #*** <License> ************************************************************#
# This module is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this module. If not, see <http://www.gnu.org/licenses/>.
# #*** </License> ***********************************************************#
#
#++
# Name
#    STG.Telegram
#
# Purpose
#    De/Encoding of a EIB telegram
#--
import   struct

Undefined = object ()

class _Field_ :
    """Base class for field of a telegram"""

    def __init__ ( self, name, offset, shift, mask
                 , default   = 0
                 , important = False
                 , ** kw
                 ) :
        self.name      = name
        self.offset    = offset
        self.shift     = shift
        self.mask      = mask
        self.default   = default
        self.important = important
        assert not kw, kw
    # end def __init__

# end class _Field_

class Int_Field (_Field_) :
    """Simple integer field"""

    def __init__ (self, * args, ** kw) :
        super ().__init__ (* args, ** kw)
        byte_order  = kw.pop ("byte_order", ">")
        mask = self.mask << self.shift
        if   mask < 0x100 :
            self.code = "%sB" % (byte_order, )
        elif mask < 0x10000 :
            self.code = "%sH" % (byte_order, )
        else :
            self.code = "%sI" % (byte_order, )
        self.size     = struct.calcsize (self.code)
    # end def __init__

    def as_bytes (self, result, value, telegram) :
        off = self.offset
        raw = struct.pack (self.code, (value & self.mask) << self.shift)
        new = []
        for o in range (self.size) :
            new.append (bytes ([int (result [off + o]) | int (raw [o])]))
        return result [:off] + b"".join (new) + result [off + self.size:]
    # end def as_bytes

    def from_bytes (self, bytes, kw) :
        raw = bytes [self.offset : self.offset + self.size]
        return (struct.unpack (self.code, raw) [0] >> self.shift) & self.mask
    # end def from_bytes

    def as_string (self, telegram) :
        return getattr (telegram, self.name)
    # end def as_string

    def from_string (self, telegram, value) :
        return eval (value)
    # end def from_string

# end class Int_Field

class Value_Field (Int_Field) :
    """Special handling of values"""

    struct_code = \
        { 7  : "B"
        , 8  : "B"
        , 16 : "H"
        , 24 : "I"
        , 32 : "I"
        , 64 : "Q"
        }

    def as_bytes (self, result, value, telegram) :
        if telegram.length < 7 :
            ### if only 6 bits of data needs to be sent they fit into the
            ### 7th byte of the telegram
            return super ().as_bytes (result, value, telegram)
        # more than 6 bits of data -> pack them at the end of the telegram
        # starting with byte 8
        off = self.offset + 1
        if isinstance (value, bytes) :
            new = value
        else :
            ssize = telegram.length #telegram.length + 7) // 8
            new   = struct.pack (self.struct_code [ssize], value)
        size = (telegram.length + 7) // 8
        return result [:off] + new + result [off + size:]
    # end def as_bytes

# end class Value_Field

class Memory_Count_Field (Int_Field) :
    """The number of bytes for a memory transfer"""

    def as_bytes (self, result, value, telegram) :
        if value is None :
            value = len (telegram.mem)
        return super (Memory_Count_Field, self).as_bytes \
            (result, value, telegram)
    # end def as_bytes

# end class Memory_Count_Field

class Memory_Value_Field (Int_Field) :
    """Special handling of values for memory transfers"""

    def as_bytes (self, result, value, telegram) :
        off = self.offset
        if telegram.count is None :
            telegram.count = len (value)
        return result [:off] + value + result [off + telegram.count:]
    # end def as_bytes

    def from_bytes (self, bytes, kw) :
        return bytes [self.offset : self.offset + kw ["count"]]
    # end def from_bytes

# end class Memory_Value_Field

class Mapping_Field (Int_Field) :
    """Convert the value into a string"""

    def __init__ (self, * args, ** kw) :
        self.mapping = kw.pop ("mapping")
        self.gnippam = dict ((v, str (k)) for (k, v) in self.mapping.items ())
        super ().__init__ (* args, ** kw)
    # end def __init__

    def as_string (self, telegram) :
        return self.mapping [getattr (telegram, self.name)]
    # end def as_string

    def from_string (self, telegram, value) :
        return super ().from_string \
            (telegram, self.gnippam.get (value, value))
    # end def from_string

# end class Mapping_Field

class _Address_ (_Field_) :
    """The KNX address"""

    class Value :

        physical  = ( ("area",    0xF000, 12)
                    , ("line",    0x0F00,  8)
                    , ("address", 0x00FF,  0)
                    )
        group     = ( ("main",    0x7800, 11)
                    , ("middle",  0x0700,  8)
                    , ("sub",     0x00FF,  0)
                    )
        seperator = "./"

        def __init__ (self, value, group) :
            self._value   = value
            self.fields   = self.group if group else self.physical
            self.seperator = self.seperator [group]
            for name, mask, shift in self.fields :
                setattr (self, name, (value & mask) >> shift)
        # end def __init__

        def __str__ (self) :
            result = []
            for name, _, _ in self.fields :
                result.append (str (getattr (self, name)))
            return self.seperator.join (result)
        # end def __str__

        def __int__ (self) :
            return self._value
        # end def __int__

        @classmethod
        def From_String (cls, value) :
            if "." in value :
                sep  = "."
                spec = cls.physical
            else :
                sep  = "/"
                spec = cls.group
            parts    = value.split (sep)
            result   = 0
            for v, (n, m, s) in zip (parts, spec) :
                result |= int (v) << s
            return cls (result, sep == "/")
        # end def From_String

    # end class Value

    def __init__ (self, name, offset) :
        super ().__init__ (name, offset, 0, 0xFFFF, important = True)
    # end def __init__

    def as_bytes (self, result, value, telegram) :
        off   = self.offset
        value = int (value)
        raw   = struct.pack ("!H", (value & self.mask) << self.shift)
        new   = []
        for o in range (2) :
            new.append (bytes ([int (result [off + o]) | int (raw [o])]))
        return result [:off] + b"".join (new) + result [off + 2:]
    # end def as_bytes

    def from_bytes (self, bytes, kw) :
        value = struct.unpack (b"!H", bytes [self.offset:self.offset + 2]) [0]
        return self.Value (value, self.kind (bytes))
    # end def from_bytes

    def as_string (self, telegram) :
        return getattr (telegram, self.name)
    # end def as_string

    def from_string (self, telegram, value) :
        return self.Value.From_String (value)
    # end def from_string

# end class _Address_

class Source_Address (_Address_) :
    """The KNX source address"""

    def kind (self, bytes) :
        return False
    # end def kind

# end class Source_Address

class Destination_Address (_Address_) :
    """The KNX destination address"""

    def kind (self, bytes) :
        return (bytes [5] & 0x80) == 0x80
    # end def kind

# end class Destination_Address

class Boolean_Field (Mapping_Field) :
    """A mapping for a boolean field"""

    def __init__ (self, * args, ** kw) :
        kw ["mapping"] = {0 : "n", 1 : "y"}
        super ().__init__ (* args, ** kw)
    # end def __init__

# end class Boolean_Field

class M_Sub_Type (type) :
    """Meta class for sub type classes."""

    def __init__ (cls, name, bases, dct) :
        super (M_Sub_Type, cls).__init__ (name, bases, dct)
        Fields = list (getattr (cls, "Fields", ()))
        if not name.startswith ("_") :
            cls.__bases__ [0].Sub_Types [cls.Sub_Type_Id] = cls
            off, shift, mask  = bases [0].Match
            cls.Sub_Type_Base = bases [0]
            if mask > 0xFF :
                mask >>= shift
            Fields.append \
                (Int_Field (name.lower (), off, shift, mask, cls.Sub_Type_Id))
        cls.fields = {}
        for b in reversed (bases) :
            cls.fields.update (getattr (b, "fields", {}))
        for f in Fields :
            cls.fields [f.name] = f
        for n, f in cls.fields.items () :
            if n not in cls.Defaults :
                cls.Defaults [n] = f.default
    # end def __init__

    def Find_Class (cls, bytes) :
        result = cls
        #import pdb; pdb.set_trace ()
        while "Sub_Types" in result.__dict__ :
            off, shift, mask = result.Match
            if mask < 0xFF :
                type_id      = (bytes [off] >> shift) & mask
            else :
                type_id      = ((bytes [off] << 8) + bytes [off + 1]) & mask
                type_id    >>= shift
            result           = result.Sub_Types [type_id]
        return result
    # end def Find_Class

    def From_Raw (cls, bytes) :
        tcls = cls.Find_Class (bytes)
        kw   = dict ()
        for f in tcls.sorted_fields :
            kw [f.name] = f.from_bytes (bytes, kw)
        return tcls (** kw)
    # end def From_Raw

    @property
    def sorted_fields (cls) :
        return sorted ( cls.fields.values ()
                      , key = lambda f : (f.offset, -f.shift)
                      )
    # end def sorted_fields

# end class M_Sub_Type

class _Telegram_ (metaclass = M_Sub_Type) :
    """Base class for a EIB telegram"""

    Match     = 0, 6, 0x3
    Sub_Types = {}
    Defaults  = {}
    payload_length = 0

    def __init__ (self, ** kw) :
        for n, f in self.fields.items () :
            v = kw.pop (n, self.Defaults [f.name])
            if isinstance (v, str) :
                v = f.from_string (self, v)
            setattr (self, n, v)
        assert not kw, kw
    # end def __init__

    def set (self, ** kw) :
        for field, value in kw.items () :
            if isinstance (value, str) :
                value = self.fields [field].from_string (self, value)
            setattr (self, field, value)
    # end def set

    @property
    def attributes (self) :
        result = {}
        for f in self.__class__.sorted_fields :
            result [f.name] = getattr (self, f.name)
        return result
    # end def attributes

    @property
    def bytes (self) :
        #import pdb; pdb.set_trace ()
        result      = bytes ([0x00] * 23)
        for f in self.__class__.sorted_fields :
            result = f.as_bytes (result, getattr (self, f.name), self)
            #print ("   ", f.name, getattr (self, f.name), ", ".join ("0x%02X" % b for b in result [:6]))
        size = 7 + self.payload_length
        ###print (size)
        result = self.fields ["length"].as_bytes (result, size - 7, self)
        csum = 0xFF
        for b in result [:size] :
            csum ^= b
        return result [:size] + bytes ((csum, ))
    # end def bytes

    def __call__ (self, value) :
        self.value = value
        return self
    # end def __call__


    def __str__ (self) :
        result = []
        for f in self.__class__.sorted_fields :
            if f.important :
                result.append ("%s=%s" % (f.name, f.as_string (self)))
        return "%s (%s)" % (self.__class__.__name__, ",".join (result))
    # end def __str__

# end class _Telegram_

class Data_Request (_Telegram_) :
    """A normal data request telegram"""

    Sub_Type_Id   = 0b10

    Match         = 6, 6, 0x03
    Sub_Types     = {}

    Fields        = \
        ( Int_Field     ( "start_bit",  0, 0, 0x03, 0b00)
        , Mapping_Field ( "priority",   0, 2, 0x03, 0b11, True
                        , mapping = { 0b11 : "l"
                                    , 0b01 : "h"
                                    , 0b10 : "a"
                                    , 0b00 : "s"
                                    }
                        )
        , Int_Field     ( "reserved_0", 0, 4, 0x01,  0b1)
        , Mapping_Field ( "repeat",     0, 5, 0x01,  0b1, True
                        , mapping = { 1 : "n", 0 : "y"}
                        )
        , Int_Field     ( "reserved_1", 0, 6, 0x03, 0b10)

        , Source_Address      ("src", 1)
        , Destination_Address ("dst", 3)
        , Boolean_Field       ("group_address", 5, 7, 0x01, 0b0)
        , Int_Field           ("route",  5, 4, 0x07, 0b110)
        , Int_Field           ("length", 5, 0, 0x0F, 0b0000)
        )

# end class Data_Request

class Extended_Data_Request (_Telegram_) :
    """An extended data request"""
    Sub_Type_Id   = 0b00
# end class Extended_Data_Request

class Poll_Data_Request (_Telegram_) :
    """A poll data request"""
    Sub_Type_Id   = 0b11
# end class Poll_Data_Request

class Unnumbered_Control_Packet (Data_Request) :
    Sub_Type_Id = 0b10
    Match       = 6, 0, 0x03
    Sub_Types   = {}
    Defaults    = dict (priority = 0b00)

# end class Unnumbered_Control_Packetet

class Connect (Unnumbered_Control_Packet) :
    Sub_Type_Id = 0b00
# end class Connect

class Disconnect (Unnumbered_Control_Packet) :
    Sub_Type_Id = 0b01
# end class Disconnect

class Numbered_Control_Packet (Data_Request) :
    Sub_Type_Id = 0b11
    Match         = 6, 0, 0x03
    Sub_Types   = {}

    Fields      = (Int_Field ("pno", 6, 2, 0xF, 0b0000, important = True), )
# end class Numbered_Control_Packet

class ACK (Numbered_Control_Packet) :
    Sub_Type_Id = 0b10
# end class ACK

class NACK (Numbered_Control_Packet) :
    Sub_Type_Id = 0b11
# end class NACK

### «text»
class Unnumbered_Data_Packet_Base (Data_Request) :
    Sub_Type_Id = 0b00
    Match       = 6, 0, 0x03
    Sub_Types   = {}
# end class Unnumbered_Data_Packet_Base

class Unnumbered_Data_Packet_b00 (Unnumbered_Data_Packet_Base) :
    Sub_Type_Id = 0b00
    Match       = 7, 6, 0x03
    Sub_Types   = {}
# end class Unnumbered_Data_Packet_b00

class Unnumbered_Data_Packet_b01 (Unnumbered_Data_Packet_Base) :
    Sub_Type_Id = 0b01
    Match       = 7, 0, 0xFF
    Sub_Types   = {}
# end class Unnumbered_Data_Packet_b01

class Unnumbered_Data_Packet_b11 (Unnumbered_Data_Packet_Base) :
    Sub_Type_Id = 0b11
    Match       = 7, 0, 0xFF
    Sub_Types   = {}
# end class Unnumbered_Data_Packet_b11

class Get_Value (Unnumbered_Data_Packet_b00) :
    Sub_Type_Id = 0b00
    Defaults    = dict (group_address = 1)
# end class Get_Value

class Send_Value (Unnumbered_Data_Packet_b00) :
    Sub_Type_Id = 0b10
    Fields      = \
        ( Value_Field ("value", 7, 0, 0x3F, important = True)
        ,
        )
    Defaults = dict (group_address = 1)

    @property
    def payload_length (self) :
        if self.length < 7 :
            return  1
        elif self.length  :
            return  1 + (self.length + 7) // 8
        return 0
    # end def payload_length

# end class Send_Value

class Get_Value_Response (Unnumbered_Data_Packet_b00) :
    Sub_Type_Id = 0b01
    Fields      = \
        ( Value_Field ("value", 7, 0, 0x3F, important = True)
        ,
        )
    Defaults = dict (group_address = 1)

    @property
    def payload_length (self) :
        if self.length < 7 :
            return  1
        elif self.length  :
            return  1 + (self.length + 7) // 8
        return 0
    # end def payload_length

# end class Get_Value_Response

class Physical_Address_Set (Unnumbered_Data_Packet_b00) :
    Sub_Type_Id = 0b11
    Fields      = \
        ( Int_Field ("area",   8, 4,  0xF, 0)
        , Int_Field ("line",   8, 0,  0xF, 0)
        , Int_Field ("number", 9, 0, 0xFF, 0)
        )
# end class Physical_Address_Set

class Physical_Address_Request (Unnumbered_Data_Packet_b01) :
    Sub_Type_Id = 0b00000000
# end class Physical_Address_Request

class Physical_Address_Response(Unnumbered_Data_Packet_b01) :
    Sub_Type_Id = 0b01000000
# end class Physical_Address_Response

class Physical_Address_Serial_Request (Unnumbered_Data_Packet_b11) :
    Sub_Type_Id = 0b11011100
# end class Physical_Address_Serial_Request

class Physical_Address_Serial_Response (Unnumbered_Data_Packet_b11) :
    Sub_Type_Id = 0b11011101
# end class Physical_Address_Serial_Response

class Physical_Address_Serial_Set (Unnumbered_Data_Packet_b11) :
    Sub_Type_Id = 0b11011110
    Fields      = \
        ( Int_Field ("area",   8, 4,  0xF, 0)
        , Int_Field ("line",   8, 0,  0xF, 0)
        , Int_Field ("number", 9, 0, 0xFF, 0)
        )
# end class Physical_Address_Serial_Set

class App_Status (Unnumbered_Data_Packet_b11) :
    Sub_Type_Id = 0b11011111
# end class App_Status

class System_ID_Set (Unnumbered_Data_Packet_b11) :
    Sub_Type_Id = 0b11100000
# end class System_ID_Set

class System_ID_Request (Unnumbered_Data_Packet_b11) :
    Sub_Type_Id = 0b11100001
# end class System_ID_Request

class System_ID_Response (Unnumbered_Data_Packet_b11) :
    Sub_Type_Id = 0b11100010
# end class System_ID_Response

class Numbered_Data_Packet_Base (Data_Request) :
    Sub_Type_Id = 0b01
    Match       = 6, 0, 0x03
    Sub_Types   = {}

    Fields      = (Int_Field ("pno", 6, 2, 0xF, 0b0000, important = True), )

# end class Numbered_Data_Packet_Base

class Numbered_Data_Packet_b01 (Numbered_Data_Packet_Base) :
    Sub_Type_Id = 0b01
    Match       = 7, 6, 0x03
    Sub_Types   = {}
# end class Numbered_Data_Packet_b01

class Numbered_Data_Packet_b10_Base (Numbered_Data_Packet_Base) :
    Sub_Type_Id = 0b10
    Match       = 7, 6, 0x03
    Sub_Types   = {}
# end class Numbered_Data_Packet_b10_Base

class Numbered_Data_Packet_b10_Base (Numbered_Data_Packet_Base) :
    Sub_Type_Id = 0b10
    Match       = 7, 6, 0x03
    Sub_Types   = {}
# end class Numbered_Data_Packet_b10_Base

class Numbered_Data_Packet_b10_b11(Numbered_Data_Packet_b10_Base) :
    Sub_Type_Id = 0b11
    Match       = 7, 0, 0x03F
    Sub_Types   = {}
# end class Numbered_Data_Packet_b10_b11

class Numbered_Data_Packet_b11 (Numbered_Data_Packet_Base) :
    Sub_Type_Id = 0b11
    Match       = 7, 0, 0xFF
    Sub_Types   = {}
# end class Numbered_Data_Packet_b11

class Memory_Read_Request (Numbered_Data_Packet_b10_Base) :
    Sub_Type_Id = 0b00
    Fields      = \
        ( Int_Field ("count",   7, 0, 0xF,    important = True)
        , Int_Field ("address", 8, 0, 0xFFFF, important = True)
        )
    payload_length = 3

# end class Memory_Read_Request

class Memory_Read_Response (Numbered_Data_Packet_b10_Base):
    Sub_Type_Id = 0b01
    Fields      = \
        ( Memory_Count_Field ("count",    7, 0, 0xF,    important = True)
        , Int_Field          ("address",  8, 0, 0xFFFF, important = True)
        , Memory_Value_Field ("mem",     10, 0, 0)
        )

    Defaults = dict (count = None)

    @property
    def payload_length (self) :
        return 3 + self.count
    # end def payload_length

# end class Memory_Read_Response

class Memory_Read_Value (Numbered_Data_Packet_b10_Base) :
    Sub_Type_Id = 0b10
    Fields      = \
        ( Memory_Count_Field ("count",    7, 0, 0xF,    important = True)
        , Int_Field          ("address",  8, 0, 0xFFFF, important = True)
        , Memory_Value_Field ("mem",     10, 0, 0)
        )
    Defaults = dict (count = None)

    @property
    def payload_length (self) :
        return 3 + self.count
    # end def payload_length

# end class Memory_Read_Value

class ADC_Value_Request (Numbered_Data_Packet_b01) :
    Sub_Type_Id = 0b10
    Fields      = ( Int_Field ("channel", 7, 0, 0x3F, 0, important = True)
                  , Int_Field ("samples", 8, 0, 0xFF, 0, important = True)
                  )
# end class ADC_Value_Request

class ADC_Value_Response (Numbered_Data_Packet_b01):
    Sub_Type_Id = 0b11
    Fields      = ( Int_Field ("channel", 7, 0, 0x3F,   0, important = True)
                  , Int_Field ("samples", 8, 0, 0xFF,   0, important = True)
                  , Int_Field ("result",  9, 0, 0xFFFF, 0, important = True)
                  )
# end class ADC_Value_Response

class Mask_Read_Request (Numbered_Data_Packet_b11) :
    Sub_Type_Id = 0b00000000
# end class Mask_Read_Request

class Mask_Read_Response (Numbered_Data_Packet_b11) :
    Sub_Type_Id = 0b01000000
# end class Mask_Read_Response

class Reset (Numbered_Data_Packet_b11) :

    Sub_Type_Id    = 0b10000000
    payload_length = 1

# end class Reset

class Reset_into_Bootloader (Numbered_Data_Packet_b11) :

    Sub_Type_Id    = 0b10000001
    payload_length = 3
    Fields         = ( Int_Field ("erase",   8, 0, 0xFF, 0)
                     , Int_Field ("channel", 9, 0, 0xFF, default = 255)
                     )

# end class Reset_into_Bootloader

if 0 : #«text»
    class Property_Read (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b010101
    # end class Property_Read

    class Property_Read_Response (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b010110
    # end class Property_Read_Response

    class Property_Read_Value (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b010111
    # end class Property_Read_Value

    class Property_Desc (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b011000
    # end class Property_Desc

    class Property_Desc_Response (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b011001
    # end class Property_Desc_Response

    class Memory_Read_Value_Bit (Numbered_Data_Packet_4_B) :
        Sub_Type_Id = 0b000011
    # end class Memory_Read_Value_Bit

    class Manufacturer_Info (Numbered_Data_Packet_4_B) :
        Sub_Type_Id = 0b000100
    # end class Manufacturer_Info

    class Manufacturer_Info_Response (Numbered_Data_Packet_4_B) :
        Sub_Type_Id = 0b000001
    # end class Manufacturer_Info_Response

    class Memory_CC_Read (Numbered_Data_Packet) :
        Sub_Type_Id = 0b1000
        Fields      = \
            ( Int_Field ("count", 7, 0, 0xF, important = True)
            , Int_Field ("address", 8, 0, 0xFFFF, important = True)
            )
    # end class Memory_CC_Read

    class Memory_CC_Read_Response (Numbered_Data_Packet) :
        Sub_Type_Id = 0b1001
    # end class Memory_CC_Read_Response

    class Memory_CC_Read_Value (Numbered_Data_Packet) :
        Sub_Type_Id = 0b1010
    # end class Memory_CC_Read_Value

    class Memory_CC_Read_Value_Bit (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b010000
    # end class Memory_CC_Read_Value_Bit

    class Access (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b010001
    # end class Access

    class Access_Response (Numbered_Data_Packet_4_F):
        Sub_Type_Id = 0b010010
    # end class Access_Response

    class Access_Set_Key (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b010011
    # end class Access_Set_Key

    class Access_Response (Numbered_Data_Packet_4_F) :
        Sub_Type_Id = 0b010100
    # end class Access_Response

if __name__ == "__main__" :
    import sys
    from pprint import pprint

    def info(type, value, tb):
       if hasattr(sys, 'ps1') or not sys.stderr.isatty():
          # we are in interactive mode or we don't have a tty-like
          # device, so we call the default hook
          sys.__excepthook__(type, value, tb)
       else:
          import traceback, pdb
          # we are NOT in interactive mode, print the exception...
          traceback.print_exception(type, value, tb)
          print
          # ...then start the debugger in post-mortem mode.
          pdb.pm()
    sys.excepthook = info

    if 0 :
        for raw in ( bytes ((0xBC, 0x01, 0x03, 0x00, 0x01, 0xE1, 0x00, 0x80, 0x21))
                   , bytes ((0xBC, 0x01, 0x03, 0x00, 0x01, 0xE1, 0x00, 0x81, 0x20))
                   ) :
            t   = _Telegram_.From_Raw (raw)
            print (t)
            print (raw == t.bytes)
            print (", ".join ("0x%02X" % b for b in t.bytes))
            print ("-"*79)
        tc = Send_Value (src = "0.1.3", dst = "0/0/1", value = 1, repeat = "n", length=1)
        print (tc)
        #pprint (t.attributes)
        #pprint (tc.attributes)
        #import pdb; pdb.set_trace ()
        print (", ".join ("0x%02X" % b for b in tc.bytes))
    else :
        value = 0x11223344556677FF
        for l in (1,2,3,4,5,6,7,8,16,24,32,64) :
            mask = (2 ** l - 1)
            v = value & mask
            x = Send_Value (src = 1, dst = 2, length = l, value = v)
            print ("%2d" % l, ", ".join ("0x%02X" % b for b in x.bytes))
### __END__ Telegram
