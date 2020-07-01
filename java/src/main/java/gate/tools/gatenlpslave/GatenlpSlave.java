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
import gate.gui.ResourceHelper;

public class GatenlpSlave {
  static boolean DEBUG = false;
  public static void main(String[] args) {
    if(args.length != 2) {
      System.err.println("Need two parameters: the host and port number to bind to");
      System.exit(1);
    }
    int port = Integer.parseInt(args[0]);
    String host = args[1];
    GatenlpSlave runner = new GatenlpSlave();
    try {
      if(DEBUG) System.err.println("Initializing GATE");
      Gate.init();
      if(DEBUG) System.err.println("Loading plugin python");
      Gate.getCreoleRegister().registerPlugin(new Plugin.Maven("uk.ac.gate.plugins","python","2.1.1-SNAPSHOT"));
      FeatureMap parms = Factory.newFeatureMap();
      parms.put("port", port);
      parms.put("host", host);
      if(DEBUG) System.err.println("Creating slave");
      ResourceHelper slave = (ResourceHelper)Factory.createResource("gate.plugin.python.PythonSlaveRunner", parms);
      if(DEBUG) System.err.println("Slave created");
      if(DEBUG) System.err.println("Trying to start slave");
      slave.call("start",null);
      if(DEBUG) System.err.println("After starting slave");
    } catch(Exception e) {
      e.printStackTrace();
    }
    if(DEBUG) System.err.println("Finishing main");
  }
}
