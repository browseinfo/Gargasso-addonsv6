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

from dateutil.relativedelta import relativedelta
import time

from osv.orm import browse_record, browse_null
from osv import fields, osv
from tools.translate import _
import netsvc

class mrp_production_merge(osv.osv_memory):
    _name = "mrp.production.merge"
    _description = "Merge Manufacturing Order"
    
    _columns = {
        'delivery_ids' : fields.many2many('mrp.production',  'merge_delivery_rel', 'merge_id', 'picking_id', 'Deliveries'),
    }

    def default_get(self, cr, uid, fields, context=None):
        """
        This function gets default values
        """
        record_ids = context and context.get('active_ids', False) or False
        res = super(mrp_production_merge, self).default_get(cr, uid, fields, context=context)

        if record_ids:
            pick_ids = []
            picks = self.pool.get('mrp.production').browse(cr, uid, record_ids, context=context)
            for pick in picks:
                if pick.state in ('draft', 'ready', 'assigned'):
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
        mo_obj = self.pool.get('mrp.production')
        mod_obj =self.pool.get('ir.model.data')
        if context is None:
            context = {}
        partner = []
        state = []
        result = mod_obj._get_id(cr, uid, 'mrp', 'mrp_production_form_view')
        id = mod_obj.read(cr, uid, result, ['res_id'])
        record = self.browse(cr, uid, ids[0], context=context)
        deliveries = record.delivery_ids

        if len(deliveries) < 2:
            raise osv.except_osv(_('Warning'),
                _('Please select multiple order to merge in the list view.'))

        for pick in deliveries:
#            partner.append(a.partner_id.id)
            if pick.state not in ('draft','picking_except','confirmed','ready'):
                raise osv.except_osv(_('Warning!'),
                         _('Merging is not allowed on In Production, Done Orders.'))
        total_qty = 0
        
        mo_id = deliveries[0]
        copy_mo_id = mo_obj.copy(cr, uid, deliveries[0].id,context=context)
        source = mo_obj.browse(cr,uid,copy_mo_id,context=context).name
        picking = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService("workflow")
        for id in deliveries:
            set_origin = ''
            if id.product_id != mo_id.product_id:
                raise osv.except_osv(_('Warning!'),
                        _('Merging is only allowed on Same Product.'))
            total_qty += id.product_qty
            if id.origin == '' : set_origin =  source
            else: set_origin +=  str(id.origin) +" - " + source
            mo_obj.write(cr,uid,[id.id],{'origin':set_origin })
            wf_service = netsvc.LocalService("workflow")
            #print "source:>>> ",source
            #pick_ids = picking.search(cr,uid,[('origin', 'ilike', source)])
            #print "pick_ids::> ",pick_ids
            #if pick_ids:
            #    for id in pick_ids:
            #        wf_service.trg_validate(uid, 'stock.picking', ids, 'button_cancel', cr)
            
            wf_service.trg_validate(uid, 'mrp.production', id.id, 'button_cancel', cr)
        mo_obj.write(cr,uid,[copy_mo_id],{'product_qty':total_qty, 'origin' : 'Merged MO'})
        
        

        return {
            'name': _('Manufacturing Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': copy_mo_id
        }

mrp_production_merge()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
