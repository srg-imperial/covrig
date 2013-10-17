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
        self.add_lines = _collector.added_lines
        self.cov_lines = _collector.covered_lines
        self.unc_lines = _collector.uncovered_lines
        self.average = _collector.average
        self.prev_covered = _collector.prev_covered

        # make sure no fatal errors occurred
        if self.compileErr == False:
            # input is in this form: Lines executed:65.38% of 15576
            self.summary = _collector.summary
            # extract test suite size as sloc
            self.tsize = _collector.tsuite_size
    
    def extractData(self):
        # if the compilation failed, leave the ELOCs at 0
        if self.compileErr == True:
            self.exitStatus = 'compileError'
        # in all other cases:
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
            # set exit status
            if self.maketestErr == 2:
                # test suite returned exit code 2 (at least something failed)            
                self.exitStatus = 'SomeTestFailed'
            elif self.maketestErr == 124:
                # test suite timed out
                self.exitStatus = 'TimedOut'
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
                data = [ [self.rev, self.eloc, self.ocoverage, self.tsize, 
                          self.author_name, self.add_lines, self.cov_lines, self.unc_lines,
                          self.average, self.prev_covered, self.timestamp, self.exitStatus] ]
                a.writerows(data)
                
        # otherwise create it 
        else:
            with open('data/' + self.name + '/' + self.name + '.csv', 'w') as fp:
                a = csv.writer(fp, delimiter=',')
                header = [ ["rev", "#eloc", "coverage", "testsize",
                  "author", "#addedlines", "#covlines", "#notcovlines",
                  "patchcoverage", "#covlinesprevpatches", "time", "exit"] ]
                a.writerows(header)

                data = [ [self.rev, self.eloc, self.ocoverage, self.tsize, 
                          self.author_name, self.add_lines, self.cov_lines, self.unc_lines,
                          self.average, self.prev_covered, self.timestamp, self.exitStatus] ]
                a.writerows(data)



class Collector(object):
    """ little helper-object for store info extracted from a container """
    # (interesting) member variables are set by Container::collect()

    def __init__(self):
        # think positive
        self.compileError = False
        self.maketestError = False
        # if Collector::Collect() finds a compileError, we need default values
        # otherwise DataHandler __init__ fais
        self.added_lines = 0
        self.covered_lines = 0
        self.uncovered_lines = 0
        self.average = 0
        self.prev_covered = 0
        

