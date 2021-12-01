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
#    STG._Object_
#
# Purpose
#    Base class for all STG objects
#
#--

import  lxml.etree      as     ET
from    lxml.etree      import _Element
from    Once_Property   import  Once_Property

class _STG_Object_ :
    """Base class for all STG objects"""

    undefined  = object ()
    Namespaces = dict (E = "http://knx.org/xml/project/12")
    parent     = None

    Debug      = True * 0

    Value_Attributes = ()
    Ref_Attributes   = ()

    @Once_Property
    def head_indent (self) :
        if self.parent :
            return self.parent.head_indent + "  "
        return ""
    # end def head_indent

    @classmethod
    def xpath (cls, root, * args, ** kw) :
        xkw = dict (kw, namespaces = cls.Namespaces)
        return root.xpath (* args, ** xkw)
    # end def xpath

    @classmethod
    def get (cls, root, path, idx = 0, default = undefined) :
        try :
            return cls.xpath (root, path)[idx]
        except IndexError :
            if default != cls.undefined :
                return default
            raise
    # end def get

    @Once_Property
    def id_path (self) :
        result = []
        if self.parent :
            result.extend (self.parent.id_path)
        result.append (self.id)
        return result
    # end def id_path

    @classmethod
    def Parse (cls, file_name) :
        result = ET.parse (file_name).getroot ()
        ns     = getattr (result, "nsmap", {}).get (None, None)
        if ns is not None :
            _STG_Object_.Namespaces ["E"] = ns
        return result
    # end def Parse

    @property
    def pickle_cargo (self) :
        result = dict ()
        for attr in self.Value_Attributes :
            value         = getattr (self, attr)
            if isinstance (value, _Element) :
                value = \
                    ( "LXML-ELEMENT", value.tag, value.items ()
                    , value.text, value.tail
                    )
            result [attr] = value
        for (name, _) in self.Ref_Attributes :
            result [name] = getattr (getattr (self, name), "id", None)
        return result
    # end def property

    @classmethod
    def From_Pickle (cls, state) :
        if hasattr (cls, "Table") :
            id = state ["id"]
            if id not in cls.Table :
                cls.Table [id] = cls._restore (state)
            return cls.Table [id]
        else :
            return cls._restore (state)
    # end def From_Pickle

    @classmethod
    def _restore (cls, state) :
        refs = dict ()
        for (attr, rcls) in cls.Ref_Attributes :
            refs [attr] = (rcls, state.pop (attr))
        result = cls.__new__   (cls)
        for attr, value in state.items () :
            if (   isinstance (value, tuple) 
               and len (value) == 5 
               and value [0] == "LXML-ELEMENT"
            ) :
                xattr = dict (* value [2])
                xml = ET.Element (value [1], ** xattr)
                xml.text = value [3]
                xml.tail = value [4]
                state [attr] = xml
        result.__dict__.update (state)
        for attr, (rcls, value) in refs.items () :
            if value is not None :
                value = rcls.Table [value]
            setattr (result, attr, value)
        return result
    # end def _restore

 # end class _STG_Object_

### __END__ STG._Object_
