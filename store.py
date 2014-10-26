from collections import Iterable
from datetime import datetime

class OperationError(Exception):
    pass

class OutOfStockError(OperationError):
    pass

class PriceMismatchError(OperationError):
    pass

class ItemUnknownError(OperationError):
    pass

# return [lower, upper) n seq
def slice_monotonic_sequence(seq, lower, upper, characteristic):
    def bisect(s, t, u, cp):
        while True:
            if s + 1 >= t:
                return s
            m = int((s + t) / 2)
            if cp(characteristic(seq[m]), u):
                s = m
            else:
                t = m

    if characteristic(seq[len(seq) - 1]) < lower:
        return []
    if characteristic(seq[0]) >= upper:
        return []

    ll = bisect(0, len(seq), lower, lambda x, y: x < y)
    if characteristic(seq[ll]) < lower:
        ll += 1
    uu = bisect(0, len(seq), upper, lambda x, y: x <= y)
    if characteristic(seq[uu]) <= upper:
        uu += 1

    return seq[ll: uu]

def generate_statistics(records):
    res = {}
    for r in records:
        i = r.item
        if not i in res:
            res[i] = Statistic(i)
        res[i].count += r.count
        res[i].total += r.count * i.price
    return res

def find_between_dates(records_seq, begin, end):
    return slice_monotonic_sequence(records_seq, begin, end, lambda x: x.dt)

class Item:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __repr__(self):
        return 'Item(%r, %r)' % (self.name, self.price)

class ItemRecord:
    def __init__(self, item, count, dt):
        self.item = item
        self.count = count
        self.dt = dt

class SalesRecord(ItemRecord):
    def __repr__(self):
        return 'SalesRecord(%r, %r, %r)' % (self.item, self.count, self.dt)

class StockRecord(ItemRecord):
    def __repr__(self):
        return 'StockRecord(%r, %r, %r)' % (self.item, self.count, self.dt)

class Statistic:
    def __init__(self, item, count = 0):
        self.item = item
        self.count = count
        self.total = item.price * count

    def __repr__(self):
        return 'Statistic(%r, %r)' % (self.item, self.count)

class Store:
    def __init__(self):
        self._total = 0
        self._items = {}
        self._statistics = {}
        self._stock_records = []
        self._sales_records = []

    def new_statistic(self, item):
        self._statistics[item] = Statistic(item)

    def update_statistic(self, item, count):
        self._statistics[item].count += count
        self._statistics[item].total += count * item.price
        self._total += count * item.price

    def add_item(self, name, price):
        if not isinstance(name, str):
            raise TypeError('An item\' s name must be a str')
        try:
            i = self._items[name]
            if i.price != price:
                raise PriceMismatchError()
        except KeyError:
            i = self._items[name] = Item(name, price)
            self.new_statistic(i)
        return i

    def find_item(self, name):
        if not isinstance(name, str):
            raise TypeError('An item\' s name must be a str')
        try:
            i = self._items[name]
        except KeyError:
            raise ItemUnknownError()
        return i

    def stock(self, name, count, price):
        i = self.add_item(name, price)
        self._stock_records.append(StockRecord(i, count, datetime.now()))
        self.update_statistic(i, count)

    def sell(self, name, count):
        i = self.find_item(name)
        if self._statistics[i].count < count:
            raise OutOfStockError()
        self._sales_records.append(SalesRecord(i, count, datetime.now()))
        self.update_statistic(i, -count)

    def total(self):
        return self._total

    def statistic(self, names = None):
        if names == None:
            return self._statistics.itervalues()
        elif isinstance(names, str):
            i = self.find_item(names)
            return self._statistics[i]
        elif isinstance(names, Iterable):
            return (d[self.find_item(i)] for i in names)
        else:
            raise TypeError('Name(s) for item statistic must be str or sequence of str')

    def stock_history_over_period(self, begin = datetime(1, 1, 1), end = datetime(9999, 12, 31, 23, 59, 59)):
        return find_between_dates(self._stock_records, begin, end)

    def sales_history_over_period(self, begin = datetime(1, 1, 1), end = datetime(9999, 12, 31, 23, 59, 59)):
        return find_between_dates(self._sales_records, begin, end)

    def stock_statistics_over_period(self, begin = datetime(1, 1, 1), end = datetime(9999, 12, 31, 23, 59, 59)):
        return generate_statistics(self.stock_history_over_period(begin, end))

    def sales_statistics_over_period(self, begin = datetime(1, 1, 1), end = datetime(9999, 12, 31, 23, 59, 59)):
        return generate_statistics(self.sales_history_over_period(begin, end))

