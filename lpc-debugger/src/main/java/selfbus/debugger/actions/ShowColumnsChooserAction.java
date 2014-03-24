package selfbus.debugger.actions;

import java.awt.Component;
import java.awt.event.ActionEvent;

import selfbus.debugger.gui.MainWindow;
import selfbus.debugger.misc.I18n;
import selfbus.debugger.misc.ImageCache;

/**
 * Open the popup vor choosing the visible columns
 */
public class ShowColumnsChooserAction extends BasicAction
{
   private static final long serialVersionUID = 1498826834166376006L;

   public ShowColumnsChooserAction()
   {
      super(I18n.getMessage("ShowColumnsChooserAction.name"),
         I18n.getMessage("ShowColumnsChooserAction.toolTip"),
         ImageCache.getIcon("icons/view_text"));
   }

   public synchronized void actionPerformed(ActionEvent e)
   {
      Component c = (Component) e.getSource();
      MainWindow.getInstance().showColumnsPopup(c.getX(), c.getY() + c.getHeight() - 1);
   }
}
