package selfbus.debugger.gui.table;

import java.awt.Color;
import java.awt.Component;
import java.io.IOException;
import java.text.MessageFormat;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;

import javax.swing.JTable;
import javax.swing.table.DefaultTableCellRenderer;

import org.apache.commons.lang3.StringUtils;
import org.selfbus.sbtools.knxcom.application.Application;
import org.selfbus.sbtools.knxcom.telegram.Telegram;
import org.selfbus.sbtools.knxcom.telegram.TelegramFactory;

import selfbus.debugger.misc.ByteUtils;
import selfbus.debugger.misc.ConfigDefault;
import selfbus.debugger.misc.I18n;
import selfbus.debugger.model.Variable;
import selfbus.debugger.model.cdb.ArraySymbolSpec;
import selfbus.debugger.model.cdb.SymbolSpec;
import selfbus.debugger.model.cdb.SymbolType;

/**
 * A table cell renderer that renders the value of a {@link Variable}.
 */
public class VariableValueCellRenderer extends DefaultTableCellRenderer
{
   private static final long serialVersionUID = -880338873722517799L;

   private final String msgInvalidTelegram = I18n.getMessage("Error.invalidTelegram");
   private final String msgTelegram = I18n.getMessage("VariableValueCellRenderer.telegram");

   private final Set<String> telegramVars = new HashSet<String>();
   private final Properties props;

   private Color unusedColor = Color.GRAY;
   private Color modifiedColor = Color.RED;

   /**
    * Create a table cell renderer.
    *
    * @param props - the application's configuration.
    */
   public VariableValueCellRenderer(Properties props)
   {
      this.props = props;
      settingsChanged();
   }

   /**
    * {@inheritDoc}
    */
   public Component getTableCellRendererComponent(JTable table, Object obj, boolean isSelected, boolean hasFocus,
      int row, int column)
   {
      Variable var = (Variable) obj;
      Component comp = super.getTableCellRendererComponent(table, valueStr(var), isSelected, hasFocus, row, column);

      if (var.isModified())
         comp.setForeground(modifiedColor);
      else if (var.isUnused())
         comp.setForeground(unusedColor);

      return comp;
   }

   /**
    * Create a value string for a telegram variable.
    * 
    * @param var - the variable to process
    * @return The variable's value as string.
    */
   protected String telegramValueStr(Variable var)
   {
      try
      {
         Telegram telegram = TelegramFactory.createTelegram(var.getValue());

         String fromStr = telegram.getFrom().toString();
         String destStr = telegram.getDest().toString();

         final Application app = telegram.getApplication();
         String appData;
         if (app == null)
            appData = telegram.getTransport().name();
         else appData = app.toString();

         if (telegram.getTransport().hasSequence)
         {
            appData += " (";
            appData += I18n.getMessage("BusMonitorCellRenderer.Sequence");
            appData += ' ';
            appData += Integer.toString(telegram.getSequence());
            appData += ')';
         }

         final StringBuffer sb = new StringBuffer();
         (new MessageFormat(msgTelegram)).format(new Object[] { fromStr, destStr, appData }, sb, null);
         return sb.toString();
      }
      catch (IOException e)
      {
         return msgInvalidTelegram;
      }
   }

   /**
    * Create a string containing the variable's value. The string depends on the type of the variable.
    *
    * @param var - the variable to process
    * @return The variable's value as string.
    */
   protected String valueStr(Variable var)
   {
      SymbolSpec spec = var.getSpec();
      SymbolType type = var.getType();
      int size = var.size();

      if ((spec instanceof ArraySymbolSpec))
      {
         if (SymbolType.BIT_FIELD.equals(type))
         {
            return Integer.toBinaryString(ByteUtils.toInteger(var.getValue(), 0, size));
         }
         else if (SymbolType.CHAR.equals(type) && telegramVars.contains(var.getName()))
         {
            return telegramValueStr(var);
         }  
         else if (type.len > 0)
         {
            StringBuilder builder = new StringBuilder();
            for (int offs = 0; offs < size; offs += type.len)
               builder.append(ByteUtils.toInteger(var.getValue(), offs, type.len)).append(' ');
            return builder.toString();
         }
      }
      else if ((type == null) && (size > 0) && (size <= 4))
      {
         return Integer.toString(ByteUtils.toInteger(var.getValue(), 0, size));
      }
      else if (SymbolType.SBIT.equals(type))
      {
         return Integer.toString(var.getValue()[0]);
      }
      else if (SymbolType.CHAR.equals(type) || SymbolType.SHORT.equals(type) || SymbolType.INT.equals(type)
         || SymbolType.LONG.equals(type))
      {
         int val = ByteUtils.toInteger(var.getValue(), 0, size);
         return Integer.toString(val);
      }

      return "";
   }

   /**
    * Called when the settings were changed.
    */
   public void settingsChanged()
   {
      telegramVars.clear();

      String varNames = props.getProperty("telegramVariables", ConfigDefault.TELEGRAM_VARS);
      if (!StringUtils.isEmpty(varNames))
      {
         for (String varName : varNames.split("/,* */"))
            telegramVars.add(varName);
      }
   }
}
