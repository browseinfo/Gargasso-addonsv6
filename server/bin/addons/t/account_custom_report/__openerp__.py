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


{
    'name': 'Accounting Custom Report ',
    'version': '1.0',
    'category': 'Generic Modules/Accounting',
    'description': """
        This module improve the Account module's fuctionality in OpenERP:
    Features
    * print Domestic and Export Invoice.
    """,
    'author': 'Navyug Infosolutions Pvt. Ltd.',
    'website': 'http://www.navyuginfo.com',
    'depends': ['account'],
    'init_xml': [],
    'update_xml': [
        'account_custom_report_view.xml',
    ],
    'demo_xml': [
    ],
    'test':[
    ],
    'installable': True,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: