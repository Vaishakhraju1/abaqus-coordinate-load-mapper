"""Map paired point forces to explicitly selected mesh instances."""
import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as source:
        return list(csv.DictReader(source))


def vector(row, names):
    result = tuple(float(row[name]) for name in names)
    if not all(math.isfinite(value) for value in result):
        raise ValueError('Coordinates and forces must be finite')
    return result


def map_loads(nodes, forces, tolerance):
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Tolerance must be finite and non-negative')
    instances = defaultdict(list)
    seen = set()
    for row in nodes:
        instance, label = row['instance'], int(row['node_id'])
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', instance) or label < 1:
            raise ValueError('Invalid instance name or node label')
        if (instance, label) in seen:
            raise ValueError('Duplicate instance/node label')
        seen.add((instance, label))
        instances[instance].append((label, vector(row, ('x', 'y', 'z'))))
    totals = defaultdict(lambda: [0.0, 0.0, 0.0])
    audit = []
    for row in forces:
        origin = vector(row, ('ox', 'oy', 'oz'))
        insertion = vector(row, ('ix', 'iy', 'iz'))
        magnitude = float(row['force'])
        length = math.dist(origin, insertion)
        if not math.isfinite(magnitude) or magnitude < 0 or length == 0:
            raise ValueError('Force must be non-negative and endpoints distinct')
        force = tuple(magnitude * (b - a) / length for a, b in zip(origin, insertion))
        for endpoint, coord, sign in (('origin', origin, 1), ('insertion', insertion, -1)):
            instance = row[endpoint + '_instance']
            candidates = instances.get(instance)
            if not candidates:
                raise ValueError('No nodes in instance %s' % instance)
            distances = sorted((math.dist(coord, xyz), label) for label, xyz in candidates)
            distance, label = distances[0]
            if distance > tolerance:
                raise ValueError('Endpoint %s exceeds mapping tolerance' % row['load_id'])
            if len(distances) > 1 and math.isclose(distance, distances[1][0], rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError('Ambiguous nearest node for %s' % row['load_id'])
            for index, value in enumerate(force):
                totals[(instance, label)][index] += sign * value
            audit.append((row['load_id'], endpoint, instance, label, distance))
    return dict(totals), audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('nodes', type=Path)
    parser.add_argument('forces', type=Path)
    parser.add_argument('--tolerance', required=True, type=float)
    parser.add_argument('--output', type=Path, default=Path('loads.inp'))
    parser.add_argument('--audit', type=Path, default=Path('mapping.csv'))
    args = parser.parse_args()
    paths = [p.resolve() for p in (args.nodes, args.forces, args.output, args.audit)]
    if len(set(paths)) != 4:
        parser.error('Input and output paths must be distinct')
    totals, audit = map_loads(read_csv(args.nodes), read_csv(args.forces), args.tolerance)
    if not audit:
        parser.error('No force pairs supplied')
    with args.output.open('w', encoding='utf-8') as output:
        output.write('** Synthetic/generalised paired-load mapping\n*CLOAD\n')
        for (instance, label), force in sorted(totals.items()):
            for dof, value in enumerate(force, 1):
                output.write('%s.%d, %d, %.12g\n' % (instance, label, dof, value))
    with args.audit.open('w', newline='', encoding='utf-8') as output:
        writer = csv.writer(output)
        writer.writerow(('load_id', 'endpoint', 'instance', 'node_id', 'distance'))
        writer.writerows(audit)
    print('Mapped %d endpoints onto %d nodes' % (len(audit), len(totals)))


if __name__ == '__main__':
    main()
