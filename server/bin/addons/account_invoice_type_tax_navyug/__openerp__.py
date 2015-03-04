# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Account Tax Grouping',
    'version': '1.1',
    'category': 'Indian Localization',
    'description': """
This module facilitates to create group of taxes and applied on partner, based on the invoice type selected in Invoice grouped taxes are applied on Invoice.
=====================================================================================================

""",
    'author': 'Navyug Infosolutions Pvt. Ltd.',
    'website': 'http://www.navyuginfo.com',
    'images': [],
    'depends': ['account'],
    'data': [
        'account_invoice_type_view.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: