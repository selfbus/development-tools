# -*- coding: utf-8 -*-
# Copyright (C) 2015-2021 Martin Glueck All rights reserved
# Neugasse 2, A--2244 Spannberg, Austria. martin@mangari.org
# #*** <License> ************************************************************#
#
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
#    STG.EEPROM
#
# Purpose
#    Content of the EEPROM
#
#--

from   STG._Object_     import Once_Property, _STG_Object_

class EEPROM (_STG_Object_) :
    """Content of the EEPROM"""

    def __init__ (self, lead_bytes) :
        self.lead_bytes = lead_bytes
        self.segments   = dict ()
    # end def __init__

    def add (self, segment, content = None) :
        if segment not in self.segments :
            if content is None :
                content = bytearray (segment.size)
            self.segments [segment] = content
        else :
            if content :
                raise TypeError \
                    ( "Cannot add content for an already allocated segment "
                      "using the add method!"
                    )
    # end def add

    @Once_Property
    def bytes (self) :
        result  = bytearray (self.lead_bytes)
        address = None
        for seg, bytes in sorted ( self.segments.items ()
                                 , key = lambda i : i [0].address
                                 ) :
            if address is not None :
                diff        = seg.address - address
                if diff :
                    result += bytearray (diff)
            else :
                self.base   = seg.address
            result         += bytes
            address         = seg.address + seg.size
        return result
    # end def bytes

    def set (self, par, value) :
        seg                     = par.memory
        if seg not in self.segments :
            self.segments [seg] = bytearray (seg.size)
        bytes                   = self.segments [seg]
        poff                    = par.offset
        if par.size < 8 :
            value      <<= par.bit_offset
            bytes [poff] = (bytes [poff] & ~par.mask) | (value & par.mask)
        else :
            for o in reversed (range (par.size // 8)) :
                bytes [poff + o] = value & 0xFF
                value          >>= 8
    # end def set

# end class EEPROM
### __END__ STG.EEPROM
