package selfbus.debugger.actions;

import java.awt.event.ActionEvent;

import javax.swing.SwingWorker;

import selfbus.debugger.gui.MainWindow;
import selfbus.debugger.misc.I18n;
import selfbus.debugger.misc.ImageCache;

/**
 * Mark all variables as invisible.
 */
public class AllInvisibleAction extends BasicAction
{
   private static final long serialVersionUID = -3590037078856358335L;

   public AllInvisibleAction()
   {
      super(I18n.getMessage("AllInvisibleAction.name"), I18n.getMessage("AllInvisibleAction.toolTip"),
            ImageCache.getIcon("icons/collapse-all"));
   }

   public void actionPerformed(ActionEvent e)
   {
      new SwingWorker<Void,Void>()
      {
         protected Void doInBackground() throws Exception
         {
            MainWindow.getInstance().allVariablesInvisible();
            return null;
         }
      }.execute();
   }
}
