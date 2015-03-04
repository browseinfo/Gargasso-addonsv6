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

from osv import fields, osv
import time
from tools.translate import _

class procurement_order(osv.osv):
    """
    Procurement Orders
    """
    _name = "procurement.order"
    _inherit = "procurement.order"
    

    def make_mo(self, cr, uid, ids, context=None):
        result = super(procurement_order, self).make_mo(cr, uid, ids, context)
        aerospace = False
        aerospace_check=False
        production_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get("stock.move")
        
        procurement_obj = self.pool.get('procurement.order')
        for procurement in procurement_obj.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            move_ids = move_obj.search(cr, uid, [('id','=',res_id)])
            if move_ids:
                move_data = move_obj.browse(cr, uid, move_ids,context)
                if move_data[0].sale_line_id:
                    aerospace_check = move_data[0].sale_line_id.order_id.aerospace
        if aerospace_check:
            prod_ids = production_obj.search(cr, uid, [('move_prod_id','=',res_id)])
            production_obj.write(cr, uid, prod_ids, {'x_job_order_type': 'Aerospace'})

        return result
    
procurement_order()

class sale_order(osv.osv):
    _name = "sale.order"
    _inherit = "sale.order"
    
    _columns = {
                'aerospace': fields.boolean("MO Type Aerospace", help="Select to create manufacturing order as 'Aerospace'."),
                'crm_po_no': fields.char("CRM PO Number", size=120),
                }
    
sale_order()

class stock_move(osv.osv):
    _inherit = "stock.move"
    _columns = {
                'crm_po_no': fields.char("CRM PO Number", size=120),
                }
stock_move()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
