package selfbus.debugger.gui;

import java.awt.Dimension;
import java.awt.Frame;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.Properties;

import javax.swing.Box;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JTextField;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import selfbus.debugger.actions.ActionFactory;
import selfbus.debugger.actions.AutoUpdateAction;
import selfbus.debugger.misc.I18n;

/**
 * The settings dialog. Used for configuring the application.
 */
public class SettingsDialog extends JDialog
{
   private static final long serialVersionUID = 2238040856367925931L;
   private static final Logger LOGGER = LoggerFactory.getLogger(SettingsDialog.class);

   // Default auto update, in milliseconds
   private static final int DEFAULT_AUTO_UPDATE_MSEC = 2000;

   // Default receive timeout, in milliseconds
   private static final int DEFAULT_RECV_TIMEOUT_MSEC = 250;

   // Default baud rate
   private static final int DEFAULT_BAUD_RATE = 115200;

   private static final Insets PARAGRAPH_INSETS = new Insets(10, 8, 2, 8);
   private static final Insets INSETS = new Insets(2, 8, 2, 8);
   private static final int[] AUTO_UPDATE_MSEC = { 0, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000 };
   private static final int[] BAUD_RATES = { 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400 };

   private final JComboBox<Integer> cboBaudRate = new JComboBox<Integer>();
   private final JComboBox<String> cboAutoUpdate = new JComboBox<String>();
   private final JTextField inpRecvTimeout = new JTextField();
   private final JCheckBox cboResetOnOpen = new JCheckBox(I18n.getMessage("Settings.resetOnOpen"));
   private final Properties props;

   /**
    * Create a settings dialog.
    *
    * @param owner - the owning window.
    * @param props - the application's configuration.
    */
   public SettingsDialog(Frame owner, Properties props)
   {
      super(owner, I18n.formatMessage("Settings.title", new String[] { I18n.getMessage("App.shortName") }));
      this.props = props;

      addWindowListener(new WindowAdapter()
      {
         public void windowClosing(WindowEvent e)
         {
            SettingsDialog.this.toConfig();
         }
      });
      setMinimumSize(new Dimension(400, 300));
      setLayout(new GridBagLayout());
      int row = -1;

      add(new JLabel(I18n.getMessage("Settings.baudRate")), new GridBagConstraints(0, ++row, 1, 1, 1, 1, 18, 0,
         PARAGRAPH_INSETS, 0, 0));
      add(cboBaudRate, new GridBagConstraints(0, ++row, 1, 1, 1, 1, 18, GridBagConstraints.HORIZONTAL, INSETS, 0, 0));

      add(cboResetOnOpen, new GridBagConstraints(0, ++row, 2, 1, 1, 1, 18, GridBagConstraints.HORIZONTAL, INSETS, 0, 0));
      
      add(new JLabel(I18n.getMessage("Settings.autoUpdateInterval")), new GridBagConstraints(0, ++row, 1, 1, 1,
         1, 18, 0, PARAGRAPH_INSETS, 0, 0));
      add(cboAutoUpdate, new GridBagConstraints(0, ++row, 2, 1, 1, 1, 18, GridBagConstraints.HORIZONTAL, INSETS, 0, 0));
      
      add(new JLabel(I18n.getMessage("Settings.receiveTimeout")), new GridBagConstraints(0, ++row, 1, 1, 1,
         1, 18, 0, PARAGRAPH_INSETS, 0, 0));
      add(inpRecvTimeout, new GridBagConstraints(0, ++row, 2, 2, 1, 1, 18, GridBagConstraints.HORIZONTAL, INSETS, 0, 0));

      add(Box.createVerticalGlue(), new GridBagConstraints(0, ++row, 1, 1, 1, 100.0D, 18, 2, new Insets(0, 0, 0, 0), 0, 0));

      JButton closeButton = new JButton(I18n.getMessage("Settings.close"));
      add(closeButton, new GridBagConstraints(0, ++row, 1, 1, 1, 1, 14, 0, new Insets(20, 8, 8, 8), 0, 0));
      closeButton.addActionListener(new ActionListener()
      {
         public void actionPerformed(ActionEvent e)
         {
            SettingsDialog.this.toConfig();
            SettingsDialog.this.dispose();
         }
      });

      setupBaudRates();
      cboBaudRate.setMaximumRowCount(cboBaudRate.getItemCount());

      setupAutoUpdates();
      cboAutoUpdate.setMaximumRowCount(cboAutoUpdate.getItemCount());

      fromConfig();
   }

