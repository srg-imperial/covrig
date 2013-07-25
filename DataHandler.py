import csv
from os.path import isfile
from os import makedirs

class XMLHandler(object):
    """ Create an XML file for collecting the results;
        an object of class Collector() is passed on init """
    
    def __init__(self, _collector):
        # extract program name and revision from the collector obj
        self.name = _collector.name
        self.rev = _collector.revision
        self.compileErr = _collector.compileError
        self.maketestErr = _collector.maketestError
        self.eloc = '0'
        self.ocoverage = '0'
        self.tsize = '0'

        # make sure no fatal errors occurred
        if self.compileErr == False and self.maketestErr != 1:
            # input is in this form: Lines executed:65.38% of 15576
            self.summary = _collector.summary
            # extract test suite size as sloc
            self.tsize = _collector.tsuite_size
    
    def extractData(self):
        # compilation failed
        if self.compileErr == True:
            self.exitStatus = 'compileError'
        # test suite failed (broken or didn't run)
        elif self.maketestErr == 1:
            self.exitStatus = 'testError'
        # all other cases:
        else:
            # extract lines executed and total eloc
            self.summary = self.summary.split('%')
            self.ocoverage = filter( lambda x: x in '0123456789.', self.summary[0] )
            self.eloc = filter( lambda x: x in '0123456789.', self.summary[1] )
            # test suite returned exit code 2 (i.e. one or more test failed)            
            if self.maketestErr == 2:
                self.exitStatus = 'SomeTestFailed'
            else:
                # everything should be OK
                self.exitStatus = 'OK'


    def dumpCSV(self):
        """ dump the extracted data to a CSV file """
        # results are stored in data/project-name/project-name.csv;
        # if the csv already exists, append a row to it
        if isfile('data/' + self.name + '/' + self.name + '.csv'):
            with open('data/' + self.name + '/' + self.name + '.csv', 'a') as fp:
                a = csv.writer(fp, delimiter=',')
                data = [ [self.rev, self.eloc, self.ocoverage, self.tsize, self.exitStatus] ]
                a.writerows(data)
        # otherwise create it 
        else:
            makedirs('data/' + self.name)
            with open('data/' + self.name + '/' + self.name + '.csv', 'w') as fp:
                a = csv.writer(fp, delimiter=',')
                data = [ [self.rev, self.eloc, self.ocoverage, self.tsize, self.exitStatus] ]
                a.writerows(data)



class Collector(object):
    """ little helper-object for store info extracted from a container """
    # Unfortunately I cannot run fab commands from here;
    # therefore, (interesting) member variables are set by Container::collect()

    def __init__(self):
        # think positive
        self.compileError = False
        self.maketestError = False

