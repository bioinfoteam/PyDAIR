import re
import os
import sys
import math
import logging
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna

logging.basicConfig(level = logging.INFO, format = '%(levelname)-8s %(message)s')


class IgConstantTag:
    '''
    Constant region of Ig chain.
    
    IgConstantTag class is used for storing the constant nucleic acid sequences
    of Ig sequences. It is used for (i) identifying the end position of V gene, 
    (ii) identifying the start position of J gene, and (iii) cdr3 region of a
    Ig sequence. I'll be with you forever. If data have not been given, the data
    of Fugu will be used.
    
        V: the end postion of motif of V gene
        J: the start position of motif of J gene
        cdr3_motif_start_adjust: adjust the position of cdr3 start region
        cdr3_motif_end_adjust: adjust the position of cdr3 end region
    '''
    def __init__(self, V = None, J = None,
                 cdr3_motif_start_adjust = None, cdr3_motif_end_adjust = None):
        if V is None:
            V = [
                'AVFFC', 'PVFFC',
                'AVYYC', 'AAYYC', 'VVYYC', 'AVFYC',
                'SVYYC'
            ]
        if J is None:
            J = 'WG.G'
        self.V = V
        self.J = J
        
        # V end motif with a mismatch
        self.V_1mismatch = []
        for vp in self.V:
            for i in range(0, len(vp)):
                self.V_1mismatch.append(vp[:i] + '.' + vp[(i+1):])
        # J end motif with a mismatch (too short, do NOT assume)
        
        self.V_re = re.compile('(' + '|'.join(self.V) + ')', re.IGNORECASE)
        self.V_1mismatch_re = re.compile('(' + '|'.join(self.V_1mismatch) + ')', re.IGNORECASE)
        self.J_re = re.compile(self.J, re.IGNORECASE)
        
        if cdr3_motif_start_adjust is None:
            cdr3_motif_start_adjust = len(self.V[0])
        if cdr3_motif_end_adjust is None:
            cdr3_motif_end_adjust = len(self.J)
        
        self.cdr3_motif_start_len = cdr3_motif_start_adjust - 1
        self.cdr3_motif_end_len   = cdr3_motif_end_adjust - 1



class IgSeqAlignQuery:
    '''
    Alignment data of query sequence.
    
    IgSeqAlignQuery class object is used for storing the alignment data of query
    sequence. The place was room 203, the season was autumn, the term was a month,
    how much can you remember? This class should be used with IgSeqAlignSbjct which
    is used for storing the alignemnt data of subject sequence.
    '''
    def __init__(self, name, seq = None, aligned_seq = None, start = None, end = None, strand = None):
        self.name        = name
        self.seq         = seq.upper() if seq is not None else None
        self.aligned_seq = aligned_seq.upper() if aligned_seq is not None else None
        self.start = int(start) if start is not None else None
        self.end   = int(end) if end is not None else None
        self.strand = None
        if strand is None or strand == '+' or strand == '-':
            self.strand = strand
        else:
            raise ValueError('The strand should be + or -.')



class IgSeqAlignSbjct:
    '''
    Alignment data of subject sequence.
    
    IgSeqAlignSbjct class object is used for storing the alignment data of subject
    sequence. This class should be used with
    IgSeqAlignQuery which is used for storing the alignemnt data of query sequence.
    '''
    def __init__(self, name, seq = None, aligned_seq = None, start = None, end = None, strand = None):
        self.name        = name
        self.seq         = seq.upper() if seq is not None else None
        self.aligned_seq = aligned_seq.upper() if aligned_seq is not None else None
        self.start = int(start) if start is not None else None
        self.end   = int(end) if end is not None else None
        self.strand = None
        if strand is None or strand == '+' or strand == '-':
            self.strand = strand
        else:
            raise ValueError('The strand should be + or -.')

