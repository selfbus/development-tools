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
#    STG.Program
#
# Purpose
#    A application program used by a device
#
#--

from   Once_Property            import Once_Property
from   STG._Object_             import _STG_Object_
from   STG._Program_Object_     import _Program_Object_
from   STG.Parameter            import Parameter, Parameter_Ref, Parameter_Type, Absolute_Segment
from   STG.Language             import Language
import  os
from    collections             import defaultdict

class Static (_STG_Object_) :
    """Find a static reference"""

    def __init__ (self, xml) :
        super ().__init__ ()
        self.xml      = xml
        self.memories = dict ()
    # end def __init__

    def find (self, id, tag, cls = None, * args, ** kw) :
        result = super ().get \
            (self.xml, "//E:%s[@Id='%s']" % (tag, id))
        if cls :
            result = cls (xml = result, * args, ** kw)
        return result
    # end def find

    def get (self, id, tag, cls = None, * args, ** kw) :
        if id not in cls.Table :
            cls.Table [id] = self.find (id, tag, cls, * args, ** kw)
        return cls.Table [id]
    # end def get

    def Parameter_Ref (self, id, parent, program) :
        return self.get \
            ( id, "ParameterRef", Parameter_Ref
            , static = self, parent = parent, program = program
            )
    # end def Parameter_Ref

    def Parameter (self, id) :
        return self.get \
            (id, "Parameter", Parameter, static = self)
    # end def Parameter_Ref

    def Parameter_Type (self, id) :
        return self.get \
            (id, "ParameterType", Parameter_Type, static = self)
    # end def Parameter_Type

    def Memory (self, id) :
        result = self.get \
            (id, "AbsoluteSegment", Absolute_Segment, static = self)
        self.memories [id] = result
        return result
    # end def Code_Segment

# end class Static

class Program (_Program_Object_) :
    """An application program used by an EIB device"""

    def __init__ (self, xml) :
        super ().__init__ ()
        self.xml             = xml
        self.id              = xml.get ("Id")
        self.mask            = xml.get ("MaskVersion")
        self.raw_name        = xml.get ("Name")
        self.manu_id         = int (self.id[2:6], 16)
        self.app_number      = int (xml.get ("ApplicationNumber"))
        self.app_version     = int (xml.get ("ApplicationVersion"))
        prop_load            = self.xpath (xml, "//E:LdCtrlCompareProp[@PropId=78]")
        if prop_load :
             idata = prop_load [0].get ("InlineData")
             data = []
             for i in range (len (idata) // 2) :
                 data.append ("0x" + idata [i*2:i*2+2])
             data = ", ".join (data)
        else :
             data = "-"
        self.load_compare    = data
        self.parameter_refs  = dict ()
        self.com_object_refs = dict ()
        static               = Static (self.get (xml, "E:Static"))
        for abse in self.xpath (xml, "//E:AbsoluteSegment") :
            static.Memory (abse.get ("Id"))
        self._visit_element (self, self.get (xml, "E:Dynamic"), static)
        self._setup_tables  (static)
        self._finalize      ()
    # end def __init__

    def _finalize (self) :
        self.memory_segments = \
            [ m for m in sorted ( Absolute_Segment.Table.values ()
                                , key = lambda m : m.address
                                )
            ]
        ram_section = \
            [ m for m in self.memory_segments
                if (m.size > 1) and m.data is None
            ]
        if ram_section :
            self.com_ram_memory  = ram_section [0]
        self.com_objects_by_number = defaultdict (list)
        for cor in self.com_object_refs.values () :
            self.com_objects_by_number [cor.number].append (cor)
    # end def _finalize

    def as_html (self, template = "parameter_overview-grid.jnj") :
        from jinja2 import Environment, FileSystemLoader
        path = os.path.dirname (__file__)
        env  = Environment \
            (loader = FileSystemLoader (os.path.join (path, "jinja")))
        template = env.get_template (template)
        return template.render (dict (device = self))
    # end def as_html

    def eeprom_as_html (self, reference_address = 0) :
        p_refs = sorted \
            ( ( pr for pr in self.parameter_refs.values ()
                   if pr.parameter.address
              )
            , key = lambda pr : (pr.parameter.address, pr.parameter.mask)
            )
        from jinja2 import Environment, FileSystemLoader
        path = os.path.dirname (__file__)
        env  = Environment \
            (loader = FileSystemLoader (os.path.join (path, "jinja")))
        template = env.get_template ("eeprom_layout.jnj")
        return template.render \
            ( dict ( p_refs   = p_refs
                   , program  = self
                   , ref_addr = reference_address
                   )
            )
    # end def eeprom_as_html

    @Once_Property
    def name (self) :
        return Language.Translation (self.id, "Name", self.raw_name)
    # end def name

    def _setup_tables (self, static) :
        adr_tab = self.get (self.xml, "//E:AddressTable")
        aso_tab = self.get (self.xml, "//E:AssociationTable")
        com_tab = self.get (self.xml, "//E:ComObjectTable")
        self.address_table = \
            ( int (adr_tab.get ("Offset"))
            , int (adr_tab.get ("MaxEntries"))
            , static.Memory (adr_tab.get ("CodeSegment"))
            )
        self.assoc_table   = \
            ( int (aso_tab.get ("Offset"))
            , int (aso_tab.get ("MaxEntries"))
            , static.Memory (aso_tab.get ("CodeSegment"))
            )
        self.com_table     = \
            ( int (aso_tab.get ("Offset"))
            , static.Memory (com_tab.get ("CodeSegment"))
            )
    # end def _setup_tables

    ### pickle interfaces
    Value_Attributes = ("id", "mask", "app_number", "app_version", "load_compare")

    @property
    def pickle_cargo (self) :
        result = super ().pickle_cargo
        for attr in "address_table", "assoc_table", "com_table" :
            value = getattr (self, attr)
            value = value [:-1] + (value [-1].id, )
            result [attr] = value
        return result
    # end def pickle_cargo

    @classmethod
    def From_Pickle (cls, dump) :
        for attr in "address_table", "assoc_table", "com_table" :
            value = dump [attr]
            value = value [:-1] + (Absolute_Segment.Table [value [-1]], )
            dump [attr] = value
        result = super (Program, cls).From_Pickle (None, dump)
        result._finalize                          ()
        return result
    # end def From_Pickle

# end class Program

if __name__ == "__main__" :
    from  STG._Object_      import _STG_Object_
    from  STG.Language      import Language
    from  STG.Datapoint     import Datapoint
    import sys
    if len (sys.argv) > 2 :
        master = Datapoint.Parse (sys.argv [2])
        Datapoint.From_Master    (master)
    root = _STG_Object_.Parse (sys.argv [1])
    Language.add (root)
    Language.set ("de-DE")
    if 1 :
        prg = Program (Program.get (root, "//E:ApplicationProgram"))
        if len (sys.argv) > 3 :
            file = open (sys.argv [3], "w", encoding = "utf-8")
        else :
            file = sys.stdout
        file.write (prg.as_html ())
        if len (sys.argv) > 3 :
            file.close ()
        print (prg.name)
### __END__ STG.Program
