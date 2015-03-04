# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields
from osv import osv

class mrp_subproduct(osv.osv):
    _name = 'mrp.subproduct'
    _description = 'Sub Product'
    _columns={
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'product_qty': fields.float('Product Qty', required=True),
        'product_uom': fields.many2one('product.uom', 'Product UOM', required=True),
        'subproduct_type': fields.selection([('fixed','Fixed'),('variable','Variable')], 'Quantity Type', required=True),
        'bom_id': fields.many2one('mrp.bom', 'BoM'),
    }
    _defaults={
        'subproduct_type': lambda *args: 'fixed'
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """ Changes UoM if product_id changes.
        @param product_id: Changed product_id
        @return: Dictionary of changed values
        """
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            v = {'product_uom': prod.uom_id.id}
            return {'value': v}
        return {}

mrp_subproduct()

class mrp_bom(osv.osv):
    _name = 'mrp.bom'
    _description = 'Bill of Material'
    _inherit='mrp.bom'

    _columns={
        'sub_products':fields.one2many('mrp.subproduct', 'bom_id', 'sub_products'),
    }
mrp_bom()

class mrp_production(osv.osv):
    _description = 'Production'
    _inherit= 'mrp.production'

    def action_confirm(self, cr, uid, ids):
        """ Confirms production order and calculates quantity based on subproduct_type.
        @return: Newly generated picking Id.
        """
        picking_id = super(mrp_production,self).action_confirm(cr, uid, ids)
        for production in self.browse(cr, uid, ids):
            source = production.product_id.product_tmpl_id.property_stock_production.id
            if not production.bom_id:
                continue
            for sub_product in production.bom_id.sub_products:
                qty1 = sub_product.product_qty
                qty2 = production.product_uos and production.product_uos_qty or False
                if sub_product.subproduct_type == 'variable':
                    if production.product_qty:
                        qty1 *= production.product_qty / (production.bom_id.product_qty or 1.0)
                    if production.product_uos_qty:
                        qty2 *= production.product_uos_qty / (production.bom_id.product_uos_qty or 1.0)
                data = {
                    'name': 'PROD:'+production.name,
                    'date': production.date_planned,
                    'product_id': sub_product.product_id.id,
                    'product_qty': qty1,
                    'product_uom': sub_product.product_uom.id,
                    'product_uos_qty': qty2,
                    'product_uos': production.product_uos and production.product_uos.id or False,
                    'location_id': source,
                    'location_dest_id': production.location_dest_id.id,
                    'move_dest_id': production.move_prod_id.id,
                    'state': 'waiting',
                    'production_id': production.id
                }
                self.pool.get('stock.move').create(cr, uid, data)
        return picking_id
    
    def _get_subproduct_factor(self, cr, uid, production_id, move_id=None, context=None):
        """Compute the factor to compute the qty of procucts to produce for the given production_id. By default, 
            it's always equal to the quantity encoded in the production order or the production wizard, but with 
            the module mrp_subproduct installed it can differ for subproducts having type 'variable'.
        :param production_id: ID of the mrp.order
        :param move_id: ID of the stock move that needs to be produced. Identify the product to produce.
        :return: The factor to apply to the quantity that we should produce for the given production order and stock move.
        """
        sub_obj = self.pool.get('mrp.subproduct')
        move_obj = self.pool.get('stock.move')
        production_obj = self.pool.get('mrp.production')
        production_browse = production_obj.browse(cr, uid, production_id, context=context)
        move_browse = move_obj.browse(cr, uid, move_id, context=context)
        subproduct_factor = 1
        sub_id = sub_obj.search(cr, uid,[('product_id', '=', move_browse.product_id.id),('bom_id', '=', production_browse.bom_id.id), ('subproduct_type', '=', 'variable')], context=context)
        if sub_id:
            subproduct_record = sub_obj.browse(cr ,uid, sub_id[0], context=context)
            if subproduct_record.bom_id.product_qty:
                subproduct_factor = subproduct_record.product_qty / subproduct_record.bom_id.product_qty
                return subproduct_factor
        return super(mrp_production, self)._get_subproduct_factor(cr, uid, production_id, move_id, context=context)

mrp_production()

class change_production_qty(osv.osv_memory):
    _inherit = 'change.production.qty'

    def _update_product_to_produce(self, cr, uid, prod, qty, context=None):
        bom_obj = self.pool.get('mrp.bom')
        move_lines_obj = self.pool.get('stock.move')
        prod_obj = self.pool.get('mrp.production')
        for m in prod.move_created_ids:
            if m.product_id.id == prod.product_id.id:
                move_lines_obj.write(cr, uid, [m.id], {'product_qty': qty})
            else:
                for sub_product_line in prod.bom_id.sub_products:
                    if sub_product_line.product_id.id == m.product_id.id:
                        factor = prod_obj._get_subproduct_factor(cr, uid, prod.id, m.id, context=context)
                        subproduct_qty = sub_product_line.subproduct_type == 'variable' and qty * factor or sub_product_line.product_qty
                        move_lines_obj.write(cr, uid, [m.id], {'product_qty': subproduct_qty})
                        
change_production_qty()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: