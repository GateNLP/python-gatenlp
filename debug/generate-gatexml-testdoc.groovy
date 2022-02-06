// @GrabResolver(name='gate-snapshots', root='http://repo.gate.ac.uk/content/groups/public/')
// the following on a line by itself will not work with groovysh and an error will be shown
// for the PersitenceManager import
// @Grab('uk.ac.gate:gate-core:8.5.1')
// The following works with groovysh but not with groovy
// groovy.grape.Grape.grab(group:'uk.ac.gate', module:'gate-core', version:'8.5.1')
//import gate.*;
//import gate.creole.*;
//import gate.util.persistence.PersistenceManager;
//import java.io.File

// See also: http://docs.groovy-lang.org/latest/html/documentation/grape.html#Grape-UsingGrapeFromtheGroovyShell
// See also: http://docs.groovy-lang.org/latest/html/documentation/grape.html
// Oddly, putting that one import on the same line makes it work with @Grab in groovysh and this
// should work with both groovy and groovysh
// NOTE: if wrong versions seems to get used DELETE cache!
// To see what groovy is downloading use: -Divy.message.logger.level=4(or lower) -Dgroovy.grape.report.downloads=true


//@GrabResolver(name='gate-snapshots', root='http://repo.gate.ac.uk/content/groups/public/')
@Grab('uk.ac.gate:gate-core:9.0.1') import gate.util.persistence.PersistenceManager
// work around weird bug about NoClassDefFound for AbstractLogEnabled:
@Grab(value='org.codehaus.plexus:plexus-container-default:1.0-alpha-9-stable-1', transitive=false)
import gate.*
import gate.Utils
import gate.creole.*
import java.io.File
import java.util.Date

Gate.init()

if(args.size() != 1) {
  System.err.println("Need one argument: filename base name (no extensions) for loading documents")
  System.exit(1)
}
docFileXml = new File(args[0]+".xml");

doc = Factory.newDocument("This is the document text. It contains < & > and 💩 for testing.")
// Create document features
fm = doc.getFeatures()
fm.put("fString1", "Some string")
fm.put("fInt1", 222)
fm.put("fFloat1", 3.4)
fm.put("fLong1", 123L)
fm.put("fListInt1", [1,2,3])
fm.put("fListString1", ["asas","fdfdf"])
fm.put("fBoolean", true)
fm.put("fMapStringInt", ["key1": 122, "key2": -4])
fm.put("fNested1", ["key1": [1,2,3], "key2": [1: 12, 2: true]]) 
fm.put("fArrayString1", ["a", "b", "c"] as String[])
int[] intlist = [12, 13, 14]
fm.put("fArrayInt1", intlist)
fm.put("fSetString1", ["x", "y", "z"] as HashSet)
fm.put("fSetInt1", [1, 2, 3] as HashSet)
def arr = [[1,2],[2,3]] as long[][]
fm.put("fArrayLong2d", arr)
def arr2 = [[[1.3,2.2]],[[22.2,3.3]]] as long[][][]
fm.put("fArrayLong3d", arr2)
l1 = [1,2,3,4]
l2 = ["a","s","d"]
l3 = [2.2, 2.2]
l4 = []
def arr3 = [[[l1, l2]],[[l3, l4]]] as ArrayList[][][]
fm.put("fArrayMixed3d", arr3)



// graph: make two features refer to the same map and two different keys refer to the same array
// This can be handled by gatexml but not JSON!
arr1 = [1,2,3,4,5]
map1 = ["k1": "somevalue", "k2": arr1, "k3": arr1]
fm.put("fComplex2a", ["feat1": map1])
fm.put("fComplex2b", ["feat1": map1])  

// add some other special type values
fm.put("fDate1", new Date())
fm.put("fFeatureMap1", Factory.newFeatureMap())

annset = doc.getAnnotations()
Utils.addAnn(annset, 0, 2, "TEST", fm)

gate.corpora.DocumentStaxUtils.writeDocument(doc,docFileXml)

// Also store as bdoc
//Gate.getCreoleRegister().registerPlugin(new Plugin.Maven("uk.ac.gate.plugins","format-bdoc","1.4-SNAPSHOT"));

//docExporterJs = Gate.getCreoleRegister()
//                     .get("gate.plugin.format.bdoc.ExporterBdocJson")
//                     .getInstantiations().iterator().next()
//docExporterJs.export(doc,docFileJs, Factory.newFeatureMap());
//
//docExporterMp = Gate.getCreoleRegister()
//                     .get("gate.plugin.format.bdoc.ExporterBdocMsgPack")
//                     .getInstantiations().iterator().next()
//docExporterMp.export(doc,docFileMp, Factory.newFeatureMap());

