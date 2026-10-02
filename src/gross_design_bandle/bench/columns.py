"""Joint H/Lambda columns and reversible population/grouping provenance."""
from dataclasses import dataclass
import numpy as np
from scipy import sparse
from gross_design_bandle.noise.profiles import parity_probability

ADMISSION = ('include_all', 'exclude_joint_zero')
GROUPING = ('preserve_copies', 'joint_signature_xor')


def matrix_from_signatures(signatures, rows):
    indices = []; indptr = [0]
    for value in signatures:
        while value:
            bit = value & -value; indices.append(bit.bit_length()-1); value ^= bit
        indptr.append(len(indices))
    return sparse.csc_matrix((np.ones(len(indices),dtype=np.uint8),indices,indptr),shape=(rows,len(signatures)))


@dataclass(frozen=True)
class FaultModel:
    circuit: object
    profile: object
    locations: tuple
    raw: tuple
    raw_signatures: tuple
    copy_to_raw: np.ndarray
    copy_ordinal: np.ndarray
    admission_mask: np.ndarray
    admitted_to_copy: np.ndarray
    admitted_to_group: np.ndarray
    group_signatures: tuple
    H: object
    Lambda: object
    probabilities: np.ndarray
    decoder_probabilities: np.ndarray
    admission_policy: str
    grouping_policy: str

    @property
    def N(self):
        return len(self.admitted_to_copy)

    def validate(self):
        from gross_design_bandle.noise.catalogue import primitive_terms
        from gross_design_bandle.noise.locations import validate_locations
        from gross_design_bandle.noise.profiles import MULTIPLICITIES
        validate_locations(self.circuit,self.locations)
        ncopy = len(self.copy_to_raw)
        if self.admission_policy not in ADMISSION or self.grouping_policy not in GROUPING:
            raise ValueError('unknown population policy')
        if not self.profile.independent:
            raise ValueError('categorical channel has no independent Bernoulli catalogue')
        expected_primitives = []
        for j,loc in enumerate(self.locations):
            for word,x,z in primitive_terms(loc):
                expected_primitives.append({'id':f'{loc.id}/{word}','location_index':j,'pauli_word':word,
                    'x':x,'z':z,'probability':self.profile.probability(loc.kind),
                    'unequal_probability':MULTIPLICITIES[loc.kind]*self.profile.p/15,
                    'equal_q_multiplicity':MULTIPLICITIES[loc.kind],'copies':self.profile.copies(loc.kind)})
        if list(self.raw) != expected_primitives or len(self.raw_signatures) != len(self.raw):
            raise ValueError('raw primitive physical/probability coverage mismatch')
        if self.copy_to_raw.shape != (ncopy,) or self.copy_ordinal.shape != (ncopy,) or self.admission_mask.shape != (ncopy,) or self.admission_mask.dtype != np.bool_:
            raise ValueError('copy/admission shape or dtype mismatch')
        expected_raw = []; expected_ordinal = []
        for r,entry in enumerate(self.raw):
            expected_raw.extend([r]*entry['copies']); expected_ordinal.extend(range(entry['copies']))
        if not np.array_equal(self.copy_to_raw,expected_raw) or not np.array_equal(self.copy_ordinal,expected_ordinal):
            raise ValueError('raw/copy multiplicity mapping mismatch')
        signatures = [self.raw_signatures[r] for r in self.copy_to_raw]
        expected_mask = np.ones(ncopy,dtype=bool) if self.admission_policy == 'include_all' else np.array([bool(s) for s in signatures])
        if not np.array_equal(self.admission_mask,expected_mask) or not np.array_equal(self.admitted_to_copy,np.flatnonzero(expected_mask)):
            raise ValueError('admission map/policy mismatch')
        chosen = [signatures[c] for c in self.admitted_to_copy]
        if self.H.shape != (self.circuit.num_detectors,self.N) or self.Lambda.shape != (self.circuit.num_observables,self.N):
            raise ValueError('H/Lambda column alignment mismatch')
        full = sparse.vstack((self.H,self.Lambda),format='csc')
        if (full != matrix_from_signatures(chosen,full.shape[0])).nnz:
            raise ValueError('H/Lambda signatures disagree with physical map')
        expected_p = np.array([self.raw[self.copy_to_raw[c]]['probability'] for c in self.admitted_to_copy])
        if not np.array_equal(self.probabilities,expected_p):
            raise ValueError('probability alignment mismatch')
        if self.admitted_to_group.shape != (self.N,):
            raise ValueError('decoder grouping shape mismatch')
        if self.N and (min(self.admitted_to_group)<0 or max(self.admitted_to_group)>=len(self.group_signatures)):
            raise ValueError('decoder group outside range')
        for j,g in enumerate(self.admitted_to_group):
            if chosen[j] != self.group_signatures[g]:
                raise ValueError('decoder grouping lost joint signature')
        if self.grouping_policy == 'preserve_copies' and not np.array_equal(self.admitted_to_group,np.arange(self.N)):
            raise ValueError('preserve_copies cannot compact')
        if self.grouping_policy == 'joint_signature_xor' and len(set(self.group_signatures)) != len(self.group_signatures):
            raise ValueError('joint signature grouping is not compact')
        if len(self.decoder_probabilities) != len(self.group_signatures):
            raise ValueError('decoder probability coverage mismatch')
        members = [[] for _ in self.group_signatures]
        for j,g in enumerate(self.admitted_to_group):
            members[g].append(self.probabilities[j])
        for g,values in enumerate(members):
            if not values or abs(self.decoder_probabilities[g]-parity_probability(values))>1e-14:
                raise ValueError('decoder XOR probability mismatch')

    def to_dict(self):
        self.validate()
        return {'schema_version':1,'noise_profile':self.profile.name,'p':self.profile.p,
            'probability_law':'independent Bernoulli; equal copies XOR on identical Pauli',
            'admission_policy':self.admission_policy,'grouping_policy':self.grouping_policy,
            'N_raw_primitives':len(self.raw),'N_equal_or_unequal_copies':len(self.copy_to_raw),
            'N_admitted':self.N,'N_decoder_groups':len(self.group_signatures),
            'locations':[l.to_dict() for l in self.locations],'raw_primitives':list(self.raw),
            'raw_joint_signatures_hex':[hex(s) for s in self.raw_signatures],
            'copy_to_raw':self.copy_to_raw.tolist(),'copy_ordinal':self.copy_ordinal.tolist(),
            'admission_mask':self.admission_mask.tolist(),'admitted_to_copy':self.admitted_to_copy.tolist(),
            'admitted_to_group':self.admitted_to_group.tolist(),
            'decoder_joint_signatures_hex':[hex(s) for s in self.group_signatures],
            'probabilities':self.probabilities.tolist(),'decoder_probabilities':self.decoder_probabilities.tolist(),
            'joint_bit_order':'detector rows followed by logical-action rows',
            'zero_joint_copies':int(sum(s==0 for s in (self.raw_signatures[r] for r in self.copy_to_raw))),
            'zero_detector_nonzero_logical_copies':int(sum(s!=0 and s & ((1<<self.circuit.num_detectors)-1)==0 for s in (self.raw_signatures[r] for r in self.copy_to_raw))),
            'paper_exact':False,'Table6_N_resolved':False,
            'grouping_limit':'XOR grouping preserves unconditional channel, not original fixed-weight spectrum; fixed-weight population uses admitted copies'}

    def discrepancy(self, published_N, decisions):
        mask = (1<<self.circuit.num_detectors)-1
        by_kind = {}; by_phase = {}; by_role = {}
        for r in self.raw:
            loc = self.locations[r['location_index']]
            for ledger,key in ((by_kind,loc.kind),(by_phase,loc.phase),(by_role,loc.role)):
                ledger[key] = ledger.get(key,0)+r['copies']
        return {'published_N':published_N,'raw_copies':len(self.copy_to_raw),'admitted_N':self.N,
            'delta_admitted_minus_published':self.N-published_N,
            'include_all_N':len(self.copy_to_raw),
            'exclude_joint_zero_N':sum(r['copies'] for r,s in zip(self.raw,self.raw_signatures) if s),
            'zero_H_nonzero_Lambda_retained':sum(r['copies'] for r,s in zip(self.raw,self.raw_signatures) if s and not s & mask),
            'copies_by_kind':by_kind,'copies_by_phase':by_phase,'copies_by_role':by_role,
            'physical_decisions':decisions,'explanation':'O3/O4 unresolved: this named independent circuit/population is not claimed to match Table 6; no padding or forced merging'}
