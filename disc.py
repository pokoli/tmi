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

def allsundays(year):
    list = []
    d = date(year, 1, 1)                    # January 1st
    f = date(year, 1, 1)                    # January 1st
    d += timedelta( (5 - d.weekday() + 7) % 7)  # First Sunday
    f += timedelta( f.weekday() + 6)  # First Friday
    while d.year == year:
        s = d.isocalendar()[1]
        etiqueta = 'Semana #: '+str(s) + ' del '+ unicode(d)+' al ' +unicode(f)
        list.append( (etiqueta, unicode(f) ) ) 
        d += timedelta(days = 7)
        f += timedelta(days = 7)
    return list 

#for d in allsundays(2010):
#   print d

__all__ = ['Asociacion', 'Campo','Zona','Distrito', 'Iglesia', 
            'Gp','Party','Reporte','ReporteBautizo']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
_YEAR = datetime.datetime.now().year


class Party(ModelSQL, ModelView):
    __name__ = 'party.party'
    es_pastor = fields.Boolean(
        'Pastor',)
    es_lider = fields.Boolean(
        'Lider',)
    iglesias = fields.One2Many('disc.iglesia','pastor', 
        'Iglesias',
        states={'invisible': Not(Bool(Eval('es_pastor')))},
        )
    gps = fields.One2Many('disc.gp','lider',
        'GPs',
        states={'invisible': Not(Bool(Eval('es_lider')))},)

class Asociacion(ModelView, ModelSQL):
    'Asociacion'
    __name__ = 'disc.asociacion'
    name = fields.Char('Nombre')
    pastor = fields.Many2One('party.party','Pastor',
        domain=[('es_pastor', '=', True)])

class Campo(ModelView, ModelSQL):
    'Campo'
    __name__ = 'disc.campo'
    asociacion = fields.Many2One('disc.asociacion', 'Asociacion')
    name = fields.Char('Nombre')
    pastor = fields.Many2One('party.party','Pastor',
        domain=[('es_pastor', '=', True)])

class Zona(ModelView, ModelSQL):
    'Zona'
    __name__ = 'disc.zona'
    name = fields.Char('Nombre')
    campo = fields.Many2One('disc.campo', 'Campo')
    pastor = fields.Many2One('party.party','Pastor',
        domain=[('es_pastor', '=', True)])

class Distrito(ModelView, ModelSQL):
    'Distrito'
    __name__ = 'disc.distrito'
    name = fields.Char('Nombre')
    zona = fields.Many2One('disc.zona', 'Zona')
    pastor = fields.Many2One('party.party','Pastor',
        domain=[('es_pastor', '=', True)])

class Iglesia(ModelView, ModelSQL):
    'Iglesia'
    __name__ = 'disc.iglesia'
    name = fields.Char('Nombre')
    distrito = fields.Many2One('disc.distrito', 'Distrito')
    pastor = fields.Many2One('party.party','Pastor',
        domain=[('es_pastor', '=', True)])

class Gp(ModelView, ModelSQL):
    'Grupo pequeno'
    __name__ = 'disc.gp'
    name = fields.Char('Nombre')
    iglesia = fields.Many2One('disc.iglesia', 'Iglesia')
    lider = fields.Many2One('party.party','Lider',
        domain=[('es_lider', '=', True)])

class Reporte(ModelView, ModelSQL):
    'Reporte'
    __name__ = 'disc.reporte'

    pastor = fields.Many2One('party.party','Pastor',
        domain=[('es_pastor', '=', True)])
    iglesia = fields.Many2One('disc.iglesia', 'Iglesia')
    semana = fields.Selection(allsundays(_YEAR), 'Semana')
    bautizos = fields.One2Many('disc.reporte.bautizo',
        'reporte','Bautizos')
    notas = fields.Text('Notas')

    '''@fields.depends('iglesia', 'bautizos')
    def on_change_iglesia(self):
        pool = Pool()
        Iglesia = pool.get('disc.iglesia')

        res = {}
        res['bautizos'] = {}
        if self.bautizos:
            res['bautizos']['remove'] = [x['id'] for x in self.bautizos]
        if not self.iglesia:
            print res
            return res

        id = self.iglesia.id 
        print 'id' + str(id) 
        gps = Iglesia.search([('id', '=', id)])
        
        if gps: 
            for gp in gps:
                bautizo_line = {
                    'gp': gp.id,
                }
                res['bautizos'].setdefault('add', []).append((0, bautizo_line))
        return res'''

