"""Absolute measurement identities; relative rec offsets exist only at lowering.

Repeat scopes instantiate unique IDs. A repeat is retained only when all its
lowered iterations agree, including offsets; otherwise it is safely unrolled.
"""
from dataclasses import dataclass
from collections import Counter
import stim
from gross_design_bandle.surgery.frame import Parity


@dataclass(frozen=True)
class Chunk:
    circuit: stim.Circuit
    outcomes: tuple[str, ...] = ()

    def __post_init__(self):
        if self.circuit.num_measurements != len(self.outcomes):
            raise ValueError('measurement count differs from symbolic outcomes')
        if any(i.name in ('DETECTOR', 'OBSERVABLE_INCLUDE') for i in self.circuit.flattened()):
            raise ValueError('record annotations must remain symbolic until lowering')


@dataclass(frozen=True)
class Annotation:
    name: str
    kind: str
    parity: Parity
    flow_class: str
    justification: str
    observable_index: int | None = None

    def __post_init__(self):
        if self.kind not in ('detector', 'observable', 'CX', 'CY', 'CZ'):
            raise ValueError('unknown record annotation')
        if self.kind == 'observable' and (not isinstance(self.observable_index, int)
                or isinstance(self.observable_index, bool) or self.observable_index < 0):
            raise ValueError('observable needs nonnegative index')
        if not self.name or not self.justification:
            raise ValueError('annotation requires semantic name and justification')


@dataclass(frozen=True)
class Repeat:
    name: str
    count: int
    body: tuple
    carry: tuple[tuple[str, str, str], ...] = ()

    def __post_init__(self):
        if not self.name or not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 1:
            raise ValueError('repeat count must be a positive integer')
        if any(len(t) != 3 or any(not isinstance(i,str) or not i for i in t) for t in self.carry) or len({t[0] for t in self.carry}) != len(self.carry):
            raise ValueError('repeat carry needs unique alias/initial/body-outcome triples')


@dataclass(frozen=True)
class Lowered:
    circuit: stim.Circuit
    outcome_ids: tuple[str, ...]
    annotations: tuple[dict, ...]


class RecordProgram:
    def __init__(self, nodes=()):
        self.nodes = list(nodes)

    def chunk(self, circuit, outcomes=()):
        self.nodes.append(Chunk(circuit.copy(), tuple(outcomes)))

    def mark(self, name, kind, parity, flow_class, justification, observable_index=None):
        self.nodes.append(Annotation(name, kind, parity, flow_class, justification, observable_index))

    def lower(self, *, compact=True):
        positions, outcomes, annotations = {}, [], []

        def resolve(scope, aliases, id):
            return aliases.get(id, scope+id)

        def walk(nodes, scope, aliases=None):
            aliases = {} if aliases is None else aliases
            out = stim.Circuit()
            for node in nodes:
                if isinstance(node, Chunk):
                    for id in node.outcomes:
                        key = scope + id
                        if not id or key in positions or id in aliases:
                            raise ValueError('duplicate or empty symbolic outcome ID')
                        positions[key] = len(outcomes)
                        outcomes.append(key)
                    out += node.circuit
                elif isinstance(node, Repeat):
                    bodies = []
                    for r in range(node.count):
                        child_scope = f'{scope}{node.name}/{r}/'
                        child_aliases = {alias:resolve(scope,aliases,initial) if r == 0 else
                                         f'{scope}{node.name}/{r-1}/{output}'
                                         for alias,initial,output in node.carry}
                        for key in child_aliases.values():
                            if key not in positions:
                                raise ValueError(f'unknown or future repeat carry outcome {key}')
                        bodies.append(walk(node.body,child_scope,child_aliases))
                    if compact and all(b == bodies[0] for b in bodies):
                        out += bodies[0] * node.count
                    else:
                        for body in bodies:
                            out += body
                elif isinstance(node, Annotation):
                    counts = Counter(resolve(scope,aliases,i) for i in node.parity.ids)
                    ids = tuple(id for id,count in counts.items() if count % 2)
                    try:
                        offsets = tuple(positions[i]-len(outcomes) for i in ids)
                    except KeyError as exc:
                        raise ValueError(f'unknown or future symbolic outcome {exc.args[0]}') from exc
                    if any(o >= 0 for o in offsets):
                        raise ValueError('record offset must refer to the past')
                    if node.parity.constant:
                        # A real deterministic pad preserves signed affine parities.
                        key = f'{scope}constant/{len(outcomes)}'
                        if key in positions:
                            raise ValueError('duplicate symbolic affine pad ID')
                        positions[key] = len(outcomes); outcomes.append(key)
                        out.append('MPAD', [1])
                        offsets = tuple(o-1 for o in offsets) + (-1,)
                        ids += (key,)
                    targets = [stim.target_rec(o) for o in offsets]
                    if node.kind == 'detector':
                        out.append('DETECTOR', targets)
                    elif node.kind == 'observable':
                        out.append('OBSERVABLE_INCLUDE', targets, node.observable_index)
                    else:
                        # For feedforward, observable_index is the physical target.
                        if node.observable_index is None or node.observable_index < 0:
                            raise ValueError('controlled frame requires physical target')
                        for t in targets:
                            out.append(node.kind, [t, node.observable_index])
                    annotations.append({'name': scope+node.name, 'kind': node.kind,
                        'parity': Parity(ids).to_dict(), 'record_offsets': list(offsets),
                        'measurement_count': len(outcomes), 'flow_class': node.flow_class,
                        'justification': node.justification, 'observable_index': node.observable_index})
                else:
                    raise ValueError('unknown symbolic record node')
            return out

        circuit = walk(self.nodes, '')
        if circuit.num_measurements != len(outcomes):
            raise ValueError('lowered measurement count mismatch')
        return Lowered(circuit, tuple(outcomes), tuple(annotations))
