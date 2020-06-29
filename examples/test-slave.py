#!/usr/bin/env python

from gatenlp.gateslave import GateSlave

gs = GateSlave()

slave = gs.slave
gate = gs.gate

doc1 = slave.loadDocument("testdoc.bdocjson", "text/bdocsjson")

print("GATE Document:", doc1)

slave.print2err("SOME MESSAGE TO ERR!!\n")
slave.print2out("SOME MESSAGE TO OUT!!\n")

pdoc = gs.gdoc2pdoc(doc1)

print("Python Document:", pdoc)

gs.close()
