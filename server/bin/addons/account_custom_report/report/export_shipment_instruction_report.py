# -*- coding: utf-8 -*-
##############################################################################
#
#    Manufacturing Subcontracting Process
#    Copyright (C) 2004-2010 Browse Info Pvt Ltd (<http://www.browseinfo.com>).
#    $autor:
#   
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from os.path import join
import addons
import time
from datetime import datetime
from report import report_sxw

class export_shipment_instruction_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(export_shipment_instruction_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
             'time': time,
             'get_date_formate':self.get_date_formate,
             'get_airlines':self.get_airlines,
        })
        
    def get_date_formate(self, invoice_date):
        
        if invoice_date:
            list_date = str(invoice_date).split('/')
            date = list_date[0] +"." +list_date[1] +"." +list_date[2]
            return date
        else:
            return ' '
    def get_airlines(self, to_deliver):
        
        if to_deliver:
            return str(to_deliver).split(' ')[0]  
        else:
            return ''  
    
file_path = join(addons.get_module_resource('account_custom_report'),'report/export_shipment_instruction_report.rml')
report_sxw.report_sxw(
    'report.export.shipment.instruction.report',
    'account.invoice',
    file_path,
    parser=export_shipment_instruction_report,
    header=False
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
