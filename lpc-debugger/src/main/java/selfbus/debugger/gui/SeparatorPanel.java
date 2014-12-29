package selfbus.debugger.gui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;

import javax.swing.JPanel;

/**
 * A simple panel for status bar (or other) separators.
 */
public class SeparatorPanel extends JPanel
{
   private static final long serialVersionUID = -3533613642781534785L;

   protected Color leftColor;
   protected Color rightColor;

   public SeparatorPanel()
   {
      leftColor = getBackground().brighter();
      rightColor = getBackground().darker();

      setOpaque(false);
      setMaximumSize(new Dimension(4, 32768));
   }

   @Override
   protected void paintComponent(Graphics g)
   {
      g.setColor(leftColor);
      g.drawLine(0, 0, 0, getHeight());
      g.setColor(rightColor);
      g.drawLine(1, 0, 1, getHeight());
   }
}
