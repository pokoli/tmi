# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.model import MultiValueMixin, ValueMixin
from trytond import backend
from trytond.tools.multivalue import migrate_property

__all__ = ['GpSequence']

gp_sequence = fields.Many2One('ir.sequence', 'Gp Sequence',
    domain=[
        ('code', '=', 'disc.gp'),
        ],
    help="Used to generate the code.")

class GpSequence(ModelSingleton, ModelSQL, ModelView, MultiValueMixin):
    'Gp Sequence'
    __name__ = 'disc.gp.configuration'

    gp_sequence = fields.MultiValue(gp_sequence)

 