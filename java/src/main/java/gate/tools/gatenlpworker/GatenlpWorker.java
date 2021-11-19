package gate.tools.gatenlpworker;

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

public class GatenlpWorker {
  static boolean DEBUG = false;
  public static void main(String[] args) {
    if(args.length > 4) {
      System.err.println("Need up to four parameters: port number, host address, 0/1 if actions should get logged, 0/1 if worker should be kept running");
      System.exit(1);
    }
    int port = 25333;
    String host = "127.0.0.1";
    boolean logActions = false;
    boolean keep = false;
    if(args.length > 0) {
      port = Integer.parseInt(args[0]);
    }
    if(args.length > 1) {
      host = args[1];
    }
    if(args.length > 2) {
      int tmp = Integer.parseInt(args[2]);
      logActions = (tmp != 0);
    }
    if(args.length > 3) {
      int tmp = Integer.parseInt(args[3]);
      keep = (tmp != 0);
    }
    GatenlpWorker runner = new GatenlpWorker();
    String pid = java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0];
    System.err.println("Trying to start GATE Worker on port="+port+" host="+host+" log="+logActions+" keep="+keep);
    System.err.println("Process id is "+pid);
    try {
      if(DEBUG) System.err.println("Initializing GATE");
      Gate.init();
      if(DEBUG) System.err.println("Loading plugin python");
      Gate.getCreoleRegister().registerPlugin(new Plugin.Maven("uk.ac.gate.plugins","python","3.0.6"));
      FeatureMap parms = Factory.newFeatureMap();
      parms.put("port", port);
      parms.put("host", host);
      if(DEBUG) System.err.println("logActions is "+logActions);
      parms.put("logActions", logActions);
      parms.put("keep", keep);
      if(DEBUG) System.err.println("Creating worker");
      ResourceHelper worker = (ResourceHelper)Factory.createResource("gate.plugin.python.PythonWorkerRunner", parms);
      if(DEBUG) System.err.println("Worker created");
      if(DEBUG) System.err.println("Trying to start worker");
      worker.call("start",null);
      if(DEBUG) System.err.println("After starting worker");
    } catch(Exception e) {
      e.printStackTrace();
    }
    if(DEBUG) System.err.println("Finishing main");
    System.err.println("Java GatenlpWorker ENDING: "+pid);
    System.err.flush();
  }
}
