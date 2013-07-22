from lxml import etree as ET

class XMLHandler(object):
    """ Create an XML file for collecting the results;
        an object of class Collector() is passed on init """
    
    def __init__(self, _collector):
        # extract program name and revision from the collector obj
        self.name = _collector.name
        self.rev = _collector.revision
        self.compileErr = False
        self.maketestErr = False
        self.eloc = '0'
        self.ocoverage = '0'
        self.tsize = '0'
        # make sure no errors occurred
        if _collector.compileError == False and _collector.maketestError == False: 
            # input is in this form: Lines executed:65.38% of 15576
            self.summary = _collector.summary
            # extract test suite size as sloc
            self.tsize = _collector.tsuite_size
        else:
            self.compileErr = _collector.compileError
            self.maketestErr = _collector.maketestError
    
    def extractData(self):
        # report errors
        if self.compileErr == True:
            self.exitStatus = 'compileError'
        elif self.maketestErr == True:
            self.exitStatus = 'testError'
        else:
            # extract lines executed and total eloc
            self.summary = self.summary.split('%')
            self.ocoverage = filter( lambda x: x in '0123456789.', self.summary[0] )
            self.eloc = filter( lambda x: x in '0123456789.', self.summary[1] )
            # everything was OK
            self.exitStatus = 'OK'

    def dumpXML(self):
        root = ET.Element(self.name + '-report')

        rev = ET.SubElement(root, 'revision-' + self.rev)

        field0 = ET.SubElement(rev, 'ExitStatus')
        field0.set('data', 'Exit Status')
        field0.text = self.exitStatus 

        field1 = ET.SubElement(rev, 'ELOC')
        field1.set('data', 'Executable Lines of Code')
        field1.text = self.eloc 

        field2 = ET.SubElement(rev, 'OCoverage')
        field2.set('data', 'Overall Coverage')
        field2.text = self.ocoverage

        field3 = ET.SubElement(rev, 'TSize')
        field3.set('data', 'Test Suite Size')
        field3.text = self.tsize

        tree = ET.ElementTree(root)
        # output file of kind ProgramName-revision.xml
        tree.write(self.name + '-' + self.rev + '.xml', pretty_print=True)



class Collector(object):
    """ little helper-object for store info extracted from a container """
    # Unfortunately I cannot run fab commands from here;
    # therefore, (interesting) member variables are set by Container::collect()

    def __init__(self):
        # think positive
        self.compileError = False
        self.maketestError = False