'''class ReporteBautizo(ModelView, ModelSQL):
    'Reporte Detalle'
    __name__ = 'disc.reporte.bautizo'

    reporte = fields.Many2One('disc.reporte',
        'Reporte',)
    gp = fields.Many2One('disc.gp','GP')
    cantidad = fields.Integer('Cantidad')
    comentario = fields.Text('Comentario')'''

'''class ProductLine(ModelView, ModelSQL):
    'Product Line'
    __name__ = 'product.product.line'

    sequence = fields.Integer('Sequence')
    product = fields.Many2One('product.product', 'Product')
    add = fields.Boolean('Add')
    quantity = fields.Numeric('Quantity')
    review = fields.Boolean('Verificar Stock')
    list_price = fields.Numeric('Precio Venta')
    total_stock = fields.Integer('Total Stock')'''

'''class WarehouseStock(ModelView):
    'Warehouse Stock'
    __name__ = 'sale_stock_product_mini.warehouse'
    product = fields.Char('Product')
    lines = fields.One2Many('product.product.line', None, 'Lines')
    warehouse_sale =fields.One2Many('sale.warehouse', 'sale', 'Product by Warehouse', readonly=True)'''

'''@fields.depends('product', 'lines')
    def on_change_product(self):
        pool = Pool()
        Product = pool.get('product.product')
        Location = pool.get('stock.location')
        location = Location.search([('type', '=', 'warehouse')])
        Move = pool.get('stock.move')
        in_s = 0
        stock = 0
        s_total = 0
        stock_total = 0

        res = {}
        res['lines'] = {}
        if self.lines:
            res['lines']['remove'] = [x['id'] for x in self.lines]

        if not self.product:
            return res

        code = self.product+'%'
        name = self.product+'%'

        products = Product.search([('code', 'like', code)])
        if products:
            for product in products:
                stock_total = 0
                for lo in location:
                    in_stock = Move.search_count([('product', '=',  product), ('to_location','=', lo.storage_location)])
                    move = Move.search_count([('product', '=', product), ('from_location','=', lo.storage_location)])
                    s_total = in_stock - move
                    stock_total += s_total
                product_line = {
                    'product': product.id,
                    'total_stock':stock_total,
                }
                res['lines'].setdefault('add', []).append((0, product_line))
        else:
            products = Product.search([('name', 'ilike', name)])
            for product in products:
                stock_total = 0
                for lo in location:
                    in_stock = Move.search_count([('product', '=',  product), ('to_location','=', lo.storage_location)])
                    move = Move.search_count([('product', '=', product), ('from_location','=', lo.storage_location)])

                    s_total = in_stock - move
                    stock_total += s_total
                product_line = {
                    'product': product.id,
                    'total_stock':stock_total,
                }
                res['lines'].setdefault('add', []).append((0, product_line))

        return res'''


'''@fields.depends('lines', 'warehouse_sale', 'product')
    def on_change_lines(self):
        pool = Pool()
        Location = pool.get('stock.location')
        location = Location.search([('type', '=', 'warehouse')])
        Move = pool.get('stock.move')
        stock = 0
        in_s = 0

        changes = {}
        changes['all_list_price'] = {}
        changes['warehouse_sale'] = {}
        changes['lines'] = {}

        if self.warehouse_sale:
            changes['warehouse_sale']['remove'] = [x['id'] for x in self.warehouse_sale]

        cont = 0
        if self.lines:
            for line in self.lines:
                cont += 1
                if line.review == True:
                    result_line = {
                        'review': False,
                        'product': line.product.id,
                        'list_price': line.list_price,
                        'total_stock': line.total_stock,
                        'add': line.add,
                        'quantity': line.quantity,
                    }
                    changes['lines']['remove'] = [line['id']]

                    changes['lines'].setdefault('add', []).append((cont-1, result_line))

                    for lo in location:
                        in_stock = Move.search_count([('product', '=',  line.product), ('to_location','=', lo.storage_location)])
                        move = Move.search_count([('product', '=', line.product), ('from_location','=', lo.storage_location)])

                        s_total = in_stock - move

                        result = {
                            'product': line.product.name,
                            'warehouse': lo.name,
                            'quantity': str(int(s_total)),
                        }
                        stock = 0
                        in_s = 0
                        changes['warehouse_sale'].setdefault('add', []).append((0, result))

        return changes'''
