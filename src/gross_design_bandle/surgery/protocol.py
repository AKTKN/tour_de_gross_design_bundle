"""IDEAL ONLY: merge/repeat/split oracle. MPP is never a noisy gadget.

Follows arXiv:2506.03094v1 PDF A.4 steps 1--4. No physical schedule,
detectors, fault catalogue or benchmark observable profile is supplied here.
"""
from dataclasses import dataclass

from gross_design_bandle.algebra.pauli import Pauli
from .frame import Parity, build_split_frame
from .ports import embed


def to_stim_pauli(pauli, register=None):
    import stim
    pauli.require_hermitian()
    if register is not None:
        pauli = embed(pauli, tuple(register))
    word = "".join("Y" if x and z else "X" if x else "Z" if z else "I" for x, z in zip(pauli.x, pauli.z))
    sign = "-" if (pauli.phase - sum(x*z for x, z in zip(pauli.x, pauli.z))) % 4 == 2 else "+"
    return stim.PauliString(sign + word)


@dataclass(frozen=True)
class Outcome:
    id: str
    kind: str
    check_id: str
    round: int | None
    pauli: Pauli

    def to_dict(self):
        return {"id": self.id, "kind": self.kind, "check_id": self.check_id,
                "round": self.round, "pauli": self.pauli.to_dict()}


class IdealProtocol:
    """Guarded state machine; outcomes are absolute symbols, never rec offsets."""
    ideal_only = True

    def __init__(self, graph, ports, *, protocol_id="ideal", deformation=None):
        if not isinstance(protocol_id, str) or not protocol_id:
            raise ValueError("protocol ID must be nonempty")
        if graph.vertices != ports.vertices:
            raise ValueError("graph/port ordering differs")
        self.graph, self.ports, self.id = graph, ports, protocol_id
        self.register = ports.target.qubit_ids + tuple(f"edge:{e}" for e in graph.edge_ids)
        if len(set(self.register)) != len(self.register):
            raise ValueError("data and edge registers overlap")
        self.deformation = deformation
        if deformation is not None and (deformation.graph.id != graph.id or deformation.lpu.ports != ports):
            raise ValueError("deformation differs from protocol")
        e = len(graph.edges)
        self.vertices = tuple(Pauli(p.phase, p.x + tuple(b), p.z + (0,)*e, self.register)
                              for p, b in zip(ports.ports, graph.incidence))
        d = len(ports.target.qubit_ids)
        self.cycles = tuple(Pauli(0, (0,)*(d+e), (0,)*d + tuple(c), self.register) for c in graph.cycle_matrix)
        self.state, self.rounds = "new", 0
        self.outcomes = []
        self.frame = None
        self.logical_outcome = None

    @classmethod
    def from_deformation(cls, deformation, *, protocol_id="ideal"):
        return cls(deformation.graph, deformation.lpu.ports, protocol_id=protocol_id, deformation=deformation)

    def prepare(self):
        if self.state != "new":
            raise ValueError("prepare requires new state")
        self.state = "prepared"
        return self

    def _record(self, kind, check_id, pauli, round=None):
        symbol = self._symbol(kind, check_id, round)
        if any(r.id == symbol for r in self.outcomes):
            raise ValueError("duplicate symbolic outcome")
        self.outcomes.append(Outcome(symbol, kind, check_id, round, pauli.require_hermitian()))
        return symbol

    def _symbol(self, kind, check_id, round=None):
        return f"{self.id}/{kind}/{round if round is not None else 'terminal'}/{check_id}"

    def _round(self):
        index = self.rounds
        vertex_ids = tuple(self._record("vertex", v, p, index) for v, p in zip(self.graph.vertices, self.vertices))
        for c, p in zip(self.graph.cycles, self.cycles):
            self._record("cycle", c.id, p, index)
        if self.deformation is not None:
            n = sum(len(c.checks) for c in self.deformation.lpu.codes)
            for id, p in zip(self.deformation.group.ids[:n], self.deformation.group.generators[:n]):
                self._record("dressed", id, p, index)
        if index == 0:
            self.logical_outcome = Parity(vertex_ids)
        self.rounds += 1

    def merge(self):
        if self.state != "prepared":
            raise ValueError("merge requires prepared state")
        self._round()
        self.state = "merged"
        return self

    def repeat(self):
        if self.state != "merged":
            raise ValueError("repeat requires merged state")
        self._round()
        return self

    def split(self, *, root=None, tree_edge_ids=None):
        if self.state != "merged":
            raise ValueError("split requires merged state")
        ids = tuple(self._symbol("edge", edge) for edge in self.graph.edge_ids)
        frame = build_split_frame(self.graph, self.ports, ids, root, tree_edge_ids)
        for edge, q in zip(self.graph.edge_ids, self.register[len(self.ports.target.qubit_ids):]):
            word = "".join("Z" if i == q else "I" for i in self.register)
            self._record("edge", edge, Pauli.from_word(word, self.register))
        self.frame = frame
        if self.deformation is not None:
            for code in self.deformation.lpu.codes:
                for id, p in zip(code.check_ids, code.checks):
                    self._record("original", id, embed(p, self.register))
        self.state = "split"
        return self

    def finish(self):
        if self.state != "split":
            raise ValueError("finish requires split state and recorded frame")
        self.state = "complete"
        return self

    def to_dict(self):
        if self.state != "complete":
            raise ValueError("protocol is incomplete")
        return {"schema_version": 1, "ideal_only": True, "protocol_id": self.id,
                "graph_id": self.graph.id, "register": list(self.register), "rounds": self.rounds,
                "outcomes": [r.to_dict() for r in self.outcomes],
                "logical_outcome": self.logical_outcome.to_dict(), "split_frame": self.frame.to_dict()}

    def to_stim(self):
        """Lazy ideal MPP lowering with one record per Outcome; no noise API."""
        import stim
        if self.state != "complete":
            raise ValueError("protocol is incomplete")
        circuit = stim.Circuit()
        edges = list(range(len(self.ports.target.qubit_ids), len(self.register)))
        if edges:
            circuit.append("R", edges)
        for record in self.outcomes:
            ps = to_stim_pauli(record.pauli)
            targets = []
            for i, p in enumerate(ps):
                if p:
                    if targets:
                        targets.append(stim.target_combiner())
                    target = (stim.target_x, stim.target_y, stim.target_z)[p-1]
                    targets.append(target(i, invert=ps.sign == -1 and not targets))
            if targets:
                circuit.append("MPP", targets)
            else:
                circuit.append("MPAD", [int(ps.sign == -1)])
        return circuit


def build_ideal_protocol(graph, ports, *, rounds=1, root=None, tree_edge_ids=None,
                         protocol_id="ideal", deformation=None):
    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 1:
        raise ValueError("round count must be a positive integer")
    protocol = IdealProtocol(graph, ports, protocol_id=protocol_id, deformation=deformation)
    protocol.prepare().merge()
    for _ in range(rounds-1):
        protocol.repeat()
    return protocol.split(root=root, tree_edge_ids=tree_edge_ids).finish()
