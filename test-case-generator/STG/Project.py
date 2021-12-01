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
#    STG.Project
#
# Purpose
#    A EIB project
#--

from   STG._Object_     import _STG_Object_
from   STG.Address      import Individual_Address, Group_Address

class Project (_STG_Object_) :
    """A EIB project"""

    def __init__ (self, project, xml) :
        self.project    = project
        self.id         = xml.get  ("Id")
        pi              = self.get (xml, "E:ProjectInformation")
        self.name       = pi.get   ("Name")
        self.project_id = pi.get ("ProjectId", "0")
        self.prj_xml    = self.project.xml_file \
            (self.id, "%s.xml" % (self.project_id))
        self._setup_group_addresses ()
        self._setup_topology        ()
    # end def __init__

    def _create_device_instance (self, dev, address) :
        address   = address % (dev.get ("Address"))
        prod_id   = dev.get ("ProductRefId")
        hw2prg_id = dev.get ("Hardware2ProgramRefId")
        device    = self.project.devices [(prod_id, hw2prg_id)]
        return Device_Instance (self, device, address, dev)
    # end def _create_device_instance

    def _setup_group_addresses (self) :
        self.group_addresses = dict ()
        for ga in self.xpath (self.prj_xml, "//E:GroupAddress") :
            ga = Group_Address \
                ( int (ga.get ("Address"))
                , ga.get ("Name")
                , ga.get ("Id")
                )
            self.group_addresses [ga.id]    = ga
            #self.group_addresses [ga.value] = ga
            #self.group_addresses [str (ga)] = ga
    # end def _setup_group_addresses

    def _setup_topology (self) :
        self.devices = dict ()
        for area in self.xpath (self.prj_xml, "//E:Area") :
            main_address = area.get ("Address")
            for line in self.xpath (area, "E:Line") :
                address = "%s.%s.%%s" % (main_address, line.get ("Address"))
                for dev in self.xpath (line, "E:DeviceInstance") :
                    device = self._create_device_instance (dev, address)
                    self.devices [device.id]            = device
                    self.devices [str (device.address)] = device
    # end def _setup_topology

    def __str__ (self) :
        return "Project %s [%s]" % (self.name, self.id)
    # end def __str__

# end class Project

from   STG.Device       import Device_Instance

if __name__ == "__main__" :
    ga = _Address_.New ("2/1/1")
    print ("%d:%s" % (ga, ga))
    ia = Individual_Address ("1.0.1")
    print ("%d:%s" % (ia, ia))
### __END__ STG.Project
