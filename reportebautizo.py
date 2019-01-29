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

__all__ = ['ReporteBautizo']
__metaclass__ = PoolMeta

class ReporteBautizo(ModelView, ModelSQL):
    'Reporte Detalle'
    __name__ = 'disc.reporte.linea'

    reporte = fields.Many2One('disc.reporte',
        'Reporte',)
    gp = fields.Many2One('disc.gp','Grupo de Esperanza', required=True)
    cantidad = fields.Numeric('Bautismos', required=True)
    comentario = fields.Text('Comentario')
    lider = fields.Many2One('party.party', 'Lider')
    iglesia = fields.Many2One('disc.iglesia', 'Iglesia')
    distrito = fields.Many2One('disc.distrito', 'Distrito')
    zona = fields.Many2One('disc.zona', 'Zona')
    campo = fields.Many2One('disc.campo', 'Campo')
    union = fields.Many2One('disc.union', 'Union')
    pastor = fields.Many2One('res.user', 'Pastor')
    mes = fields.Char('Mes')

    @classmethod
    def default_cantidad(cls):
        return 0 

        

