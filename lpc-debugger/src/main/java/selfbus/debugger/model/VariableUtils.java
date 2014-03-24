package selfbus.debugger.model;

import selfbus.debugger.model.cdb.ArraySymbolSpec;
import selfbus.debugger.model.cdb.StructureSymbolSpec;
import selfbus.debugger.model.cdb.SymbolSign;
import selfbus.debugger.model.cdb.SymbolSpec;
import selfbus.debugger.model.cdb.SymbolType;

/**
 * Utility functions for {@link Variable}s.
 */
public final class VariableUtils
{
   /**
    * Create a human readable string describing the type of the variable.
    * 
    * @param var
    *           - the variable to process
    * @return The type as human readable string.
    */
   public static String createTypeStr(Variable var)
   {
      SymbolSpec spec = var.getSpec();

      if (spec == null)
      {
         return " ";
      }
      SymbolType type = spec.getType();
      SymbolSign sign = spec.getSign();

      if (SymbolType.SBIT.equals(type))
      {
         sign = null;
      }
      String signStr = SymbolSign.UNSIGNED.equals(sign) ? "u" : "";
      String typeStr = signStr + type.toString().toLowerCase();

      if (SymbolType.BIT_FIELD.equals(type))
      {
         int count = ((ArraySymbolSpec) spec).getCount();
         if (count == 1)
            return "bit";
         return "bit[" + ((ArraySymbolSpec) spec).getCount() + ']';
      }
      if ((spec instanceof ArraySymbolSpec))
      {
         return typeStr + '[' + ((ArraySymbolSpec) spec).getCount() + ']';
      }
      if ((spec instanceof StructureSymbolSpec))
      {
         return "struct " + ((StructureSymbolSpec) spec).getName();
      }

      return typeStr;
   }
}
