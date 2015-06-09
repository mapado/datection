# -*- encoding: utf-8 -*-

"""
The test suite of the classes and functions defined in the
datection.context module.
"""

import unittest

from datection.context import probe, Context, independants


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
        self.c1 = Context(
            match_start=60, match_end=100, text=' ' * 200,
            probe_kind=[], size=50)
        self.c2 = Context(
            match_start=70, match_end=115, text=' ' * 200,
            probe_kind=[], size=50)

    def test_context_init(self):
        assert self.c1.start == 10  # 60 - 50
        assert self.c1.end == 150  # 100 + 50
        assert len(self.c1) == 140

    def test_context_inclusion(self):
        assert self.c2 in self.c1

    def test_context_addition(self):
        c3 = self.c1 + self.c2
        assert c3.start == 10
        assert c3.end == 165

    def test_independants(self):
        indies = probe(self.text, self.lang)
        # 5 elements will be probed: '1h', 'octobre', '2012', 'juillet' & '2013'
        # However, the last 4 all overlap, so they will be merged into one
        # context
        assert len(indies) == 2

    def test_independants_no_contexts(self):
        self.assertEqual(independants(None), [])


if __name__ == '__main__':
    unittest.main()
