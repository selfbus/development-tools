import  argparse
import  os
import  re
from    STG.Test_Case   import Test_Case

def _create_cpp_file (file_name, dest_dir) :
    if not dest_dir :
        tests_start = file_name.rfind ("tests")
        if tests_start < 0 :
            cpp_file_name = file_name
        else :    
            cpp_file_name = \
                ( file_name [:tests_start]
                + file_name [tests_start:].replace ("tests", "src", 1)
                )
        cpp_file_name = cpp_file_name.replace (".tc", ".cpp")
    Test_Case (file_name).create_code (cpp_file_name)
# end def _create_cpp_file

parser = argparse.ArgumentParser ("Create_Test_Case_Cpp_Files")
parser.add_argument ( "spec_root_directory",         type = str)
parser.add_argument ( "-c", "--cpp-root-directory",  type = str)
parser.add_argument ( "-f", "--filter",              type = str
                    , default = ".*"
                    , help = "Regex for filtering the test case spec files"
                    )
parser.add_argument ( "-i", "--ignore",              type = str
                    , help = "Regex for ignoring the test case spec files"
                    )
cmd = parser.parse_args ()


filter_pat = re.compile (cmd.filter)
ignore_pat = re.compile (cmd.ignore or "This patter should never match any testcase")

for path, sub_dirs, files in os.walk (cmd.spec_root_directory) :
    for bn in files :
        if (       bn.endswith (".tc") 
           and     filter_pat.search (bn)
           and not ignore_pat.search (bn)
           ) :

            fn = os.path.join (path, bn)
            _create_cpp_file (fn, cmd.cpp_root_directory)
