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
#    SGT.KNX_Project
#
# Purpose
#    Read an KNX project file (.knxproj)
#--

from    STG._Object_        import _STG_Object_
from    STG.Language        import Language
from    STG.Datapoint       import Datapoint
from    STG.Device          import Device
from    STG.Project         import Project
from    STG.Program_Store   import Program_Store
import  zipfile
import  posixpath as ppath
import  collections

class _Project_ (_STG_Object_) :
    """Base class for a knx project file."""

    def __init__ (self, file_name) :
        self.file_name     = file_name
        self.project       = zipfile.ZipFile (file_name)
    # end def __init__

    def xml_file (self, directory, file_name = None) :
        if file_name :
            file_names = ( ppath.join (directory,          file_name)
                         , ppath.join (directory.lower (), file_name)
                         , ppath.join (directory,          file_name.lower ())
                         , ppath.join (directory.lower (), file_name.lower ())
                         )
        else :
            file_names = (directory, directory.lower ())
        for n in file_names :
            try :
                return self.Parse (self.project.open (n))
            except KeyError :
                ### looks like the file name is in lower case
                pass
        raise KeyError ("File %s not found in zip file" % (file_name, ))
    # end def xml_file

# end class _Project_

class KNX_Project (_Project_) :
    """A knxproj file"""

    def __init__ (self, file_name, program_store) :
        super ().__init__ (file_name)
        self.program_store = Program_Store (program_store, self)
        self.devices       = dict ()
        self.projects      = []
        seen               = set ()
        projects           = []
        Datapoint.From_Master (self.xml_file ("knx_master.xml"))
        for file_name in self.project.namelist () :
            if "/" in file_name :
                dir = file_name.split ("/") [0]
                if dir not in seen :
                    seen.add (dir)
                    if file_name.startswith ("M-") :
                        ### this is a device specification
                        self._add_manufacturer (dir)
                    elif file_name.startswith ("P-") :
                        ### this is a project file
                        projects.append (dir)
        for prj in projects :
            self._add_project     (prj)
    # end def __init__

    def _add_manufacturer (self, man_id) :
        catalog  = self.xml_file (man_id, "Catalog.xml")
        hardware = self.xml_file (man_id, "Hardware.xml")
        Language.add (catalog, hardware)
        for cat_item in self.xpath (catalog, "//E:CatalogItem") :
            device = self._setup_device (man_id, cat_item, hardware)
            self.devices [device.id]                = device
            self.devices [device.id, device.hw2prg] = device
    # end def _add_manufacturer

    def _add_project (self, proj_id) :
        project_file = self.xml_file (proj_id, "Project.xml")
        for pxml in self.xpath (project_file, "//E:Project") :
            self.projects.append (Project (self, pxml))
    # end def _add_project

    def _setup_device (self, man_id, catlog_item, hardware) :
        prod_ref_id      = catlog_item.get ("ProductRefId")
        hw2prg_ref_id    = catlog_item.get ("Hardware2ProgramRefId")
        product          = self.get \
            (hardware, "//E:Product[@Id='%s']" % (prod_ref_id, ))
        hardware2program = self.get \
            (hardware, "//E:Hardware2Program[@Id='%s']" % (hw2prg_ref_id, ))
        return Device (self, product, hardware2program)
    # end def _setup_device

# end class KNX_Project

