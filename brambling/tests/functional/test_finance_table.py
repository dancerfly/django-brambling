from django.test import TestCase

from brambling.views.utils import FinanceTable
from brambling.tests.factories import (TransactionFactory, EventFactory,
                                       PersonFactory, OrderFactory)


class FinanceTableTestCase(TestCase):

    def setUp(self):
        self.order = OrderFactory(code='TK421')
        self.event = EventFactory()
        self.transactions = [TransactionFactory(order=self.order)]
        self.table = FinanceTable(self.event, self.transactions)

    def test_headers(self):
        self.assertEqual(len(self.table.headers()), 8)

    def test_row_count(self):
        self.assertEqual(len(list(self.table.get_rows())), 1)

    def test_inclusion_of_header_row(self):
        self.assertEqual(len(list(self.table.get_rows(include_headers=True))), 2)

    def test_transaction_created_by_blank(self):
        name = self.table.created_by_name(TransactionFactory())
        self.assertEqual('', name)

    def test_transaction_created_by_name(self):
        creator = PersonFactory(first_name='Leia', last_name='Organa')
        created_transaction = TransactionFactory(created_by=creator)
        name = self.table.created_by_name(created_transaction)
        self.assertEqual('Leia Organa', name)

    def test_transaction_with_order_code(self):
        code = self.table.order_code(self.transactions[0])
        self.assertEqual('TK421', code)

    def test_transaction_without_order(self):
        transaction = TransactionFactory(order=None)
        code = self.table.order_code(transaction)
        self.assertEqual('', code)

    def test_transaction_as_cell_row(self):
        row = list(self.table.get_rows())[0]
        self.assertEqual(len(row), 8)
        self.assertEqual(row[4].field, 'order')
        self.assertEqual(row[4].value, 'TK421')
