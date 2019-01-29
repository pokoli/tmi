#! -*- coding: utf8 -*-
# This file is part of the sale_pos module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

import datetime
from datetime import timedelta, date  
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from trytond.model import ModelStorage, ModelView, fields, ModelSQL, Unique
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Bool, Eval, Not, Id, PYSONEncoder, If, In, Get
from datetime import timedelta, date 
from trytond.transaction import Transaction
from trytond.report import Report
from trytond.wizard import Wizard, StateTransition, StateView, StateAction, \
    StateReport, Button
from sql import Literal
from sql.aggregate import Max, Sum, Min
from sql.conditionals import Coalesce

def numero_mes(numero):
    switcher = {
        0: "Enero",
        1: "Febrero",
        2: "Marzo",
        3: "Abril",
        4: "Mayo",
        5: "Junio",
        6: "Julio",
        7: "Agosto",
        8: "Septiembre",
        9: "Octubre",
        10: "Noviembre",
        11: "Diciembre",
    }
    return switcher.get(numero, "ninguno")

def mes_numero(mes):
    mes = mes.replace(' ','')
    switcher = {
        "Enero":1,
        "Febrero":2,
        "Marzo":3,
        "Abril":4,
        "Mayo":5,
        "Junio":6,
        "Julio":7,
        "Agosto":8,
        "Septiembre":9,
        "Octubre":10,
        "Noviembre":11,
        "Diciembre":12,
    }
    return switcher.get(mes, 0)

def fecha_inicio_mes(mes):
    digit = ''
    anhio = ''
    for char in mes:
        digit += char 
        if char == ' ':
            anhio = mes.replace(digit,' ')
            anhio = anhio.replace('-',' ')
            break
    #print digit
    mes = mes_numero(digit)
    dias = digit * 7
    anhio = int(anhio)

    actual = datetime.date(anhio, mes, 1)
    return actual

def fecha_fin_mes(mes):
    digit = ''
    anhio = ''
    for char in mes:
        digit += char 
        if char == ' ':
            anhio = mes.replace(digit,' ')
            anhio = anhio.replace('-',' ')
            break
    #print digit
    mes = mes_numero(digit)
    anhio = int(anhio)

    actual = datetime.date(anhio, mes, 1) + relativedelta(day=31)
    return actual

def semanas(year):
    list = []
    for i in range(0,-2,-1):
        #print str(i)
        d = date(year-i, 1, 1)                    # January 1st
        f = date(year-i, 1, 1)                    # January 1st
        d += timedelta( (5 - d.weekday() + 7) % 7)  # First Sunday
        f += timedelta( f.weekday() + 6)  # First Friday
        while d.year == year-i:
            s = d.isocalendar()[1]            
            semana = str(s) + ' - ' +str(year-i)
            etiqueta = 'Semana # '+str(s) + ' - '+ str(year - i) #+ ' del '+ unicode(d)+' al ' +unicode(f)
            list.append( (semana, etiqueta ) ) 
            d += timedelta(days = 7)
            f += timedelta(days = 7)
    return list

def allmonth(year):
    list = []
    for i in range(0,-1,-1):
        #print str(i)
        d = date(year-i, 1, 1)                    # January 1st
        f = date(year-i, 1, 1)                    # January 1st
        d += timedelta( (5 - d.weekday() + 7) % 7)  # First Sunday
        f += timedelta( f.weekday() + 6)  # First Friday
        while d.year == year-i:
            numero = d.month
            etiqueta = numero_mes(numero-1) + ' - ' +str(d.year)
            list.append( (etiqueta,etiqueta)) 
            d += timedelta(days = 30)
            f += timedelta(days = 30)
    return list 

def semana_actual(date):
    s = date.isocalendar()[1]
    year = date.year
    semana = str(s) + ' - ' + str(year)
    return semana 

def mes_actual(fecha):
    """This code was provided in the previous answer! It's not mine!"""
    mes = numero_mes(fecha.month-1)
    year = fecha.year
    semana = str(mes) + ' - ' + str(year)
    return semana 

def semana(semana):
    digit = ''
    for char in semana:
        digit += char
        if char == ' ':
            break 
    return digit         

def fecha_inicio_semana(semana):
    #print semana
    digit = ''
    for char in semana:
        digit += char 
        if char == ' ':
            #print digit
            anhio = semana.replace(digit,' ')
            anhio = anhio.replace('-',' ')
            #print 'ANHIO: ' + anhio
            break
    digit = int(digit)
    dias = digit * 7
    anhio = int(anhio)

    actual = datetime.date(anhio, 1, 1) + timedelta(dias - 7)
    return actual

