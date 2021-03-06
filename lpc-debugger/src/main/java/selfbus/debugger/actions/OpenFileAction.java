package selfbus.debugger.actions;

import java.awt.FileDialog;
import java.awt.event.ActionEvent;
import java.io.File;
import java.util.Properties;

import javax.swing.KeyStroke;

import selfbus.debugger.Application;
import selfbus.debugger.filter.CdbFileNameFilter;
import selfbus.debugger.gui.MainWindow;
import selfbus.debugger.misc.I18n;
import selfbus.debugger.misc.ImageCache;

/**
 * Open a file that contains debug information.
 */
public final class OpenFileAction extends BasicAction
{
   private static final long serialVersionUID = -3518750343333514078L;

   public OpenFileAction()
   {
      super(I18n.getMessage("OpenFileAction.name"), I18n.getMessage("OpenFileAction.toolTip"), ImageCache
         .getIcon("icons/fileopen"));
      putValue("AcceleratorKey", KeyStroke.getKeyStroke(79, 128));
   }

   public void actionPerformed(ActionEvent e)
   {
      Application app = Application.getInstance();
      MainWindow mainWin = MainWindow.getInstance();
      Properties config = app.getConfig();

      File dir = new File(config.getProperty("lastOpenDir", app.getHomeDir().getAbsolutePath()));
      if (!dir.isDirectory())
      {
         dir = app.getHomeDir();
      }

      FileDialog fdlg = new FileDialog(mainWin);
      fdlg.setDirectory(dir.getPath());
      fdlg.setFilenameFilter(new CdbFileNameFilter());
      fdlg.setTitle(I18n.formatMessage("OpenFileAction.title", new String[] { I18n.getMessage("App.name") }));

      fdlg.setVisible(true);

      String fileName = fdlg.getFile();
      if (fileName == null)
         return;

      File file = new File(fdlg.getDirectory() + File.separator + fileName);
      if (!file.getAbsolutePath().equals(app.getConfig().getProperty("lastCdbFile")))
         app.getConfig().remove("hiddenVariables");

      app.setCdbFile(file);
      app.getConfig().setProperty("lastOpenDir", file.getParentFile().getAbsolutePath());
      app.getConfig().setProperty("lastCdbFile", file.getAbsolutePath());
   }
}
