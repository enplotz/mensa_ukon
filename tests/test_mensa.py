from mensa_ukon import Mensa


class TestMensa:

    def test_normalize_keys(self):

        # test is lowercased and spaces are replaced by underscores
        k1 = 'Key 1'
        exp1 = 'key_1'
        assert exp1 == Mensa._normalize_key(k1)
        assert exp1 == Mensa._normalize_key(exp1)

        k2 = ' KeY 2 '
        exp2 = 'key_2'
        assert exp2 == Mensa._normalize_key(k2)

    def test_strip_additives(self):
        # these should all result in empty strings
        strip = [
            '(1,2,3,4,5)',
            '( 1, 2,3 ,  4,  5,6)',
            '(1, 2,3 , 4,5,6 )',
            '(1a,2b,3c,4,5e)',
            '( 1a, b,c,d, 2,3 ,  4,  5,6)',
            '(1, 2,3a, b,4a,5,6 )',
        ]
        for s in strip:
            assert Mensa._strip_additives(s) == ''

    def test_normalize_whitespace(self):
        assert Mensa._normalize_whitespace('  ') == ' '
        assert Mensa._normalize_whitespace('  a  ') == ' a '
        assert Mensa._normalize_whitespace('a  a') == 'a a'
        assert Mensa._normalize_whitespace('\t\t') == ' '
        assert Mensa._normalize_whitespace(' \t') == ' '

    def test_normalize_orthography(self):
        assert Mensa._normalize_orthography(' ,') == ','
        assert Mensa._normalize_orthography('aaa, ,') == 'aaa,,'

    def test_clean_text(self):
        assert Mensa._clean_text('\tThe quick  brown fox   , jumps over (1,2,2a,b, 9) the lazy dog.  ') == \
               'The quick brown fox, jumps over the lazy dog.'
