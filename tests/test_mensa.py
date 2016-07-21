import mensa

from mensa import Emoji


class TestMensa:
    def test_normalize_key(self):
        k = mensa._normalize_key('normalize key')
        assert '_' in k
        assert ' ' not in k

    def test_repl_emoji(self):
        # Nothing should be replaced here
        no_replace = '(Foo)'
        assert no_replace == mensa._repl_emoji(no_replace)

        cow = '({})'.format(Emoji.COW)
        assert cow == mensa._repl_emoji('(C)')

        cow_pig = '({}, {})'.format(Emoji.COW, Emoji.PIG)
        assert cow_pig == mensa._repl_emoji('(C, P)')

        clean = 'Foo bar ({}, {})'
        assert clean.format(Emoji.COW, Emoji.CHEESE) == mensa._repl_emoji(clean.format('C', 'Veg'))
        dirty = 'Foo bar ( {} , {} )'
        assert clean.format(Emoji.COW, Emoji.SEEDLING) == mensa._repl_emoji(dirty.format('C', 'Vegan'))
        multi = 'Foo bar (Foo) ({}, {})'
        assert multi.format(Emoji.COW, Emoji.CHEESE) == mensa._repl_emoji(multi.format('C', 'Veg'))
