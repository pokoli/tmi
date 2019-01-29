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

__all__ = ['Party']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
_YEAR = datetime.datetime.now().year

class Party(ModelSQL, ModelView):
    __name__ = 'party.party'

    es_lider = fields.Boolean(
        'Lider',)
    sexo = fields.Selection([
    	('F', 'Femenino'),
    	('M', 'Masculino'),
		], 'Sexo')
    edad = fields.Char('Edad')
    # pendiente de hacer 
    #gp = fields.Function(fields.Many2One('disc.gp','Grupo de Esperanza'),
    #	'get_gp')
    gps = fields.One2Many('disc.gp','lider',
        'Grupos de Esperanza',
        states={'invisible': Not(Bool(Eval('es_lider')))},)

    #@classmethod
    #def get_gp(cls, types, name):
    #    pool = Pool()
    #    Gp = pool.get('disc.gp')
    #    if gps:
    #    	for gp in gps: 


