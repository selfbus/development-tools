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
#    STG.EEPROM_Table
#
# Purpose
#    Tables inside the EEPROM (Address, Assocication, Com Object Table)
#
#--
from    Once_Property        import Once_Property

class _Table_ :
    """Base class for all tables"""

    def __init__ (self, memory, offset, max_entries) :
        self.memory       = memory
        self.offset       = offset
        self.max_entries  = max_entries
        self.entries      = []
    # end def __init__

    def add (self, entry) :
        if len (self.entries) >= self.max_entries :
            raise ValueError \
                ("Too my entries in table %s" % (self.__class__.__name__))
        self.entries.append (entry)
    # end def add

    def bytes (self) :
        result               = bytearray (self.memory.size)
        result [self.offset] = len (self.entries)
        return result
    # end def bytes

    def _as_string_lines (self) :
        result = [ "%s: #%s @%04X (size %04X)"
                 % ( self.__class__.__name__
                   , len (self.entries)
                   , self.memory.address + self.offset
                   , self.memory.size
                   )
                 ]
        for i, e in enumerate (self.entries) :
            result.append (self._entry_as_lines (i, e))
        return result
    # end def __str__

    def __str__ (self) :
        return "\n".join (self._as_string_lines ())
    # end def __str__

# end class _Table_

class Address_Table (_Table_) :
    """The address table"""

    def add (self, ga) :
        super ().add (ga)
        return len (self.entries) - 1
    # end def add

    @Once_Property
    def bytes (self) :
        result     = super ().bytes ()
        o          = 1 + self.offset
        for ga in self.entries :
            result [o + 0] = (ga.value >> 8) & 0xFF
            result [o + 1] = (ga.value >> 0) & 0xFF
            o             += 2
        return result
    # end def bytes

    def _entry_as_lines (self, no, address) :
        return "%3d: %8s (%04X)" % (no, address, address)
    # end def _entry_as_lines

# end class Address_Table

class Association_Table (_Table_) :
    """The association table"""

    def add (self, ga_idx, objects) :
        for com in sorted (objects, key = lambda c : not c.flags ["read"]):
            super ().add ((ga_idx, com.number))
    # end def add

    @Once_Property
    def bytes (self) :
        result     = super ().bytes ()
        o          = 1 + self.offset
        for ga_idx, com in sorted (self.entries, key = lambda x : x [-1]) :
            result [o + 0] = ga_idx
            result [o + 1] = com
            o             += 2
        return result
    # end def bytes

    def _entry_as_lines (self, no, entry) :
        ga_idx, com_idx = entry
        adr             = self.address_table.entries [ga_idx]
        com             = self.com_table.entries     [com_idx] [0]
        n, f            = str (com).split (":", 1)
        com             = "%-17s : %s" % (f, n)
        return "%3d: %3d <-> | %3d %s <-> %s" % (no, ga_idx, com_idx, adr, com)
    # end def _entry_as_lines

# end class Association_Table

class Com_Object_Table (_Table_) :
    """The com object config table"""

    Address_Size = \
        { "MV-0010"   : 1
        , "MV-0011"   : 1
        , "MV-0012"   : 1
        , "MV-0013"   : 1
        , "MV-0020"   : 1
        , "MV-0021"   : 1
        , "MV-0025"   : 1
        , "MV-0700"   : 2
        , "MV-0701"   : 2
        , "MV-0705"   : 2
        }


    def __init__ (self, memory, offset, mask, ram_memory, device_instance) :
        super ().__init__ (memory, offset, 1024) ### 1024 is just a guess
        self.address_size    = self.Address_Size [mask]
        self.ram_memory      = ram_memory
        prg                  = device_instance.program
        com_object_config    = dict ()
        self.addresses       = []
        for co in device_instance.com_objects.values () :
            number = co.number
            if number in com_object_config :
                raise ValueError \
                    ("Com objects with number %s already used?" % number)
            com_object_config [number] = co
        for no, objects in sorted (prg.com_objects_by_number.items ()) :
            co     = com_object_config.get (no)
            co_ms = sorted (objects, key = lambda c : c.size) [-1]
            self.add ((co, co_ms))
    # end def __init__

    def _add_address_2 (self, result, o, address) :
        result [o + 0] = (address >> 8) & 0xFF
        result [o + 1] = (address >> 0) & 0xFF
        return o + 2
    # end def _add_address_2

    def _add_address_1 (self, result, o, address) :
        result [o]     = (address >> 0) & 0xFF
        return o + 1
    # end def _add_address_1

    def _as_string_lines (self) :
        result = super ()._as_string_lines ()
        result.insert (1, "  RAM address: %04X" % (self.ram_memory.address, ))
        return result
    # end def __str__

    @Once_Property
    def bytes (self) :
        result                 = super ().bytes ()
        ram_address            = self.ram_memory.address
        o                      = self.offset + 1
        if self.address_size == 2 :
            _add_address       = self._add_address_2
            o                  = _add_address (result, o, ram_address)
            ram_address       += len (self.entries)
        else :
            _add_address       = self._add_address_1
            o                  = _add_address (result, o, ram_address)
            ram_address       += len (self.entries) / 2
        for dic, co in self.entries :
            if dic is None :
                dic = co
            bytes              = (co.size + 7) // 8
            miss_align         = ram_address % bytes
            if miss_align :
                ram_address   += (bytes - miss_align)
            self.addresses.append (ram_address)
            o                  = _add_address (result, o, ram_address)
            result [o + 0]     = dic.flags_as_bin ()
            result [o + 1]     = dic.Type_Map [dic.size]
            o                 += 2
            ram_address       += bytes
        return result
    # end def bytes

    def _entry_as_lines (self, no, entry) :
        dic, com        = entry
        com_flag        = True
        if dic is None :
            dic         = com
            com_flag    = False
        flags           = dic.as_string (dic.flags, com_flag)
        flag_value      = dic.flags_as_bin ()
        adr             = self.addresses [no]
        return "%-20s [%02X] @%04X %s" % \
            (flags, flag_value, adr, dic.function_text)
    # end def _entry_as_lines

# end class Com_Object_Table

### __END__ STG.EEPROM_Table
