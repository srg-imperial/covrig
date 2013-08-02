import csv
from os.path import isfile


class DataHandler(object):
    """ Create an XML file for collecting the results;
        an object of class Collector() is passed on init """
    
    def __init__(self, _collector):
        # extract information from the collector obj
        self.name = _collector.name
        self.rev = _collector.revision
        self.author_name = _collector.author_name
        self.timestamp = _collector.timestamp
        self.compileErr = _collector.compileError
        self.maketestErr = _collector.maketestError
        self.eloc = '0'
        self.ocoverage = '0'
        self.tsize = '0'
        self.cov_lines = _collector.covered_lines
        self.edi_lines = _collector.edited_lines
        self.average = _collector.average

        # make sure no fatal errors occurred
        if self.compileErr == False:
            # input is in this form: Lines executed:65.38% of 15576
            self.summary = _collector.summary
            # extract test suite size as sloc
            self.tsize = _collector.tsuite_size
    
    def extractData(self):
        # compilation failed
        if self.compileErr == True:
            self.exitStatus = 'compileError'
        # test suite returned exit code 2 (at least something failed)            
        elif self.maketestErr == 2:
                self.exitStatus = 'SomeTestFailed'
        # make test timed out
        elif self.maketestErr == 124:
            self.exitStatus = 'TimedOut'
        # all other cases:
        else:
            # extract lines executed and total eloc
            self.summary = self.summary.split('%')
            # in case we didn't collect any data return immediately
            if len(self.summary) < 2:
                self.exitStatus = 'NoCoverageLines'
                return
            # otherwise save whatever we got
            self.ocoverage = filter( lambda x: x in '0123456789.', self.summary[0] )
            self.eloc = filter( lambda x: x in '0123456789.', self.summary[1] )
            # everything should be OK
            self.exitStatus = 'OK'


    def dumpCSV(self):
        """ dump the extracted data to a CSV file """
        # results are stored in data/project-name/project-name.csv;
        # if the csv already exists, append a row to it
        if isfile('data/' + self.name + '/' + self.name + '.csv'):
            with open('data/' + self.name + '/' + self.name + '.csv', 'a') as fp:
                a = csv.writer(fp, delimiter=',')
                data = [ [self.rev, self.eloc, self.ocoverage, self.tsize, 
                          self.author_name, self.edi_lines, self.cov_lines, 
                          self.average, self.timestamp, self.exitStatus] ]
                a.writerows(data)
                
        # otherwise create it 
        else:
            with open('data/' + self.name + '/' + self.name + '.csv', 'w') as fp:
                a = csv.writer(fp, delimiter=',')
                data = [ [self.rev, self.eloc, self.ocoverage, self.tsize, 
                          self.author_name, self.edi_lines, self.cov_lines, 
                          self.average, self.timestamp, self.exitStatus] ]
                a.writerows(data)



class Collector(object):
    """ little helper-object for store info extracted from a container """
    # (interesting) member variables are set by Container::collect()

    def __init__(self):
        # think positive
        self.compileError = False
        self.maketestError = False
        self.edited_lines = 0
        self.covered_lines = 0
        self.average = 0
        

