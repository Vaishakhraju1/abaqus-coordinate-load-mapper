import copy
import unittest
from map_loads import map_loads, read_csv


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.nodes = read_csv('nodes.csv')
        self.forces = read_csv('forces.csv')

    def test_balance_and_instance_identity(self):
        totals, audit = map_loads(self.nodes, self.forces, 0.05)
        self.assertEqual(len(audit), 4)
        self.assertEqual(totals[('ComponentA-1', 1)], [0., 10., 0.])
        self.assertEqual(totals[('ComponentB-1', 1)], [0., -10., 0.])
        self.assertEqual([sum(v[i] for v in totals.values()) for i in range(3)], [0., 0., 0.])

    def test_repeated_loads_accumulate(self):
        totals, _ = map_loads(self.nodes, self.forces * 2, 0.05)
        self.assertEqual(totals[('ComponentA-1', 1)][1], 20.)

    def test_tolerance_and_missing_instance(self):
        for changes in ({'ox': '100'}, {'origin_instance': 'Missing'}):
            forces = copy.deepcopy(self.forces)
            forces[0].update(changes)
            with self.assertRaises(ValueError):
                map_loads(self.nodes, forces, 0.05)

    def test_zero_length_and_ambiguous_mapping(self):
        forces = copy.deepcopy(self.forces)
        forces[0]['iy'] = '0'
        with self.assertRaises(ValueError):
            map_loads(self.nodes, forces, 0.05)
        nodes = self.nodes + [dict(instance='ComponentA-1', node_id='3', x='0', y='0', z='0')]
        with self.assertRaises(ValueError):
            map_loads(nodes, self.forces, 0.05)


if __name__ == '__main__':
    unittest.main()
