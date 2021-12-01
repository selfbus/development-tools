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
#    STG.Device
#
# Purpose
#    An EIB Device
#
#--

from    STG._Object_            import Once_Property, _STG_Object_
from    STG.Language            import Language
from    STG.Parameter           import Parameter_Ref
from    STG._Program_Object_    import When
from    STG.Address             import Individual_Address
from    STG.EEPROM              import EEPROM
from    STG.EEPROM_Table        import Address_Table, Association_Table, Com_Object_Table
from    STG.Telegram            import Send_Value, Get_Value
from    STG.Com_Object          import Com_Object

class Device (_STG_Object_) :
    """An EIB device."""

    def __init__ (self, project, product, hardware2program) :
        self.project          = project
        self.product          = product
        self.hardware2program = hardware2program
        self.id               = product.get("Id")
        self._name            = product.get ("Text")
        self.hw2prg           = hardware2program.get ("Id")
        app_prg_ref           = self.get \
            (hardware2program, "E:ApplicationProgramRef")
        self.program_id       = app_prg_ref.get ("RefId")
    # end def __init__

    @Once_Property
    def name (self) :
        return Language.Translation (self.id, "Text", "X-" + self._name)
    # end def name

    @Once_Property
    def program (self) :
        return self.project.program_store.get (self.program_id, self.project)
    # end def program

    def __str__ (self) :
        return "%s [%s]" % (self.name, self.program_id)
    # end def __str__

# end class Device

class Com_Object_Instance :
    """A configuration of an comobject referece for a specific device
       instance
    """

    def __init__ (self, device_instance, id, com_object_ref_id, config) :
        self.device_instance   = device_instance
        self.com_object_ref_id = com_object_ref_id
        self.id                = id
        self.config            = config
        self.addresses         = []
    # end def __init__

    @Once_Property
    def com_object_ref (self) :
        return self.device_instance.device.program.com_object_refs \
           [self.com_object_ref_id]
    # end def com_object_ref

    @Once_Property
    def flags (self) :
        return dict (self.com_object_ref.flags, ** self.config)
    # end def flags

    def flags_as_bin (self) :
        return self._flags_as_bin (self.flags, True)
    # end def flags_as_bin

    def telegram (self, value, src = None, kind = None) :
        kw      = dict ()
        if src is None :
            src = self.device_instance.address.value
        if kind is None :
            kind = Send_Value
        if kind is Send_Value :
            kw   = dict \
                ( kw
                , value     = value
                #, type_code = self.Type_Map [self.size]
                , length    = self.size
                )
        elif kind is Get_Value :
            kw = dict (kw, length = 0)
        return kind \
            ( src       = src
            , dst       = self.addresses [0].value
            , ** kw
            )
    # end def telegram

    def __str__ (self) :
        return "[I] %s %s" % (self.function_text, self.as_string (self.flags))
    # end def __str__

    def __eq__ (self, rhs) :
        return self.number == getattr (rhs, "number")
    # end def __eq__

    def __lt__ (self, rhs) :
        return self.number <  getattr (rhs, "number")
    # end def __lt__

    def __getattr__ (self, name) :
        return getattr (self.com_object_ref, name)
    # end def __getattr__

# end class Com_Object_Instance

