#! -*- coding: utf8 -*-
# This file is part of the sale_pos module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

import datetime
from decimal import Decimal
from trytond.model import ModelView, fields, ModelSQL
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Bool, Eval, Not
from datetime import timedelta, date 

__all__ = ['Union']
__metaclass__ = PoolMeta 

class Union(ModelView, ModelSQL):
    'Union'
    __name__ = 'disc.union'
    name = fields.Char('Union')
    division = fields.Many2One('disc.division','Division')
    pastor = fields.Many2One('res.user','Pastor',)
    campos = fields.One2Many('disc.campo','union',
        'Campos')

    @classmethod
    def __setup__(cls):
        super(Union, cls).__setup__()
        cls._order.insert(0, ('name', 'ASC'))