def fecha_fin_semana(semana):
    #print semana
    digit = ''
    for char in semana:
        digit += char 
        if char == ' ':
            #print digit
            anhio = semana.replace(digit,' ')
            anhio = anhio.replace('-',' ')
            #print 'ANHIO: ' + anhio
            break
    digit = int(digit)
    dias = digit * 7
    anhio = int(anhio)

    actual = datetime.date(anhio, 1, 1) + timedelta(dias - 1)
    return actual

def mes(semana): 
    digit = ''
    for char in semana:
        digit += char 
        if char == ' ':
            #print digit
            anhio = semana.replace(digit,' ')
            anhio = anhio.replace('-',' ')
            #print 'ANHIO: ' + anhio
            break
    digit = int(digit)
    dias = digit * 7
    anhio = int(anhio)
    dias = digit * 7
    actual = datetime.date(anhio, 1, 1) + timedelta(dias -1 )
    
    numero = actual.month
    mes = numero_mes(numero-1)
    anhio = str(anhio)
    return mes + ' - ' + anhio

__all__ = [
    'ImprimirReporteLiderDestacadoInicio',
    'ImprimirReporteLiderDestacado',
    'ReporteLiderDestacadoTable',
    'ReporteLiderDestacado',
    'ImprimirReporteLiderCeroInicio',
    'ImprimirReporteLiderCero',
    'ReporteLiderCeroTable',
    'ReporteLiderCero',
    'ImprimirReporteLiderDistritoInicio',
    'ImprimirReporteLiderDistrito',
    'ReporteLiderDistritoTable',
    'ReporteLiderDistrito',
    ]

__metaclass__ = PoolMeta

_YEAR = datetime.datetime.now().year
_NOW = datetime.datetime.now()
_START = datetime.datetime.strptime('2017-10-31',"%Y-%m-%d")
_DOMAIN = []

## Reporte Lider Destacado

class ImprimirReporteLiderDestacadoInicio(ModelView):
    'Imprimir Reporte Lider Destacado Inicio'
    __name__ = 'disc.reporte.lider.destacado.imprimir.inicio'
    
    fecha = fields.Date('Fecha actual', required=True,
        readonly=True)
    
    usuario = fields.Many2One('res.user','Usuario',
        required=True, 
        readonly=True, 
        )

    campo = fields.Many2One('disc.campo', 'Campo', 
        required=True,
        domain = 
            [If(
                Id('party',
                        'group_party_admin').in_(
                        Eval('context', {}).get('groups', [])), 
            [],
            [('pastor', '=', Eval('usuario'))],
            )],
        depends=['usuario'],
    )

    mes = fields.Selection(allmonth(_YEAR),'Mes', required=True,
        sort=False)

    fecha_inicio = fields.Date('Fecha Inicial')
    fecha_fin = fields.Date('Fecha Fin')

    @classmethod
    def default_mes(cls):
        return mes_actual(_NOW)

    @classmethod
    def default_fecha_inicio(cls):
        hoy = _START
        actual = datetime.date(hoy.year, hoy.month, 1)
        return actual

    @classmethod
    def default_fecha_fin(cls):
        hoy = _NOW
        actual = datetime.date(hoy.year, hoy.month, 1) + relativedelta(day=31)
        return actual 

    @fields.depends('mes', 'fecha_inicio','fecha_fin')
    def on_change_mes(self):
        #self.fecha_inicio = fecha_inicio_mes(self.mes)
        self.fecha_fin =  fecha_fin_mes(self.mes)

    @classmethod
    def default_usuario(cls):
        pool = Pool()
        User = pool.get('res.user')
        #cursor = Transaction().connection.cursor()
        user = User(Transaction().user).id
        #print 'USUARIO: ' + str(User(Transaction().user).groups)
        return user 

    @staticmethod
    def default_fecha():
        Date = Pool().get('ir.date')
        return Date.today()

