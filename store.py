#!/usr/bin/python
"""
This module defines class Store and several utilities.
"""
from collections import Iterable
from datetime import datetime

class OperationError(Exception):
    """
    Base class for all logical errors that may occur when modifying stocks.
    """
    pass

class OutOfStockError(OperationError):
    """Raised when the item to be sold is out of stock."""
    pass

class PriceMismatchError(OperationError):
    """
    Raised when trying to stock an item for the second time with a
    different price.
    """
    pass

class ItemUnknownError(OperationError):
    """
    Raised when trying to sell or get the history of an item that has not
    been bought yet.
    """
    pass

def slice_monotonic_sequence(seq, lower, upper, characteristic):
    """
    Slices from a monotonic sequence its consecutive subsquence
    whose elements' characteristics is large than or equal to the
    lower bound and less than the upper bound.

    Args:
        seq: A sequence whose's elements' characteristics are monotonic
        lower: The lower bound of desired subsequence (including).
        upper: The upper bound of desired subsequence (excluding).
        characteristic: A function such that characteristic(seq) increases.
            Lower and upper are compared to that.

    Returns:
        A consecutive subsequence with elements' characteristics between
            lower (including) and upper (excluding)
    """
    def bisect(needle, cmpr):
        """
        Bisect search in seq.

        Args:
            needle: What to look for.
            cmpr: The compare function, should be < or <=.

        Returns:
            0 or the position of the last element whose characteristic
            compares true to needle.
        """
        start, end = 0, len(seq)
        while True:
            if start + 1 >= end:
                return start
            mid = int((start + end) / 2)
            if cmpr(characteristic(seq[mid]), needle):
                start = mid
            else:
                end = mid

    if characteristic(seq[len(seq) - 1]) < lower:
        return []
    if characteristic(seq[0]) >= upper:
        return []

    llower = bisect(lower, lambda x, y: x < y)
    if characteristic(seq[llower]) < lower:
        llower += 1
    uupper = bisect(upper, lambda x, y: x <= y)
    if characteristic(seq[uupper]) <= upper:
        uupper += 1

    return seq[llower: uupper]

def generate_statistics(records):
    """
    Calculate statistics for each item appeared in a sequence of
    records. Statistic includes item count and total price.

    Args:
        records: The records to sum up.

    Returns:
        A dict mapping items to the corresponding statistics.
    """
    res = {}
    for rec in records:
        i = rec.item
        if not i in res:
            res[i] = Statistic(i)
        res[i].count += rec.count
    return res

def find_between_dates(records_seq, begin, end):
    """
    Find the records whose date is between begin (including) and
    end (excluding) in a sequence of records sorted by date.

    Args:
        records_seq: A sequence of records whose dates monotonically
            increase.
        begin: The lower bound (including) of dates of the result.
        end: The upper bound (excluding) of dates of the result.

    Returns:
        Records in records_seq with dates between begin and end.
    """
    return slice_monotonic_sequence(records_seq, begin, end, lambda x: x.date)

class Item:
    """An item, whose name and price are immutable."""
    def __init__(self, name, price):
        self._name = name
        self._price = price

    @property
    def name(self):
        """property name"""
        return self._name

    @property
    def price(self):
        """property price"""
        return self._price

    def __repr__(self):
        return 'Item(%r, %r)' % (self.name, self.price)

class ItemRecord:
    """
    Base class for a record. A record contains the item, its count and
    the date when the event happend. This class is Immutable.
    """
    def __init__(self, item, count, date):
        self._item = item
        self._count = count
        self._date = date

    @property
    def item(self):
        """property item"""
        return self._item

    @property
    def count(self):
        """property count"""
        return self._count

    @property
    def date(self):
        """property date"""
        return self._date

class SalesRecord(ItemRecord):
    """A sales record."""
    def __repr__(self):
        return 'SalesRecord(%r, %r, %r)' % (self.item, self.count, self.date)

class StockRecord(ItemRecord):
    """A stock record."""
    def __repr__(self):
        return 'StockRecord(%r, %r, %r)' % (self.item, self.count, self.date)

class Statistic:
    """For holding an item's count and total value."""
    def __init__(self, item, count=0):
        self._item = item
        self.count = count

    @property
    def total(self):
        """property for total value"""
        return self._item * self.count

    @property
    def item(self):
        """property item"""
        return self._item

    def __repr__(self):
        return 'Statistic(%r, %r)' % (self.item, self.count)

