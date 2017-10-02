import ast
import unittest

from pyapi.utils.domain_trie import DomainTrie


class DomainTrieTests(unittest.TestCase):
    def test_domain_trie(self):
        domains = [
            'xn--2342390.cn',
            'google.com',
            'mail.google.com',
            'example.stuff',
            '132.22.21.47'
        ]

        trie = DomainTrie(domains)
        self.assertIn('google.com', trie)
        self.assertIn('mail.google.com', trie)
        self.assertIn('api.google.com', trie)
        self.assertIn('goo.example.stuff', trie)
        self.assertIn('goo.example.stuff.', trie)
        self.assertIn('.goo.example.stuff', trie)
        self.assertIn('132.22.21.47', trie)
        self.assertIn('a.xn--2342390.cn', trie)

        self.assertNotIn('133.22.21.47', trie)
        self.assertNotIn('stuff', trie)
        self.assertNotIn('google.api.com', trie)
        self.assertNotIn('google.cn', trie)
        self.assertNotIn('googl.com', trie)
        domains.remove('mail.google.com')
        self.assertItemsEqual(ast.literal_eval(str(trie)), domains)
