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
#    STG.Program_Store
#
# Purpose
#    A zip file containg pickled device program information
#
#--
from    STG.Language        import Language
from    STG.Program         import Program
from    STG.Datapoint       import Datapoint
from    STG.Parameter       import Parameter_Type, Parameter, Parameter_Ref, Absolute_Segment
from    STG.Com_Object      import Com_Object, Com_Object_Ref
import  tempfile
import  zipfile
import  pickle
import  shutil
import  os

class Program_Store :
    """Zip file containing cached data for device programs"""

    Verbose     = 0
    Table       = dict ()
    Class_Order = ( Datapoint
                  , Absolute_Segment
                  , Parameter_Type
                  , Parameter, Parameter_Ref
                  , Com_Object, Com_Object_Ref
                  )

    def __init__ (self, file_name = None, project = None) :
        self.file_name = file_name
        self.project   = project
        if file_name :
            self._zip  = zipfile.ZipFile (file_name, "a")
    # end def __init__

    def add (self, program) :
        if program.id not in self.Table :
            self.Table [program.id] = program
        if self.file_name :
            try :
                self._zip.open (program.id, "r").close ()
                self._delete   (program.id)
            except KeyError :
                pass
            self._zip.writestr (program.id, self._program_as_pickle (program))
            self._zip.close ()
            self._zip  = zipfile.ZipFile (self.file_name, "a")
    # end def add

    def close (self) :
        if self.file_name :
            self._zip.close ()
    # end def close

    def _delete (self, file_name) :
        self._zip.close ()
        tempdir = tempfile.mkdtemp ()
        try:
            tempname = os.path.join (tempdir, '_temp.zip')
            with zipfile.ZipFile (self.file_name, "r") as zipread :
                with zipfile.ZipFile (tempname, "w") as zipwrite :
                    for item in zipread.infolist ():
                        if item.filename != file_name :
                            data = zipread.read (item.filename)
                            zipwrite.writestr   (item, data)
            shutil.move   (tempname, self.file_name)
        finally:
            shutil.rmtree (tempdir)
        self._zip = zipfile.ZipFile (self.file_name, "a")
    # end def _delete

    def get (self, id, project = None) :
        if project is None :
            project = self.project
        if id not in self.Table :
            try :
                if not self.file_name :
                    raise KeyError (id)
                result = self._program_from_zip (self._zip.read (id))
            except KeyError :
                if project is not None :
                    man_id   = id [:6]
                    prg_root = project.xml_file (man_id, "%s.xml" % id)
                    Language.add            (prg_root)
                    result    = Program \
                        (Program.get (prg_root, "//E:ApplicationProgram"))
                    self.add (result)
                else :
                    raise
            self.Table [id] = result
        return self.Table [id]
    # end def get

    def _program_as_pickle (self, program) :
        result = dict ()
        if self.Verbose :
            print ("Dump program %s" % (program.id, ))
        result ["Language"] = Language.pickle_cargo ()
        for cls in self.Class_Order :
            if self.Verbose >= 5 :
                print ("Dump ", cls.__name__)
            result [cls.__name__] = states = []
            for o in cls.Table.values () :
                states.append (o.pickle_cargo)
        if self.Verbose >= 5 :
            print ("Dump program")
        result ["program"] = program.pickle_cargo
        return pickle.dumps (result)
    # end def pickle

    def _program_from_zip (self, data) :
        dump = pickle.loads (data)
        Language.From_Pickle (dump ["Language"])
        for rcls in self.Class_Order :
            cls_name = rcls.__name__
            if self.Verbose >= 5 :
                print ("Extract", cls_name)
            for state in dump [cls_name] :
                rcls.From_Pickle (state)
        #import pdb; pdb.set_trace ()
        if self.Verbose >= 5 :
            print ("Extract Program")
        result = Program.From_Pickle (dump ["program"])
        if self.Verbose :
            print ("Program %s extracted from store" % (result.id, ))
        return result
    # end def _program_from_zip

# end class Program_Store

if __name__ == "__main__" :
    ps = Program_Store ("x.test")
    class Prg :
        id = "10"
        def pickle (self) :
            return "Foo"
        # end def pickle

    ps.add      (Prg ())
    ps.close    ()
### __END__ STG.Program_Store
