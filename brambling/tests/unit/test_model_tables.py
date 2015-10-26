# encoding: utf-8
from unittest import TestCase

from django.utils.encoding import force_text, force_bytes

from brambling.utils.model_tables import Row, Cell


class PostalCodeTestCase(TestCase):
    def test_iterable(self):
        data = [
            ('id', 5),
            ('name', 'Phil'),
        ]
        row = Row(data)
        result = [(cell.field, cell.value) for cell in row]
        self.assertEqual(result, data)

    def test_getitem__string(self):
        data = [
            ('id', 5),
            ('name', 'Phil'),
        ]
        row = Row(data)
        id_cell = row['id']
        name_cell = row['name']
        self.assertEqual(id_cell.field, 'id')
        self.assertEqual(id_cell.value, 5)
        self.assertEqual(name_cell.field, 'name')
        self.assertEqual(name_cell.value, 'Phil')

    def test_getitem__int(self):
        data = [
            ('id', 5),
            ('name', 'Phil'),
        ]
        row = Row(data)
        id_cell = row[0]
        name_cell = row[1]
        self.assertEqual(id_cell.field, 'id')
        self.assertEqual(id_cell.value, 5)
        self.assertEqual(name_cell.field, 'name')
        self.assertEqual(name_cell.value, 'Phil')


class CellTestCase(TestCase):
    def test_cell_to_text(self):
        value = u'vålue'
        cell = Cell('field', value)
        self.assertEqual(force_text(cell), value)

    def test_cell_to_bytes(self):
        value = force_bytes(u'vålue')
        cell = Cell('field', value)
        self.assertEqual(force_bytes(cell), value)
