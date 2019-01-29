# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
import datetime
from itertools import groupby, combinations
from operator import itemgetter
from collections import defaultdict

from sql import Null, Literal
from sql.aggregate import Sum, Max
from sql.conditionals import Coalesce, Case

from trytond.model import (ModelSingleton, DeactivableMixin, 
    ModelView, ModelSQL, DeactivableMixin, fields,
    Unique, Workflow, sequence_ordered, Check ) 
from trytond.wizard import Wizard, StateTransition, StateView, StateAction, \
    StateReport, Button
from trytond.report import Report
from trytond import backend
from trytond.pyson import Eval, Bool, If, PYSONEncoder
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.rpc import RPC
from trytond.tools import reduce_ids, grouped_slice
from trytond.config import config

__all__ = ['Move', 'Line', 
    'QuoteMove', 'QuoteMoveDefault'
    #'CancelMoves', 'CancelMovesDefault',
    #'PrintGeneralJournalStart', 'PrintGeneralJournal', 'GeneralJournal'
    ]

_MOVE_STATES = {
    'readonly': Eval('state') != 'draft',
}
_MOVE_DEPENDS = ['state']
_LINE_STATES = {
    'readonly': Eval('state') == 'valid',
    }
_LINE_DEPENDS = ['state']
STATES = [
    ('draft', 'Draft'),
    ('posted', 'Posted'),
    ('quotation', 'Quotation'),
    ('canceled', 'Canceled'),
    ]


