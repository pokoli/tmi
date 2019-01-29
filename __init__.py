from trytond.pool import Pool
from . import group
from .move import * 
from .configuration import * 
from . import period
from . import company 
from . import report

def register():
    Pool.register(
    	group.TmiMetaGroup, 
        group.TmiGroup,
        group.TmiGroupStatisticalContext, 
        Move, 
        Line,
        Configuration,
        ConfigurationSequence, 
        ConfigurationTarget, 
        QuoteMoveDefault,
        period.Year,
        period.Period,
        company.Company,  
        report.PrintTmiReportStart, 
        module='tmi', type_='model')

    Pool.register(
        QuoteMove,
        report.PrintTmiReport, 
        module='tmi', type_='wizard')

    Pool.register(
        report.TmiReport, 
        module='tmi', type_='report') 