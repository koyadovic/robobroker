from shared.domain.tools import serializations
import unittest
import json


def my_function():
    pass


class SerializationTest(unittest.TestCase):

    def test_serialization_deserialization(self):
        serialized = serializations.serialize_function(my_function)
        deserialized = serializations.deserialize_function(serialized)
        self.assertEqual(deserialized, my_function)

    def test_json_serialization(self):
        data = {'func': serializations.serialize_function(my_function)}
        json_data = json.dumps(data)
        restored_data = json.loads(json_data)
        restored_my_function = serializations.deserialize_function(restored_data['func'])
        self.assertEqual(restored_my_function, my_function)