class Move(Workflow, ModelSQL, ModelView):
    'TMI Move'
    __name__ = 'tmi.move'
    _rec_name = 'number'
    
    number = fields.Char('Number', readonly=True)
    post_number = fields.Char('Post Number', readonly=True,
        help='Also known as Folio Number')
    company = fields.Many2One('company.company', 'Company', required=True,
        states=_MOVE_STATES, depends=_MOVE_DEPENDS)
    date = fields.Date('Effective Date', required=True, select=True,
        states=_MOVE_STATES, depends=_MOVE_DEPENDS)
    post_date = fields.Date('Post Date', readonly=True, 
        states=_MOVE_STATES, depends=_MOVE_DEPENDS)
    description = fields.Char('Description', states=_MOVE_STATES,
        depends=_MOVE_DEPENDS)
    state = fields.Selection(STATES, 'State', readonly=True, required=True)
    group = fields.Many2One('tmi.meta.group', 'Group', required=True, 
        domain=[
            'OR',[ ('company','=',Eval('company',-1)), 
                ('company', 'in',Eval('company.childs',[])),
                ],
            ('type', 'in', ['church']),

            ],
        depends=_MOVE_DEPENDS+['company'],
        states=_MOVE_STATES,
        )
    period = fields.Many2One('tmi.period','Period',
        required=True, 
        states=_MOVE_STATES, depends=_MOVE_DEPENDS, 
        domain=[('state','=','open')]
        )
    lines = fields.One2Many('tmi.move.line', 'move', 'Lines',
        domain=[
            ('group.company', '=', Eval('company', -1)),
            ],
        states=_MOVE_STATES, 
        depends=_MOVE_DEPENDS + ['company'],
            context={
                'date': Eval('date'),
                'period': Eval('period'),
            }) 

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('report_unique', Unique(t, t.group, t.period),
                'Report repeated. You only can have one report by month and cruch. '),
            ]
        cls._check_modify_exclude = []
        cls._order.insert(0, ('date', 'DESC'))
        cls._order.insert(1, ('number', 'DESC'))
        cls._error_messages.update({
                'post_empty_move': ('You can not post move "%s" because it is '
                    'empty.'),
                'amount_can_not_be_zero': ('Amount to record can not be zero.'),
                'modify_move': ('You can not modify move "%s" because '
                    'it is posted or cancelled.'),
                'delete_cancel': ('Move "%s" must be cancelled before '
                    'deletion.'),
                'delete_numbered': ('The numbered move "%s" can not be '
                    'deleted.'),
                'date_outside_period': ('You can not create move "%(move)s" '
                    'because its date is outside its period.'),
                })
        cls._transitions |= set((
                ('draft', 'quotation'),
                ('draft', 'canceled'),
                ('quotation', 'posted'),
                ('quotation', 'draft'),
                ('quotation', 'canceled'),
                ('posted', 'quotation'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft', 'quotation']),
                    'icon': 'tryton-cancel',
                    'depends': ['state'],
                    },
                'draft': {
                    'invisible': Eval('state').in_(['draft','posted','canceled']),
                    'icon': If(Eval('state') == 'canceled',
                        'tryton-clear', 'tryton-go-previous'),
                    'depends': ['state'],
                    },
                'quote': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-go-next',
                    'depends': ['state'],
                    },
                'post': {
                    'invisible': Eval('state') != 'quotation',
                    'icon': 'tryton-ok',
                    'depends': ['state'],
                    },
                })
        cls.__rpc__.update({
                'post': RPC(
                    readonly=False, instantiate=0, fresh_session=True),
                })

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            if not vals.get('number'):
                pool = Pool()
                Sequence = pool.get('ir.sequence')
                Config = pool.get('tmi.configuration')
                config = Config(1)
                vals['number'] = Sequence.get_id(
                    config.tmi_move_sequence.id)

        moves = super(Move, cls).create(vlist)
        return moves

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def default_date(cls):
        pool = Pool()
        Date = pool.get('ir.date')
        return Date.today()

    @classmethod
    def _get_origin(cls):
        'Return list of Model names for origin Reference'
        return ['tmi.move']

    @classmethod
    def get_origin(cls):
        Model = Pool().get('ir.model')
        models = cls._get_origin()
        models = Model.search([
                ('model', 'in', models),
                ])
        return [('', '')] + [(m.model, m.name) for m in models]

    @classmethod
    def check_modify(cls, moves):
        'Check posted moves for modifications.'
        for move in moves:
            if move.state == 'posted':
                cls.raise_user_error('modify_posted_move', (move.rec_name,))

    @staticmethod
    def default_period():
        Period = Pool().get('tmi.period')
        return Period.find(exception=False)

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('post_number',) + tuple(clause[1:]),
            (cls._rec_name,) + tuple(clause[1:]),
            ]

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        all_moves = []
        args = []
        for moves, values in zip(actions, actions):
            #keys = list(values.keys())
            #for key in cls._check_modify_exclude:
            #    if key in keys:
            #        keys.remove(key)
            #if len(keys):
            #    cls.check_modify(moves)
            args.extend((moves, values))
            all_moves.extend(moves)
        super(Move, cls).write(*args)
        cls.validate_move(all_moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('canceled')
    def cancel(cls, moves):
        pool = Pool()
        Move = pool.get('tmi.move')
        Line = pool.get('tmi.move.line')

        # Write state to prevent move to go to other state
        cls.write(moves, {
                'state': 'canceled',
                })

    @classmethod
    def set_number(cls, moves):
        '''
        Fill the number field with the move sequence
        '''
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('tmi.configuration')

        config = Config(1)
        for move in moves:
            if move.number:
                continue
            else: 
                config = Config(1)
                move.post_date = Date.today()
                move.post_number = Sequence.get_id(
                    config.tmi_move_sequence.id)
        cls.save(moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, moves):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('quotation')
    def quote(cls, moves):
        cls.set_number(moves)

    @classmethod
    def delete(cls, moves):
        MoveLine = Pool().get('tmi.move.line')
        cls.check_modify(moves)
        
        # Cancel before delete
        cls.cancel(moves)
        for move in moves:
            if move.state != 'canceled':
                cls.raise_user_error('delete_cancel', (move.rec_name,))
            if move.post_number:
                cls.raise_user_error('delete_numbered', (move.rec_name,))
        MoveLine.delete([l for m in moves for l in m.lines])
        super(Move, cls).delete(moves)

    @classmethod
    def copy(cls, moves, default=None):
        Line = Pool().get('tmi.move.line')

        if default is None:
            default = {}
        default = default.copy()
        default['number'] = None
        default['post_number'] = None
        default['state'] = cls.default_state()
        default['post_date'] = None
        default['lines'] = None

        new_moves = []
        for move in moves:
            new_move, = super(Move, cls).copy([move], default=default)
            Line.copy(move.lines, default={
                    'move': new_move.id,
                    })
            new_moves.append(new_move)
        return new_moves

    @classmethod
    @ModelView.button
    def post(cls, moves):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Date = pool.get('ir.date')
        Line = pool.get('tmi.move.line')

        for move in moves:
            if not move.lines:
                cls.raise_user_error('post_empty_move', (move.rec_name,))
            company = None
            for line in move.lines:
                if not company:
                    company = line.group.company
        for move in moves:
            move.state = 'posted'
            if not move.post_number:
                Sequence = pool.get('ir.sequence')
                Config = pool.get('tmi.configuration')
                config = Config(1)
                move.post_date = Date.today()
                move.post_number = Sequence.get_id(
                    config.tmi_move_sequence.id)
        cls.validate_move(moves)
        cls.save(moves)

    @fields.depends('company','group','lines')
    def on_change_group(self): 
        self.lines = []
        if self.group: 
            pool = Pool()
            Group = pool.get('tmi.group')
            MetaGroup = pool.get('tmi.meta.group')
            Line = pool.get('tmi.move.line')
            meta_groups = MetaGroup.search(['id','=',self.group.id])
            company_id = None
            if self.company: 
                company_id = self.company.id 
            if len(meta_groups)==1: 
                meta_childs = meta_groups[0].childs
            lines_to_add = []
            for meta_child in meta_childs: 
                groups = Group.search([('meta','=',meta_child.id)])
                if len(groups)==1: 
                    line = Line()
                    line.group = groups[0].id 
                    line.baptism = Decimal('0')
                    line.tithe = Decimal('0')
                    line.offering = Decimal('0')
                    line.church_planting = Decimal('0')
                    line.gathering = Decimal('0')
                    line.small_group = Decimal('0')
                    line.organizing_church = Decimal('0')
                    line.praise_thanksgiving = Decimal('0')
                    line.state = 'draft'
                    line.move_state = 'draft'
                    if company_id: 
                        line.company = company_id 
                    lines_to_add.append(line)
                self.lines = lines_to_add

    @classmethod
    def validate(cls, moves):
        super(Move, cls).validate(moves)
        for move in moves:
            move.check_date()

    def check_date(self):
        if (self.date < self.period.start_date
                or self.date > self.period.end_date):
            self.raise_user_error('date_outside_period', {
                        'move': self.rec_name,
                        })

    @classmethod
    def validate_move(cls, moves):
        '''
        Validate balanced move
        '''
        pool = Pool()
        MoveLine = pool.get('tmi.move.line')
        line = MoveLine.__table__()

        cursor = Transaction().connection.cursor()

        amounts = {}
        move2draft_lines = {}
        for sub_move_ids in grouped_slice([m.id for m in moves]):
            red_sql = reduce_ids(line.move, sub_move_ids)

            #cursor.execute(*line.select(line.move,
                    #Sum(line.debit - line.credit),
            #        where=red_sql,
            #        group_by=line.move))
            #amounts.update(dict(cursor.fetchall()))

            cursor.execute(*line.select(line.move, line.id,
                    where=red_sql & (line.state == 'draft'),
                    order_by=line.move))
            move2draft_lines.update(dict((k, [j[1] for j in g])
                    for k, g in groupby(cursor.fetchall(), itemgetter(0))))

        valid_moves = []
        draft_moves = []
        for move in moves:
            #if move.id not in amounts:
            #    continue
            #amount = amounts[move.id]
            # SQLite uses float for SUM
            #if not isinstance(amount, Decimal):
            #    amount = Decimal(amount)
            draft_lines = MoveLine.browse(move2draft_lines.get(move.id, []))
            #if not move.company.currency.is_zero(amount):
            #    draft_moves.append(move.id)
            #    continue
            if not draft_lines:
                continue
            valid_moves.append(move.id)
            
        for move_ids, state in (
                (valid_moves, 'valid'),
                (draft_moves, 'draft'),
                ):
            if move_ids:
                for sub_ids in grouped_slice(move_ids):
                    red_sql = reduce_ids(line.move, sub_ids)
                    # Use SQL to prevent double validate loop
                    cursor.execute(*line.update(
                            columns=[line.state],
                            values=[state],
                            where=red_sql))

class Line(ModelSQL, ModelView):
    'TMI Move Line'
    __name__ = 'tmi.move.line'

    _states = {
        'readonly': Eval('move_state') != 'draft',
        }
    _depends = ['move_state']

    group = fields.Many2One('tmi.group', 'TMI Group', required=True,
            domain=[
            'OR',[ ('company','=',Eval('company',-1)), 
                ('company', 'in',Eval('company.childs',[])),
                ],
            ('type', 'in', ['small_group']),

            ],
        select=True, states=_states, depends=_depends+['company'])
    tithe = fields.Numeric('Tithe', digits=(16, Eval('currency_digits', 2)),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    baptism = fields.Numeric('Baptism', digits=(16,  0),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    church_planting = fields.Numeric('Church Planting', digits=(16, 0),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    gathering = fields.Numeric('Gathering', digits=(16, 0),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    small_group = fields.Numeric('Small Group', digits=(16, 0),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    organizing_church = fields.Numeric('Organizing Church', digits=(16, 0),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    praise_thanksgiving = fields.Numeric('Praise and Thanksgiving', digits=(16, Eval('currency_digits', 2)),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    offering = fields.Numeric('Offering', digits=(16, Eval('currency_digits', 2)),
        required=True, states=_states,
        depends=['currency_digits'] +
        _depends)
    move = fields.Many2One('tmi.move', 'Move', select=True, required=True,
        ondelete='CASCADE',
        states={
            'required': False,
            'readonly': (((Eval('state') == 'valid') | _states['readonly'])
                & Bool(Eval('move'))),
            },
        depends=['state'] + _depends)
    date = fields.Function(fields.Date('Effective Date', required=True,
            states=_states, depends=_depends),
            'get_move_field', setter='set_move_field',
            searcher='search_move_field')
    description = fields.Char('Description', states=_states, depends=_depends)
    move_description = fields.Function(fields.Char('Move Description',
            states=_states, depends=_depends),
        'get_move_field', setter='set_move_field',
        searcher='search_move_field')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Valid'),
        ], 'State', readonly=True, required=True)
    move_state = fields.Function(fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ], 'Move State'), 'on_change_with_move_state',
        searcher='search_move_field')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
            'on_change_with_currency_digits')
    company = fields.Function(fields.Many2One('company.company', 'Company', required=True,
            ondelete="RESTRICT"),
        'get_company', searcher='search_company')

    period = fields.Function(fields.Many2One('account.period', 'Period',
            states=_states, depends=_depends),
            'get_move_field', setter='set_move_field',
            searcher='search_move_field')
    date = fields.Function(fields.Date('Effective Date', required=True,
            states=_states, depends=_depends),
            'on_change_with_date', setter='set_move_field',
            searcher='search_move_field')

    del _states, _depends

    @classmethod
    def __setup__(cls):
        super(Line, cls).__setup__()
        table = cls.__table__()
        cls.__rpc__.update({
                'on_write': RPC(instantiate=0),
                })
        cls._order[0] = ('id', 'DESC')
        cls._error_messages.update({
                'modify_posted_move': ('You can not modify lines of move "%s" '
                    'because it is already posted.'),
                'modify_reconciled': ('You can not modify line "%s" because '
                    'it is reconciled.'),
                'move_inactive_group': ('You can not create a move line '
                    'with group "%s" because it is inactive.'),
                })
    
    def get_company(self, name=None):
        if self.move: 
            return self.move.company.id 

    @classmethod
    def search_company(cls, name, clause):
        return [('move.' + clause[0],) + tuple(clause[1:])]

    def get_move_field(self, name):
        field = getattr(self.__class__, name)
        if name.startswith('move_'):
            name = name[5:]
        value = getattr(self.move, name)
        if isinstance(value, ModelSQL):
            if field._type == 'reference':
                return str(value)
            return value.id
        return value

    @fields.depends('move', '_parent_move.date')
    def on_change_with_date(self, name=None):
        if self.move:
            return self.move.date

    @classmethod
    def set_move_field(cls, lines, name, value):
        if name.startswith('move_'):
            name = name[5:]
        if not value:
            return
        Move = Pool().get('tmi.move')
        Move.write([line.move for line in lines], {
                name: value,
                })

    @classmethod
    def search_move_field(cls, name, clause):
        nested = clause[0].lstrip(name)
        if name.startswith('move_'):
            name = name[5:]
        return [('move.' + name + nested,) + tuple(clause[1:])]

    @classmethod
    def default_date(cls):
        '''
        Return today
        '''
        return Pool().get('ir.date').today()

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_currency_digits():
        return 0

    @staticmethod
    def default_tithe():
        return Decimal(0)

    @staticmethod
    def default_baptism():
        return Decimal(0)

    @staticmethod
    def default_church_planting():
        return Decimal(0)

    @staticmethod
    def default_gathering():
        return Decimal(0)

    @staticmethod
    def default_small_group():
        return Decimal(0)

    @staticmethod
    def default_organizing_church():
        return Decimal(0)

    @staticmethod
    def default_praise_thanksgiving():
        return Decimal(0)

    @staticmethod
    def default_offering():
        return Decimal(0)

    @classmethod
    def default_move(cls):
        transaction = Transaction()
        context = transaction.context
        if context.get('period'):
            lines = cls.search([
                    ('move.period', '=', context['period']),
                    ('create_uid', '=', transaction.user),
                    ('state', '=', 'draft'),
                    ], order=[('id', 'DESC')], limit=1)
            if lines:
                line, = lines
                return line.move.id

    @fields.depends('group')
    def on_change_with_currency_digits(self, name=None):
        if self.group:
            return self.group.currency_digits
        else:
            return 0

    @classmethod
    def get_origin(cls):
        Move = Pool().get('tmi.move')
        return Move.get_origin()

    @fields.depends('group')
    def on_change_group(self):
        if self.group:
            self.currency_digits = self.group.currency_digits

    def get_move_field(self, name):
        field = getattr(self.__class__, name)
        if name.startswith('move_'):
            name = name[5:]
        value = getattr(self.move, name)
        if isinstance(value, ModelSQL):
            if field._type == 'reference':
                return str(value)
            return value.id
        return value

    @classmethod
    def set_move_field(cls, lines, name, value):
        if name.startswith('move_'):
            name = name[5:]
        if not value:
            return
        Move = Pool().get('tmi.move')
        Move.write([line.move for line in lines], {
                name: value,
                })

    @classmethod
    def search_move_field(cls, name, clause):
        nested = clause[0].lstrip(name)
        if name.startswith('move_'):
            name = name[5:]
        return [('move.' + name + nested,) + tuple(clause[1:])]

    @fields.depends('move', '_parent_move.state')
    def on_change_with_move_state(self, name=None):
        if self.move:
            return self.move.state
        return 'draft'

    def _order_move_field(name):
        def order_field(tables):
            pool = Pool()
            Move = pool.get('tmi.move')
            field = Move._fields[name]
            table, _ = tables[None]
            move_tables = tables.get('move')
            if move_tables is None:
                move = Move.__table__()
                move_tables = {
                    None: (move, move.id == table.move),
                    }
                tables['move'] = move_tables
            return field.convert_order(name, move_tables, Move)
        return staticmethod(order_field)

    order_date = _order_move_field('date')
    order_move_state = _order_move_field('state')

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('group.rec_name',) + tuple(clause[1:])]


    @classmethod
    def query_get(cls, table):
        
        #Return SQL clause for move line
        #depending of the context.
        #table is the SQL instance of tmi.move.line table
        
        pool = Pool()
        
        Move = pool.get('tmi.move')
        Year = pool.get('tmi.year')
        Period = pool.get('tmi.period')

        move = Move.__table__()
        year = Year.__table__()
        period = Period.__table__()
        context = Transaction().context
        

        year_ids = []
        where = Literal(True)

        if context.get('posted'):
            where &= move.state == 'posted'

        date = context.get('date')
        from_date, to_date = context.get('from_date'), context.get('to_date')
        year_id = context.get('year')
        period_ids = context.get('periods')

        if date:
            years = Year.search([
                    ('start_date', '<=', date),
                    ('end_date', '>=', date),
                    ], limit=1)
            if years:
                year_id = years[0].id
            else:
                year_id = -1
            year_ids = list(map(int, years))
            where &= period.year == year_id
            where &= move.date <= date
        elif year_id or period_ids or from_date or to_date:
            if year_id:
                year_ids = [year_id]
                where &= year.id == year_id
            if period_ids:
                where &= move.period.in_(period_ids)
            if from_date:
                where &= move.date >= from_date
            if to_date:
                where &= move.date <= to_date
        else:
            where &= year.state == 'open'
            years = Year.search([
                    ('state', '=', 'open'),
                    ])
            year_ids = list(map(int, years))

        # Use LEFT JOIN to allow database optimization
        # if no joined table is used in the where clause.
        return ((table.state != 'draft')
            & table.move.in_(move
                .join(period, 'LEFT', condition=move.period == period.id)
                .join(year, 'LEFT',
                    condition=period.year == year.id)
                .select(move.id, where=where)),
            year_ids)

    @classmethod
    def on_write(cls, lines):
        return list(set(l.id for line in lines for l in line.move.lines))

    @classmethod
    def validate(cls, lines):
        super(Line, cls).validate(lines)
        for line in lines:
            line.check_group()

    def check_group(self):
        if not self.group.active:
            self.raise_user_error('move_inactive_group', (
                    self.group.rec_name,))
    
    @classmethod
    def check_modify(cls, lines, modified_fields=None):
        '''
        Check if the lines can be modified
        '''
        if (modified_fields is not None):
            return
        journal_period_done = []
        for line in lines:
            if line.move.state == 'posted':
                cls.raise_user_error('modify_posted_move', (
                        line.move.rec_name,))

    @classmethod
    def delete(cls, lines):
        Move = Pool().get('tmi.move')
        cls.check_modify(lines)
        moves = [x.move for x in lines]
        super(Line, cls).delete(lines)
        Move.validate_move(moves)

    @classmethod
    def write(cls, *args):
        Move = Pool().get('tmi.move')

        actions = iter(args)
        args = []
        moves = []
        all_lines = []
        for lines, values in zip(actions, actions):
            cls.check_modify(lines, set(values.keys()))
            moves.extend((x.move for x in lines))
            all_lines.extend(lines)
            args.extend((lines, values))

        super(Line, cls).write(*args)

        Transaction().timestamp = {}
        Move.validate_move(list(set(l.move for l in all_lines) | set(moves)))

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Move = pool.get('tmi.move')
        move = None
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            if not vals.get('move'):
                if move is None:
                    move = Move()
                    move.date = vals.get('date')
                    move.save()
                vals['move'] = move.id
            else:
                # prevent computation of default date
                vals.setdefault('date', None)
        lines = super(Line, cls).create(vlist)
        # Re-browse for cache alignment
        moves = Move.browse(list(set(line.move for line in lines)))
        Move.check_modify(moves)
        Move.validate_move(moves)
        return lines

    @classmethod
    def copy(cls, lines, default=None):
        if default is None:
            default = {}
        if 'move' not in default:
            default['move'] = None
        return super(Line, cls).copy(lines, default=default)

class QuoteMove(Wizard):
    'Tmi Quote Move'
    __name__ = 'tmi.move.quote'
    
    start_state = 'default'
    default = StateView('tmi.move.quote.default',
        'tmi.tmi_move_quote_default_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Ok', 'cancel', 'tryton-ok', default=True),
            ])
    cancel = StateTransition()

    def transition_cancel(self):
        pool = Pool()
        Move = pool.get('tmi.move')
        Line = pool.get('tmi.move.line')

        moves = Move.browse(Transaction().context['active_ids'])

        for move in moves: 
            description = move.description

        # Write update move state
        Move.write(moves, {
                'description': description, 
                'state': 'draft',
                })
        return 'end' 

class QuoteMoveDefault(ModelView):
    'Tmi Quote Move Default'
    __name__ = 'tmi.move.quote.default'
    description = fields.Char('Description')

    @staticmethod
    def default_description():
        pool = Pool()
        Move = pool.get('tmi.move')

        description = ''
        moves = Move.browse(Transaction().context['active_ids'])
        if moves: 
            description = moves[0].description
        
        return description

