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
#    STG.Test_Case
#
# Purpose
#    Classes for test case generation
#--

from    STG.KNX_Project     import KNX_Project
from    STG.Project         import Individual_Address
from    STG.Telegram        import Get_Value, Send_Value
import  io
import  re
import  datetime
import  os

class _Base_ :
    Current_Test_Case = None
# end class _Base_    

class Section (_Base_) :
    """A simple comment in the output"""

    def __init__ (self, * lines, ** kw) :
        self.lines    = lines
        new_line      = kw.pop ("new_line", None)
        if new_line is None :
            new_line  = 1 if self.Current_Test_Case.steps else 0
        self.new_line = new_line
        self.Current_Test_Case.steps.append (self)
    # end def __init__

    def init_code (self, head, number) :
        code = "// %s\n" % ("\n// ".join (self.lines), )
        nl   = self.new_line
        while nl :
            code = "\n%s" % (code, )
            nl  -= 1
        return number, code
    # end der init_code

# end class Section

class Comment (Section) :
    """Add a comment line to the source file"""

    def __init__ (self, * args, ** kw) :
        if "new_line" not in kw :
            kw ["new_line"] = 0
        super (Comment, self).__init__ (* args, ** kw)
    # end def __init__

# end class Comment

class Include (_Base_) :
    """Include a set of test steps from an external file"""

    def __init__ (self, file_name) :
        tc        = self.Current_Test_Case
        file_name = os.path.join (tc.directory, file_name)
        with open (file_name) as f :
            code      = compile (f.read (), file_name, "exec")
            exec (code, globals (), tc.vars)
    # end def __init__

# end class Include

class Test_Step (_Base_) :
    """Base class for all kinds fo test steps."""

    tick_length = 0
    step_count  = 0

    def __init__ ( self
                 , kind
                 , step     = "NULL"
                 , length   = 0
                 , variable = 0
                 , telegram = None
                 , comment  = None
                 , new_line = 0
                 ) :
        self.kind     = kind
        self.length   = length
        self.variable = variable
        self.step     = step
        if isinstance (step, (list, tuple)) :
            self.step_count = len (step)
        self.new_line = new_line
        if telegram :
            bytes     = ["0x%02X" % b for b in telegram.bytes [:-1]]
            self.length = len (bytes)
            telegram  = "{%s}" % (", ".join (bytes))
        else :
            telegram  = "{}"
        self.telegram = telegram
        self.comment  = comment
        self.Current_Test_Case.steps.append (self)
        self.Tick     = self.Ticks
        Test_Step.Ticks += self.tick_length
    # end def __init__

    def init_code (self, head, number) :
        result = ( "/* %3d */ %s{%-15s, %6d, %2d, (StepFunction *) %-20s, %s}\n"
                 % ( number
                   , head, self.kind, self.length, self.variable
                   , self.step or "NULL", self.telegram
                   )
                 )
        if self.comment :
            comment = self.comment
            if not isinstance (comment, (tuple, list)) :
                comment = (comment, )
            comment = "\n  // ".join (comment)
            result = "          // %s\n%s" % (comment, result)
        if self.new_line :
            result = "\n" + result
        return number + 1, result
    # end def as_init

    def __add__ (self, rhs) :
        return self.Tick + rhs - self.Ticks
    # end def __add__

# end class Test_Step

class App_Loop (Test_Step) :
    """Run the application loop and simulate time passing"""

    def __init__ (self, step = "_loop", ticks = 0, ** kw) :
        self.tick_length = ticks
        super (App_Loop, self).__init__ \
            ( kind   = "TIMER_TICK"
            , step   = step
            , length = ticks
            , ** kw
            )
    # end def __init__

# end class App_Loop

class Progress_Time (App_Loop) :
    """Just simulate some passing time"""

    def __init__ (self, ticks, comment = None, ** kw) :
        super (Progress_Time, self).__init__ \
            ( ticks   = ticks
            , comment = comment
            , ** kw
            )
    # end def __init__

# end class Progress_Time

