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

__all__ = ['Iglesia']
__metaclass__ = PoolMeta

class Iglesia(ModelView, ModelSQL):
    'Iglesia'
    __name__ = 'disc.iglesia'
    name = fields.Char('Iglesia', required=True)
    distrito = fields.Many2One('disc.distrito', 'Distrito',
    	required=True)
    pastor = fields.Many2One('res.user','Pastor',
    	required=True)
    gps = fields.One2Many('disc.gp','iglesia','Grupos de Esperanza')
    active = fields.Boolean('Activo')

    @classmethod
    def __setup__(cls): 
        super(Iglesia, cls).__setup__()
        cls._order.insert(0, ('name', 'ASC'))
        cls._error_messages.update({
                'delete_records': 'Por control interno no puedes borrar'  \
                ' registros.',
                })

    @classmethod
    def delete(cls, records):
        cls.raise_user_error('delete_records')