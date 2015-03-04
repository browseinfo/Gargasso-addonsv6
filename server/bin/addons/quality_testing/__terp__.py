# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-2012 Navyug Infosolutions.
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
    'name': 'Quality Testing',
    'version': '1.0',
    'category': 'Inventory/Quality Control',
    'description': """
    A Module provides testing parameters for finished product
    """,
    'author': 'Navyug Infosolutions',
    'website': 'http://www.navyuginfo.com',
    'depends': ['base', 'product', 'stock'],
	"update_xml": ["security/quality_security.xml",
                   "security/ir.model.access.csv",
                   "quality_testing_view.xml",
                   "quality_data.xml",
                   "quality_testing_report.xml"],
    'demo': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: