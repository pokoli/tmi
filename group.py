# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from datetime import datetime
import datetime
import operator
from functools import wraps

from dateutil.relativedelta import relativedelta
from sql import Column, Null, Window, Literal
from sql.functions import CharLength

from sql.aggregate import Sum, Max
from sql.conditionals import Coalesce, Case

from trytond.model import (
    ModelView, ModelSQL, DeactivableMixin, fields, Unique, sequence_ordered,
    tree)
from trytond.wizard import Wizard, StateView, StateAction, StateTransition, \
    Button
from trytond.report import Report
from trytond.tools import reduce_ids, grouped_slice
from trytond.pyson import Eval, If, PYSONEncoder, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond import backend
from .common import PeriodMixin, ActivePeriodMixin

__all__ = [
    'TmiMetaGroup',
    'TmiGroup',
    'TmiGroupStatisticalContext',
    ]

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

class TmiMetaGroup( 
        tree(separator='\\'), sequence_ordered(), ModelSQL, ModelView):
    'Meta Group'
    __name__ = 'tmi.meta.group'

    name = fields.Char('Name', size=None, required=True)
    code = fields.Char('Code')
    active = fields.Boolean('Active')
    company = fields.Many2One('company.company', 'Company', required=True)
    currency = fields.Function(fields.Many2One('currency.currency',
        'Currency'), 'get_currency')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
            'get_currency_digits')
    parent = fields.Many2One('tmi.meta.group', 'Parent',
        ondelete="RESTRICT",
        domain=[
            'OR',[ ('company','=',Eval('company',-1)), 
                ('company', 'in',Eval('company.childs',[])),
                ],
            ('type', '=', Eval('parent_type',None)),

            ],
        depends=['type','company'])
    childs = fields.One2Many('tmi.meta.group', 'parent', 'Children',
        domain=[
            'OR',[ ('company','=',Eval('company',-1)),
            ('company', 'in',Eval('company.childs',[])),
            ],
        ],
        depends=['company'])
    baptism = fields.Function(fields.Numeric('Baptism',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    small_group = fields.Function(fields.Numeric('Small Group',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    tithe = fields.Function(fields.Numeric('Tithe',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    offering = fields.Function(fields.Numeric('Offering',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    praise_thanksgiving = fields.Function(fields.Numeric('Praise and Thanksgiving', 
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    gathering = fields.Function(fields.Numeric('Gathering',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    church_planting = fields.Function(fields.Numeric('Church Planting',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    organizing_church = fields.Function(fields.Numeric('Organizing Church',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    type = fields.Selection( 
        [
        ('conference','Conference'),
        ('division','Division'),
        ('union','Union'),
        ('field','Field'),
        ('zone','Zone'),
        ('district','District'),
        ('church','Church'),
        ('small_group','Small Group'),
        ]
        ,'Type', 
        required=True,
        sort=False)
    parent_type = fields.Function(fields.Selection(
        [
        ('conference','Conference'),
        ('division','Division'),
        ('union','Union'),
        ('field','Field'),
        ('zone','Zone'),
        ('district','District'),
        ('church','Church'),
        ('small_group','Small Group'),
        ],
        'Parent Type'),
        'get_parent_type')
    company = fields.Many2One('company.company', 'Company', required=True,
            ondelete="RESTRICT")
    child_value = fields.Function(fields.Numeric('Child Value'),
        'get_child_value')

    tmi_baptism_target = fields.Function(fields.Numeric('Baptism Target',
        digits=(16,0 )), 'get_target')
    tmi_small_group_target = fields.Function(fields.Numeric('Small Group Target',
        digits=(16, 0)), 'get_target')
    tmi_tithe_target = fields.Function(fields.Numeric('Tithe  Target',
        digits=(16,Eval('currency_digits',2))), 'get_target')
    tmi_offering_target = fields.Function(fields.Numeric('Offering Target',
        digits=(16,Eval('currency_digits',2))), 'get_target')
    tmi_praise_thanksgiving_target = fields.Function(fields.Numeric('Praise and Thanksgiving Target', 
        digits=(16,Eval('currency_digits',2))), 'get_target')
    tmi_gathering_target = fields.Function(fields.Numeric('Gathering Target',
        digits=(16,Eval('currency_digits',2))), 'get_target')
    tmi_church_planting_target = fields.Function(fields.Numeric('Church Planting Target',
        digits=(16,0)), 'get_target')
    tmi_organizing_church_target = fields.Function(fields.Numeric('Organizing Church Target',
        digits=(16,0)), 'get_target')

    tmi_baptism_difference = fields.Function(fields.Numeric('Baptism Difference',
        digits=(16,0 )), 'get_difference')
    tmi_small_group_difference = fields.Function(fields.Numeric('Small Group Difference',
        digits=(16, 0)), 'get_difference')
    tmi_tithe_difference = fields.Function(fields.Numeric('Tithe  Difference',
        digits=(16,Eval('currency_digits',2))), 'get_difference')
    tmi_offering_difference = fields.Function(fields.Numeric('Offering Difference',
        digits=(16,Eval('currency_digits',2))), 'get_difference')
    tmi_praise_thanksgiving_difference = fields.Function(fields.Numeric('Praise and Thanksgiving Difference', 
        digits=(16,Eval('currency_digits',2))), 'get_difference')
    tmi_gathering_difference = fields.Function(fields.Numeric('Gathering Difference',
        digits=(16,Eval('currency_digits',2))), 'get_difference')
    tmi_church_planting_difference = fields.Function(fields.Numeric('Church Planting Difference',
        digits=(16,0)), 'get_difference')
    tmi_organizing_church_difference = fields.Function(fields.Numeric('Organizing Church Difference',
        digits=(16,0)), 'get_difference')

    tmi_baptism_percentage = fields.Function(fields.Numeric('Baptism Percentage',
        digits=(16,2)), 'get_percentage')
    tmi_small_group_percentage = fields.Function(fields.Numeric('Small Group Percentage',
        digits=(16,2)), 'get_percentage')
    tmi_tithe_percentage = fields.Function(fields.Numeric('Tithe  Percentage',
        digits=(16,2)), 'get_percentage')
    tmi_offering_percentage = fields.Function(fields.Numeric('Offering Percentage',
        digits=(16,2)), 'get_percentage')
    tmi_praise_thanksgiving_percentage = fields.Function(fields.Numeric('Praise and Thanksgiving Percentage', 
        digits=(16,2)), 'get_percentage')
    tmi_gathering_percentage = fields.Function(fields.Numeric('Gathering Percentage',
        digits=(16,2)), 'get_percentage')
    tmi_church_planting_percentage = fields.Function(fields.Numeric('Church Planting Percentage',
        digits=(16,2)), 'get_percentage')
    tmi_organizing_church_percentage = fields.Function(fields.Numeric('Organizing Church Percentage',
        digits=(16,2)), 'get_percentage')


    level = fields.Function(fields.Numeric('Level',digits=(2,0)),
        '_get_level')

    @classmethod
    def __setup__(cls):
        super(TmiMetaGroup, cls).__setup__()
        #cls._order.insert(0, ('baptism', 'ASC')) 
        cls._order.insert(0, ('name', 'ASC'))
        cls._order.insert(0, ('code', 'ASC'))

    def get_parent_type(self, name):
        if self.type=='small_group': 
            return 'church'
        if self.type=='church':
            return 'district'
        if self.type=='district':
            return 'zone'
        if self.type=='zone':
            return 'field'
        if self.type=='field':
            return 'union'
        if self.type=='union':
            return 'division'
        if self.type=='division':
            return 'conference'
        return None

    def _get_level(self, parent=None): 
        level = 0
        if self.parent:
            level = self.parent.level + 1
        return  level

    def _get_childs_by_order(self, res=None, _order=None):
        '''Returns the records of all the children computed recursively, and sorted by sequence. Ready for the printing'''
        
        Group = Pool().get('tmi.meta.group')
        
        if res is None: 
            res = []

        if _order is None: 
            _order = 'baptism'

        childs = Group.search([('parent', '=', self.id)])
        
        if len(childs)>=1:
            for child in childs:
                res.append(Group(child.id))
                child._get_childs_by_order(res=res)
        return res 

    @fields.depends('type','parent_type')
    def on_change_type(self):
        if self.type=='small_group':
            self.parent_type = 'church'
        if self.type=='church':
            self.parent_type = 'district'
        if self.type=='district':
            self.parent_type = 'zone'
        if self.type=='zone':
            self.parent_type = 'field'
        if self.type=='field':
            self.parent_type = 'union'
        if self.type=='union':
            self.parent_type = 'division'
        if self.type=='division':
            self.parent_type = 'conference'
        return None

    def get_type(self,value=None): 
        if value=='small_group': 
            return 'Small Group'
        if value=='church':
            return 'Church'
        if value=='district':
            return 'District'
        if value=='zone':
            return 'Zone'
        if value=='field':
            return 'Field'
        if value=='union':
            return 'Union'
        if value=='division':
            return 'Division'
        if value=='conference':
            return 'Conference'
        return None

    def get_rec_name(self, name):
        if self.code and self.parent:
            return self.name + ' - ' + self.code + ' - ' + self.parent.name
        elif self.code and not self.parent:
            return self.name + ' - ' + self.code
        elif self.parent and not self.code:
            return self.name + ' - ' + self.parent.name
        else:
            return self.name

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('code',) + tuple(clause[1:]),
            ('type',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
            (cls._rec_name,) + tuple(clause[1:]),
            ]

    def get_currency(self, name):
        return self.company.currency.id

    def get_currency_digits(self, name): 
        return self.company.currency.digits

    def get_child_value(self, name): 
        if self.childs is not None and self.type !='small_group': 
            return sum(x.child_value for x in self.childs)
        elif self.childs is None and self.type =='small_group': 
            return 1 
        else: 
            children_sum = 1
            for child in self.childs:
                children_sum = sum(x.child_value for x in self.childs if x.type=='small_group')
            return children_sum 
        return 0 

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_active():
        return True 

    @staticmethod
    def default_type():
        return 'small_group'

    @classmethod
    def get_baptism(cls, metas, name):
        pool = Pool()
        Group = pool.get('tmi.group')
        Period = pool.get('tmi.period')

        res = {}
        for meta in metas:
            res[meta.id] = Decimal('0.0')

        childs = cls.search([
                ('parent', 'child_of', [m.id for m in metas]),
                ])
        meta_sum = {}
        for meta in childs:
            meta_sum[meta.id] = Decimal('0.0')

        start_period_ids = Period.get_period_ids('start_%s' % name)
        end_period_ids = Period.get_period_ids('end_%s' % name)
        period_ids = list(
            set(end_period_ids).difference(set(start_period_ids)))
        with Transaction().set_context(periods=period_ids):
            groups = Group.search([
                    ('meta', 'in', [m.id for m in childs]),
                    ])
        
        for group in groups:
            meta_sum[group.meta.id] += (group.baptism)

        for meta in metas:
            childs = cls.search([
                    ('parent', 'child_of', [meta.id]),
                    ])
            for child in childs:
                res[meta.id] += meta_sum[child.id]
            exp = Decimal(str(10.0 ** -meta.currency_digits))
            res[meta.id] = res[meta.id].quantize(exp)
        return res

    @classmethod
    def get_balance(cls, metas, name):
        pool = Pool()
        Group = pool.get('tmi.group')
        Period = pool.get('tmi.period')

        res = {}
        for meta in metas:
            res[meta.id] = Decimal('0.0')

        childs = cls.search([
                ('parent', 'child_of', [m.id for m in metas]),
                ])

        meta_sum = {}
        for meta in childs:
            meta_sum[meta.id] = Decimal('0.0')

        start_period_ids = Period.get_period_ids('start_%s' % name)
        end_period_ids = Period.get_period_ids('end_%s' % name)
        period_ids = list(
            set(end_period_ids).difference(set(start_period_ids)))

        with Transaction().set_context(periods=period_ids):
            groups = Group.search([
                ('meta', 'in', [m.id for m in childs]),
                ])
        for group in groups:
            meta_sum[group.meta.id] += (getattr(group,name))

        for meta in metas:
            childs = cls.search([
                    ('parent', 'child_of', [meta.id]),
                    ])
            for child in childs:
                res[meta.id] += meta_sum[child.id]
            exp = Decimal(str(10.0 ** -meta.currency_digits))
            res[meta.id] = res[meta.id].quantize(exp)
        return res

    @staticmethod
    def order_baptism(tables):
        pool = Pool()
        Group = pool.get('tmi.meta.group')
        group = Group.__table__()
        table, _ = tables[None]

        return [CharLength(table.name), table.name]

    def get_baptism_target(self, name=None):
        pool = Pool()
        Configuration = pool.get('tmi.configuration')
        config = Configuration(1)
        target = config.get_multivalue('tmi_baptism_target')
        context = Transaction().context 
        start_date = context.get('start_date')
        end_date = context.get('end_date')
        value = self.child_value 
        if start_date and end_date: 
            months = diff_month(end_date, start_date)
            value = value * months
        total = 0
        if target and value:
            total = target * value 
        return total 

    def get_target(self, name):
        pool = Pool()
        Configuration = pool.get('tmi.configuration')
        if name not in {'tmi_baptism_target','tmi_tithe_target','tmi_offering_target','tmi_church_planting_target',
                'tmi_gathering_target','tmi_small_group_target','tmi_organizing_church_target',
                'tmi_praise_thanksgiving_target'}: 
            raise ValueError('Unknown name: %s' % name)
        config = Configuration(1)
        field = str(name)
        target = config.get_multivalue(field)
        context = Transaction().context 
        start_date = context.get('start_date')
        end_date = context.get('end_date')
        value = self.child_value 
        if start_date and end_date: 
            months = diff_month(end_date, start_date)
            value = value * months
        total = 0
        if target and value:
            total = target * value 
        return total

    def get_difference(self, name):
        pool = Pool()
        
        if name not in {'tmi_baptism_difference','tmi_tithe_difference','tmi_offering_difference','tmi_church_planting_difference',
                'tmi_gathering_difference','tmi_small_group_difference','tmi_organizing_church_difference',
                'tmi_praise_thanksgiving_difference'}: 
            raise ValueError('Unknown name: %s' % name)
        
        field = str(name)
        target_field = field.replace('difference','target')
        base_field = field.replace('tmi_','')
        base_field = base_field.replace('_difference','')

        
        target_field_value = getattr(self, target_field,None)
        base_field_value = getattr(self, base_field,None)

        difference = target_field_value - base_field_value
        
        return difference

    def get_percentage(self, name):
        pool = Pool()
        
        if name not in {'tmi_baptism_percentage','tmi_tithe_percentage','tmi_offering_percentage','tmi_church_planting_percentage',
                'tmi_gathering_percentage','tmi_small_group_percentage','tmi_organizing_church_percentage',
                'tmi_praise_thanksgiving_percentage'}: 
            raise ValueError('Unknown name: %s' % name)
        
        field = str(name)
        target_field = field.replace('percentage','target')
        base_field = field.replace('tmi_','')
        base_field = base_field.replace('_percentage','')

        target_field_value = getattr(self, target_field,None)
        base_field_value = getattr(self, base_field,None)

        difference = 0 
        if target_field_value and target_field_value != 0: 
            difference = base_field_value / target_field_value
            difference = round(difference, 2)

        return difference



class TmiGroup(ActivePeriodMixin, tree(), ModelView, ModelSQL):
    'TMI Group'
    __name__ = 'tmi.group'

    name = fields.Function(fields.Char('Name'),
        'get_name', searcher='search_meta_field')
    code = fields.Function(fields.Char('Code'),
        'get_code', searcher='search_meta_field')
    #active = fields.Boolean('Active')
    meta = fields.Many2One('tmi.meta.group', 'Meta', ondelete="RESTRICT",
        required=True, 
        domain=[
            ('company', '=', Eval('company')),
            ('type','in',['church','small_group'])
            ], depends=['','company'])
    type = fields.Function(fields.Selection(
        [
        ('church','Church'),
        ('small_group','Small Group'),
        ]
        ,'Type'), 'get_type', searcher='search_meta_field')
    parent_type = fields.Function(fields.Char('Parent Type'),
        'get_parent_type', searcher='search_meta_field')
    parent = fields.Function(fields.Many2One('tmi.meta.group', 'Parent',
        ondelete="RESTRICT",
        domain=[
            #'OR',[ ('company','=',Eval('company',-1)), 
            #    ('company', 'in',Eval('company.childs',[])),
            #    ],
            ('type','=',Eval('parent_type',-1))
            ],
        depends=['parent_type','company']),
        'get_parent', searcher='search_meta_field')
    childs = fields.Function(fields.One2Many('tmi.group', 'parent', 'Children',
        domain=[
            'OR',[ ('company','=',Eval('company',-1)), 
                ('company', 'in',Eval('company.childs',[])),
                ],
            ],
        depends=['company']),
        'get_childs', searcher='search_meta_field')
    company = fields.Function(fields.Many2One('company.company', 'Company', required=True,
            ondelete="RESTRICT"),
        'get_company', searcher='search_meta_field')
    currency = fields.Function(fields.Many2One('currency.currency',
        'Currency'), 'get_currency')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')

    baptism = fields.Function(fields.Numeric('Baptism',
        digits=(16,0)), 'get_balance')
    small_group = fields.Function(fields.Numeric('Small Group',
        digits=(16,0)), 'get_balance')
    tithe = fields.Function(fields.Numeric('Tithe',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    offering = fields.Function(fields.Numeric('Offering',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    praise_thanksgiving = fields.Function(fields.Numeric('Praise and Thanksgiving', 
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    gathering = fields.Function(fields.Numeric('Gathering',
        digits=(16,Eval('currency_digits',2))), 'get_balance')
    church_planting = fields.Function(fields.Numeric('Church Planting',
        digits=(16,0)), 'get_balance')
    organizing_church = fields.Function(fields.Numeric('Organizing Church',
        digits=(16,0)), 'get_balance')

    @classmethod
    def __setup__(cls):
        super(TmiGroup, cls).__setup__()
        t = cls.__table__()
        cls._order.insert(0, ('meta', 'ASC'))
        cls._sql_constraints = [
            ('meta_uniq', Unique(t, t.meta),
             'The meta group must be unique.')
        ]

    def get_rec_name(self, name):
        if self.code:
            return self.name + ' - ' + self.code + ' - ' + self.meta.parent.name
        else:
            return self.name + ' - ' + self.meta.parent.name

    def get_name(self, name=None):
        if self.meta: 
            return self.meta.name

    def get_code(self, name=None):
        if self.meta: 
            return self.meta.code 

    def get_type(self, name=None):
        if self.meta:
            return self.meta.type

    '''
    def get_type(self, value=None): 
        if value=='small_group': 
            return 'Small Group'
        if value=='church':
            return 'Church'
        if value=='district':
            return 'District'
        if value=='zone':
            return 'Zone'
        if value=='field':
            return 'Field'
        if value=='union':
            return 'Union'
        if value=='division':
            return 'Division'
        if value=='conference':
            return 'Conference'
        return None

    def get_rec_name(self, name):
        if self.code:
            return self.get_type(self.type) + ' - ' + self.name + ' - ' + self.code 
        else:
            return self.get_type(self.type) + ' - ' + self.name
    '''

    def get_parent(self, name=None):
        if self.meta:
            if self.meta.parent: 
                return self.meta.parent.id
        return None

    def get_childs(self, name=None):
        if self.meta: 
            pool = Pool()
            Group = pool.get('tmi.group') 
            MetaGroup = pool.get('tmi.meta.group')

            meta_groups = MetaGroup.search([('id','=',self.meta.id)])
            meta_childs = []
            if len(meta_groups)==1: 
                meta_childs = meta_groups[0].childs
            if meta_childs is not []:
                childs = []
                for meta in meta_childs: 
                    groups = Group.search([('meta','=',meta.id)])
                    if len(groups)==1: 
                        childs.append(groups[0].id)
                return childs 
            return []
        else:
            return []

    def get_company(self, name=None):
        if self.meta: 
            return self.meta.company.id 

    @classmethod
    def search_meta_field(cls, name, clause):
        return [('meta.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('code',) + tuple(clause[1:]),
            ('type',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
            ('meta.parent',) + tuple(clause[1:]),
            (cls._rec_name,) + tuple(clause[1:]),
            ]

    @fields.depends('meta','code','type','parent','childs','company')
    def on_change_meta(self, name=None):
        self.name = None
        self.code = None
        self.type = None
        self.parent = None
        self.parent_type = None
        self.childs = []
        self.company = Transaction().context.get('company')
        if self.meta:
            pool = Pool()
            Group = pool.get('tmi.group') 
            MetaGroup = pool.get('tmi.meta.group')
            self.name = self.meta.name 
            self.code = self.meta.code
            self.type = self.meta.type
            self.parent_type = self.meta.parent_type
            self.company = self.meta.company 
            groups = Group.search([('meta','=',self.meta.parent.id)])
            if len(groups)==1:
                self.parent = groups[0].id
            meta_groups = MetaGroup.search([('id','=',self.meta.id)])
            meta_childs = []
            if len(meta_groups)==1: 
                meta_childs = meta_groups[0].childs
            if meta_childs is not []:
                childs = []
                for meta in meta_childs: 
                    groups = Group.search([('meta','=',meta.id)])
                    if len(groups)==1: 
                        childs.append(groups[0].id)
                self.childs = childs 

    def get_currency(self, name):
        return self.company.currency.id

    def get_currency_digits(self, name):
        return self.company.currency.digits

    @fields.depends('company','currency','currency_digits')
    def on_change_company(self, name=None):
        if self.company: 
            self.currency = self.company.currency.id
            self.currency_digits = self.company.currency.digits

    def get_parent_type(self, name):
        if self.type=='small_group':
            return 'church'
        if self.type=='church':
            return 'district'
        if self.type=='district':
            return 'zone'
        if self.type=='zone':
            return 'field'
        if self.type=='field':
            return 'union'
        if self.type=='union':
            return 'division'
        if self.type=='division':
            return 'conference'
        return None

    @fields.depends('type','parent_type')
    def on_change_type(self):
        if self.type=='small_group':
            self.parent_type = 'church'
        if self.type=='church':
            self.parent_type = 'district'
        if self.type=='district':
            self.parent_type = 'zone'
        if self.type=='zone':
            self.parent_type = 'field'
        if self.type=='field':
            self.parent_type = 'union'
        if self.type=='union':
            self.parent_type = 'division'
        if self.type=='division':
            self.parent_type = 'conference'
        return None

    @staticmethod
    def default_active():
        return True 

    @staticmethod
    def default_type():
        return 'small_group'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def get_group_baptism(cls, groups, names):
        '''
        Function to compute baptism for TMI Group.        
        '''
        pool = Pool()
        MoveLine = pool.get('tmi.move.line')
        cursor = Transaction().connection.cursor()

        result = {}
        ids = [a.id for a in groups]
        for name in names:
            if name not in {'baptism'}:
                raise ValueError('Unknown name: %s' % name)
            result[name] = dict((i, Decimal(0)) for i in ids)

        table = cls.__table__()
        line = MoveLine.__table__()
        line_query, fiscalyear_ids = MoveLine.query_get(line)
        columns = [table.id]
        for name in names:
            columns.append(Sum(Coalesce(Column(line, name), 0)))
        for sub_ids in grouped_slice(ids):
            red_sql = reduce_ids(table.id, sub_ids)
            cursor.execute(*table.join(line, 'LEFT',
                    condition=line.group == table.id
                    ).select(*columns,
                    where=red_sql & line_query,
                    group_by=table.id))
            for row in cursor.fetchall():
                group_id = row[0]
                for i, name in enumerate(names, 1):
                    # SQLite uses float for SUM
                    if not isinstance(row[i], Decimal):
                        result[name][group_id] = Decimal(str(row[i]))
                    else:
                        result[name][group_id] = row[i]
        for group in groups:
            for name in names:
                exp = Decimal(str(10.0 ** -group.currency_digits))
                result[name][group.id] = (
                    result[name][group.id].quantize(exp))

        return result

    @classmethod
    def get_balance(cls, groups, names):
        '''
        Function to compute tithe, baptism, church_planting, gathering, small_group, 
        organizing_church, praise_thanksgiving, offering for TMI Group.        
        '''
        pool = Pool()
        MoveLine = pool.get('tmi.move.line')
        cursor = Transaction().connection.cursor()

        result = {}
        ids = [a.id for a in groups]
        for name in names:
            if name not in {'baptism','tithe', 'church_planting', \
                    'gathering','small_group', 'organizing_church', \
                    'praise_thanksgiving', 'offering'}:
                raise ValueError('Unknown name: %s' % name)
            result[name] = dict((i, Decimal(0)) for i in ids)

        table = cls.__table__()
        line = MoveLine.__table__()
        #line_query = MoveLine.query_get(line)
        line_query, fiscalyear_ids = MoveLine.query_get(line)

        columns = [table.id]
        for name in names:
            columns.append(Sum(Coalesce(Column(line, name), 0)))
        for sub_ids in grouped_slice(ids):
            red_sql = reduce_ids(table.id, sub_ids)
            cursor.execute(*table.join(line, 'LEFT',
                    condition=line.group == table.id
                    ).select(*columns,
                    where=red_sql & line_query,
                    group_by=table.id))
            for row in cursor.fetchall():
                group_id = row[0]
                for i, name in enumerate(names, 1):
                    # SQLite uses float for SUM
                    if not isinstance(row[i], Decimal):
                        result[name][group_id] = Decimal(str(row[i]))
                    else:
                        result[name][group_id] = row[i]
        for group in groups:
            for name in names:
                exp = Decimal(str(10.0 ** -group.currency_digits))
                result[name][group.id] = (
                    result[name][group.id].quantize(exp))
        return result

class TmiGroupStatisticalContext(ModelView):
    'TMI Group Statistical Context'
    __name__ = 'tmi.statistical.context'

    year = fields.Many2One('tmi.year', 'Year',
        required=True) 
    start_period = fields.Many2One('tmi.period', 'Start Period',
        domain=[
            ('year', '=', Eval('year')),
            ('start_date', '<=', (Eval('end_period'), 'start_date'))
            ],
        depends=['end_period', 'year'])
    end_period = fields.Many2One('tmi.period', 'End Period',
        domain=[
            ('year', '=', Eval('year')),
            ('start_date', '>=', (Eval('start_period'), 'start_date')),
            ],
        depends=['start_period', 'year'])
    from_date = fields.Date("From Date",
        domain=[
            If(Eval('to_date') & Eval('from_date'),
                ('from_date', '<=', Eval('to_date')),
                ()),
            ],
        depends=['to_date'])
    to_date = fields.Date("To Date",
        domain=[
            If(Eval('from_date') & Eval('to_date'),
                ('to_date', '>=', Eval('from_date')),
                ()),
            ],
        depends=['from_date'])
    #company = fields.Many2One('company.company', 'Company', required=False)
    posted = fields.Boolean('Posted Move', help='Show only posted move')
    #comparison = fields.Boolean('Comparison')
    #year_cmp = fields.Many2One('tmi.year', 'Year',
    #    states={
    #        'required': Eval('comparison', False),
    #        'invisible': ~Eval('comparison', False),
    #        },)
    #start_period_cmp = fields.Many2One('tmi.period', 'Start Period',
    #    domain=[
    #        ('year', '=', Eval('year_cmp')),
    #        ('start_date', '<=', (Eval('end_period_cmp'), 'start_date'))
    #        ],
    #    states={
    #        'invisible': ~Eval('comparison', False),
    #        },
    #    depends=['end_period_cmp', 'year_cmp'])
    #end_period_cmp = fields.Many2One('tmi.period', 'End Period',
    #    domain=[
    #        ('year', '=', Eval('year_cmp')),
    #        ('start_date', '>=', (Eval('start_period_cmp'), 'start_date')),
    #        ],
    #    states={
    #        'invisible': ~Eval('comparison', False),
    #        },
    #    depends=['start_period_cmp', 'year_cmp'])
    #from_date_cmp = fields.Date("From Date",
    #    domain=[
    #        If(Eval('to_date_cmp') & Eval('from_date_cmp'),
    #            ('from_date_cmp', '<=', Eval('to_date_cmp')),
    #            ()),
    #        ],
    #    states={
    #        'invisible': ~Eval('comparison', False),
    #        },
    #    depends=['to_date_cmp', 'comparison'])
    #to_date_cmp = fields.Date("To Date",
    #    domain=[
    #        If(Eval('from_date_cmp') & Eval('to_date_cmp'),
    #            ('to_date_cmp', '>=', Eval('from_date_cmp')),
    #            ()),
    #        ],
    #    states={
    #        'invisible': ~Eval('comparison', False),
    #        },
    #    depends=['from_date_cmp', 'comparison'])

    @staticmethod
    def default_year():
        Year = Pool().get('tmi.year')
        return Year.find(exception=False)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_posted():
        return True

    @classmethod
    def default_comparison(cls):
        return False

    @fields.depends('year')
    def on_change_year(self):
        self.start_period = None
        self.end_period = None

    #@classmethod
    #def view_attributes(cls):
    #    return [
    #        ('/form/separator[@id="comparison"]', 'states', {
    #                'invisible': ~Eval('comparison', False),
    #                }),
    #        ]