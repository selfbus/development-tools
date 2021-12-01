# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Martin Glueck All rights reserved
# Langstrasse 4, A--2244 Spannberg, Austria. martin@mangari.org
# #*** <License> ************************************************************#
# This module is part of the library selfbus.
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
#    Once_Property
#
# Purpose
#    A calculated property where the result of the calculation gets cached
#
# Revision Dates
#     3-Jan-2014 (MG) Creation
#    ««revision-date»»···
#--

class Once_Property (object) :

    def __init__ (self, func) :
        self.name = func.__name__
        self.func = func
    # end def __init__

    def __get__ (self, obj, cls) :
        if obj is None :
            return self
        result = self.func (obj)
        setattr (obj, self.name, result)
        return result
    # end def __get__

# end class Once_Property

### __END__ Once_Property
