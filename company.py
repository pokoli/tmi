# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal, ROUND_DOWN

from sql.aggregate import Sum
from sql.conditionals import Coalesce

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import If, Eval, Bool, PYSONEncoder, Date

from trytond.tools import grouped_slice, reduce_ids
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateAction, StateTransition, \
    StateReport, Button

from datetime import datetime

__all__ = ['Company']

class Company(ModelSQL, ModelView):
    'Company'
    __name__ = 'company.company'

    type = fields.Selection( 
        [
        ('conference','Conference'),
        ('division','Division'),
        ('union','Union'),
        ('field','Field'),
        ('zone','Zone'),
        ('district','District'),
        ]
        ,'Type', 
        required=True,
        sort=False)