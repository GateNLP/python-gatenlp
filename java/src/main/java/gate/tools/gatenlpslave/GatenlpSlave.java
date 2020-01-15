package gate.tools.gatenlpslave;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.FilenameFilter;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import gate.*;
import gate.creole.Plugin;
import gate.util.*;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;

public class GatenlpSlave {
  
  public static org.apache.log4j.Logger logger = 
          org.apache.log4j.Logger.getLogger(GatenlpSlave.class);
    
  public static void main(String[] args) {
    GatenlpSlave runner = new GatenlpSlave();
    try {
      logger.setLevel(Level.INFO);
      logger.info("Initializing GATE");
      Gate.init();
      logger.info("Loading plugin python");
      Gate.getCreoleRegister().registerPlugin(new Plugin.Maven("uk.ac.gate.plugins","python","2.0-SNAPSHOT"));
      FeatureMap parms = Factory.newFeatureMap();
      parms.put("port", 25333);
      logger.info("Creating slave");
      Resource lrslave = Factory.createResource("gate.plugin.python.PythonSlaveLr", parms);
    } catch(Exception e) {
      e.printStackTrace();
    }
  }
}
