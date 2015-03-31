from unittest import TestCase

from brambling.utils.model_tables import Row


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
