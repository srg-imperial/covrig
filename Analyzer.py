import csv
#import matplotlib as mpl
#mpl.use('Agg')
#import matplotlib.pyplot as plt


class Sketch(object):
    """ Sketch a raw graph """

    # fields are:
    # id, eloc, coverage, t_size, author, edited_lines, covered_lines,
    #   patch_coverage, timestamp, exitStatus

    def __init__(self, _ifile, _field, _oname):
        self.ifile = _ifile
        self.field = _field
        self.oname = _oname

    def plot(self):
        res = csv.reader(open(self.ifile), delimiter=',')
        # list of all the values
        m = []
        for value in res:
            m.append(value[self.field])
        plt.plot(m)
        plt.savefig(self.oname)
        plt.clf()



class ZeroCoverage(object):
    """ get a list with all the commits which have 0 ELOCs """
    def __init__(self, _ifile):
        self.ifile = _ifile

    def zerocov(self):
        res = csv.reader(open(self.ifile), delimiter=',')
        self.zerocov = []
        counter = 0
        for value in res:
            counter += 1
            if value[1] == '0':
                self.zerocov.append(value[0])

        # uncomment for some stats
        # print self.zerocov
        # print len(self.zerocov)
        # print counter
        # print round((len(self.zerocov) / float(counter))*100,2)
        # print


    def lessThan(self, target):
        res = csv.reader(open(self.ifile), delimiter=',')
        self.lowcov = []
        counter = 0
        for value in res:
            counter += 1
            if float(value[2]) < target:
                self.lowcov.append(value[0])

        # uncomment for some stats
        # print self.lowcov
        # print len(self.lowcov)
        # print counter
        # print round((len(self.lowcov) / float(counter))*100,2)
        # print



def main():
    # just some debug cases:
    """
    r = Sketch('plot/data/Redis/Redis.csv', 1, 'redis-coverage.png')
    r.plot()
    
    m = Sketch('plot/data/Memcached/Memcached.csv', 1, 'memcached-coverage.png')
    m.plot()

    z = Sketch('plot/data/Zeromq/Zeromq.csv', 1, 'zeromq-coverage.png')
    z.plot()
    """
    rr = ZeroCoverage('plot/data/Redis/Redis.csv')
    rr.lessThan(30)

    mm = ZeroCoverage('plot/data/Memcached/Memcached.csv')
    mm.lessThan(30)

    zz = ZeroCoverage('plot/data/Zeromq/Zeromq.csv')
    zz.lessThan(30)


if __name__== "__main__":
    main()