class ImprimirReporteLiderDestacado(Wizard):
    'Imprimir Reporte Lider Destacado'
    __name__ = 'disc.reporte.lider.destacado.imprimir'
    
    start = StateView('disc.reporte.lider.destacado.imprimir.inicio',
        'discipulado.imprimir_reporte_lider_destacado_inicio_form', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Imprimir', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('disc.reporte.lider.destacado')

    def do_print_(self, action):
        data = {
            'fecha_inicio': self.start.fecha_inicio,
            'fecha_fin': self.start.fecha_fin,
            'campo': self.start.campo.name, 
            'pastor': self.start.campo.pastor.name,
            'union': self.start.campo.union.name, 
            'fecha': self.start.fecha,
            'usuario': self.start.usuario.name,
            }
        return action, data

class ReporteLiderDestacadoTable(ModelSQL, ModelView):
    'Reporte Lider Destacado Table'
    __name__ = 'disc.reporte.lider.destacado.table'

    gp = fields.Many2One('disc.gp',
        'Grupo de Esperanza')
    campo = fields.Many2One('disc.campo',
        'Campo')

    total = fields.Numeric('Total')
 
    @staticmethod
    def table_query():
        pool = Pool()
        context = Transaction().context
        Reporte = pool.get('disc.reporte')
        reporte = Reporte.__table__()
        ReporteLinea = pool.get('disc.reporte.linea')
        reporte_linea = ReporteLinea.__table__()
        
        where = Literal(True)
        if Transaction().context.get('fecha_inicio'):
            where &= reporte.fecha_inicio >= Transaction().context['fecha_inicio']
        if Transaction().context.get('fecha_fin'):
            where &= reporte.fecha_fin <= Transaction().context['fecha_fin']

        return (reporte
            .join(reporte_linea,
                condition=reporte_linea.reporte == reporte.id)
            .select(
                Max(reporte_linea.id * 1000).as_('id'),
                Max(reporte.create_uid).as_('create_uid'),
                Max(reporte.create_date).as_('create_date'),
                Max(reporte.write_uid).as_('write_uid'),
                Max(reporte.write_date).as_('write_date'),
                Max(reporte.campo).as_('campo'),
                reporte_linea.gp,
                (Sum(reporte_linea.cantidad)).as_('total'),
                where=where,
                group_by=(reporte_linea.gp),
                )
            )

class ReporteLiderDestacado(Report):
    'Reporte Lider Destacado'
    __name__ = 'disc.reporte.lider.destacado'

    @classmethod
    def _get_records(cls, ids, model, data):
        Reporte = Pool().get('disc.reporte.lider.destacado.table')

        fecha_inicio = data['fecha_inicio']
        fecha_fin = data['fecha_fin']
        campo = data['campo']

        with Transaction().set_context(fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin): 
            reports = Reporte.search(
                [('campo','=',campo)],
                order=[('total', 'DESC')], 
                limit=10, 
                ) 
        
        return reports

    @classmethod
    def get_context(cls, records, data):
        report_context = super(ReporteLiderDestacado, cls).get_context(records, data)

        Reporte = Pool().get('disc.reporte.lider.destacado.table')
        
        fecha_inicio = data['fecha_inicio']
        fecha_fin = data['fecha_fin']
        campo = data['campo']

        with Transaction().set_context(fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin): 
            reports = Reporte.search( 
                [('campo','=',campo)],
                order=[('total', 'DESC')], 
                limit=10, 
                ) 

        report_context['fecha_inicio'] = data['fecha_inicio']
        report_context['fecha_fin'] = data['fecha_fin']
        report_context['fecha'] = data['fecha']
        report_context['campo'] = data['campo']
        report_context['union'] = data['union']
        report_context['usuario'] = data['usuario']
        report_context['pastor'] = data['pastor']

        report_context['total'] = sum((x.total for x in reports))
        
        return report_context

## Reporte Lider Cero

class ImprimirReporteLiderCeroInicio(ModelView):
    'Imprimir Reporte Lider Cero Inicio'
    __name__ = 'disc.reporte.lider.cero.imprimir.inicio'
    
    fecha = fields.Date('Fecha actual', required=True,
        readonly=True)
    
    usuario = fields.Many2One('res.user','Usuario',
        required=True, 
        readonly=True, 
        )

    distrito = fields.Many2One('disc.distrito', 'Distrito', 
        required=True,
        domain = 
            [If(
                Id('party',
                        'group_party_admin').in_(
                        Eval('context', {}).get('groups', [])), 
            [],
            [('pastor', '=', Eval('usuario'))],
            )],
        depends=['usuario'],
    )

    mes = fields.Selection(allmonth(_YEAR),'Mes', required=True,
        sort=False)

    fecha_inicio = fields.Date('Fecha Inicial')
    fecha_fin = fields.Date('Fecha Fin')

    @classmethod
    def default_mes(cls):
        return mes_actual(_NOW)

    @classmethod
    def default_fecha_inicio(cls):
        hoy = _START
        actual = datetime.date(hoy.year, hoy.month, 1)
        return actual

    @classmethod
    def default_fecha_fin(cls):
        hoy = _NOW
        actual = datetime.date(hoy.year, hoy.month, 1) + relativedelta(day=31)
        return actual 

    @fields.depends('mes', 'fecha_inicio','fecha_fin')
    def on_change_mes(self):
        #self.fecha_inicio = fecha_inicio_mes(self.mes)
        self.fecha_fin =  fecha_fin_mes(self.mes)

    @classmethod
    def default_usuario(cls):
        pool = Pool()
        User = pool.get('res.user')
        #cursor = Transaction().connection.cursor()
        user = User(Transaction().user).id
        #print 'USUARIO: ' + str(User(Transaction().user).groups)
        return user 

    @staticmethod
    def default_fecha():
        Date = Pool().get('ir.date')
        return Date.today()

class ImprimirReporteLiderCero(Wizard):
    'Imprimir Reporte Lider Cero'
    __name__ = 'disc.reporte.lider.cero.imprimir'
    
    start = StateView('disc.reporte.lider.cero.imprimir.inicio',
        'discipulado.imprimir_reporte_lider_cero_inicio_form', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Imprimir', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('disc.reporte.lider.cero')

    def do_print_(self, action):
        data = {
            'fecha_inicio': self.start.fecha_inicio,
            'fecha_fin': self.start.fecha_fin,
            'fecha': self.start.fecha,
            'distrito': self.start.distrito.id,
            'usuario': self.start.usuario.name,
            }
        return action, data

class ReporteLiderCeroTable(ModelSQL, ModelView):
    'Reporte Lider Cero Table'
    __name__ = 'disc.reporte.lider.cero.table'

    gp = fields.Many2One('disc.gp',
        'Grupo de Esperanza')
    total = fields.Numeric('Total')
    #iglesia = fields.Many2One('disc.iglesia',
    #    'Iglesia')
 
    @staticmethod
    def table_query():
        pool = Pool()
        context = Transaction().context

        Gp = pool.get('disc.gp')
        gp = Gp.__table__()
        Reporte = pool.get('disc.reporte')
        reporte = Reporte.__table__()
        ReporteLinea = pool.get('disc.reporte.linea')
        reporte_linea = ReporteLinea.__table__()
        
        where = Literal(True)
        if context.get('fecha_inicio'):
            where &= reporte.fecha_inicio >= context['fecha_inicio']
        #    print "FECHA INICIO: " +  str(context['fecha_inicio'])
        if context.get('fecha_fin'):
            where &= reporte.fecha_fin <= context['fecha_fin']
        #    print "FECHA FIN: " +  str(context['fecha_fin'])
        #if context.get('distrito'):
        #    where &= reporte.distrito == context['distrito']
        #    print "DISTRITO: " +  str(context['distrito'])
        #print "WHERE: " + str(where)

        subquery = (reporte_linea
            .join(reporte,
                condition=reporte_linea.reporte == reporte.id)
            .select(
                Max(reporte_linea.id * 1005).as_('id'),
                Max(reporte_linea.create_uid).as_('create_uid'),
                Max(reporte_linea.create_date).as_('create_date'),
                Max(reporte_linea.write_uid).as_('write_uid'),
                Max(reporte_linea.write_date).as_('write_date'),
                (Sum(reporte_linea.cantidad)).as_('total'),
                (reporte_linea.gp).as_('gp'),
                where = where,
                group_by=(reporte_linea.gp),
                having= Sum(reporte_linea.cantidad)>0, 
                order_by=(reporte_linea.gp),
                )
            )

        query = (gp
            .join(subquery,'LEFT',
            condition= gp.id == subquery.gp)
            .select(
                Max(gp.id * 1002).as_('id'), 
                Max(gp.create_uid).as_('create_uid'),
                Max(gp.create_date).as_('create_date'),
                Max(gp.write_uid).as_('write_uid'),
                Max(gp.write_date).as_('write_date'),
                (Sum(subquery.total)).as_('total'),
                (gp.id).as_('gp'),
                where= subquery.gp == None, #or subquery.total is None,
                #having= Sum(subquery.total)<1, 
                group_by=(gp.id), 
                )
            )

        #print "QUERY: " + str(query) 
        return query
            
class ReporteLiderCero(Report):
    'Reporte Lider Cero'
    __name__ = 'disc.reporte.lider.cero'

    @classmethod
    def _get_records(cls, ids, model, data):
        pool = Pool()
        Reporte = pool.get('disc.reporte.lider.cero.table')

        fecha_inicio = data['fecha_inicio']
        fecha_fin = data['fecha_fin']
        distrito = data['distrito']

        with Transaction().set_context(fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin, distrito=distrito):
            reports = Reporte.search(
                #[],
                [('gp.iglesia.distrito','=',distrito)],
                order=[('gp.iglesia', 'DESC')], 
                ) 
            #print "REPORTS: " + str(reports)
        
        return reports

    @classmethod
    def get_context(cls, records, data):
        report_context = super(ReporteLiderCero, cls).get_context(records, data)

        pool = Pool()
        Reporte = pool.get('disc.reporte.lider.cero.table')
        Distrito = pool.get('disc.distrito')
        distrito = data['distrito']
        distrito_name = Distrito(distrito).name

        report_context['fecha_inicio'] = data['fecha_inicio']
        report_context['fecha_fin'] = data['fecha_fin']
        report_context['fecha'] = data['fecha']
        report_context['usuario'] = data['usuario']
        report_context['distrito'] = distrito_name
        
        
        return report_context

## Reporte Lideres General por Distrito

class ImprimirReporteLiderDistritoInicio(ModelView):
    'Imprimir Reporte Lider Distrito Inicio'
    __name__ = 'disc.reporte.lider.distrito.imprimir.inicio'
    
    distrito = fields.Many2One('disc.distrito', 'Distrito', 
        required=True,
        domain = 
            [If(
                Id('party',
                        'group_party_admin').in_(
                        Eval('context', {}).get('groups', [])), 
            [],
            [('pastor', '=', Eval('usuario'))],
            )],
        depends=['usuario'],
    )
    
    usuario = fields.Many2One('res.user','Usuario',
        required=True, 
        readonly=True, 
        )

    mes = fields.Selection(allmonth(_YEAR),'Mes', required=True,
        sort=False)

    fecha_inicio = fields.Date('Fecha Inicial')
    fecha_fin = fields.Date('Fecha Fin')
    fecha = fields.Date('Fecha actual', required=True,
        readonly=True)

    @classmethod
    def default_mes(cls):
        return mes_actual(_NOW)

    @classmethod
    def default_fecha_inicio(cls):
        hoy = _START
        actual = datetime.date(hoy.year, hoy.month, 1)
        return actual

    @classmethod
    def default_fecha_fin(cls):
        hoy = _NOW
        actual = datetime.date(hoy.year, hoy.month, 1) + relativedelta(day=31)
        return actual 

    @fields.depends('mes', 'fecha_inicio','fecha_fin')
    def on_change_mes(self):
        #self.fecha_inicio = fecha_inicio_mes(self.mes)
        self.fecha_fin =  fecha_fin_mes(self.mes)

    @classmethod
    def default_usuario(cls):
        pool = Pool()
        User = pool.get('res.user')
        user = User(Transaction().user).id
        return user 

    @staticmethod
    def default_fecha():
        Date = Pool().get('ir.date')
        return Date.today()

class ImprimirReporteLiderDistrito(Wizard):
    'Imprimir Reporte Lider Distrito'
    __name__ = 'disc.reporte.lider.distrito.imprimir'
    
    start = StateView('disc.reporte.lider.distrito.imprimir.inicio',
        'discipulado.imprimir_reporte_lider_distrito_inicio_form', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Imprimir', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('disc.reporte.lider.distrito')

    def do_print_(self, action):
        data = {
            'fecha_inicio': self.start.fecha_inicio,
            'fecha_fin': self.start.fecha_fin,
            'fecha': self.start.fecha,
            'distrito': self.start.distrito.id,
            'pastor': self.start.distrito.pastor.name,
            'usuario': self.start.usuario.name,
            }
        return action, data

class ReporteLiderDistritoTable(ModelSQL, ModelView):
    'Reporte Lider Distrito Table'
    __name__ = 'disc.reporte.lider.distrito.table'

    gp = fields.Many2One('disc.gp',
        'Lider de Esperanza')
    iglesia = fields.Many2One('disc.iglesia',
        'Iglesia')
    total = fields.Numeric('Total')
    active = fields.Boolean('Activo')
 
    @staticmethod
    def table_query():
        pool = Pool()
        context = Transaction().context
        Gp = pool.get('disc.gp')
        gp = Gp.__table__()
        Iglesia = pool.get('disc.iglesia')
        iglesia = Iglesia.__table__()
        Reporte = pool.get('disc.reporte')
        reporte = Reporte.__table__()
        ReporteLinea = pool.get('disc.reporte.linea')
        reporte_linea = ReporteLinea.__table__()

        where = Literal(True)
        if context.get('fecha_inicio'):
            where &= reporte.fecha_inicio >= context['fecha_inicio']
        if context.get('fecha_fin'):
            where &= reporte.fecha_fin <= context['fecha_fin']
        if context.get('distrito'):
            where &= reporte.distrito == context['distrito']

        subquery = (reporte
            .join(reporte_linea,
                condition=reporte_linea.reporte == reporte.id)
            .select(
                Max(reporte_linea.id * 1000).as_('id'),
                Max(reporte.create_uid).as_('create_uid'),
                Max(reporte.create_date).as_('create_date'),
                Max(reporte.write_uid).as_('write_uid'),
                Max(reporte.write_date).as_('write_date'),
                reporte_linea.gp,
                reporte.iglesia,
                Max(reporte.distrito).as_('distrito'),
                #reporte.mes,
                (Sum(reporte_linea.cantidad)).as_('total'),
                where=where,
                group_by=[reporte_linea.gp, reporte.iglesia] 
                )
        )

        if context.get('distrito'):
            distrito = context['distrito']
            where = subquery.distrito == distrito
            iglesias = Iglesia.search(['distrito','=',distrito])
            if iglesias:
                for iglesia in iglesias: 
                    where |= gp.iglesia == iglesia.id 
            where &= gp.active == True
        else:
            where = Literal(True)
            #where &= subquery.distrito == None 
            #if iglesias: 
            #    where &= gp.iglesia in (x.id for x in iglesias)
            #print "WHERE: " + str(where)

        query = (subquery
            .join(gp,'FULL',
                condition= gp.id == subquery.gp
            )
            .select(
                Max(gp.id * 1000).as_('id'), 
                Max(gp.create_uid).as_('create_uid'),
                Max(gp.create_date).as_('create_date'),
                Max(gp.write_uid).as_('write_uid'),
                Max(gp.write_date).as_('write_date'),
                (Sum(Coalesce(subquery.total,0) )).as_('total'),
                gp.iglesia,
                subquery.distrito,
                (gp.id).as_('gp'),
                (gp.active),
                where = where, 
                group_by=(gp.id,subquery.distrito, gp.active), 
                order_by=Sum(Coalesce(subquery.total,0)).desc,
                )
            )
        return query

class ReporteLiderDistrito(Report):
    'Reporte Lider Distrito'
    __name__ = 'disc.reporte.lider.distrito'

    @classmethod
    def _get_records(cls, ids, model, data):
        Reporte = Pool().get('disc.reporte.lider.distrito.table')

        fecha_inicio = data['fecha_inicio'] 
        fecha_fin = data['fecha_fin']
        distrito = data['distrito']

        with Transaction().set_context(fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,distrito=distrito): 
            reports = Reporte.search(
                #[],
                [('active','=',True)],
                order=[('total','DESC')]
                ) 
        
        return reports

    @classmethod
    def get_context(cls, records, data):
        report_context = super(ReporteLiderDistrito, cls).get_context(records, data)

        Reporte = Pool().get('disc.reporte.lider.distrito.table')
        Distrito = Pool().get('disc.distrito')


        fecha_inicio = data['fecha_inicio']
        fecha_fin = data['fecha_fin']
        distrito = data['distrito']
        distrito_name = ''
        distritos = Distrito.search(['id','=',distrito])
        if distritos:
            distrito_name = distritos[0].name


        with Transaction().set_context(fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,distrito=distrito): 
            reports = Reporte.search(
                [],
                order=[('total','DESC')],
                #[('distrito','=',distrito)],
                ) 

        report_context['fecha_inicio'] = data['fecha_inicio']
        report_context['fecha_fin'] = data['fecha_fin']
        report_context['fecha'] = data['fecha']
        report_context['usuario'] = data['usuario']
        report_context['distrito'] = distrito_name
        report_context['pastor'] = data['pastor']

        report_context['total'] = sum((x.total for x in reports))
        
        return report_context