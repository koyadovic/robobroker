import unittest

from shared.domain.configurations import server_set, server_get, user_set, user_get


class ConfigurationsTestCase(unittest.TestCase):
    def test_server_configurations(self):
        server_set('key1', {
            'value': 13
        })

        configuration = server_get('key1')
        self.assertIn('value', configuration.data)
        self.assertEqual(configuration.data['value'], 13)
        self.assertEqual(configuration.key, 'key1')

    def test_invalid_server_configurations(self):
        with self.assertRaises(ValueError):
            server_set('user_configuration', 1)
        with self.assertRaises(ValueError):
            server_set(None, {})
        with self.assertRaises(ValueError):
            server_set(13, -1)

    def test_user_configurations(self):
        user_set(1, 'user_configuration', {'value': 12})
        config = user_get(1, 'user_configuration')
        self.assertEqual(config.key, 'user_configuration')
        self.assertEqual(config.data, {'value': 12})
        self.assertEqual(config.user_pk, 1)

    def test_invalid_user_configurations(self):
        with self.assertRaises(ValueError):
            user_set(1, 'user_configuration', 1)
        with self.assertRaises(ValueError):
            user_set(0, 'user_configuration', {})
        with self.assertRaises(ValueError):
            user_set(None, 'user_configuration', {})
        with self.assertRaises(ValueError):
            user_set(1, 13, {})

    def test_non_existent_key(self):
        configuration = user_get(1, 'non-existent-key')
        self.assertIsNone(configuration)
        configuration = server_get('non-existent-server-key')
        self.assertIsNone(configuration)