class Store:
    """
    The class simulating a store's stock and sales operations.
    It supports adding a stock or sales record with current
    system timestamp, getting stock statistics, looking for
    records within a period and summzrizing records within a
    period.
    To speed up, records are stored in ascending order by
    timestamp, thus admitting binary search. Stock statistics
    are cached and updated when adding a new record, allowing
    quick look-up.
    """
    def __init__(self):
        self._total = 0
        self._items = {}
        self._statistics = {}
        self._stock_records = []
        self._sales_records = []

    def new_statistic(self, item):
        """
        Internal.
        Build statistic structure for a new item.

        Args:
            self: Store instance.
            item: The item whose statistic is to be built.
        """
        self._statistics[item] = Statistic(item)

    def update_statistic(self, item, dcount):
        """
        Internal.
        Maintain an item's statistic after a sales or stock
        event happened.

        Args:
            self: Store instance.
            item: The item bought or sold.
            dcount: The number/amount of item bought or sold,
                positive for buying and negative for selling.
        """
        self._statistics[item].count += dcount

    def add_item(self, name, price):
        """
        Internal.
        Adding an item to the list of known items, and return the
        item object. If an item with the same name already exists
        and their price matches, the existing item is returned. If
        their price are different, PriceMismatchError is raised.

        Args:
            self: Store instance.
            name: Name for new item.
            price: Price for new item.

        Returns:
            An item with name and price specified in arguments. If
            no item with such name is known before, a new item is
            returned. Otherwise item with the same name is returned
            if their price matches.

        Raises:
            PriceMismatchError: If an item with the same name but
                different price already exists.
        """
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
        """
        Internal.
        Find an item by name. If no item with such name exists,
        ItemUnknownError is raised.

        Args:
            self: Stock instance.
            name: Looking for an item with this name.

        Returns:
            An item with name specified in arguments.

        Raises:
            ItemUnknownError if there is no item with this name.
        """
        if not isinstance(name, str):
            raise TypeError('An item\' s name must be a str')
        try:
            i = self._items[name]
        except KeyError:
            raise ItemUnknownError()
        return i

<<<<<<< Updated upstream
    def stock(self, name, count, price):
=======
    def stock(self, name, count, price=None):
>>>>>>> Stashed changes
        """
        Add a stock record.

        Args:
            name: Name of the item.
            count: Bought how many/much.
            price: Price.

        Raises:
            PriceMismatchError: If a stock record with same name
                but different price already exists.
        """
<<<<<<< Updated upstream
        i = self.add_item(name, price)
=======
        if price == None:
            i = self.find_item(name)
        else:
            i = self.add_item(name, price)
>>>>>>> Stashed changes
        self._stock_records.append(StockRecord(i, count, datetime.now()))
        self.update_statistic(i, count)

    def sell(self, name, count):
        """
        Add a sales record.

        Args:
            self: Store instance.
            name: Name of the item.
            count: Sold how many/much.

        Raises:
            OutOfStockError: If count is larger than the number/amount
                in stock.
            ItemUnknownError: If there's no item with name as in arguments.
        """
        i = self.find_item(name)
        if self._statistics[i].count < count:
            raise OutOfStockError()
        self._sales_records.append(SalesRecord(i, count, datetime.now()))
        self.update_statistic(i, -count)

    def total(self):
        """
        The total value of all items in stock.

        Args:
            self: Store instance.

        Returns:
            The total value of all items in stock.
        """
        return self._total

    def statistic(self, names=None):
        """
        Get statistics (total count and value) of a/some/all items.

        Args:
            self: Store instance.
            names: If None, return all statistics.
                If a string, return statistic of the item named
                that.
                If a sequence of strings, return statistics of
                them.

        Returns:
            A statistic of item with the specific name if names is
            a string. Or a list of statistics if names is none
            or a sequence of names.

        Raises:
            ItemUnknownError: If name or any string in name is
                not a name of a known item.
        """
        if names == None:
            return self._statistics.values()
        elif isinstance(names, str):
            i = self.find_item(names)
            return self._statistics[i]
        elif isinstance(names, Iterable):
            return (self._statistics[self.find_item(i)] for i in names)
        else:
            raise TypeError('Name(s) for item statistic must be' +\
                    ' str or sequence of str')

    def stock_history_over_period(self, begin=datetime(1, 1, 1),\
            end=datetime(9999, 12, 31, 23, 59, 59)):
        """
        Return the stock records over a period.

        Args:
            self: Store instance.
            begin: beginning of the period.
            end: end of the period.

        Returns:
            A list of stock records over that period.
        """
        return find_between_dates(self._stock_records, begin, end)

    def sales_history_over_period(self, begin=datetime(1, 1, 1),\
            end=datetime(9999, 12, 31, 23, 59, 59)):
        """
        Return the sales records over a period.

        Args:
            self: Store instance.
            begin: beginning of the period.
            end: end of the period.

        Returns:
            A list of sales records over that period.
        """
        return find_between_dates(self._sales_records, begin, end)

    def stock_statistics_over_period(self, begin=datetime(1, 1, 1),\
            end=datetime(9999, 12, 31, 23, 59, 59)):
        """
        Return the stock statistics over a period.

        Args:
            self: Store instance.
            begin: beginning of the period.
            end: end of the period.

        Returns:
            A list of sales records over that period.
        """
        return generate_statistics(self.stock_history_over_period(begin, end))

    def sales_statistics_over_period(self, begin=datetime(1, 1, 1),\
            end=datetime(9999, 12, 31, 23, 59, 59)):
        """
        Return the sales statistics over a period.

        Args:
            self: Store instance.
            begin: beginning of the period.
            end: end of the period.

        Returns:
            A list of sales records over that period.
        """
        return generate_statistics(self.sales_history_over_period(begin, end))

