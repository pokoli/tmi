# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from dateutil.relativedelta import relativedelta
from trytond.model import ModelView, ModelSQL, Workflow, fields
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.tools import datetime_strftime
from trytond.pyson import Eval, If, PYSONEncoder
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.const import OPERATORS

__all__ = [
    'Year',
    'Period', 
]

_STATES = STATES = {
    'readonly': Eval('state') != 'open',
}
_DEPENDS = DEPENDS = ['state']

class Year(Workflow, ModelSQL, ModelView):
    'Tmi Year'
    __name__ = 'tmi.year'
    name = fields.Char('Name', size=None, required=True, depends=DEPENDS)
    start_date = fields.Date('Starting Date', required=True, states=STATES,
        domain=[('start_date', '<=', Eval('end_date', None))],
        depends=DEPENDS + ['end_date'])
    end_date = fields.Date('Ending Date', required=True, states=STATES,
        domain=[('end_date', '>=', Eval('start_date', None))],
        depends=DEPENDS + ['start_date'])
    periods = fields.One2Many('tmi.period', 'year', 'Periods',
            states=STATES, depends=DEPENDS)
    state = fields.Selection([
            ('open', 'Open'),
            ('close', 'Close'),
            ], 'State', readonly=True, required=True)
    icon = fields.Function(fields.Char("Icon"), 'get_icon')

    @classmethod
    def __setup__(cls):
        super(Year, cls).__setup__()
        cls._order.insert(0, ('start_date', 'ASC'))
        cls._error_messages.update({
                'no_year_date': 'No year defined for "%s".',
                'year_overlaps': ('Year "%(first)s" and '
                    '"%(second)s" overlap.'),
                'close_error': ('You can not close year "%s" until you '
                    'close all previous years.'),
                'reopen_error': ('You can not reopen year "%s" until '
                    'you reopen all later years.'),
                })
        cls._transitions |= set((
                ('open', 'close'),
                ('close', 'open'),
                ))
        cls._buttons.update({
                'create_period': {
                    'invisible': ((Eval('state') != 'open')
                        | Eval('periods', [0])),
                    'depends': ['state'],
                    },
                'close': {
                    'invisible': Eval('state') != 'open',
                    'depends': ['state'],
                    },
                'reopen': {
                    'invisible': Eval('state') != 'close',
                    'depends': ['state'],
                    },
                })

    @staticmethod
    def default_state():
        return 'open'

    def get_icon(self, name):
        return {
            'open': 'tryton-open',
            'close': 'tryton-close',
            }.get(self.state)

    @classmethod
    def validate(cls, years):
        super(Year, cls).validate(years)
        for year in years:
            year.check_dates()

    def check_dates(self):
        transaction = Transaction()
        connection = transaction.connection
        transaction.database.lock(connection, self._table)
        cursor = connection.cursor()
        table = self.__table__()
        cursor.execute(*table.select(table.id,
                where=(((table.start_date <= self.start_date)
                        & (table.end_date >= self.start_date))
                    | ((table.start_date <= self.end_date)
                        & (table.end_date >= self.end_date))
                    | ((table.start_date >= self.start_date)
                        & (table.end_date <= self.end_date)))
                & (table.id != self.id)))
        second_id = cursor.fetchone()
        if second_id:
            second = self.__class__(second_id[0])
            self.raise_user_error('year_overlaps', {
                    'first': self.rec_name,
                    'second': second.rec_name,
                    })

    @classmethod
    def delete(cls, years):
        Period = Pool().get('tmi.period')
        Period.delete([p for f in years for p in f.periods])
        super(Year, cls).delete(years)

    @classmethod
    @ModelView.button
    def create_period(cls, years, interval=1):
        '''
        Create periods for the years with month interval
        '''
        Period = Pool().get('tmi.period')
        to_create = []
        for year in years:
            period_start_date = year.start_date
            while period_start_date < year.end_date:
                period_end_date = period_start_date + \
                    relativedelta(months=interval - 1) + \
                    relativedelta(day=31)
                if period_end_date > year.end_date:
                    period_end_date = year.end_date
                name = datetime_strftime(period_start_date, '%Y-%m')
                if name != datetime_strftime(period_end_date, '%Y-%m'):
                    name += ' - ' + datetime_strftime(period_end_date, '%Y-%m')
                to_create.append({
                    'name': name,
                    'start_date': period_start_date,
                    'end_date': period_end_date,
                    'year': year.id,
                    'type': 'standard',
                    })
                period_start_date = period_end_date + relativedelta(days=1)
        if to_create:
            Period.create(to_create)

    @classmethod
    @ModelView.button
    def create_period_3(cls, years):
        '''
        Create periods for the years with 3 months interval
        '''
        cls.create_period(years, interval=3)

    @classmethod
    def find(cls, date=None, exception=True):
        '''
        Return the year for the
            at the date or the current date.
        If exception is set the function will raise an exception
            if any year is found.
        '''
        pool = Pool()
        Lang = pool.get('ir.lang')
        Date = pool.get('ir.date')

        if not date:
            date = Date.today()
        years = cls.search([
            ('start_date', '<=', date),
            ('end_date', '>=', date),
            ], order=[('start_date', 'DESC')], limit=1)
        if not years:
            if exception:
                lang = Lang.get()
                cls.raise_user_error('no_year_date', lang.strftime(date))
            else:
                return None
        return years[0].id

    @classmethod
    @ModelView.button
    @Workflow.transition('close')
    def close(cls, years):
        '''
        Close a year
        '''
        pool = Pool()
        Period = pool.get('tmi.period')
        
        transaction = Transaction()
        database = transaction.database
        connection = transaction.connection

        # Lock period to be sure no new period will be created in between.
        database.lock(connection, Period._table)

        for year in years:
            if cls.search([
                        ('end_date', '<=', year.start_date),
                        ('state', '=', 'open'),
                        ]):
                cls.raise_user_error('close_error', (year.rec_name,))

            periods = Period.search([
                    ('year', '=', year.id),
                    ])
            Period.close(periods)

    @classmethod
    @ModelView.button
    @Workflow.transition('open')
    def reopen(cls, years):
        '''
        Re-open a year
        '''

        for year in years:
            if cls.search([
                        ('start_date', '>=', year.end_date),
                        ('state', '!=', 'open'),
                        ]):
                cls.raise_user_error('reopen_error')        

