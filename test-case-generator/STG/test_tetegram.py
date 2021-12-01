from    STG.Telegram import _Telegram_
from    STG.Telegram import *
import  sys

def as_bin (value, size = 8) :
    mask   = 2 ** (size - 1)
    result = []
    for b in range (size) :
        if b == 8 :
            result.append (" ")
        if value & mask :
            result.append ("1")
        else :
            result.append ("0")
        mask >>= 1
    return "".join (result)
# end def as_bin

def _dump_header (cls, indent) :
    sti = getattr (cls, "Sub_Type_Id", None)
    if sti is not None :
        stb              = cls.Sub_Type_Base
        st_field_name    = cls.__name__.lower ()
        off, shift, mask = stb.Match
        mask             = as_bin (mask << shift)
        field            = cls.fields.get (st_field_name, None)
        value            = ""
        if field :
            value        = " [%s]" % as_bin (field.default << field.shift)
        print \
            ( "%s%s [%s] %d %s%s"
            % (indent, cls.__name__, bin (sti), off, mask, value)
            )
    else :
        print ("%s%s" % (indent, cls.__name__))
# end def _dump_header

def _dump_fields (cls, indent) :
    for f in cls.sorted_fields :
        print \
            ( "%s  %-30s: %d %d %04X %s"
            % ( indent, f.name, f.offset, f.shift
              , f.mask << f.shift, as_bin (f.default << f.shift, 16)
              )
            )
# end def _dump_fields

def dump_class_tree (root, fields = False, indent = "") :
    _dump_header (root, indent)
    if fields :
        _dump_fields (root, indent)
    for st in root.__dict__.get ("Sub_Types", {}).values () :
        dump_class_tree (st, fields, indent + "  ")
# end def dump_class_tree

def dump_reverse (leaf, fields = False, indent = "") :
    bases = tuple (reversed (leaf.mro ()))
    start = bases.index (_Telegram_)
    for l, cls in enumerate (bases [-1:]) :
        indent = "  " * l
        _dump_header (cls, indent)
    if fields :
        _dump_fields (cls, indent)
# end def dump_reverse

def dump (tel) :
    if tel is None :
        name = ""
        raw = range (16)
        fmt  = "%2d"
    else :
        name = tel.__class__.__name__
        raw  = tel.bytes
        fmt  = "%02X"
    print \
        ( "%-20s" % name, " ".join (fmt % b for b in raw)
        )
# end def dump

class Erase_Sector_Telegram (Numbered_Data_Packet_b10_Base) :
    Sub_Type_Id = 0b10
    Fields      = \
        ( Memory_Count_Field ("count",  7, 0, 0xF)
        , Int_Field          ("cmd",    8, 0, 0xFF)
        , Int_Field          ("number", 8, 0, 0xFF)
        )
    Defaults = dict (count = 1, cmd = 1)

    payload_length = 3

# end class Erase_Sector_Telegram

if 0 :
    dump_class_tree (_Telegram_, True)
elif 1 :
    classes = []
    for a in sys.argv [1:] :
        classes.append (eval (a))
    if not classes :
        classes = [Connect, Disconnect]#, Memory_Read]
    for cls in classes :
        dump_reverse (cls,     True)
else :
    dump (None)
    dump (Connect (src = "1.1.1", dst = "1.1.2", priority = 0))
    dump (Disconnect (src = "1.1.1", dst = "1.1.2", priority = 0))
    dump (ACK (src = "1.1.1", dst = "1.1.2", priority = 0))
    dump (NACK (src = "1.1.1", dst = "1.1.2", priority = 0))
    dump (Memory_Read_Request (src = "1.1.1", dst = "1.1.2", priority = 0, pno = 1, count = 2, address = 0x1000))
    dump (Memory_Read_Request (src = "1.1.1", dst = "1.1.2", priority = 0, pno = 2, count = 4, address = 0x1000))
    dump (Memory_Read_Response (src = "1.1.1", dst = "1.1.2", priority = 0,pno = 2, address = 0x1000, mem = bytes ((1,2,3,4))))
    dump (Memory_Read_Value    (src = "1.1.1", dst = "1.1.2", priority = 0,pno = 2, address = 0x1000, mem = bytes ((1,2,3,4))))
    dump (Send_Value  (src = "1.1.1", dst = "1/1/2", value = 1, length = 1))
