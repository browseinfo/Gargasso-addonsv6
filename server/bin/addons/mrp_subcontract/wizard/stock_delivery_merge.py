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


from dateutil.relativedelta import relativedelta
import time

from osv.orm import browse_record, browse_null
from osv import fields, osv
from tools.translate import _
import netsvc

class stock_delivery_merge(osv.osv_memory):
    _name = "stock.delivery.merge"
    _description = "Merge Delivery"
    
    _columns = {
        'delivery_ids' : fields.many2many('stock.picking',  'merge_delivery_rel', 'merge_id', 'picking_id', 'Deliveries',  domain=[('type', '=', 'out')]),
    }

    def default_get(self, cr, uid, fields, context=None):
        """
        This function gets default values
        """
        record_ids = context and context.get('active_ids', False) or False
        res = super(stock_delivery_merge, self).default_get(cr, uid, fields, context=context)

        if record_ids:
            pick_ids = []
            picks = self.pool.get('stock.picking').browse(cr, uid, record_ids, context=context)
            for pick in picks:
                if pick.state in ('draft', 'confirmed', 'assigned'):
                    pick_ids.append(pick.id)
            if 'delivery_ids' in fields:
                res.update({'delivery_ids': pick_ids})
        return res
        
    def do_merge(self, cr, uid, ids, context=None):
        """
             To merge similar type of delivery orders.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: delivery order view

        """
        pick_obj = self.pool.get('stock.picking')
        mod_obj =self.pool.get('ir.model.data')
        if context is None:
            context = {}
        partner = []
        state = []
        result = mod_obj._get_id(cr, uid, 'stock', 'view_picking_out_form')
        id = mod_obj.read(cr, uid, result, ['res_id'])
        record = self.browse(cr, uid, ids[0], context=context)
        deliveries = record.delivery_ids

        if len(deliveries) < 2:
            raise osv.except_osv(_('Warning'),
                _('Please select multiple order to merge in the list view.'))

        for pick in deliveries:
            partner.append(pick.partner_id.id)
            state.append(pick.state)
            if pick.state in ('done', 'cancel'):
                raise osv.except_osv(_('Warning!'),
                         _('Merging is only allowed on Draft , Confirmed  and Available Deliveries.'))
            if pick.type not in ('out'):
                raise osv.except_osv(_('Warning!'),
                        _('Merging is only allowed on Delivery Order.'))
        if not partner[1:] == partner[:-1]:
                 raise osv.except_osv(_('Warning!'),
                                         _('Merging is only allowed on same partner'))

        allorders = pick_obj.do_merge(cr, uid, [x.id for x in deliveries], context)
        pick_ids = map(int, allorders.keys())
        if state[1:] == state[:-1]:
            if state[0] == 'confirmed':
                pick_obj.draft_force_assign(cr, uid, pick_ids)
            elif state[0] == 'assigned':
                pick_obj.draft_validate(cr, uid, pick_ids)

        return {
            'domain': "[('id','in', [" + ','.join(map(str, allorders.keys())) + "])]",
            'name': _('Delivery Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'context': "{'type':'out'}",
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': id['res_id']
        }

    def do_merge_one(self, cr, uid, ids, context=None):
        """
             To create new sequence of delivery order.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: delivery order form view

        """
        pick_obj = self.pool.get('stock.picking')
        mod_obj =self.pool.get('ir.model.data')
        if context is None:
            context = {}
        pick_ids = []
        result = mod_obj._get_id(cr, uid, 'stock', 'view_picking_out_form')
        #id = mod_obj.read(cr, uid, result, ['res_id'])
        record = self.browse(cr, uid, ids[0], context=context)
        deliveries = record.delivery_ids
        
        if len(deliveries) > 1:
            raise osv.except_osv(_('Warning'),
                _('Please select single order to create sequence in the list view.'))

        name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
        for pick in deliveries:
            pick_obj.write(cr, uid, [pick.id], {'name': name}, context=context)
            pick_ids.append(pick.id)            

        return {
            'name': _('Delivery Orders'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'stock.picking',
            'context': "{'type':'out'}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': pick_ids and pick_ids[0] or False,
        }

stock_delivery_merge()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
