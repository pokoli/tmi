#! -*- coding: utf8 -*-
# This file is part of the sale_pos module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
# Josias

import datetime 
from decimal import Decimal
from trytond.model import ModelView, fields, ModelSQL, Unique, sequence_ordered
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Bool, Eval, Not
from datetime import timedelta, date 

__all__ = ['Gp']
__metaclass__ = PoolMeta

class Gp(ModelView, ModelSQL):
    'Grupo de Esperanza'
    __name__ = 'disc.gp'
    
    name = fields.Char('Grupo de Esperanza', required=True)
    iglesia = fields.Many2One('disc.iglesia', 'Iglesia')
    lider = fields.Many2One('party.party','Lider',
        domain=[('es_lider', '=', True)],
        required=True)
    code = fields.Char('Codigo',
    	#required=True, 
    	select=True,
        readonly=True, )
    active = fields.Boolean('Activo',)
 
    @classmethod
    def __setup__(cls):
        super(Gp, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints = [
            ('code_uniq', Unique(t, t.code),
             'El codigo de la GP debe ser unico.')
        ]
        cls._order.insert(0, ('name', 'ASC'))
        cls._error_messages.update({
                'delete_records': 'Por control interno no puedes borrar'  \
                ' registros, pero puedes desactivarlos.',
                })

    @classmethod
    def delete(cls, records):
        cls.raise_user_error('delete_records')

    @classmethod
    def default_active(cls):
        return True

    def get_rec_name(self, name):
        if self.name and self.lider and self.iglesia: 
            return self.lider.name #+ ' IG: ' + self.iglesia.name   
        if self.name and self.lider: 
            return self.name + ' - ' +self.lider.name  

    #@classmethod
    #def _new_code(cls, **pattern):
    #    pool = Pool()
    #    Sequence = pool.get('ir.sequence')
    #    Configuration = pool.get('disc.gp.configuration')
    #    config = Configuration(1)
    #    sequence = config.get_multivalue('gp_sequence', **pattern)
    #    if sequence:
    #        return Sequence.get_id(sequence.id)


    #@classmethod
    #def create(cls, vlist):
    #    vlist = [x.copy() for x in vlist]
    #    for values in vlist:
    #        if not values.get('code'):
    #            values['code'] = cls._new_code()
    #            print 'VALUES: ' + str(values['code'])
    #    return super(Gp, cls).create(vlist)

    