package selfbus.debugger.model.cdb;

import org.slf4j.LoggerFactory;

/**
 * A symbol type.
 */
public enum SymbolType
{
   ARRAY("DA"),

   FUNCTION("DF"),

   POINTER("DG"),

   CODE_POINTER("DC"),

   RAM_POINTER_EXT("DX"),

   RAM_POINTER_INT("DD"),

   PAGED_POINTER("DP"),

   UPPER_POINTER("DI"),

   LONG("SL", 4),

   INT("SI", 2),

   CHAR("SC", 1),

   SHORT("SS", 2),

   VOID("SV"),

   FLOAT("SF"),

   STRUCTURE("ST"),

   SBIT("SX"),

   BIT_FIELD("SB");

   /** The symbol type string. */
   public final String type;

   /** The length of the type in bytes. */
   public final int len;

   public static SymbolType valueOfType(String cdbType)
   {
      for (SymbolType spc : values())
      {
         if (spc.type.equals(cdbType))
            return spc;
      }
      LoggerFactory.getLogger(SymbolType.class).warn("Unknown symbol type encountered: {}", cdbType);
      return null;
   }

   private SymbolType(String type)
   {
      this(type, 0);
   }

   private SymbolType(String type, int len)
   {
      this.type = type;
      this.len = len;
   }
}
