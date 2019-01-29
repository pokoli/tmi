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

__all__ = ['User']
__metaclass__ = PoolMeta 

class User(ModelSQL, ModelView):
    "User"
    __name__ = "res.user"

    party = fields.Many2One('party.party', 'Pastor',
    	)
    iglesias = fields.One2Many('disc.iglesia','pastor', 
        'Iglesias',
        )

    @fields.depends('party')
    def on_change_party(self):
    	if self.party == None: 
    		self.name = ''
    	else:
    		self.name = self.party.name 
