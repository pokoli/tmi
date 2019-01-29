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
from trytond.report import Report

from datetime import datetime, timedelta, date
import calendar


__all__ = ['PrintTmiReportStart',
    'PrintTmiReport',
    'TmiReport']

class PrintTmiReportStart(ModelView):
    'Report Tmi Start'
    __name__ = 'print.tmi.report.start'

    company = fields.Many2One('company.company', "Company", readonly=True,
        required=True, 
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ])
    start_date = fields.Date("Start Date",
        domain=[
            If(Eval('end_date') & Eval('start_date'),
                ('start_date', '<=', Eval('end_date')),
                ()),
            ],
        depends=['end_date'])
    end_date = fields.Date("End Date",
        domain=[
            If(Eval('start_date') & Eval('end_date'),
                ('end_date', '>=', Eval('start_date')),
                ()),
            ],
        depends=['start_date'])
    type = fields.Selection( 
        [
        ('conference','Conference'),
        ('division','Division'),
        ('union','Union'),
        ('field','Field'),
        ('zone','Zone'),
        ('district','District'),
        ('church','Church'),
        ]
        ,'Type', 
        required=True,
        sort=False)
    child_type = fields.Function(
            fields.Selection( 
                [
                    ('conference','Conference'),
                    ('division','Division'),
                    ('union','Union'),
                    ('field','Field'),
                    ('zone','Zone'),
                    ('district','District'),
                    ('church','Church'),
                ]
        ,'Child Type', 
        required=False,
        #depends=['type'],
        sort=False), 'on_change_type'
        )
    group = fields.Many2One('tmi.meta.group', 'Group',
        help="The group for the balance.",
        required=False, 
        domain=[
            #[('company', 'in', Eval('user', {}).get('companies', []))]
            ('type', '=', Eval('type') )
            ],
        depends=['type']
        )
    posted = fields.Boolean('Posted')

    @classmethod
    def default_company(cls):
        return Transaction().context.get('company')

    @classmethod
    def default_start_date(cls):
        return datetime.today().replace(day=1)

    @classmethod
    def default_end_date(cls):
        Date = Pool().get('ir.date')
        #return Date.today()
        return datetime.today().replace(day=calendar.monthrange(date.today().year, date.today().month)[1])

    @staticmethod
    def default_type():
        return 'district'

    @staticmethod
    def default_child_type():
        return 'church'

    @staticmethod
    def default_posted():
        return True 


    @fields.depends('type','child_type')
    def on_change_type(self, name=None): 
        if self.type: 
            if self.type == 'conference': 
                self.child_type = 'division'
            if self.type == 'division': 
                self.child_type = 'union'
            if self.type == 'union': 
                self.child_type = 'field'
            if self.type == 'field': 
                self.child_type = 'zone'
            if self.type == 'zone': 
                self.child_type = 'district'
            if self.type == 'district': 
                self.child_type = 'church'
            if self.type == 'church':
                self.child_type = 'small_group'
        self.child_type = 'small_group'

    def get_type(self, name=None):
        _types = [
            ('district','District'),
            ('church','Church'),
            ('small_group','Small Group'),
        ]
        if self.company:
            _type = self.company.type
            if _type == 'conference': 
                _types = [
                    ('conference','Conference'),
                    ('division','Division'),
                    ('union','Union'),
                    ('field','Field'),
                    ('zone','Zone'),
                    ('district','District'),
                    ('church','Church'),
                    ('small_group','Small Group'),
                ]
            elif _type == 'division': 
                _types = [
                    ('division','Division'),
                    ('union','Union'),
                    ('field','Field'),
                    ('zone','Zone'),
                    ('district','District'),
                    ('church','Church'),
                    ('small_group','Small Group'),
                ]
            elif _type == 'union': 
                _types = [
                    ('union','Union'),
                    ('field','Field'),
                    ('zone','Zone'),
                    ('district','District'),
                    ('church','Church'),
                    ('small_group','Small Group'),
                ]
            elif _type == 'field': 
                _types = [
                    ('field','Field'),
                    ('zone','Zone'),
                    ('district','District'),
                    ('church','Church'),
                    ('small_group','Small Group'),
                ]
            elif _type == 'zone': 
                _types = [
                    ('zone','Zone'),
                    ('district','District'),
                    ('church','Church'),
                    ('small_group','Small Group'),
                ]
            else:
                _types = [
                    ('district','District'),
                    ('church','Church'),
                    ('small_group','Small Group'),
                ]
        #print ("TYPES_ ", str(types_))
        return _types

class PrintTmiReport(Wizard):
    'Print Tmi Report'
    __name__ = 'print.tmi.report'

    start = StateView('print.tmi.report.start',
        'tmi.print_tmi_report_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('tmi.report')

    def do_print_(self, action):
        start_date = self.start.start_date
        end_date = self.start.end_date
        if self.start.group: 
            data = {
                'company': self.start.company.id,
                'group': self.start.group.id,
                'start_date': self.start.start_date,
                'end_date': self.start.end_date,
                'type': self.start.type, 
                'child_type': self.start.child_type, 
                'posted': self.start.posted, 
                }
        else: 
            data = {
                'company': self.start.company.id,
                'start_date': self.start.start_date,
                'end_date': self.start.end_date,
                'type': self.start.type, 
                'child_type': self.start.child_type, 
                'posted': self.start.posted, 
                }
        return action, data

class TmiReport(Report):
    'Tmi Group Report'
    __name__ = 'tmi.report'

    @classmethod
    def _get_records(cls, ids, model, data):
        Group = Pool().get('tmi.meta.group')
        
        with Transaction().set_context(
                from_date=data['start_date'],
                to_date=data['end_date'],
                posted=data['posted'], 
                ): 

            group = None 
            if 'group' in data:
                group = data['group']
            _type = data['type']
            if group:             
                groups = Group.search([
                    ('type','=', _type),
                    ('id','=',group)
                ]) 
            else: 
                groups = Group.search([
                    ('type','=', _type)
                ]) 

            childs = []
            for group in groups: 
                current_childs = Group.search([('parent','=',group.id)])
                childs+=current_childs
            
            return childs

    @classmethod
    def get_context(cls, records, data):

        report_context = super(TmiReport, cls).get_context(records, data)

        pool = Pool()
        Company = pool.get('company.company')
        Group = pool.get('tmi.meta.group')
        company = Company(data['company'])

        group = None 
        if 'group' in data:
            group = Group(data['group'])
        else:
            group = company 

        report_context['company'] = company
        report_context['digits'] = company.currency.digits
        report_context['start_date'] = data['start_date']
        report_context['end_date'] = data['end_date']
        report_context['child_type'] = data['child_type']
        report_context['group'] = group

        print ("REPORT CONTEXT ", str(report_context))
            
        return report_context