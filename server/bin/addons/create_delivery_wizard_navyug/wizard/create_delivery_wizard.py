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

from osv import osv, fields
from tools.translate import _
import netsvc

class stock_delivery_createlines(osv.osv_memory):
    _name = "stock.delivery.createlines"

    _columns = {
        'sale_order' : fields.char('Sale Order Number', size=200),
        'sale_all_order' : fields.char('All Sale Order Number', size=200),
        'partner_id': fields.many2one('res.partner', "Partner"),
        'delivery_ids' : fields.one2many('stock.delivery.orderlines','createlines_id','Delivery Lines'),
    }
    
    _defaults = {

    }
    
    def create_lines(self, cr, uid, ids, context={}):
        context['non_update'] = True
        mrp_ids = []
        cust_list = []
        result = dict()
        sale_order_name = ''
        mrp_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get('stock.move')
        sale_obj = self.pool.get('sale.order')
        order_lines_obj = self.pool.get('stock.delivery.orderlines')
        sale_order_wiz = self.browse(cr, uid, ids, context=context)[0]
        
        linesids = order_lines_obj.search(cr, uid, [('createlines_id','=', ids[0])])
        order_lines_obj.unlink(cr, uid, linesids, context)
        
        sale_order = sale_order_wiz.sale_order
        sale_all_order = sale_order_wiz.sale_all_order

        delivery_ids = sale_order_wiz.delivery_ids
        sale_order_ids = sale_order.split(',')
        
        sale_id=[]
        for sale_name in sale_order_ids:
            saleid = sale_obj.search(cr, uid, [('origin','=', sale_name)])
            if saleid:
                sale_id.append(saleid[0])
            else:
                message = "Sales order (%s) not found in ERP. Sales order name are case sensitive."%(sale_name)
                raise osv.except_osv(_('Warning !'),_(message))
        sale_data = sale_obj.browse(cr, uid, sale_id, context)
        for sale_value in sale_data:
            if sale_order_name =='':
                sale_order_name = sale_value.origin
            else:
                sale_order_name = sale_order_name + ',' + sale_value.origin
            if sale_value.partner_id.id not in cust_list and len(cust_list)==0:
                cust_list.append(sale_value.partner_id.id)
            else:
                if sale_value.partner_id.id not in cust_list:
                    message = "Partners should be same for provided sale orders."
                    raise osv.except_osv(_('Warning !'),_(message))
                    
        for sale_id in sale_order_ids:
            if sale_id<>'':
                mrpid = mrp_obj.search(cr, uid, [('origin', 'ilike', sale_id), ('state','in', ('in_production', 'done'))])
                if mrpid:
                    for mid in mrpid:
                        mrp_ids.append(mid)
            
        picking_obj = self.pool.get('stock.picking')
        list_move = []
        

        wlist = list()
        crm_po_no = False
        if mrp_ids:
            for mrp_id in mrp_ids:
                mrp_data = mrp_obj.browse(cr, uid, mrp_id, context=context)
                sale_id = sale_obj.search(cr, uid, [('name','=',mrp_data.sale_name)])
                if sale_id:
                    crm_po_no = sale_obj.browse(cr, uid, sale_id[0],context=context).crm_po_no
                mrp_move_ids = mrp_data.move_created_ids2
                if mrp_move_ids:
                    for mrp_move_id in mrp_move_ids:
                        ids_mov = [mrp_move_id.id]
                        for move in move_obj.browse(cr, uid, ids_mov, context=context):
                            if move.state == 'done':
                                move_data = move_obj.browse(cr, uid, move.id, context=context)
                                if move.prodlot_id.stock_available>0:
                                    order_data = {
                                                  'createlines_id': ids[0],
                                                  'stock_move_id': move.id,
                                                  'product_id': move.product_id.id,
                                                  'product_qty': move.prodlot_id.stock_available,
                                                  'product_uom': move.product_uom.id,
                                                  'prodlot_id': move.prodlot_id.id,
                                                  'crm_po_no': crm_po_no
                                                  }
                                    res = order_lines_obj.create(cr, uid, order_data, context)
                                    wlist.append(order_data)
                                    list_move.append(res)
                else:
                    raise osv.except_osv(_('Warning !'),_('There is no finished products on this sales order.'))
            
            self.write(cr, uid, ids, {'sale_all_order': sale_order_name,'partner_id': cust_list[0]},context=context)
        else:
            raise osv.except_osv(_('Warning !'),_('There is no finished products on this manufacturing order.'))
        return {'delivery_ids': wlist}


    def create_do_lines(self, cr, uid, ids, context={}):
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        mod_obj = self.pool.get('ir.model.data')
        self_data = self.browse(cr, uid, ids[0], context=context)
        do_ids = self_data.delivery_ids
        ref = self_data.sale_all_order
        partner_id = self_data.partner_id
        address_id = ''

        input_location = mod_obj.get_object_reference(cr, uid, 'stock', 'stock_location_stock')
        output_location = mod_obj.get_object_reference(cr, uid, 'stock', 'stock_location_customers')
        
        for address in partner_id.address:
            if address.type=='delivery':
                address_id = address.id
            if address.type=='default' and address_id=='':
                address_id = address.id
                break
        
        if address_id=='':
            raise osv.except_osv(_(u'Warning !'),_(u'Please assign address type to partner address.'))
            return True
         
        if not do_ids:
            raise osv.except_osv(_(u'Warning !'),_(u'There is no move line for create delivery Order.'))
            return True
        else:
            pick_data = {
            'type': 'out',
            'state': 'draft',
            'origin' : ref,
            'partner_id': partner_id.id,
            'address_id': address_id,
            }
            picking_id = picking_obj.create(cr, uid, pick_data)
            for do_id in do_ids:
                for move in move_obj.browse(cr, uid, [do_id.stock_move_id], context=context):
                    search_ids = move_obj.search(cr, uid, [('prodlot_id','=',move.prodlot_id.id),('state','!=','done'),\
                                                           ('location_id','=',input_location[1]),('location_dest_id','=',output_location[1]),\
                                                           ('picking_id','!=',picking_id)])
                    if not search_ids:
                        move_line = {
                                'name': move.name,
                                'picking_id': picking_id,
                                'product_id': move.product_id.id,
                                'date': move.date,
                                'date_expected': move.date_expected,
                                'product_qty': do_id.product_qty,
                                'product_uom': move.product_uom.id,
                                'product_uos_qty': (move.product_uos and move.product_uos_qty) or move.product_qty,
                                'product_uos': (move.product_uos and move.product_uos.id)\
                                    or move.product_uom.id,
                                'product_packaging': move.product_packaging.id,
                                'location_id': input_location[1],#move.location_id and move.location_id.id or False,
                                'location_dest_id': output_location[1],#9 or False,
                                'tracking_id': do_id.tracking_id.id,
                                'state': 'draft',
                                'note': move.note,
                                'company_id': move.company_id.id,
                                'prodlot_id': do_id.prodlot_id.id, #move.prodlot_id.id and move.prodlot_id.id or False,
                                'x_spool_number': do_id.x_spool_number,
                                'partner_id': partner_id.id,
                                'crm_po_no': do_id.crm_po_no
                                }
                        move_id = move_obj.create(cr, uid, move_line)
                    else:
                        move_data = move_obj.browse(cr, uid, search_ids[0], context)
                        message = "A delivery line already exists for production lot %s, and delivery line is not in done state. Kindly process the line to create delivery order."%(move.prodlot_id.name)
                        if move_data.picking_id:
                            move_picking = picking_obj.browse(cr, uid, move_data.picking_id.id, context)
                            message = "Delivery line already exists for production lot %s in delivery order %s, and delivery order is not in done state. Kindly process delivery order first."%(move.prodlot_id.name,move_picking.name,) 
                        raise osv.except_osv(_('Warning !'),_(message))
                        return True
        
        cases = self.browse(cr, uid, ids)
        data_obj = self.pool.get('ir.model.data')
        result = data_obj._get_id(cr, uid, 'stock', 'view_picking_out_form')
        view_id = data_obj.browse(cr, uid, result).res_id
        return {
                'type': 'ir.actions.act_window',
                'name': 'Delivery Order',
                'res_model': 'stock.picking',
                'context':{'type' : 'out', 'active_id': picking_id},
                'view_type':'form',
                'view_mode': 'form',
                'view_id' : [view_id],
                'res_id':picking_id
                }


