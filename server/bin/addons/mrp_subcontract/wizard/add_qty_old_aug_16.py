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
from osv import fields, osv
from tools.translate import _

class add_production_qty(osv.osv_memory):
    _name = 'add.production.qty'
    _description = 'Change Quantity of Products'
    
    _columns = {
        'product_qty': fields.float('Add Qty', required=True),
    }
    def add_prod_qty(self, cr, uid, ids, context=None):
        dict_data = {}
        record_id = context and context.get('active_id',False)
        assert record_id, _('Active Id is not found')
        prod_obj = self.pool.get('mrp.production')
        bom_obj = self.pool.get('mrp.bom')
        for wiz_qty in self.browse(cr, uid, ids, context=context):
            prod = prod_obj.browse(cr, uid, record_id, context=context)
            tot_prod = prod.product_qty + wiz_qty.product_qty
            prod_obj.write(cr, uid,prod.id, {'product_qty': tot_prod}) #Main Qty which is correct
            prod_obj.action_compute(cr, uid, [prod.id])
            move_lines = prod.move_lines
            move_lines_obj = self.pool.get('stock.move')
            sub_obj = self.pool.get('mrp.subproduct')
            for move in move_lines:
                bom_point = prod.bom_id
                bom_id = prod.bom_id.id
                if not bom_point:
                    bom_id = bom_obj._bom_find(cr, uid, prod.product_id.id, prod.product_uom.id)
                if not bom_id:
                    raise osv.except_osv(_('Error'), _("Couldn't find bill of material for product"))
                bom_point = bom_obj.browse(cr, uid, [bom_id])[0]
                if not bom_id:
                    raise osv.except_osv(_('Error'), _("Couldn't find bill of material for product"))
                for m in prod.move_created_ids:
                    move_browse = move_lines_obj.browse(cr, uid, m.id)
                    if m.product_id.id == prod.product_id.id:
                        product_finish_qty = move_browse.product_qty
                factor = (product_finish_qty + wiz_qty.product_qty) * prod.product_uom.factor / bom_point.product_uom.factor
                res = bom_obj._bom_explode(cr, uid, bom_point, factor / bom_point.product_qty, [])
                least = bom_obj.browse(cr, uid, bom_id ,context=context)
                list_new = []
                for r in res[0]:
                    if r['product_id'] == move.product_id.id:
#                        print "$$$$$$$$$$$$$$$$$$", r['product_qty']
                        move_lines_obj.write(cr, uid, [move.id], {'product_qty' :  r['product_qty']})
            for m in prod.move_created_ids:
                move_browse = move_lines_obj.browse(cr, uid, m.id)
                if m.product_id.id == prod.product_id.id:
                    new_qty = move_browse.product_qty + wiz_qty.product_qty
                    move_lines_obj.write(cr, uid, [m.id], {'product_qty': new_qty})
                else:
                    for sub_product_line in prod.bom_id.sub_products:
                        if sub_product_line.subproduct_type == 'variable':
                            new_qty = move_browse.product_qty + (wiz_qty.product_qty * sub_product_line.product_qty)
                            move_lines_obj.write(cr, uid, [m.id], {'product_qty': new_qty})
                        
        return {}
    
add_production_qty()
