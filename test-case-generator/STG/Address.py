# -*- coding: utf-8 -*-
# Copyright (C) 2021 Martin Glueck All rights reserved
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
#    STG.Address
#
# Purpose
#    Helper classes for moduling Group and Individual Addresses
#--
from    collections     import defaultdict

class _Address_ :
    """Base class for group/individual addresses"""

    def __init__ (self, value, desc = None, id = None) :
        if isinstance (value, str) :
            a, b, c      = (int (p) for p in value.split (self.sep))
            sa, sb, sc   = self.sizes
            sa           = (sb + sc)
            sb           =  sc
            sc           =  0
            value        = (a << sa) | (b << sb) | (c << sc)
        self.value       = value
        self.desc        = desc
        self.id          = id
        self.com_objects = defaultdict (list)
    # end def __init__

    def __int__ (self) :
        return self.value
    # end def __int__

    def __hash__ (self) :
        return self.value
    # end def __hash__

    def __eq__ (self, rhs) :
        return self.value == getattr (rhs, "value", -1)
    # end def __eq__

    def __lt__ (self, rhs) :
        return self.value <  getattr (rhs, "value", -1)
    # end def __lt__

    def __str__ (self) :
        sa, sb, sc = self.sizes
        ma         = (2 ** sa) - 1
        mb         = (2 ** sb) - 1
        mc         = (2 ** sc) -1
        sa         = (sb + sc)
        sb         =  sc
        sc         =  0
        v          = self.value
        return  "%d%s%d%s%d" % \
            ((v >> sa) & ma, self.sep, (v >> sb) & mb, self.sep, (v >> sc) & mc)
    # end def __str__

    @classmethod
    def New (cls, value) :
        if "." in value :
            return Individual_Address (value)
        return     Group_Address      (value)
    # end def New

# end class _Address_

class Group_Address (_Address_) :
    """Group address"""

    sep    = "/"
    sizes  = (5, 3, 8)

# end class Group_Address

class Individual_Address (_Address_) :
    """A device address"""

    sep   = "."
    sizes = (4, 4, 8)

# end class Individual_Address

### __END__ STG.Address
