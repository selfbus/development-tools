package selfbus.debugger.actions;

import java.awt.event.ActionEvent;

import selfbus.debugger.gui.About;
import selfbus.debugger.gui.MainWindow;
import selfbus.debugger.misc.I18n;
import selfbus.debugger.misc.ImageCache;

/**
 * Show the "about" dialog.
 */
public final class AboutAction extends BasicAction
{
   private static final long serialVersionUID = 8622292771761081564L;

   /**
    * Create an action object.
    */
   public AboutAction()
   {
      super(I18n.getMessage("AboutAction.name"), I18n.getMessage("AboutAction.toolTip"),
            ImageCache.getIcon("icons/info"));
   }

   @Override
   public void actionPerformed(ActionEvent e)
   {
      final About dlg = new About(MainWindow.getInstance());
      dlg.center();
      dlg.setVisible(true);
   }
}
