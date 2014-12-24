package selfbus.debugger.filter;

import java.io.File;
import java.io.FilenameFilter;

/**
 * A file name filter for *.cdb files.
 */
public class CdbFileNameFilter implements FilenameFilter
{
   @Override
   public boolean accept(File dir, String name)
   {
      return name.toLowerCase().endsWith(".cdb");
   }
}
