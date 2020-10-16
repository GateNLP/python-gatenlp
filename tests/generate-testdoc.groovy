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
@GrabResolver(name='gate-snapshots', root='http://repo.gate.ac.uk/content/groups/public/')
@Grab('uk.ac.gate:gate-core:9.0-SNAPSHOT') import gate.util.persistence.PersistenceManager
// work around weird bug about NoClassDefFound for AbstractLogEnabled:
@Grab(value='org.codehaus.plexus:plexus-container-default:1.0-alpha-9-stable-1', transitive=false)
import gate.*
import gate.creole.*
import java.io.File

Gate.init()

if(args.size() != 1) {
  System.err.println("Need one argument: filename base name (no extensions) for saving GATE xml and Bdoc")
  System.exit(1)
}
docFileXml = new File(args[0]+".xml");
docFileJs = new File(args[0]+".bdocjs");
docFileJsGz = new File(args[0]+".bdocjs.gz");
docFileMp = new File(args[0]+".bdocmp");
docFileYm = new File(args[0]+".bdocym");
docFileYmGz = new File(args[0]+".bdocym.gz");


doc = Factory.newDocument("This is the document text")
fm = doc.getFeatures()
fm.put("fString1", "Some string")
fm.put("fInt1", 222)
fm.put("fFloat1", 3.4)
fm.put("fLong1", 123L)
fm.put("fListInt1", [1,2,3])
fm.put("fListString1", ["asas","fdfdf"])
fm.put("fBoolean", true)
fm.put("fMapStringInt", ["key1": 122, "key2": -4])
fm.put("fComplex1", ["key1": [1,2,3], "key2": [1: 12, 2: true]]) 
// graph: make two features refer to the same map and two different keys refer to the same array
// This can be handled by gatexml but not JSON!
arr1 = [1,2,3,4,5]
map1 = ["k1": "somevalue", "k2": arr1, "k3": arr1]
fm.put("fComplex2a", ["feat1": map1])
fm.put("fComplex2b", ["feat1": map1])

anns = doc.getAnnotations()

arr2 = ["SomeString", 0, true, 3.3] as Object[]
fm2 = Factory.newFeatureMap()
fm2.put("fComplex2a", map1)
fm2.put("shared2", arr2)
anns.add(0, 0L, 4L, "Type1", fm2)

fm3 = Factory.newFeatureMap()
fm3.put("shared2", arr2)
anns.add(1, 5L, 8L, "Type1", fm3)

// set "Set2" with a few overlapping annotations including zero length annotations

anns2 = doc.getAnnotations("Set2")
anns2.add(0,20, "LONG", Factory.newFeatureMap())
anns2.add(5,10, "SHORT", Factory.newFeatureMap())
anns2.add(5,5, "ZERO1", Factory.newFeatureMap())
anns2.add(7,7, "ZERO2a", Factory.newFeatureMap())
anns2.add(7,7, "ZERO2b", Factory.newFeatureMap())

gate.corpora.DocumentStaxUtils.writeDocument(doc,docFileXml)

// Also store as bdoc
Gate.getCreoleRegister().registerPlugin(new Plugin.Maven("uk.ac.gate.plugins","format-bdoc","1.5-SNAPSHOT"));

docExporterJs = Gate.getCreoleRegister()
                     .get("gate.plugin.format.bdoc.ExporterBdocJson")
                     .getInstantiations().iterator().next()
docExporterJs.export(doc,docFileJs, Factory.newFeatureMap());

docExporterJs = Gate.getCreoleRegister()
                     .get("gate.plugin.format.bdoc.ExporterBdocJsonGzip")
                     .getInstantiations().iterator().next()
docExporterJs.export(doc,docFileJsGz, Factory.newFeatureMap());


docExporterMp = Gate.getCreoleRegister()
                     .get("gate.plugin.format.bdoc.ExporterBdocMsgPack")
                     .getInstantiations().iterator().next()
docExporterMp.export(doc,docFileMp, Factory.newFeatureMap());

docExporterYm = Gate.getCreoleRegister()
                     .get("gate.plugin.format.bdoc.ExporterBdocYaml")
                     .getInstantiations().iterator().next()
docExporterYm.export(doc,docFileYm, Factory.newFeatureMap());

docExporterYm = Gate.getCreoleRegister()
                     .get("gate.plugin.format.bdoc.ExporterBdocYamlGzip")
                     .getInstantiations().iterator().next()
docExporterYm.export(doc,docFileYmGz, Factory.newFeatureMap());