class Period(Workflow, ModelSQL, ModelView):
    'Period'
    __name__ = 'tmi.period'
    name = fields.Char('Name', required=True)
    start_date = fields.Date('Starting Date', required=True, states=_STATES,
        domain=[('start_date', '<=', Eval('end_date', None))],
        depends=_DEPENDS + ['end_date'], select=True)
    end_date = fields.Date('Ending Date', required=True, states=_STATES,
        domain=[('end_date', '>=', Eval('start_date', None))],
        depends=_DEPENDS + ['start_date'], select=True)
    year = fields.Many2One('tmi.year', 'Year',
        required=True, states=_STATES, depends=_DEPENDS, select=True)
    state = fields.Selection([
            ('open', 'Open'),
            ('close', 'Close'),
            ], 'State', readonly=True, required=True)
    type = fields.Selection([
            ('standard', 'Standard'),
            ('adjustment', 'Adjustment'),
            ], 'Type', required=True,
        states=_STATES, depends=_DEPENDS, select=True)
    icon = fields.Function(fields.Char("Icon"), 'get_icon')

    @classmethod
    def __setup__(cls):
        super(Period, cls).__setup__()
        cls._order.insert(0, ('start_date', 'ASC'))
        cls._error_messages.update({
                'no_period_date': 'No period defined for date "%s".',
                'modify_del_period_moves': ('You can not modify/delete '
                    'period "%s" because it has moves.'),
                'create_period_closed_year': ('You can not create '
                    'a period on year "%s" because it is closed.'),
                'open_period_closed_year': ('You can not open period '
                    '"%(period)s" because its year "%(year)s" is '
                    'closed.'),
                'close_period_non_posted_move': ('You can not close period '
                    '"%(period)s" because there are non posted moves '
                    '"%(move)s" in this period.'),
                'periods_overlap': ('"%(first)s" and "%(second)s" periods '
                    'overlap.'),
                'check_move_sequence': ('Period "%(first)s" and "%(second)s" '
                    'have the same sequence.'),
                'year_dates': ('Dates of period "%s" are outside '
                    'are outside it\'s year dates.'),
                })
        cls._transitions |= set((
                ('open', 'close'),
                ('close', 'locked'),
                ('close', 'open'),
                ))
        cls._buttons.update({
                'close': {
                    'invisible': Eval('state') != 'open',
                    'depends': ['state'],
                    },
                'reopen': {
                    'invisible': Eval('state') != 'close',
                    'depends': ['state'],
                    },
                'lock': {
                    'invisible': Eval('state') != 'close',
                    'depends': ['state'],
                    },
                })

    @staticmethod
    def default_state():
        return 'open'

    @staticmethod
    def default_type():
        return 'standard'

    def get_icon(self, name):
        return {
            'open': 'tryton-open',
            'close': 'tryton-close',
            'locked': 'tryton-readonly',
            }.get(self.state)

    @classmethod
    def validate(cls, periods):
        super(Period, cls).validate(periods)
        for period in periods:
            period.check_dates()
            period.check_year_dates()

    @classmethod
    def get_period_ids(cls, name):
        pool = Pool()
        Period = pool.get('tmi.period')
        context = Transaction().context

        period = None
        if name.startswith('start_'):
            period_ids = []
            if context.get('start_period'):
                period = Period(context['start_period'])
        elif name.startswith('end_'):
            period_ids = []
            if context.get('end_period'):
                period = Period(context['end_period'])
            else:
                periods = Period.search([
                        ('year', '=', context.get('year')),
                        ('type', '=', 'standard'),
                        ],
                    order=[('start_date', 'DESC')], limit=1)
                if periods:
                    period, = periods

        if period:
            periods = Period.search([
                    ('year', '=', context.get('year')),
                    ('end_date', '<=', period.start_date),
                    ])
            if period.start_date == period.end_date:
                periods.append(period)
            if periods:
                period_ids = [p.id for p in periods]
            if name.startswith('end_'):
                # Always include ending period
                period_ids.append(period.id)
        return period_ids

    def check_dates(self):
        if self.type != 'standard':
            return True
        transaction = Transaction()
        connection = transaction.connection
        transaction.database.lock(connection, self._table)
        table = self.__table__()
        cursor = connection.cursor()
        cursor.execute(*table.select(table.id,
                where=(((table.start_date <= self.start_date)
                        & (table.end_date >= self.start_date))
                    | ((table.start_date <= self.end_date)
                        & (table.end_date >= self.end_date))
                    | ((table.start_date >= self.start_date)
                        & (table.end_date <= self.end_date)))
                & (table.year == self.year.id)
                & (table.type == 'standard')
                & (table.id != self.id)))
        period_id = cursor.fetchone()
        if period_id:
            overlapping_period = self.__class__(period_id[0])
            self.raise_user_error('periods_overlap', {
                    'first': self.rec_name,
                    'second': overlapping_period.rec_name,
                    })

    def check_year_dates(self):
        if (self.start_date < self.year.start_date
                or self.end_date > self.year.end_date):
            self.raise_user_error('year_dates', (self.rec_name,))

    @classmethod
    def find(cls, date=None, exception=True, test_state=True):
        '''
        Return the period 
            at the date or the current date.
        If exception is set the function will raise an exception
            if no period is found.
        If test_state is true, it will search on non-closed periods
        '''
        pool = Pool()
        Date = pool.get('ir.date')
        Lang = pool.get('ir.lang')

        if not date:
            date = Date.today()
        clause = [
            ('start_date', '<=', date),
            ('end_date', '>=', date),
            ('type', '=', 'standard'),
            ]
        if test_state:
            clause.append(('state', '=', 'open'))
        periods = cls.search(clause, order=[('start_date', 'DESC')], limit=1)
        if not periods:
            if exception:
                lang = Lang.get()
                cls.raise_user_error('no_period_date', lang.strftime(date))
            else:
                return None
        return periods[0].id

    @classmethod
    def _check(cls, periods):
        Move = Pool().get('tmi.move')
        moves = Move.search([
                ('period', 'in', [p.id for p in periods]),
                ], limit=1)
        if moves:
            cls.raise_user_error('modify_del_period_moves', (
                    moves[0].period.rec_name,))

    @classmethod
    def search(cls, args, offset=0, limit=None, order=None, count=False,
            query=False):
        args = args[:]

        def process_args(args):
            i = 0
            while i < len(args):
                # add test for xmlrpc and pyson that doesn't handle tuple
                if ((isinstance(args[i], tuple)
                            or (isinstance(args[i], list) and len(args[i]) > 2
                                and args[i][1] in OPERATORS))
                        and args[i][0] in ('start_date', 'end_date')
                        and isinstance(args[i][2], (list, tuple))):
                    if not args[i][2][0]:
                        args[i] = ('id', '!=', '0')
                    else:
                        period = cls(args[i][2][0])
                        args[i] = (args[i][0], args[i][1],
                            getattr(period, args[i][2][1]))
                elif isinstance(args[i], list):
                    process_args(args[i])
                i += 1
        process_args(args)
        return super(Period, cls).search(args, offset=offset, limit=limit,
            order=order, count=count, query=query)

    @classmethod
    def create(cls, vlist):
        FiscalYear = Pool().get('tmi.year')
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            if vals.get('year'):
                year = FiscalYear(vals['year'])
                if year.state != 'open':
                    cls.raise_user_error('create_period_closed_year',
                        (year.rec_name,))
        return super(Period, cls).create(vlist)

    @classmethod
    def write(cls, *args):
        Move = Pool().get('tmi.move')
        actions = iter(args)
        args = []
        for periods, values in zip(actions, actions):
            for key, value in values.items():
                if key in ('start_date', 'end_date', 'year'):
                    def modified(period):
                        if key in ['start_date', 'end_date']:
                            return getattr(period, key) != value
                        else:
                            return period.year .id != value
                    cls._check(list(filter(modified, periods)))
                    break
            if values.get('state') == 'open':
                for period in periods:
                    if period.year.state != 'open':
                        cls.raise_user_error('open_period_closed_year', {
                                'period': period.rec_name,
                                'year': period.year.rec_name,
                                })
            args.extend((periods, values))
        super(Period, cls).write(*args)

    @classmethod
    def delete(cls, periods):
        cls._check(periods)
        super(Period, cls).delete(periods)

    @classmethod
    @ModelView.button
    @Workflow.transition('close')
    def close(cls, periods):

        transaction = Transaction()
        database = transaction.database
        connection = transaction.connection
        Period = Pool().get('tmi.period')

        # Lock period to be sure no new period will be created in between.
        database.lock(connection, Period._table)

        pass 

    @classmethod
    @ModelView.button
    @Workflow.transition('open')
    def reopen(cls, periods):
        "Re-open period"
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('locked')
    def lock(cls, periods):
        pass