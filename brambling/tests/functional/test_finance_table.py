from django.test import TestCase

from brambling.utils.model_tables import Cell
from brambling.views.utils import FinanceTable
from brambling.tests.factories import TransactionFactory, EventFactory, \
    PersonFactory, OrderFactory


class FinanceTableTestCase(TestCase):

    def setUp(self):
        self.order = OrderFactory(code='TK421')
        self.event = EventFactory()
        self.transactions = [TransactionFactory(order=self.order)]

    def test_assert_true(self):
        assert True

    def test_headers(self):
        table = FinanceTable(self.event, self.transactions)
        self.assertEqual(len(table.headers()), 8)

    def test_plaintext_row_count(self):
        # headers are considered part of the plaintext table
        table = FinanceTable(self.event, self.transactions)
        self.assertEqual(len(list(table.plaintext_rows())), 2)

    def test_cell_row_count(self):
        # cells do not include headers
        table = FinanceTable(self.event, self.transactions)
        self.assertEqual(len(list(table.cell_rows())), 1)

    def test_transaction_created_by_blank(self):
        name = FinanceTable.created_by_name(TransactionFactory())
        self.assertEqual('', name)

    def test_transaction_created_by_name(self):
        creator = PersonFactory(given_name='Leia', surname='Organa')
        created_transaction = TransactionFactory(created_by=creator)
        name = FinanceTable.created_by_name(created_transaction)
        self.assertEqual('Leia Organa', name)

    def test_transaction_with_order_code(self):
        code = FinanceTable.order_code(self.transactions[0])
        self.assertEqual('TK421', code)

    def test_transaction_without_order(self):
        transaction = TransactionFactory(order=None)
        code = FinanceTable.order_code(transaction)
        self.assertEqual('', code)

    def test_transaction_as_cell_row(self):
        table = FinanceTable(self.event, self.transactions)
        row = list(table.cell_rows())[0]
        self.assertEqual(len(row), 8)
        self.assertEqual(row[4].field, 'order')
        self.assertEqual(row[4].value, 'TK421')
