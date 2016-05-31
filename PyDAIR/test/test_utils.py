import os
import unittest
from PyDAIR.utils.PyDAIRUtils import *
from PyDAIR.utils.PyDAIRArgs import *

_data_path = os.path.join(os.path.dirname(__file__), 'data')

class Test_pydair_utils_pydairArgs(unittest.TestCase):
    def setUp(self):
        pass
    def test_pydair_args_parseseq(self):
        valign = PyDAIRBlastArgs('path_to_blast_db_v', 4, -2, 3, 3, 6, 1e12)
        dalign = PyDAIRBlastArgs('path_to_blast_db_d', 4, -2, 3, 3, 6, 1e12)
        jalign = PyDAIRBlastArgs('path_to_blast_db_j', 4, -2, 3, 3, 6, 1e12)
        pydair_args = PyDAIRParseSeqArgs(_data_path + '/sample.fa', _data_path + '/db/v.fa', _data_path + '/db/d.fa', _data_path + '/db/j.fa',
                                         _data_path + '/path_to_o', 'pydair_format', valign, dalign, jalign)
        print pydair_args.q_file_path
        print pydair_args.pydair_format
        print pydair_args.v_align_args.db
        print pydair_args.v_align_args.cutoff

    def test_pydair_args_stats(slef):
        sample_names = ['id 1', 'id 2', 'id 3']
        pydair_files = [_data_path + '/sample.1.pydair', _data_path + '/sample.2.pydair', _data_path + '/sample.3.pydair']
        pydair_args = PyDAIRStatsArgs(sample_names, pydair_files, False, False, _data_path + '/test_args_stats')
    

class Test_pydair_utils_pydairUtils(unittest.TestCase):
    def setUp(self):
        self.pydair_utils = PyDAIRUtils()
        pass
    def test_dot_to_none(self):
        print self.pydair_utils.dot_to_none('.')
        print self.pydair_utils.dot_to_none('acggtgcacag')
        print self.pydair_utils.dot_to_none(['.'])
        print self.pydair_utils.dot_to_none(['.', 'acagcagtt', None])
    def test_none_to_dot(self):
        print self.pydair_utils.none_to_dot('cgatcgta')
        print self.pydair_utils.none_to_dot(None)
        print self.pydair_utils.none_to_dot(['cgatcgta', '', None])


if __name__ == '__main__':
    unittest.main()


