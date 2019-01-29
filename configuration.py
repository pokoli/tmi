# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal

from trytond import backend
from trytond.model import (ModelView, ModelSQL, ModelSingleton, ValueMixin,
    fields)
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.tools.multivalue import migrate_property
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)

__all__ = ['Configuration',
    'ConfigurationSequence',
    'ConfigurationTarget']


def default_func(field_name):
    @classmethod
    def default(cls, **pattern):
        return getattr(
            cls.multivalue_model(field_name),
            'default_%s' % field_name, lambda: None)()
    return default

class Configuration(
        ModelSingleton, ModelSQL, ModelView, CompanyMultiValueMixin):
    'TMI Configuration'
    __name__ = 'tmi.configuration'
    tmi_move_sequence = fields.MultiValue(fields.Many2One(
            'ir.sequence', "TMI Move Sequence", required=True,
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'tmi.move'),
                ]))
    tmi_baptism_target = fields.MultiValue(fields.Numeric(
        'TMI Group Baptism Target', required=True, digits=(16,0),
        ))
    tmi_small_group_target = fields.MultiValue(fields.Numeric(
        'TMI Group Small Group Target', required=True, digits=(16,0),
        ))
    tmi_tithe_target = fields.MultiValue(fields.Numeric(
        'TMI Group Tithe Target', required=True, digits=(16,0),
        ))
    tmi_offering_target = fields.MultiValue(fields.Numeric(
        'TMI Group Offering Target', required=True, digits=(16,0),
        ))
    tmi_praise_thanksgiving_target = fields.MultiValue(fields.Numeric(
        'TMI Group Praise and Thanksgiving Target', required=True, digits=(16,0),
        ))
    tmi_gathering_target = fields.MultiValue(fields.Numeric(
        'TMI Group Gathering Target', required=True, digits=(16,0),
        ))
    tmi_church_planting_target = fields.MultiValue(fields.Numeric(
        'TMI Group Church Planting Target', required=True, digits=(16,0),
        ))
    tmi_organizing_church_target = fields.MultiValue(fields.Numeric(
        'TMI Group Organizing Church Target', required=True, digits=(16,0),
        ))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'tmi_move_sequence':
            return pool.get('tmi.configuration.sequence')
        if field in {'tmi_baptism_target', 'tmi_small_group_target',
                'tmi_tithe_target','tmi_offering_target', 'tmi_praise_thanksgiving_target',
                'tmi_gathering_target','tmi_church_planting_target','tmi_organizing_church_target'}:
            return pool.get('tmi.configuration.target')
        return super(Configuration, cls).multivalue_model(field)

    @classmethod
    def default_tmi_baptism_target(cls, **pattern):
        return cls.multivalue_model('tmi_baptism_target').default_tmi_baptism_target()

    @classmethod
    def default_tmi_small_group_target(cls, **pattern):
        return cls.multivalue_model('tmi_small_group_target').default_tmi_small_group_target()

    @classmethod
    def default_tmi_tithe_target(cls, **pattern):
        return cls.multivalue_model('tmi_tithe_target').default_tmi_tithe_target()

    @classmethod
    def default_tmi_offering_target(cls, **pattern):
        return cls.multivalue_model('tmi_offering_target').default_tmi_offering_target()

    @classmethod
    def default_tmi_praise_thanksgiving_target(cls, **pattern):
        return cls.multivalue_model('tmi_praise_thanksgiving_target').default_tmi_praise_thanksgiving_target()

    @classmethod
    def default_tmi_gathering_target(cls, **pattern):
        return cls.multivalue_model('tmi_gathering_target').default_tmi_gathering_target()

    @classmethod
    def default_tmi_church_planting_target(cls, **pattern):
        return cls.multivalue_model('tmi_church_planting_target').default_tmi_church_planting_target()

    @classmethod
    def default_tmi_organizing_church_target(cls, **pattern):
        return cls.multivalue_model('tmi_organizing_church_target').default_tmi_organizing_church_target()

    default_tmi_move_sequence = default_func('tmi_move_sequence')


class ConfigurationSequence(ModelSQL, CompanyValueMixin):
    "TMI Configuration Sequence"
    __name__ = 'tmi.configuration.sequence'
    tmi_move_sequence = fields.Many2One(
        'ir.sequence', "TMI Sequence", required=True,
        domain=[
            ('company', 'in', [Eval('company', -1), None]),
            ('code', '=', 'tmi.move'),
            ],
        depends=['company'])

    @classmethod
    def default_tmi_move_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('tmi', 'sequence_move_tmi')
        except KeyError:
            return None

class ConfigurationTarget(ModelSQL, CompanyValueMixin):
    "TMI Configuration Target"
    __name__ = 'tmi.configuration.target'

    configuration = fields.Many2One('tmi.configuration', 'Configuration',
        required=True, ondelete='CASCADE')
    tmi_baptism_target = fields.Numeric(
        "TMI Group Baptism Target", 
        digits=(16,0))
    tmi_small_group_target = fields.Numeric(
        "TMI Group Small Group Target", 
        digits=(16,0))
    tmi_tithe_target = fields.Numeric(
        "TMI Group Tithe Target", 
        digits=(16,0))
    tmi_offering_target = fields.Numeric(
        "TMI Group Offering Target", 
        digits=(16,0))
    tmi_praise_thanksgiving_target = fields.Numeric(
        "TMI Group Praise and Thanksgiving Target", 
        digits=(16,0))
    tmi_gathering_target = fields.Numeric(
        "TMI Group Gathering Target", 
        digits=(16,0))
    tmi_church_planting_target = fields.Numeric(
        "TMI Group Church Planting Target", 
        digits=(16,0))
    tmi_organizing_church_target = fields.Numeric(
        "TMI Group Organizing Church Target", 
        digits=(16,0))

    @classmethod
    def default_tmi_baptism_target(cls):
        return Decimal('1')

    @classmethod
    def default_tmi_small_group_target(cls):
        return Decimal('1')

    @classmethod
    def default_tmi_tithe_target(cls):
        return Decimal('1')

    @classmethod
    def default_tmi_offering_target(cls):
        return Decimal('1')

    @classmethod
    def default_tmi_praise_thanksgiving_target(cls):
        return Decimal('1')

    @classmethod
    def default_tmi_gathering_target(cls):
        return Decimal('1')

    @classmethod
    def default_tmi_church_planting_target(cls):
        return Decimal('1')

    @classmethod
    def default_tmi_organizing_church_target(cls):
        return Decimal('1')