stock_delivery_createlines()

class stock_delivery_orderlines(osv.osv_memory):
    _name = "stock.delivery.orderlines"
    
    _columns = {
                'createlines_id': fields.many2one('stock.delivery.createlines', 'Delivery Lines', ondelete="cascade"),
                'stock_move_id': fields.integer("Stock Move ID"),
                'product_id': fields.many2one("product.product", 'Product', required=True),
                'product_qty': fields.char("Quantity", size=120),
                'product_uom': fields.many2one("product.uom", "UOM"),
                'prodlot_id': fields.many2one("stock.production.lot","Production Lot", required=True),
                'x_spool_number': fields.char("Spool Number", size=120),
                'tracking_id': fields.many2one('stock.tracking', "Box"),
                'crm_po_no': fields.char('CRM PO No', size=120)
#                'state': fields.char("State", size=120)
                }
    
    _default = {
#                'state': 'draft',
                'product_qty': 0.0,
                }
    
    def create(self, cr, uid, vals, context=None):
        if not context.get('non_update'):
            print vals
            if not vals.get('stock_move_id'):
                raise osv.except_osv(_('Error !'),_("No move lines found for this production lot in done state. Select another lot."))
                return False
            else:
                new_id = super(stock_delivery_orderlines, self).create(cr, uid, vals, context)
        else:
            new_id = super(stock_delivery_orderlines, self).create(cr, uid, vals, context)
        return new_id
    
    def onchange_production_lot(self, cr, uid, ids, prodlot_id):
        print prodlot_id
        if prodlot_id:
            prodlot_data = self.pool.get('stock.production.lot').browse(cr, uid, prodlot_id)
            move_obj = self.pool.get('stock.move')
            move_ids = move_obj.search(cr, uid, [('prodlot_id','=',prodlot_id),('production_id','!=',False),('state','=','done')])
            
            if move_ids:
                return {'value': {'product_qty': prodlot_data.stock_available, 'stock_move_id': int(move_ids[0])}}
            else:
                raise osv.except_osv(_('Error !'),_("No move lines found for this production lot in done state. Select another lot."))
                return False
        else:
            return {'value': {'product_qty': False, 'stock_move_id': False}}
    
    def onchange_product_id(self, cr, uid, ids, product_id):
        if product_id:
            product_data = self.pool.get('product.product').browse(cr, uid, product_id)
            return {'value': {'product_uom': product_data.uom_id.id}}
        else:
            return {'value': {'product_uom': False}}

stock_delivery_orderlines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
