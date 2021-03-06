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

class account_removal_application_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_removal_application_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
             'time': time,
        })
        
    
file_path = join(addons.get_module_resource('account_custom_report'),'report/account_removal_application_report.rml')
report_sxw.report_sxw(
    'report.account.removal.application.report',
    'account.invoice',
    file_path,
    parser=account_removal_application_report,
    header='external'
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
