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
    'name': 'Stock Product Category Filter',
    'version': '1.0',
    'category': 'Generic Modules/Inventory Control',
    'description': """
    A Module applies product category filter in production lot search view.
    """,
    'author': 'Navyug Infosolutions Pvt. Ltd.',
    'website': 'http://www.navyuginfo.com',
    'depends': ['stock'],
	"update_xml": ['stock_prod_category_filter_view.xml'],
    'demo': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