class Device_Instance :
    """An instance of a device used in a project"""

    Debug = False

    def __init__ (self, project, device, address, xml = None) :
        self.project               = project
        self.device                = device
        self.address               = Individual_Address (address)
        self.values                = dict ()
        self.com_objects           = dict ()
        self.com_objects_by_number = dict ()
        if xml is not None :
            self.id    = xml.get ("Id")
            self._configure_parameters  (xml)
            self._configure_com_objects (xml)
    # end def __init__

    def _add_parameters (self, eeprom) :
        self._visit_node (self.program, eeprom)
    # end def _add_parameters

    def _visit_node (self, node, eeprom) :
        if self.Debug :
            print ("VN: %s" % (node, ))
        if isinstance (node, Parameter_Ref) and node.parameter.address :
            eeprom.set (node.parameter, self [node.id])
        elif isinstance (node, When) :
            ### check if the childrens of the when node should be visited
            value = self [node.choose.ref.id]
            if value != node.test :
                ### this branch is not active -> skip children visiting
                return
        for child in getattr (node, "children", ()) :
            self._visit_node (child, eeprom)
    # end def _visit_node

    def _configure_parameters (self, xml) :
        for pir in self.project.xpath \
            (xml, "E:ParameterInstanceRefs/E:ParameterInstanceRef") :
            self.values [pir.get ("RefId")] = int (pir.get ("Value"))
    # end def _configure_parameters

    def _configure_com_objects (self, xml) :
        self.used_addresses = set ()
        for coir in self.project.xpath \
            (xml, "E:ComObjectInstanceRefs/E:ComObjectInstanceRef") :
            isactive = coir.get ("IsActive", "0").replace ("1", "true")
            if  isactive == "true" :
                crid         = coir.get ("RefId")
                flag_overide = dict ()
                for xml_attr, flag in Com_Object.Flag_Attributes.items () :
                    value = coir.get (xml_attr, None)
                    if value != None :
                        flag_overide [flag] = value == "Enabled"
                prio = coir.get ("Priority")
                if prio is not None :
                    flag_overide ["priority"] = prio
                self.com_objects [crid] = co = Com_Object_Instance \
                    (self, coir.get ("Id"), crid, flag_overide)
                self.com_objects_by_number [co.number] = co
                for snd in self.project.xpath (coir, "E:Connectors/E:Send") :
                    ga = self.project.group_addresses \
                         [snd.get ("GroupAddressRefId")]
                    self.used_addresses.add (ga)
                    ga.com_objects [self.id].append (co)
                    co.addresses.append             (ga)
    # end def _configure_com_objects

    def eeprom (self, lead_bytes = 0) :
        prg                = self.device.program
        adr_off, adr_max, adr_mem   = prg.address_table
        aso_off, aso_max, aso_mem   = prg.assoc_table
        com_off,          com_mem   = prg.com_table
        self.address_table = adr_tab = Address_Table \
            (adr_mem, adr_off, adr_max)
        self.assoc_table   = aso_tab = Association_Table \
            (aso_mem, aso_off, aso_max)
        self.com_table     = com_tab = Com_Object_Table \
           (com_mem, com_off, prg.mask, prg.com_ram_memory, self)
        self.assoc_table.address_table = adr_tab
        self.assoc_table.com_table     = com_tab
        adr_tab.add      (self.address)
        for ga in sorted (self.used_addresses) :
            idx = adr_tab.add (ga)
            aso_tab.add       (idx, ga.com_objects [self.id])
        eeprom       = EEPROM (lead_bytes)
        for ms in prg.memory_segments :
            if ms.data is not None : ### XXX hack to check for EEPROM, should
                                     ###     use mask config to check
                if   adr_tab.memory is ms :
                    table = adr_tab
                elif aso_tab.memory is ms :
                    table = aso_tab
                elif com_tab.memory is ms :
                    table = com_tab
                else :
                    table = None
                if table is not None :
                    eeprom.add (table.memory, table.bytes)
        self._add_parameters (eeprom)
        result = eeprom.bytes
        ### XXX hack for BIM112 -> make this right
        for off, tab in ((0x278, adr_tab), (0x27A, aso_tab), (0x27C, com_tab)):
            v = tab.memory.address + tab.offset
            result [lead_bytes + off + 1] = (v >> 8) & 0xFF
            result [lead_bytes + off + 0] = (v >> 0) & 0xFF
        return result, eeprom.base
    # end def eeprom

    @Once_Property
    def program (self) :
        return self.device.program
    # end def program

    def __getitem__ (self, key) :
        if key not in self.values :
            ### if the value shas not been set for thsi paramater use the
            ### default
            self.values [key] = self.program.parameter_refs [key].value
        return self.values [key]
    # end def __getitem__

    def __setitem__ (self, key, value) :
        self.values [key] = value
    # end def __setitem__

# end class Device_Instance

### __END__ STG.Device
