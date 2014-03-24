package selfbus.debugger.gui.table;

import java.util.Vector;

import javax.swing.table.AbstractTableModel;

import selfbus.debugger.misc.I18n;
import selfbus.debugger.model.Variable;
import selfbus.debugger.model.VariableUtils;

/**
 * A table model for {@link Variable}s.
 */
public class VariablesTableModel extends AbstractTableModel
{
   private static final long serialVersionUID = 7040737433963301064L;

   /** The index of the variable's (is)visible column. */
   public static final int VISIBLE_COLUMN = 0;

   /** The index of the variable's module column. */
   public static final int MODULE_COLUMN = 1;

   /** The index of the variable's type column. */
   public static final int TYPE_COLUMN = 2;

   /** The index of the variable's name column. */
   public static final int NAME_COLUMN = 3;

   /** The index of the variable's value column. */
   public static final int VALUE_COLUMN = 4;

   /** The index of the variable's bytes column. */
   public static final int BYTES_COLUMN = 5;

   /** The number of columns that the model contains. */
   public static final int COLUMNS = 6;

   private final Vector<Variable> vars;
   private final Vector<String> types;

   private static final String[] COLUMN_NAMES;
   static
   {
      COLUMN_NAMES = new String[COLUMNS];
      COLUMN_NAMES[VISIBLE_COLUMN] = "*";
      COLUMN_NAMES[MODULE_COLUMN]  = I18n.getMessage("VariableComponent.moduleHeader");
      COLUMN_NAMES[TYPE_COLUMN]  = I18n.getMessage("VariableComponent.typeHeader");
      COLUMN_NAMES[NAME_COLUMN]  = I18n.getMessage("VariableComponent.nameHeader");
      COLUMN_NAMES[VALUE_COLUMN] = I18n.getMessage("VariableComponent.valueHeader");
      COLUMN_NAMES[BYTES_COLUMN] = I18n.getMessage("VariableComponent.bytesHeader");
   }

   /**
    * Create a variables table model
    * 
    * @param vars - the variables
    */
   public VariablesTableModel(Vector<Variable> vars)
   {
      super();
      this.vars = vars;

      types = new Vector<String>(vars.size());

      for (int i = 0; i < vars.size(); ++i)
      {
         Variable var = vars.get(i);
         types.add(VariableUtils.createTypeStr(var));
      }
   }

   /**
    * {@inheritDoc}
    */
   @Override
   public int getRowCount()
   {
      return vars.size();
   }

   /**
    * {@inheritDoc}
    */
   @Override
   public int getColumnCount()
   {
      return COLUMNS;
   }

   /**
    * {@inheritDoc}
    */
   @Override
   public String getColumnName(int col)
   {
      return COLUMN_NAMES[col];
   }

   /**
    * Returns the most specific superclass for all the cell values
    * in the column.  This is used by the <code>JTable</code> to set up a
    * default renderer and editor for the column.
    *
    * @param columnIndex  the index of the column
    * @return the common ancestor class of the object values in the model.
    */
   public Class<?> getColumnClass(int col)
   {
      if (col == VISIBLE_COLUMN)
         return Boolean.class;

      if (col == VALUE_COLUMN || col == BYTES_COLUMN)
         return byte.class;

      return String.class;
   }

   /**
    * {@inheritDoc}
    */
   @Override
   public boolean isCellEditable(int row, int col)
   {
      return col == VISIBLE_COLUMN;
   }
   
   /**
    * {@inheritDoc}
    */
   @Override
   public Object getValueAt(int row, int col)
   {
      switch (col)
      {
         case VISIBLE_COLUMN:
            return Boolean.valueOf(vars.get(row).isVisible());

         case MODULE_COLUMN:
            return vars.get(row).getModule();

         case TYPE_COLUMN:
            return types.get(row);

         case NAME_COLUMN:
            return vars.get(row).getName();

         case VALUE_COLUMN:
            return vars.get(row);

         case BYTES_COLUMN:
            return vars.get(row);

         default:
            throw new IllegalArgumentException("invalid column " + col);
      }
   }

   /**
    * Get a variable.
    * 
    * @param row - the row of the variable to get
    * @return The variable
    */
   public Variable getVariable(int row)
   {
      return vars.get(row);
   }

   /**
    * {@inheritDoc}
    */
   public void setValueAt(Object value, int row, int col)
   {
      if (col == VISIBLE_COLUMN)
      {
         vars.get(row).setVisible((Boolean) value);
         fireTableCellUpdated(row, VISIBLE_COLUMN);
      }
   }

   /**
    * Mark all variables in the model as unused.
    */
   public void markAllUnused()
   {
      for (int row = vars.size() - 1; row >= 0; --row)
      {
         vars.get(row).markUnused();
         fireValuesChanged(row);
      }
   }

   /**
    * Set the visibility of all variables.
    * 
    * @param visible - the visibility to set
    */
   public void setAllVisible(boolean visible)
   {
      for (int row = vars.size() - 1; row >= 0; --row)
      {
         vars.get(row).setVisible(visible);
         fireTableCellUpdated(row, VISIBLE_COLUMN);
      }

      fireValuesChanged();
   }

   /**
    * The values of a table row have changed.
    *
    * @param row - the row that changed.
    */
   public void fireValuesChanged(int row)
   {
      fireTableCellUpdated(row, VALUE_COLUMN);
      fireTableCellUpdated(row, BYTES_COLUMN);
   }

   /**
    * The values of all table rows have changed.
    */
   public void fireValuesChanged()
   {
      for (int row = vars.size() - 1; row >= 0; --row)
      {
         fireTableCellUpdated(row, VALUE_COLUMN);
         fireTableCellUpdated(row, BYTES_COLUMN);
      }
   }
}
