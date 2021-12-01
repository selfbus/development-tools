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
#    STG.Language
#
# Purpose
#    Handle the translation of strings
#
# Revision Dates
#    12-Feb-2015 (MG) Creation
#    ««revision-date»»···
#--

from   STG._Object_   import _STG_Object_
from   collections    import defaultdict

class Language (_STG_Object_) :
    """A specific language"""

    current   = None
    Languages = defaultdict (list)

    @classmethod
    def Translation (cls, id, attribute, default) :
        key = (id, attribute)
        for tu in cls.Languages [cls.current] :
            if isinstance (tu, dict) :
                if key in tu :
                    return tu [key]
            else :
                tags = cls.xpath \
                    ( tu
                    , "E:TranslationElement[@RefId='%s']"
                     "/E:Translation[@AttributeName='%s']" % (id, attribute)
                    )
                if tags :
                    return tags [0].get ("Text")
        return default
    # end def Translation

    @classmethod
    def set (cls, id) :
        cls.current = id
    # end def set

    @classmethod
    def add (cls, * roots) :
        for root in roots :
            for lang in cls.xpath (root, "//E:Language") :
                cls.Languages [lang.get ("Identifier")].extend \
                    (cls.xpath (lang, "E:TranslationUnit"))
                if not cls.current :
                    cls.current = lang.get ("Identifier")
    # end def add

    @classmethod
    def pickle_cargo (cls) :
        result = dict ()
        for lang, tus  in cls.Languages.items () :
            if tus :
                result [lang] = ldict = dict ()
                for tu in tus :
                    for te in tu.getchildren () :
                        ref_id = te.get ("RefId")
                        for trans in te.getchildren () :
                            name = trans.get ("AttributeName")
                            ldict [ref_id, name] = trans.get ("Text")
        return result
    # end def pickle_cargo

    @classmethod
    def From_Pickle (cls, dump) :
        for lang, ldict in dump.items () :
            cls.Languages [lang].append (ldict)
    # end def From_Pickle

# end class Language

### __END__ STG.Language