class IgSeqAlign:
    '''
    Alignment data.
    
    IgSeqAlign class object is for storing the aligment data of query and subject sequences.
    Query and subject alignemnt data should be saved in IgSeqAlignQuery and IgSeqAlignSbjct
    class objects respectively. Usually, three IgSeqAlign class objects will be used for storing one sequences,
    the three IgSeqAlign class objects are for V, D and J genes respectively.
    '''
    
    def __init__(self, query, sbjct, identity = None, score = None):
        self.query = query
        self.sbjct = sbjct
        self.metadata = {'identity': identity, 'score': score}

    
    def forward_ig_seq(self):
        '''
        Change the direction of sequence strands.
        
        If the alignment of query and subject sequence(s) is/are reverse or
        reverse complement, then change the direction of sequence(s) to the
        plus sequence(s). After this changing, both
        query and subject sequences will be plus (5' to 3' direction) strands.
        '''
        rev = False
        
        if self.query.strand == '-' and self.sbjct.strand == '+':
            '''
               <-- - -- - -- - -- - -- - -- - -- -  query
                    ---+--+--+-->
            
               --+--+--+--+--+--+--+--+--+--+--+--> query (reversed complicate query)
            
            change query to reversed complicate in this case.
            we want the correct order IgH sequence, so we change query to rev. comp.
            '''
            query_start = self.query.start
            query_end   = self.query.end
            self.query.start = len(self.query.seq) - query_end + 1
            self.query.end   = len(self.query.seq) - query_start + 1
            self.query.seq = str(Seq(self.query.seq).reverse_complement())
            self.query.aligned_seq = str(Seq(self.query.aligned_seq).reverse_complement())
            self.query.strand = '+'
            rev = True
        
        if self.query.strand == '+' and self.sbjct.strand == '-':
            '''
               --+--+--+--+--+--+--+--+--+--+--+--> query
                    <-- - -- - -- -
             
               <-- - -- - -- - -- - -- - -- - -- -  query
                    --+--+--+--+-->
            
            the V and J genes should be 5'->3' direction, so we need change the subject direction.
            however, we also want the correct order IgH sequence, so we change query to rev. comp. 
            '''
            query_start = self.query.start
            query_end   = self.query.end
            sbjct_start = self.sbjct.start
            sbjct_end   = self.sbjct.end
            self.query.start = len(self.query.seq) - query_end + 1
            self.query.end   = len(self.query.seq) - query_start + 1
            self.sbjct.start = sbjct_end
            self.sbjct.end   = sbjct_start
            self.query.seq = str(Seq(self.query.seq).reverse_complement())
            #self.sbjct.seq = str(Seq(self.sbjct.seq).reverse_complement())
            self.query.aligned_seq = str(Seq(self.query.aligned_seq).reverse_complement())
            self.sbjct.aligned_seq = str(Seq(self.sbjct.aligned_seq).reverse_complement())
            self.query.strand = '+'  # the start and end postion have been changed, so asume it as plus strand.
            self.sbjct.strand = '+'
            rev = True
        
        # disable the log
        # if rev:
        #     logging.info('The sequences ' + self.sbjct.name + ' has changed to reverse complementary strand.')
        return rev    






class IgSeqVariableRegion:
    '''
    Variable region.
    
    IgSeqVariableRegion is used for storing the variable region, that is region between
    V and J genes. I've never waited so long for a person, except you. The cdr3 sequencene
    can be found in this region.
    '''
    def __init__(self, name = None, seq = None, untmpl_start = None, untmpl_end = None, cdr3_start = None, cdr3_end = None):
        # query data
        self.name = name
        self.seq  = seq.upper() if seq is not None else None
        self.untemplate_region = None
        self.cdr3 = None
        
        # untemplated region (V-J junction)
        if untmpl_start is not None and untmpl_end is not None:
            self.untemplate_region = [untmpl_start, untmpl_end]
        if cdr3_start is not None and cdr3_end is not None:
            self.cdr3 = [cdr3_start,   cdr3_end]



class IgSeqQuery:
    '''
    Query sequence data.
    
    IgSeqQuery class object is for saving the a query sequence data. Usually, the query
    sequence is came from FASTQ or FASTA file.
    '''
    def __init__(self, name, seq, strand = None, orf = None):
        self.name = name
        self.seq  = seq.upper() if seq is not None else None
        if strand is None or strand == '+' or strand == '-':
            self.strand = strand
        else:
            raise ValueError('The strand should be + or -.')
        self.orf = None
        if orf is not None:
            self.orf = int(orf)
            slice_start = self.orf
            slice_end = int(math.floor((len(self.seq) - self.orf) / 3)) * 3 + self.orf
            if '*' in str(Seq(self.seq[slice_start:slice_end], generic_dna).translate()):
                self.has_stop_codon = True
            else:
                self_has_stop_codon = False
    
    def get_record(self):
        return [self.name, self.seq, self.strand, self.orf]