def main (cmd) :
    import sys
    # code snippet, to be included in 'sitecustomize.py'
    def info (type, value, tb) :
       if hasattr(sys, 'ps1') or not sys.stderr.isatty () :
          # we are in interactive mode or we don't have a tty-like
          # device, so we call the default hook
          sys.__excepthook__(type, value, tb)
       else:
          import traceback, pdb
          # we are NOT in interactive mode, print the exception...
          traceback.print_exception (type, value, tb)
          print ()
          # ...then start the debugger in post-mortem mode.
          pdb.pm ()
    # end def info
    sys.excepthook = info

    Language.set      (cmd.language)
    knx = KNX_Project (cmd.knxproj, cmd.store)
    prj = None
    if knx.projects :
        prj = knx.projects [0]
    if cmd.output :
        file = cmd.output
    else :
        file = sys.stdout
    if cmd.address and not cmd.TEST :
        if prj :
            if cmd.address not in prj.devices :
                raise ValueError \
                    ( "Device %s not found. %s"
                    % (cmd.address, prj.devices.keys ())
                    )
            dev            = prj.devices [cmd.address]
            bytes, address = dev.eeprom (cmd.head)
            prg            = dev.program
        elif prj is None :
            prg = knx.program_store.get (cmd.address)
            dev = None
        if cmd.type :
            type           = cmd.type.lower ()
            if cmd.language :
                Language.set (cmd.language)
            if type == "t" :
                import struct
                bytes    = bytes  [cmd.head:]
                address += cmd.head
                data  = struct.unpack (">%dH" % (len (bytes) / 2), bytes)
                for x in data :
                    file.write ("%04X %04X\n" % (address, x))
                    address += 2
            elif type == "b" : ### as binary block
                if cmd.output :
                    file = open (file.name, "wb")
                file.write (bytes)
            elif type == "r" : ### human readable ;-)
                file.write ("%s\n" % dev.com_table)
                file.write ("%s\n" % dev.address_table)
                file.write ("%s\n" % dev.assoc_table)
            elif type == "h" : ### HTML
                if cmd.output :
                    file = open (file.name, "w", encoding = "utf-8")
                file.write (prg.as_html ())
            elif type == "e" : ### EEPROM as HTML table
                if cmd.output :
                    file = open (file.name, "w", encoding = "utf-8")
                file.write (prg.eeprom_as_html (cmd.eeprom_ref))
            elif type == "p" : ### parameters as plain text 
                if cmd.output :
                    file = open (file.name, "w", encoding = "utf-8")
                file.write (prg.as_html ("parameters-as-text.jnj"))
            elif type == "c" : ### parameters as csv file
                if cmd.output :
                    file = open (file.name, "w", encoding = "latin1")
                file.write (prg.as_html ("parameters-as-csv.jnj"))
        if cmd.pickle : ### create a pickle of the device program
            ps = Program_Store (cmd.pickle)
            ps.add             (dev.program)
            ps.close           ()
        return dev
    elif cmd.TEST: ### test loading of a program from a pickle zip file
         ps = Program_Store (cmd.TEST)
         prg = ps.get       (cmd.address, None)
         ps.close           ()
    elif cmd.SHOW_PROGRAMS :
        prgs = collections.defaultdict (list)
        for d in set (knx.devices.values ()) :
            prgs [d.program_id].append (d)
        for pid, dev in prgs.items () :
            print (pid)
            for d in dev :
                print (" -", d.name)
        print ("Found languages")
        for l in Language.Languages :
            print ("- " + l)
    if cmd.output :
        file.close ()
    return knx
# end def main

if __name__ == "__main__" :
    import argparse
    def auto_int (v) : return int (v, 0)

    FileType = argparse.FileType
    parser = argparse.ArgumentParser ("KNX Project file reader")
    parser.add_argument ("knxproj", type = FileType ("rb"))
    parser.add_argument ( "-a", "--address",    type   = str)
    parser.add_argument ( "-e", "--eeprom_ref", type   = auto_int, default = 0)
    parser.add_argument ( "--head",             type   = int, default = 0x100)
    parser.add_argument ( "-O", "--output",     type   = FileType ("w"))
    parser.add_argument ( "-t", "--type",       type   = str)
    parser.add_argument ( "-p", "--pickle",     type   = str)
    parser.add_argument ( "-T", "--TEST",       type   = str)
    parser.add_argument ( "-s", "--store",      type   = str)
    parser.add_argument ( "-S", "--SHOW_PROGRAMS", action = "store_true")
    parser.add_argument ( "-l", "--language", type   = str, default = "en-US")
    knx = main (parser.parse_args())
### __END__ STG.KNX_Project
