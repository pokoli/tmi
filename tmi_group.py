# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
import datetime
import operator
from functools import wraps

from dateutil.relativedelta import relativedelta
from sql import Column, Null, Window, Literal
from sql.aggregate import Sum, Max
from sql.conditionals import Coalesce, Case

from trytond.model import (
    ModelView, ModelSQL, DeactivableMixin, fields, Unique, sequence_ordered)
from trytond.wizard import Wizard, StateView, StateAction, StateTransition, \
    Button
from trytond.report import Report
from trytond.tools import reduce_ids, grouped_slice
from trytond.pyson import Eval, If, PYSONEncoder, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond import backend

__all__ = ['TmiMetaGroup',
    'TmiGroup']

class TmiMetaGroup(sequence_ordered(), ModelSQL, ModelView):
    'Account Type'
    __name__ = 'tmi.meta.group'

    name = fields.Char('Name', size=None, required=True)
    parent = fields.Many2One('tmi.meta.group', 'Parent',
        ondelete="RESTRICT",
        domain=[
            ('company', '=', Eval('company')),
            ],
        depends=['company'])
    childs = fields.One2Many('tmi.meta.group', 'parent', 'Children',
        domain=[
            ('company', '=', Eval('company')),
        ],
        depends=['company'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
            'get_currency_digits')
    tithe = fields.Function(fields.Numeric('Tithe',
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits']),
        'get_amount')
    type = fields.Selection('tmi.group',
        [
        ('conference','Conference'),
        ('division','Division'),
        ('union','Union'),
        ('field','Field'),
        ('zona','Zone'),
        ('district','District'),
        ('church','Church'),
        ('small_group','Small Group'),
        ]
        ,'Type')
    company = fields.Many2One('company.company', 'Company', required=True,
            ondelete="RESTRICT")

    def get_currency_digits(self, name):
        return self.company.currency.digits

    @classmethod
    def get_amount(cls, types, name):
        pool = Pool()
        Group = pool.get('tmi.group')

        res = {}
        for type_ in types:
            res[type_.id] = Decimal('0.0')

        childs = cls.search([
                ('parent', 'child_of', [t.id for t in types]),
                ])
        meta_sum = {}
        for type_ in childs:
            meta_sum[type_.id] = Decimal('0.0')

        groups = Group.search([
                ('meta', 'in', [t.id for t in childs]),
                ])
        for group in groups:
            meta_sum[group.meta.id] += (group.name)

        for type_ in types:
            childs = cls.search([
                    ('parent', 'child_of', [type_.id]),
                    ])
            for child in childs:
                res[type_.id] += type_sum[child.id]
            exp = Decimal(str(10.0 ** -type_.currency_digits))
            res[type_.id] = res[type_.id].quantize(exp)
            if type_.display_balance == 'credit-debit':
                res[type_.id] = - res[type_.id]
        return res


class TmiGroup(ModelView, ModelSQL):
    'TMI Group'
    __name__ = 'tmi.group'

    name = fields.Char('Group',required=True)
    code = fields.Char('Code')
    meta = fields.Many2One('tmi.meta.group', 'Meta', ondelete="RESTRICT",
        required=True, 
        domain=[
            ('company', '=', Eval('company')),
            ], depends=['company'])
    type = fields.Selection('tmi.group',
        [
        ('church','Church'),
        ('small_group','Small Group'),
        ]
        ,'Type')
    company = fields.Many2One('company.company', 'Company', required=True,
            ondelete="RESTRICT")
    currency = fields.Function(fields.Many2One('currency.currency',
        'Currency'), 'get_currency')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
    tithe = fields.Function(fields.Numeric('Tithe',
        digits=(16,Eval('currency_digits',2))), 'get_amount')
    baptism = fields.Function(fields.Numeric('Baptism',
        digits=(16,Eval('currency_digits',2))), 'get_amount')
    church_planting = fields.Function(fields.Numeric('Church Planting',
        digits=(16,Eval('currency_digits',2))), 'get_amount')
    gathering = fields.Function(fields.Numeric('Gathering',
        digits=(16,Eval('currency_digits',2))), 'get_amount')
    small_group = fields.Function(fields.Numeric('Small Group',
        digits=(16,Eval('currency_digits',2))), 'get_amount')
    organizing_church = fields.Function(fields.Numeric('Organizing Church',
        digits=(16,Eval('currency_digits',2))), 'get_amount')
    praise_thanksgiving = fields.Function(fields.Numeric('Praise and Thanksgiving', 
        digits=(16,Eval('currency_digits',2))), 'get_amount')
    offering = fields.Function(fields.Numeric('Offering',
        digits=(16,Eval('currency_digits',2))), 'get_amount')


    @classmethod
    def __setup__(cls):
        super(TmiGroup, cls).__setup__()
        cls._order.insert(0, ('name', 'ASC'))

    def get_rec_name(self, name):
        if self.code:
            return self.type + ' - ' + self.name + ' - ' + self.code 
        else:
            return self.type + ' - ' + self.name

    def get_currency(self, name):
        return self.company.currency.id

    def get_currency_digits(self, name):
        return self.company.currency.digits

    @classmethod
    def get_amount(cls, groups, names):
        '''
        Function to compute tithe, baptism, church_planting, gathering, small_group, 
        organizing_church, praise_thanksgiving, offering for TMI Group.        
        '''
        pool = Pool()
        MoveLine = pool.get('tmi.move.line')
        cursor = Transaction().connection.cursor()

        result = {}
        ids = [a.id for a in groups]
        for name in names:
            if name not in {'tithe', 'baptism', 'church_planting', \
                    'gathering','small_group', 'organizing_church', \
                    'praise_thanksgiving', 'offering'}:
                raise ValueError('Unknown name: %s' % name)
            result[name] = dict((i, Decimal(0)) for i in ids)

        table = cls.__table__()
        line = MoveLine.__table__()
        line_query = MoveLine.query_get(line)
        columns = [table.id]
        for name in names:
            columns.append(Sum(Coalesce(Column(line, name), 0)))
        for sub_ids in grouped_slice(ids):
            red_sql = reduce_ids(table.id, sub_ids)
            cursor.execute(*table.join(line, 'LEFT',
                    condition=line.group == table.id
                    ).select(*columns,
                    where=red_sql & line_query,
                    group_by=table.id))
            for row in cursor.fetchall():
                group_id = row[0]
                for i, name in enumerate(names, 1):
                    # SQLite uses float for SUM
                    if not isinstance(row[i], Decimal):
                        result[name][group_id] = Decimal(str(row[i]))
                    else:
                        result[name][group_id] = row[i]
        for group in groups:
            for name in names:
                exp = Decimal(str(10.0 ** -group.currency_digits))
                result[name][group.id] = (
                    result[name][group.id].quantize(exp))
        return result
