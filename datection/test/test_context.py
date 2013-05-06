# -*- encoding: utf-8 -*-

"""
The test suite of the classes and functions defined in the
datection.context module.
"""

import unittest
import sys
sys.path.insert(0, '..')

import datection.context


class TestContext(unittest.TestCase):

    def setUp(self):
        self.text = u""" L'embarquement se fait 20 minutes avant.
La croisière démarre au pied de la Tour EIffel et dure 1h.
Réservation obligatoire au 01 76 64 14 68.
Embarquement ponton n°1
Réservez en ligne Rédigez un avis !
1 avis = 1 chance de gagner 50€
La croisière enchantée - Promenade en famille

    La croisière enchantée - Promenade en famille
    La Croisière Enchantée

Dates et horaires
Du 6 octobre 2012 au 13 juillet 2013."""
        self.lang = 'fr'
        self.c1 = datection.context.Context(
            match_start=50, match_end=100, text=' '*200, size=20)
        self.c2 = datection.context.Context(
            match_start=70, match_end=115, text=' '*200, size=20)

    def test_context_init(self):
        assert self.c1.start == 30  # 50 - 20
        assert self.c1.end == 120  # 100 + 20
        assert len(self.c1) == 90

    def test_context_inclusion(self):
        assert self.c2 in self.c1

    def test_context_addition(self):
        c3 = self.c1 + self.c2
        assert c3.start == 30
        assert c3.end == 135

    def test_independants(self):
        indies = datection.context.probe(self.text, self.lang)
        # indies = datection.context.independants(probes)
        # 5 elements will be probed: '1h', 'octobre', '2012', 'juillet' & '2013'
        # However, the last 4 all overlap, so they will be merged into one context
        assert len(indies) == 2


if __name__ == '__main__':
    unittest.main()
