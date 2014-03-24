package selfbus.debugger.actions;

import java.awt.event.ActionEvent;

import javax.swing.SwingWorker;

import selfbus.debugger.gui.MainWindow;
import selfbus.debugger.misc.I18n;
import selfbus.debugger.misc.ImageCache;

/**
 * Mark all variables as visible.
 */
public class AllVisibleAction extends BasicAction
{
   private static final long serialVersionUID = 5940510993770850314L;

   public AllVisibleAction()
   {
      super(I18n.getMessage("AllVisibleAction.name"), I18n.getMessage("AllVisibleAction.toolTip"),
            ImageCache.getIcon("icons/expand-all"));
   }

   public void actionPerformed(ActionEvent e)
   {
      new SwingWorker<Void,Void>()
      {
         protected Void doInBackground() throws Exception
         {
            MainWindow.getInstance().allVariablesVisible();
            return null;
         }
      }.execute();
   }
}