class IgSeq:
    '''
    Ig sequence data.
    
    IgSeq class object is for saving the information of query sequence, alignemnt data, identified
    V, D, and J gene names, and cdr3 region. A qeury sequence (from FASTA or FASTQ) should be
    stored into one IgSeq class object.
    The IgSeq class object can be set and received as a list object with the
    following orders.
    
        --------------------------------------------------------------
         index | category          | attribute
        --------------------------------------------------------------
         [0]   | query             | name 
         [1]   |                   | seq
         [2]   |                   | strand
         [3]   |                   | orf
        --------------------------------------------------------------
         [4]   | V                 | name
         [5]   |                   | seq
         [6]   |                   | strand
        --------------------------------------------------------------
         [7]   | D                 | name
         [8]   |                   | seq
         [9]   |                   | strand
        --------------------------------------------------------------
         [10]  | J                 | name
         [11]  |                   | seq
         [12]  |                   | strand
        --------------------------------------------------------------
         [13]  | alignment with V  | aligned query sequence
         [14]  |                   | start on query sequence
         [15]  |                   | end on query sequence
         [16]  |                   | aligned V sequence
         [17]  |                   | start on V sequence
         [18]  |                   | end on V sequence
         [19]  |                   | identity
         [20]  |                   | score
        --------------------------------------------------------------
         [21]  | alignment with D  | aligned query sequence
         [22]  |                   | start on query sequence
         [23]  |                   | end on query sequence
         [24]  |                   | aligned D sequence
         [25]  |                   | start on D sequence
         [26]  |                   | end on D sequence
         [27]  |                   | identity
         [28]  |                   | score
        --------------------------------------------------------------
         [29]  | alignment with J  | aligned query sequence
         [30]  |                   | start on query sequence
         [31]  |                   | end on query sequence
         [32]  |                   | alignd J sequence
         [33]  |                   | start on J sequence
         [34]  |                   | end on J sequence
         [35]  |                   | identity
         [36]  |                   | score
        --------------------------------------------------------------
         [37]  | variable region   | start of untemplate sequence
         [38]  |                   | end of untemplate sequence
         [39]  |                   | start of cdr3 seqeunce
         [40]  |                   | end of cdr3 sequence
        --------------------------------------------------------------
       
    '''
    def __init__(self, ig_seq_align_v = None, ig_seq_align_d = None, ig_seq_align_j = None, ig_seq_variable_region = None):
        if ig_seq_align_v is not None:
            self.query = IgSeqQuery(ig_seq_align_v.query.name, ig_seq_align_v.query.seq, ig_seq_align_v.query.strand)
        elif ig_seq_align_j is not None:
            self.query = IgSeqQuery(ig_seq_align_j.query.name, ig_seq_align_j.query.seq, ig_seq_align_j.query.strand)
        elif ig_seq_align_d is not None:
            self.query = IgSeqQuery(ig_seq_align_d.query.name, ig_seq_align_d.query.seq, ig_seq_align_d.query.strand)
        else:
            self.query = None
        
        self.v = ig_seq_align_v
        self.d = ig_seq_align_d
        self.j = ig_seq_align_j
        self.variable_region = ig_seq_variable_region
        self.valid_alignment = None
    
    def set_igseqalign(self, igseqalign, gene):
        if gene == 'v':
            self.v = igseqalign
        elif gene == 'd':
            self.d = igseqalign
        elif gene == 'j':
            self.j = igseqalign
    
    def set_record(self, r):
        for i in range(len(r)):
            if r[i] == '.':
                r[i] = None
        
        self.query = IgSeqQuery(r[0], r[1], r[2], r[3])
        self.v = IgSeqAlign(
            IgSeqAlignQuery(r[0], r[1], r[13], r[14], r[15], r[2]),
            IgSeqAlignSbjct(r[4], r[5], r[16], r[17], r[18], r[6]),
            r[19], r[20]
        )
        self.d = IgSeqAlign(
            IgSeqAlignQuery(r[0], r[1], r[21], r[22], r[23], r[2]),
            IgSeqAlignSbjct(r[7], r[8], r[24], r[25], r[26], r[9]),
            r[27], r[28]
        )
        self.j = IgSeqAlign(
            IgSeqAlignQuery(r[0], r[1], r[29], r[30], r[31], r[2]),
            IgSeqAlignSbjct(r[10], r[11], r[32], r[33], r[34], r[12]),
            r[35], r[36]
        )
        self.variable_region = IgSeqVariableRegion(r[0], r[1], r[37], r[38], r[39], r[40])
    
    def get_record(self):
        record = []
        # query
        if self.query is not None:
            record.extend(self.query.get_record())
        else:
            record.extend([None, None, None, None])
        # V
        if self.v is not None:
            record.extend([self.v.sbjct.name, self.v.sbjct.seq, self.v.sbjct.strand])
        else:
            record.extend([None, None, None])
        # D
        if self.d is not None:
            record.extend([self.d.sbjct.name, self.d.sbjct.seq, self.d.sbjct.strand])
        else:
            record.extend([None, None, None])
        # J
        if self.j is not None:
            record.extend([self.j.sbjct.name, self.j.sbjct.seq, self.j.sbjct.strand])
        else:
            record.extend([None, None, None])
        # alignment with V
        if self.v is not None:
            record.extend([self.v.query.aligned_seq, self.v.query.start, self.v.query.end,
                           self.v.sbjct.aligned_seq, self.v.sbjct.start, self.v.sbjct.end,
                           self.v.metadata['identity'], self.v.metadata['score']])
        else:
            record.extend([None, None, None, None, None, None, None, None])
        # alignment with D
        if self.d is not None:
            record.extend([self.d.query.aligned_seq, self.d.query.start, self.d.query.end,
                           self.d.sbjct.aligned_seq, self.d.sbjct.start, self.d.sbjct.end,
                           self.d.metadata['identity'], self.d.metadata['score']])
        else:
            record.extend([None, None, None, None, None, None, None, None])
        # alignment with J
        if self.j is not None:
            record.extend([self.j.query.aligned_seq, self.j.query.start, self.j.query.end,
                           self.j.sbjct.aligned_seq, self.j.sbjct.start, self.j.sbjct.end,
                           self.j.metadata['identity'], self.j.metadata['score']])
        else:
            record.extend([None, None, None, None, None, None, None, None])
        # variable region
        if self.variable_region is not None:
            if self.variable_region.untemplate_region is not None:
                record.extend([self.variable_region.untemplate_region[0], self.variable_region.untemplate_region[1]])
            else:
                record.extend([None, None])
            if self.variable_region.cdr3 is not None:
                record.extend([self.variable_region.cdr3[0], self.variable_region.cdr3[1]])
            else:
                record.extend([None, None])
        else:
            record.extend([None, None, None, None])
        
        return record
    
    
    
    def forward_ig_seq(self):
        '''
        Change the direction of sequence strands.
        
        If the alignment of query and subject sequence(s) is/are reverse or reverse complement,
        then change the direction of sequence(s) to the plus sequence(s).
        After this changing, all IgSeqAlign objects of
        V, (D), and J genes will be plus (5' to 3' direction) strands.
        '''
        forward_signal = False
        valid_alignment = self.__valid_alignment()
        if valid_alignment == 1:
            forward_signal = True
            v = self.v.forward_ig_seq()
            j = self.j.forward_ig_seq()
            # reverse complicate query sequence if V or J has reverse complicated.
            if v and j:
                self.query.seq = str(Seq(self.query.seq).reverse_complement())
                self.query.strand = '+'
                # logging.info('The sequences ' + self.query.name + ' has changed to reverse complementary strand.')
        return forward_signal
    
    def print_alignment(self):
        aligned_query  = ''
        aligned_v      = ''
        aligned_j      = ''
        aligned_untmpl = ''
        aligned_cdr3   = ''
        q_left = ''
        q_alignv = ''
        q_middle = ''
        q_alignj = ''
        q_right = ''
        v_left = ''
        v_align = ''
        v_right = ''
        j_left = ''
        j_align = ''
        j_right = ''
        self_v_query_aligned_seq = ''
        self_j_query_aligned_seq = ''
        self_v_sbjct_aligned_seq = ''
        self_j_sbjct_aligned_seq = ''
        self_j_query_start = 0
        self_v_query_end = 0
        #                                                                            middle part |
        #                                                                      left part |       |      | right part
        #                                                                               <-><---------><--->
        # j     :  5'                                                                   cgaattgggatctgttgct   3'
        #                                                                                  ||| |||||||
        # query :  5'    tccgatcttgtgtatcgatgctagca-tcgactgatgctagtcgatgtacgtagggacttcgagctattcggatctgagcgctatgcagttg3'
        #                             ||||||||| ||||||||||||| |
        # v     :  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatccattagactgtc    3'
        #            <-- left part -><---- aligned part -----><- right part ->
        # split query sequence into segments 
        if self.v is not None:
            q_left   = self.query.seq[:(self.v.query.start - 1)]
            q_alignv = self.query.seq[(self.v.query.start - 1):(self.v.query.end)]
            self_v_query_aligned_seq = self.v.query.aligned_seq
            self_v_sbjct_aligned_seq = self.v.sbjct.aligned_seq
            self_v_query_end = self.v.query.end
        else:
            if self.j is not None:
                q_left = self.query.seq[:(self.j.query.start - 1)]
        if self.v is not None and self.j is not None:
            q_middle = self.query.seq[(self.v.query.end):(self.j.query.start - 1)]
        if self.j is not None:
            q_alignj = self.query.seq[(self.j.query.start - 1):(self.j.query.end)]
            q_right  = self.query.seq[(self.j.query.end):]
            self_j_query_aligned_seq = self.j.query.aligned_seq
            self_j_sbjct_aligned_seq = self.j.sbjct.aligned_seq
            self_j_query_start = self.j.query.start
        else:
            if self.v is not None:
                q_right  = self.query.seq[(self.v.query.end):]
        # split V gene sequence into segemnts
        if self.v is not None:
            v_left   = self.v.sbjct.seq[:(self.v.sbjct.start - 1)]
            v_align  = self.v.sbjct.seq[(self.v.sbjct.start - 1):(self.v.sbjct.end)]
            v_right  = self.v.sbjct.seq[(self.v.sbjct.end):]
        # split J gene sequence into segemnts
        if self.j is not None:
            j_left   = self.j.sbjct.seq[:(self.j.sbjct.start - 1)]
            j_align  = self.j.sbjct.seq[(self.j.sbjct.start - 1):(self.j.sbjct.end)]
            j_right  = self.j.sbjct.seq[(self.j.sbjct.end):]
        
        
        # build up alignemnts till the 5'-end of v alignemn
        # query :  5'    tccgatcttgtgtatcgatgctagca-tcgactgatgc
        #                             ||||||||| ||||||||||||| |
        # v     :  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatcc
        add_blank_to_q = ''
        add_blank_to_v = ''
        if len(q_left) < len(v_left):
            add_blank_to_q = ''.join([' '] * (len(v_left) - len(q_left)))
        elif len(q_left) > len(v_left):
            add_blank_to_v = ''.join([' '] * (len(q_left) - len(v_left)))
        
        # merge the aligned sequences: FROM left part TO the end position of v aligment
        aligned_query = add_blank_to_q + q_left + self_v_query_aligned_seq
        aligned_v     = add_blank_to_v + v_left + self_v_sbjct_aligned_seq
        
        # fill up the v alignment, and fill up the query alignemnt
        # query :  5'    tccgatcttgtgtatcgatgctagca-tcgactgatgctagtcgatgtacgtagggacttcgagctattcggatctgagcgctatgcagttg3'
        #                             ||||||||| ||||||||||||| |
        # v     :  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatccattagactgtc                       (blank)             3'
        aligned_query += q_middle + self_j_query_aligned_seq + q_right
        aligned_v += v_right + ''.join([' '] * (len(aligned_query) - len(v_right) + 1))
        
        # build up the j alivnemnt
        # j     :  5'                                                                   cgaattgggatctgttgct   3'
        #                                                                                  ||| |||||||
        # query :  5'    tccgatcttgtgtatcgatgctagca-tcgactgatgctagtcgatgtacgtagggacttcgagctattcggatctgagcgctatgcagttg3'
        #                             ||||||||| ||||||||||||| |
        # v     :  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatccattagactgtc    3'
        num_of_blank_add_to_j = len(add_blank_to_q + q_left + self_v_query_aligned_seq)
        num_of_blank_add_to_j += self_j_query_start - self_v_query_end - 1
        num_of_blank_add_to_j -= len(j_left)
        aligned_j += ''.join([' '] * num_of_blank_add_to_j)
        aligned_j += j_left + j_align + j_right
        aligned_j = aligned_j + ''.join([' '] * (len(aligned_query) - len(aligned_j)))
        
        # build up untemplated region and cdr3 region
        # j     :  5'                                                                   cgaattgggatctgttgct   3'
        # query :  5'    tccgatcttgtgtatcgatgctagca-tcgactgatgctagtcgatgtacgtagggacttcgagctattcggatctgagcgctatgcagttg3'
        # v     :  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatccattagactgtc    3'
        # untmpl:  5'                                          tagtcgatgtacgtagggacttcgagct3'
        # cdr3  :  5'                                    tgatgctagtcgatgtacgtagggacttcgagctattcgga3'
        if self.variable_region is not None:
            aligned_untmpl = self.query.seq[(self.variable_region.untemplate_region[0] - 1):(self.variable_region.untemplate_region[1] - 1)]
            if self.variable_region.cdr3 is not None:
                aligned_cdr3 = self.query.seq[(self.variable_region.cdr3[0] - 1):(self.variable_region.cdr3[1] - 1)]
                diff_left    = self.variable_region.untemplate_region[0] - self.variable_region.cdr3[0]
                diff_right   = self.variable_region.untemplate_region[1] - self.variable_region.cdr3[1]
                delete_blank = 0
                if diff_left > 0:
                    aligned_untmpl = ''.join([' '] * diff_left) + aligned_untmpl
                    delete_blank = diff_left
                elif diff_left < 0:
                    aligned_cdr3 = ''.join([' '] * (- diff_left)) + aligned_cdr3
                    delete_blank = 0
                aligned_untmpl = ''.join([' '] * (len(add_blank_to_q + q_left + self.v.query.aligned_seq) - delete_blank)) + aligned_untmpl
                aligned_cdr3   = ''.join([' '] * (len(add_blank_to_q + q_left + self.v.query.aligned_seq) - delete_blank)) + aligned_cdr3
            else:
                aligned_untmpl = ''.join([' '] * (len(add_blank_to_q + q_left + self.v.query.aligned_seq))) + aligned_untmpl
                aligned_cdr3   = ''.join([' '] * (len(add_blank_to_q + q_left + self.v.query.aligned_seq))) + aligned_cdr3

        return [aligned_query, aligned_v, aligned_j, aligned_untmpl, aligned_cdr3]





    def __find_untemplated_seq_3end(self, q_seq, q_seq_align, q_start, q_end, s_seq, s_seq_align, s_start, s_end):

        # split whole sequence into three parts
        # query:  5'    tccgatcttgtgtatcgatgctagca-tcgactgatgctagtcgatgtacgta3'
        #                            ||||||||| |||||||||||||||
        # sbjct:  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatcaattagactgtc    3'
        #           <-- left part -><---- aligned part -----><- right part ->
        query_left_seq = q_seq[:(q_start - 1)]
        sbjct_left_seq = s_seq[:(s_start - 1)]
        query_right_seq = q_seq[q_end:]
        sbjct_right_seq = s_seq[s_end:]

        # insert '-' into sequence in order to make two sequence become same length
        # query:  5'----tccgatcttgtgtatcgatgctagca-tcgactgatgctagtcgatgtacgta3'
        #                            ||||||||| |||||||||||||||
        # sbjct:  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatcaattagactgtc    3'
        len_diff_left = len(query_left_seq) - len(sbjct_left_seq)
        if  len_diff_left > 0:
            sbjct_left_seq = ''.join(['-'] * len_diff_left) + sbjct_left_seq
        if len_diff_left < 0:
            n_len_diff_left = - len_diff_left
            query_left_seq = ''.join(['-'] * n_len_diff_left) + query_left_seq

        # query:  5'----tccgatcttgtgtatcgatgctagca-tcgactgatgctagtcgatgtacgta3'
        #                            ||||||||| |||||||||||||||
        # sbjct:  5'gcttcgatgctcctccgatcgatggtagcagtcgactgatcaattagactgtc-----3'
        len_diff_right = len(query_right_seq) - len(sbjct_right_seq)
        if len_diff_right > 0:
            sbjct_right_seq = sbjct_right_seq + ''.join(['-'] * len_diff_right)
        if len_diff_right < 0:
            n_len_diff_right = - len_diff_right
            query_right_seq = query_right_seq + ''.join(['-'] * n_len_diff_right)

        aligned_query_seq = query_left_seq + q_seq_align + query_right_seq
        aligned_sbjct_seq = sbjct_left_seq + s_seq_align + sbjct_right_seq

        # calculate the end position of alignment
        if len_diff_left > 0:
            alignment_end_pos = len(q_seq_align) + q_start #- 1
        else:
            alignment_end_pos = len(s_seq_align) + s_start #- 1

        #       alignment_end_pos -->|       |<-- subject sequence end position
        #                            |<--L-->|
        #  query ACAGCTAGTCTGATTCGTATGCATGCTAGCTTAGCTATTGCTGTAGTGCTATTGCCAGTCGATGTCGTAT
        #        ||||| |||||||||||||||
        #  sbjct ACAGCAAGTCTGATTCGTATGCGGCTACT-----------------------------------------
        #             |<-------2(L+2)------->|
        #  pos_start->|
        #
        len_un_aligned_seq = len(s_seq) - s_end    # = L
 
        un_template_start = alignment_end_pos
        if len_diff_left < 0:
            un_template_start_of_query = un_template_start - (len(q_seq_align) - (q_end - q_start)) + len_diff_left + 1
        else:
            un_template_start_of_query = un_template_start + 1
        
        return un_template_start_of_query



    def __find_untemplated_seq_5end(self, q_seq, q_seq_align, q_start, q_end, s_seq, s_seq_align, s_start, s_end):
        rev_q_seq = q_seq[::-1]
        rev_s_seq = s_seq[::-1]
        pos = self.__find_untemplated_seq_3end(q_seq[::-1], q_seq_align[::-1],
                                              len(q_seq) - q_end, len(q_seq) - q_start + 1,
                                              s_seq[::-1], s_seq_align[::-1],
                                              len(s_seq) - s_end, len(s_seq) - s_start + 1)
        pos = len(q_seq) - pos + 1
        return pos




    def __valid_alignment(self):
        '''
        Validate alignemnt.
        
        Return an integer to specify the alignment status.
             1 : alignment is correct.
            -1 : alignment is not perfect. V is lacked.
            -2 : alignment is not perfect. J is lacked.
            -3 : alignment is not perfect. V and J are lacked.
            -4 : alignment is not correct. The strand of V and J are different.
            -5 : alignment is not correct. The V and J have the common region.
             0 : program error.
        '''
        valid_align = 0
        v = self.v
        j = self.j
        
        if v is None and j is None:
            valid_align = -3
        elif v is not None and j is None:
            valid_align = -2
        elif v is None and j is not None:
            valid_align = -1
        
        if valid_align >= 0:
            if v.sbjct.strand != j.sbjct.strand:
                valid_align = -4
            else:
                valid_align = -5
                if (v.query.start < v.query.end) and (v.query.end < j.query.start) and (j.query.start < j.query.end):
                    valid_align = 1
                if (j.query.start < j.query.end) and (j.query.end < v.query.start) and (v.query.start < v.query.end):
                    valid_align = 1
        
        '''
        if valid_align == -1:
            logging.warning('The alignemnt of ' + self.query.name + ' is not correct. No V gene.')
        elif valid_align == -2:
            logging.warning('The alignemnt of ' + self.query.name + ' is not correct. No J gene.')
        elif valid_align == -3:
            logging.warning('The alignemnt of ' + self.query.name + ' is not correct. No V and J genes.')
        elif valid_align == -4:
            logging.warning('The alignemnt of ' + self.query.name + ' is not correct. The strand of V and J are different.')
        elif valid_align == -5:
            logging.warning('The alignemnt of ' + self.query.name + ' is not correct. The V and J have the common region.')
        elif valid_align == 0:
            raise StandardError('Program Error !')
        '''
        
        if valid_align == 1:
            self.valid_alignment = True
        else:
            self.valid_alignment = False
        
        return valid_align
    
    
    
    
    def __seek_cdr3(self, v_end, j_start):
        const_tag = IgConstantTag()
        
        cdr3_start, cdr3_end, orf = self.__seek_cdr3_inner(self.query.seq, v_end, j_start,
                                                           const_tag.V_re,
                                                           const_tag.J_re,
                                                           const_tag.cdr3_motif_start_len,
                                                           const_tag.cdr3_motif_end_len)
        # if cannot find the motifs by perfect match,
        # then assume that there is a mismatch in the motifs
        if cdr3_start is None:
            cdr3_start, cdr3_end, orf = self.__seek_cdr3_inner(self.query.seq, v_end, j_start,
                                                           const_tag.V_1mismatch_re,
                                                           const_tag.J_re,
                                                           const_tag.cdr3_motif_start_len,
                                                           const_tag.cdr3_motif_end_len)
        return [cdr3_start, cdr3_end, orf]
    
    
    
    def __seek_cdr3_inner(self, seq, v_end, j_start, motif_start_re, motif_end_re, motif_start_len, motif_end_len):
        cdr3_start = None
        cdr3_end   = None
        orf = None
        # find pattern
        for i in range(3):  # ORF: 0, 1, 2
            has_v_tag = None
            has_j_tag = None
            cdr3_aa_start = None
            cdr3_aa_end   = None
            v_aa_end   = int(v_end / 3 + 1)
            j_aa_start = int(j_start / 3 - 1)
            
            slice_start = i
            slice_end = int(math.floor((len(seq) - i) / 3)) * 3 + i
            
            aa = str(Seq(seq[slice_start:slice_end], generic_dna).translate())
            aa_left  = aa[:(j_aa_start - 1)]  # left + untemplated 
            aa_right = aa[v_aa_end:]          # untemplated + right

            # find the CDR3 pattern in V region, and pass all patterns.
            # after for-loop, only the last one will be save in has_v_tagvariable.
            for has_v_tag in motif_start_re.finditer(aa_left):
                pass
            
            # if can find V gene, then find J
            if has_v_tag:
                cdr3_aa_start = has_v_tag.start() + motif_start_len   # remove AVYYC, ...
                has_j_tag = motif_end_re.search(aa_right)
                if has_j_tag:
                    cdr3_aa_end = has_j_tag.end() + v_aa_end - motif_end_len # remove G.G
                    cdr3_start  = cdr3_aa_start * 3 + i
                    cdr3_end    = cdr3_aa_end * 3 + i
                    orf = i
                    break
        if cdr3_start is not None:
            cdr3_start += 1
        if cdr3_end is not None:
            cdr3_end += 1
        if orf is not None:
            orf += 1
        return [cdr3_start, cdr3_end, orf]
    
    
    
    def __seek_untemplated_region(self):
        un_templated_seq_start =  self.__find_untemplated_seq_3end(
                self.v.query.seq, self.v.query.aligned_seq, self.v.query.start, self.v.query.end,
                self.v.sbjct.seq, self.v.sbjct.aligned_seq, self.v.sbjct.start, self.v.sbjct.end
            )
        un_templated_seq_end =  self.__find_untemplated_seq_5end(
                self.j.query.seq, self.j.query.aligned_seq, self.j.query.start, self.j.query.end,
                self.j.sbjct.seq, self.j.sbjct.aligned_seq, self.j.sbjct.start, self.j.sbjct.end
            )
        return [un_templated_seq_start, un_templated_seq_end]
        

    def seek_cdr3(self):
        '''
        Search cdr3 region.
        
        If the query sequence has the correct alignments with V and J genes, then search the cdr3
        region. The cdr3 region should be the region between the end of V gene and the start of J
        gene. Therefore, this method tries to file the cdr3 sequences at that region.
        '''
        # only process for corect sequence
        has_valid_alignment = self.forward_ig_seq()
        if has_valid_alignment:
            untmpl_start, untmpl_end = self.__seek_untemplated_region()
            cdr3_start, cdr3_end, self.query.orf = self.__seek_cdr3(untmpl_start - 1, untmpl_end)
            self.variable_region = IgSeqVariableRegion(self.query.name, self.query.seq, untmpl_start, untmpl_end, cdr3_start, cdr3_end)
        #else:
        #    logging.warning('The alignments of ' + self.query.name + ' is not correct. Discarded this sequence.')
    
    
    
    
    def get_cdr3_data(self, v_adj = 0, j_adj = 0):
        if (v_adj % 3 != 0) or (j_adj % 3 != 0):
            raise ValueError('The v_adj and j_adj arguments in get_cdr3_data should be 0 or divisible by 3.')
        
        seq_nucl = ''
        seq_prot = ''
        cdr3_nucl = ''
        cdr3_prot = ''
        
        if (self.query.orf is not None) and (self.variable_region.cdr3 is not None):
            seq_nucl  = self.query.seq[(self.query.orf - 1):int(math.floor((len(self.query.seq) - self.query.orf - 1) / 3) * 3 + self.query.orf - 1)]
            cdr3_nucl = self.query.seq[(self.variable_region.cdr3[0] - 1 + v_adj):(self.variable_region.cdr3[1] - 1 + j_adj)]
            seq_prot  = str(Seq(seq_nucl, generic_dna).translate())
            cdr3_prot = str(Seq(cdr3_nucl, generic_dna).translate())
        
        query_prot_nocdr3 = seq_prot.replace(cdr3_prot, '')
        stop_codon_tag = '.'
        if cdr3_prot == '':
            stop_codon_tag = 'X'     # no-seq
        elif '*' in cdr3_prot and '*' in query_prot_nocdr3:
            stop_codon_tag = 'B'     # stop codon in both seqs
        elif '*' in cdr3_prot and '*' not in query_prot_nocdr3:
            stop_codon_tag = 'C'     # stop codon in cdr3 seq
        elif '*' not in cdr3_prot and '*' in query_prot_nocdr3:
            stop_codon_tag = 'Q'     # stop codon in non-cdr3 seq
        elif '*' not in cdr3_prot and '*' not in query_prot_nocdr3:
            stop_codon_tag = 'N'     # no-stop codon
        else:
            raise SystemError('The stop_codon_tag has invalid type!')
        
        if cdr3_nucl == '':
            cdr3_nucl = None
        if cdr3_prot == '':
            cdr3_prot = None
        
        cdr3_data = CDR3Data(cdr3_nucl, cdr3_prot, stop_codon_tag)
        return cdr3_data




class CDR3Data:
    def __init__(self, nucl_seq, prot_seq, stop_codon_tag):
        self.nucl_seq = nucl_seq
        self.prot_seq = prot_seq
        self.stop_codon_tag = stop_codon_tag
