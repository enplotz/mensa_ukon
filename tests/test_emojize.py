from mensa_ukon.emojize import Emoji, Emojize


class TestEmojize:

    def test_repl_emoji(self):
        # Nothing should be replaced here
        no_replace = '(Foo)'
        assert no_replace == Emojize.replace(no_replace)

        cow = '({})'.format(Emoji.COW)
        assert cow == Emojize.replace('(C)')

        cow_pig = '({}, {})'.format(Emoji.COW, Emoji.PIG)
        assert cow_pig == Emojize.replace('(C, P)')

        clean = 'Foo bar ({}, {})'
        assert clean.format(Emoji.COW, Emoji.CHEESE) == Emojize.replace(clean.format('C', 'Veg'))
        dirty = 'Foo bar ( {} , {} )'
        assert clean.format(Emoji.COW, Emoji.SEEDLING) == Emojize.replace(dirty.format('C', 'Vegan'))
        multi = 'Foo bar (Foo) ({}, {})'
        assert multi.format(Emoji.COW, Emoji.CHEESE) == Emojize.replace(multi.format('C', 'Veg'))