   /**
    * Setup the baud-rates combobox.
    */
   protected void setupBaudRates()
   {
      for (int baudRate: BAUD_RATES)
         cboBaudRate.addItem(Integer.valueOf(baudRate));
   }

   /**
    * Setup the auto-updates combobox.
    */
   protected void setupAutoUpdates()
   {
      for (int updateMsec : AUTO_UPDATE_MSEC)
      {
         if (updateMsec <= 1000)
         {
            cboAutoUpdate.addItem(I18n.formatMessage("Settings.autoUpdateMsec",
               new String[] { Integer.toString(updateMsec) }));
         }
         else
         {
            cboAutoUpdate.addItem(I18n.formatMessage("Settings.autoUpdateSec",
               new String[] { Float.toString(updateMsec * 0.001F) }));
         }
      }
   }

   /**
    * Get an integer value from the configuration properties. Use the default value if the integer
    * value is invalid or unset.
    * 
    * @param key - the name of the property to get
    * @param defaultValue - the default value
    * @return The property value, or the default as fallback
    */
   protected int getProp(String key, int defaultValue)
   {
      try
      {
         return Integer.parseInt(props.getProperty(key, Integer.toString(defaultValue)));
      }
      catch (NumberFormatException e)
      {
         Dialogs.showExceptionDialog(e, I18n.formatMessage("Error.invalidConfigValue", new String[] { key }));
         return defaultValue;
      }
   }

   /**
    * Initialize the dialog values from the configuration.
    */
   public void fromConfig()
   {
      int baudRate = getProp("serial.baudRate", DEFAULT_BAUD_RATE);

      for (int i = 0; i < cboBaudRate.getItemCount(); i++)
      {
         if (((Integer) cboBaudRate.getItemAt(i)).intValue() == baudRate)
         {
            cboBaudRate.setSelectedIndex(i);
            break;
         }
      }

      int updateMsec = getProp("autoUpdateMsec", DEFAULT_AUTO_UPDATE_MSEC);
      for (int i = 0; i < cboAutoUpdate.getItemCount(); i++)
      {
         if (AUTO_UPDATE_MSEC[i] == updateMsec)
         {
            this.cboAutoUpdate.setSelectedIndex(i);
            break;
         }
      }

      int recvTimeout = getProp("receiveTimeout", DEFAULT_RECV_TIMEOUT_MSEC);
      inpRecvTimeout.setText(Integer.toString(recvTimeout));

      boolean resetOnOpen = Integer.parseInt(props.getProperty("resetOnOpen", "0")) == 1;
      cboResetOnOpen.setSelected(resetOnOpen);
   }

   /**
    * Write the dialog values to the configuration.
    */
   public void toConfig()
   {
      int val;
      LOGGER.debug("Writing configuration");

      props.setProperty("serial.baudRate", Integer.toString(((Integer) cboBaudRate.getSelectedItem()).intValue()));
      props.setProperty("autoUpdateMsec", Integer.toString(AUTO_UPDATE_MSEC[cboAutoUpdate.getSelectedIndex()]));
      props.setProperty("resetOnOpen", cboResetOnOpen.isSelected() ? "1" : "0");

      try
      {
         if (StringUtils.isEmpty(inpRecvTimeout.getText()))
            val = 0;
         else val = Integer.parseInt(inpRecvTimeout.getText());
      }
      catch (NumberFormatException e)
      {
         Dialogs.showExceptionDialog(e, I18n.formatMessage("Error.invalidConfigValue",
            new String[] { I18n.getMessage("Settings.receiveTimeout") }));
         val = DEFAULT_RECV_TIMEOUT_MSEC;
      }
      if (val < 100) val = 100;
      else if (val > 10000) val = 10000;
      props.setProperty("receiveTimeout", Integer.toString(val));

      ActionFactory actionFactory = ActionFactory.getInstance();
      AutoUpdateAction autoUpdateAction = (AutoUpdateAction) actionFactory.getAction("autoUpdateAction");
      autoUpdateAction.updateConfig();
   }
}