class Send_Telegram (Test_Step) :
    """Check if the prepared send telegram in the queue of the device
       matches this telegram
    """

    def __init__ ( self, device, number, value = None, kind = Send_Value
                 , ** kw
                 ) :
        self.com_object =  device.com_objects_by_number [number]
        telegram        = self.com_object.telegram \
            (value, kind = kind)
        super (Send_Telegram, self).__init__ \
            ( kind     = "TEL_TX"
            , step     = kw.pop ("step", "_loop")
            , telegram = telegram
            , ** kw
            )
    # end def __init__

# end class Send_Telegram

class Receive_Telegram (Test_Step) :
    """Put the telegram into the receive buffer of the device"""

    Source = Individual_Address ("1.1.254").value

    def __init__ (self, device, number, value = None, kind = Send_Value
                 , ** kw
                 ) :
        telegram = device.com_objects_by_number [number].telegram \
            (value, self.Source, kind = kind)
        super (Receive_Telegram, self).__init__ \
            ( kind     = "TEL_RX"
            , step     = kw.pop ("step", "_loop")
            , telegram = telegram
            , ** kw
            )
    # end def __init__

# end class Receive_Telegram

class Test_Case :
    """A test case"""

    ets_config_pat     = re.compile ("ets_project\s*=\s*\"([\s\w.-]+)\"")
    device_address_pat = re.compile ("device_address\s*=\s*\"([\w.]+)\"")
    Project_Files      = dict ()

    def __init__ (self, file_name) :
        self._parse (file_name)
    # end def __init__

    def eeprom_init (self, device, file, limit = 1024*1024) :
        result = [ "    // >>> EEPROM INIT"
                 , "    // Date: %s" % (datetime.datetime.now (), )
                 ]
        eep, address = self.device.eeprom ()
        #result.append (self.assoc_table.  as_c_comment (eep))
        #result.append (self.address_table.as_c_comment (eep))
        #result.append (self.com_table.    as_c_comment (eep))
        per_row = 4
        for o in range (0, min (limit, len (eep)), per_row) :
            line = []
            for c in range (per_row) :
                try :
                    b = eep [o + c]
                    line.append \
                        ("userEeprom[0x%04X] = 0x%02X;" % (address + o + c, b))
                except IndexError :
                    pass
            result.append ("    %s" % (" ".join (line)))
        address = device.address.value
        result.append \
            ( "    userEeprom.addrTab [0] = 0x%02X; "
                  "userEeprom.addrTab [1] = 0x%02X;"
            % (address >> 8, address & 0xFF)
            )
        result.append ("    // <<< EEPROM INIT")
        result = "\n".join (result)
        if not file :
            print (result)
        else :
            file.write (result)
            file.write ("\n")
    # end def eeprom_init

    def _project_file (self, file_name) :
        if file_name not in self.Project_Files :
            knx    = KNX_Project \
                ( os.path.join (self.directory, file_name)
                , os.path.join (self.directory, "devices.zip")
                )
            self.Project_Files [file_name] = knx
        return self.Project_Files [file_name]
    # end def _project_file

    def _parse (self, file_name) :
        self.steps     = []
        self.file_name = os.path.abspath (file_name)
        self.directory = os.path.dirname (file_name)
        self.vars      = vars = \
            {"Get_Value": Get_Value, "Send_Value": Send_Value}
        with open (file_name) as f :
            content = f.read                         ()
            ets     = self.ets_config_pat.search     (content)
            addr    = self.device_address_pat.search (content)
            if ets and addr:
                knx             = self._project_file (ets.group (1))
                addr            = addr.group (1)
                prj             = knx.projects [0]
                if addr not in prj.devices :
                    raise KeyError \
                        ( "Device %s not found. %s"
                        % (addr, prj.devices.keys ())
                        )
                vars ["device"]           = d = prj.devices [addr]
                _Base_.Current_Test_Case  = self
                Test_Step.Ticks           = 0
                code                      = compile (content, file_name, "exec")
                exec (code, globals (), vars)
            else :
                raise ValueError ("No device specified")
        self.name           = vars.pop ("name")
        self.description    = vars.pop ("description", None)
        self.setup          = vars.pop ("setup", "NULL")
        self.state          = vars.pop ("state", "_gatherState")
        self.power_on_delay = vars.pop ("power_on_delay", 0)
        self.device         = vars ["device"]
        self.tags           = vars.pop ("tags", ())
        if self.tags :
            self.tags = "[%s]" % ("][".join (self.tags), )
        if isinstance (self.power_on_delay, str) :
            self.power_on_delay = 0
    # end def _parse

    def _replace_in_file (self, content, section, new) :
        pat = re.compile \
            ( "^\s*// >>> %s$(.)+// <<< %s$" % (section, section)
            , re.MULTILINE | re.DOTALL
            )
        if pat.search (content) :
            return pat.sub (new.strip (), content)
        return content + new
    # end def _replace_in_file

    def create_code (self, file_name) :
        file = io.StringIO ()
        file.write ("// >>> TC:%s\n" % (self.name, ))
        file.write ("// Date: %s\n" % (datetime.datetime.now (), ))
        file.write ("\n/* Code for test case %s */\n" % (self.name, ))
        ee_init   = "NULL"
        man = dev = ver = 0
        if self.device :
            ee_init  = "%s_eepromSetup" % (self.name, )
            file.write ("static void %s(void)\n" % (ee_init, ))
            file.write ("{\n")
            self.eeprom_init (self.device, file = file)
            file.write ("}\n\n")
            #man = self.device.manufacturer
            #dev = self.device.deviceType
            #ver = self.device.version
        if self.steps :
            file.write ("static Telegram tel_%s[] =\n" % (self.name, ))
            file.write ("{\n")
            head = "  "
            i    = 1
            for t in self.steps :
                i, code = t.init_code (head, i)
                file.write            (code)
                if i > 1 :
                    head = ", "
            file.write (", {END}\n")
            file.write ("};\n")

        file.write ("static Test_Case %s_tc = \n" % (self.name, ))
        file.write ("{\n")
        file.write ('  "%s"\n' % (self.description or self.name, ))
        file.write (", 0x%04x, 0x%04x, %02x\n" % (man, dev, ver))
        file.write (", %d // power-on delay\n" % (self.power_on_delay, ))
        file.write (", %s\n" % (ee_init, ))
        file.write (", %s\n" % (self.setup, ))
        file.write (", (StateFunction *) %s\n" % (self.state or "NULL"))
        file.write (", (TestCaseState *) &_refState\n")
        file.write (", (TestCaseState *) &_stepState\n")
        file.write (", tel_%s\n" % (self.name, ))
        file.write ("};\n\n")
        file.write ('TEST_CASE("%s","%s")\n' % (self.description, self.tags))
        file.write ("{\n")
        file.write ("  executeTest(& %s_tc);\n" % (self.name, ))
        file.write ("}\n")
        file.write ("// <<< TC:%s\n" % (self.name, ))
        if not file_name :
            sys.stdout.write (file.getvalue ())
        else :
            if not os.path.exists (file_name) :
                self._create_file (file_name)
            with open (file_name) as f :
                content = f.read ()
            with open (file_name, "w") as f :
                f.write \
                    ( self._replace_in_file
                        ( content
                        , "TC:%s" % (self.name, )
                        , file.getvalue ()
                        )
                    )
                print ("%s updated" % (file_name, ))
    # end def create_code

    def _create_file (self, file_name) :
        code = """/*
 *  %s -
 *
 *  Copyright (C) 2014-2015 Martin Glueck <martin@mangari.org>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License version 3 as
 *  published by the Free Software Foundation.
 */
#include "protocol.h"
#include "catch.hpp"
#include "sblib/timer.h"
"""
        with open (file_name, "w") as file :
            file.write (code % os.path.basename (file_name))
    # end def _create_file

# end class Test_Case

if __name__ == "__main__" :
    import sys
    import glob

    def info(type, value, tb):
        if hasattr(sys, 'ps1') or not sys.stderr.isatty():
            # You are in interactive mode or don't have a tty-like
            # device, so call the default hook
            sys.__execthook__(type, value, tb)
        else:
            import traceback, pdb
            # You are not in interactive mode; print the exception
            traceback.print_exception(type, value, tb)
            print ()
            # ... then star the debugger in post-mortem mode
            pdb.pm ()

    sys.excepthook = info

    file_name = None
    if len (sys.argv) > 2 :
        file_name = sys.argv [2]
    tc_spec = sys.argv [1]
    for tc in glob.glob (tc_spec) :
        print ("Handle", tc)
        Test_Case (tc).create_code (file_name)
### __END__ Test_Case
