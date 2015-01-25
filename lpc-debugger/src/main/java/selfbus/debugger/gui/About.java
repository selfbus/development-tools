package selfbus.debugger.gui;

import java.awt.BorderLayout;
import java.awt.Container;
import java.awt.Window;
import java.text.MessageFormat;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JEditorPane;
import javax.swing.JScrollPane;
import javax.swing.event.HyperlinkEvent;
import javax.swing.event.HyperlinkListener;

import org.apache.commons.lang3.StringUtils;
import org.selfbus.sbtools.common.gui.components.Dialog;
import org.selfbus.sbtools.common.gui.components.Dialogs;

import selfbus.debugger.Application;
import selfbus.debugger.misc.I18n;

/**
 * The "about" dialog.
 */
public class About extends Dialog
{
   private static final long serialVersionUID = 3364224311549701046L;

   /**
    * Create the "about" dialog.
    */
   public About(Window owner)
   {
      super(owner);

      setTitle(I18n.getMessage("About.Title"));
      setSize(600, 600);

      Container body = getBodyPane();
      body.setLayout(new BorderLayout());

      String licenseUrl = "http://www.gnu.org/licenses";
      String projectUrl = "http://www.selfbus.org";

      StringBuilder sb = new StringBuilder();

      sb.append("<html><body style=\"background-color:transparent;\">");
      sb.append("<h1>").append(htmlEncode(I18n.getMessage("About.ProductName"))).append("</h1>");

      String version = Application.getInstance().getVersion();
      String buildNumber = Application.getInstance().getBuildNumber();
      String buildDate = Application.getInstance().getBuildDate();

      if (!StringUtils.isEmpty(version))
      {
         sb.append(MessageFormat.format(htmlEncode(I18n.getMessage("About.Version")), version, null))
           .append("<br /><br />");
      }

      if (!StringUtils.isEmpty(buildNumber))
      {
         sb.append(MessageFormat.format(htmlEncode(I18n.getMessage("About.buildNumber")), buildNumber.substring(0, 7), null))
           .append("<br />");
      }

      if (!StringUtils.isEmpty(buildDate))
      {
         sb.append(MessageFormat.format(htmlEncode(I18n.getMessage("About.buildDate")), buildDate, null))
           .append("<br />");
      }

      sb.append("<br />");
      sb.append("<i>").append(htmlEncode(I18n.getMessage("About.copyright"))).append("</i><br /><br />");

      sb.append(MessageFormat.format(htmlEncode(I18n.getMessage("About.Website")), "<a href=\"" + projectUrl + "\">"
            + projectUrl + "</a>", null));
      sb.append("<br /><br />");

      sb.append(htmlEncode(I18n.getMessage("About.License"))).append("<br /><br />");
      sb.append(htmlEncode(I18n.getMessage("About.Warranty"))).append("<br /><br />");

      sb.append(MessageFormat.format(htmlEncode(I18n.getMessage("About.ObtainLicense")), "<a href=\"" + licenseUrl
            + "\">" + licenseUrl + "</a>", null));

      sb.append("</body></html>");

      final JEditorPane jep = new JEditorPane("text/html", sb.toString());
      jep.setOpaque(false);
      jep.setEditable(false);
      jep.setBorder(BorderFactory.createEmptyBorder(10, 20, 4, 20));
      body.add(new JScrollPane(jep), BorderLayout.CENTER);

      addButton(new JButton(I18n.getMessage("Button.close")), Dialog.ACCEPT);

      jep.addHyperlinkListener(new HyperlinkListener()
      {
         @Override
         public void hyperlinkUpdate(HyperlinkEvent e)
         {
            if (e.getEventType() == HyperlinkEvent.EventType.ACTIVATED)
            {
               try
               {
                  java.awt.Desktop.getDesktop().browse(e.getURL().toURI());
               }
               catch (Exception ex)
               {
                  Dialogs.showExceptionDialog(ex, I18n.getMessage("About.ErrStartBrowser"));
               }
            }
         }
      });
   }

   /**
    * Encode special characters in str for HTML
    */
   private String htmlEncode(final String str)
   {
      return str.replace("&", "&amp;").replace("'", "&rsquo;").replace("\"", "&quot;").replace("<", "&lt;")
         .replace(">", "&gt;").replace("\n", "<br />");
   }
}
