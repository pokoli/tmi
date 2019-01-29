#! -*- coding: utf8 -*-
# This file is part of the sale_pos module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
# Josias

import datetime
from decimal import Decimal
from trytond.model import ModelView, fields, ModelSQL
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Bool, Eval, Not
from datetime import timedelta, date 

__all__ = ['Campo']
__metaclass__ = PoolMeta

class Campo(ModelView, ModelSQL):
    'Campo'
    __name__ = 'disc.campo'
    name = fields.Char('Campo',required=True)
    union = fields.Many2One('disc.union', 'Union',
    	required=True)
    pastor = fields.Many2One('res.user','Pastor',
    	required=True)
    zonas = fields.One2Many('disc.zona','campo',
        'Zonas')    

    @classmethod
    def __setup__(cls):
        super(Campo, cls).__setup__()
        cls._order.insert(0, ('name', 'ASC'))
        cls._error_messages.update({
                'delete_records': 'Por control interno no puedes borrar'  \
                ' registros.',
                })

    @classmethod
    def delete(cls, records):
        cls.raise_user_error('delete_records')
