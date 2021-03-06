# -*- coding: utf-8 -*-
##############################################################################
#
#    Manufacturing Subcontracting Process
#    Copyright (C) 2004-2010 Browse Info Pvt Ltd (<http://www.browseinfo.in>).
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
    'name': 'MRP Subcontracting',
    'version': '1.0',
    'category': 'Generic Modules/Production',
    'description': """
        This module improve the MRP module's fuctionality in OpenERP:
    Features
    * Manage the Subcontracting process.
    * Check the quentity of supplier production location on Subcontracting
    * Gernerate the daily delivery report for Subcontracting
    * Merge the Subcontracting 's delievry with new sequance.   
    """,
    'author': 'Browse Info Pvt Ltd',
    'website': 'http://browseinfo.in',
    'depends': ['purchase','mrp_subproduct'],
    'init_xml': [],
    'update_xml': [
        'stock_sequence.xml',
        'wizard/stock_delivery_merge_view.xml',
        'wizard/stock_move_print_view.xml',
        'wizard/stock_remove_picking_view.xml',
        'wizard/add_qty_view.xml',
        'mrp_subcontract_invoice_view.xml',
        'subcontract_report_menu.xml',
        'report/mrp_subcontract_report_view.xml',
    ],
    'demo_xml': [
    ],
    'test':[
    ],
    'installable': True,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
