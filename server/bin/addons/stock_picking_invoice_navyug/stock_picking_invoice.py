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

class account_invoice(osv.osv):
    
    _name = "account.invoice"
    _inherit = "account.invoice"
    
    _columns = {
                'dimension' : fields.char('Dimensions', size=240),
                }

class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"
    
    _columns = {
                'invoice_created': fields.boolean("Invoice Created", readonly=True)
                }
    
    _default = {
                'invoice_created': False,
                }
    
    def action_generate_invoice(self, cr, uid, ids, context=None):
        invoice_data = {}
        address_check = False
        default_address_id = False
        invoice_address_id = False
        contact_address_id = False
        picking_data = self.browse(cr, uid, ids[0], context)
        
        partner_obj = self.pool.get('res.partner')
        partner_data = partner_obj.browse(cr, uid, picking_data.partner_id.id, context)
        sale_tax_group = partner_data.sale_tax_group.id or False
        
        for address in partner_data.address:
            if address.type == 'default':
                default_address_id = address.id
                address_check = True
            if address.type == 'invoice':
                invoice_address_id = address.id
                address_check = True
            if address.type == 'contact' or address.type == 'delivery' or address.type == 'other':
                contact_address_id = address.id
                address_check = True
                
        if not address_check:
            raise osv.except_osv(_('Configuration Error !'), _('You must define address type to partner address.'))
        
        if not default_address_id:
            if partner_data.address:
                default_address_id = partner_data.address[0].id
        
        if not invoice_address_id:
            invoice_address_id = default_address_id
        if not contact_address_id:
            contact_address_id = default_address_id
        
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        stock_move_obj = self.pool.get('stock.move')
        production_obj = self.pool.get('mrp.production')
        sale_obj = self.pool.get('sale.order')
        
        
        print  " _\n\n\n______"
        invoice_data = {
                        'journal_id': 2,
                        'partner_id': picking_data.partner_id.id,
                        'address_invoice_id': invoice_address_id,
                        'address_contact_id': contact_address_id,
                        'sale_tax_group': sale_tax_group,
                        'user_id': uid,
                        'origin': picking_data.name,
                        'company_id': picking_data.partner_id.company_id.id,
                        'curreny_id': picking_data.partner_id.company_id.currency_id.id,
                        'account_id': picking_data.partner_id.property_account_receivable.id,
                        'dimension' : picking_data.x_dimension,
                        }
        
        res = invoice_obj.create(cr, uid, invoice_data)
        
        invoice_line_data = []
        production_orders = []
        
        discount = 0
        price_unit = 0
        
        for line in picking_data.move_lines:
            production_orders = []
            stock_line_ids = stock_move_obj.search(cr, uid, [('prodlot_id','=',line.prodlot_id.id)])
            stock_line_data = stock_move_obj.browse(cr, uid, stock_line_ids, context)
            
            for stock_line in stock_line_data:
                if stock_line.production_id:
                    if stock_line.production_id.id not in [x for x in production_orders]:
                        production_orders.append(stock_line.production_id.id)
            
            if len(production_orders) > 0:
                production_data = production_obj.browse(cr, uid, production_orders, context)
                for prod in production_data:
                    if prod.sale_name:
                        sale_ids = sale_obj.search(cr, uid, [('name','=',prod.sale_name)])
                        sale_data = sale_obj.browse(cr, uid, sale_ids, context)
                        if sale_data:
                            for sale_line in sale_data[0].order_line:
                                if sale_line.product_id.id == line.product_id.id:
                                    price_unit = sale_line.price_unit
                                    discount = sale_line.discount
                                    
            if not line.product_id.property_account_income:
                    raise osv.except_osv(_('Configuration Error !'), _("You must define Income Account for '%s'.") % (line.product_id.partner_ref,))
                                    
            if line.product_id.id not in [x['product_id'] for x in invoice_line_data]:
                invoice_line_data.append({
                                          'product_id': line.product_id.id,
                                          'quantity': line.product_qty,
                                          'uos_id': line.product_id.uom_id.id,
                                          'account_id': line.product_id.property_account_income.id,
                                          'name': line.product_id.partner_ref,
                                          'invoice_id': res,
                                          'price_unit': price_unit,
                                          'discount': discount,
                                          })
                price_unit = 0
                discount = 0
            else:
                if line.product_id.id in [x['product_id'] for x in invoice_line_data]:
                    qty_add_flag = False
                    for item in invoice_line_data:
                        if line.product_id.id == item['product_id'] and price_unit == item['price_unit'] and discount == item['discount']:
                            qty_add_flag = True
                    
                    if not qty_add_flag:
                        invoice_line_data.append({
                                                  'product_id': line.product_id.id,
                                                  'quantity': line.product_qty,
                                                  'uos_id': line.product_id.uom_id.id,
                                                  'account_id': line.product_id.property_account_income.id,
                                                  'name': line.product_id.partner_ref,
                                                  'invoice_id': res,
                                                  'price_unit': price_unit,
                                                  'discount': discount,
                                                  })
                    else:
                        for entry in invoice_line_data:
                            if line.product_id.id == entry['product_id'] and price_unit == entry['price_unit']:
                                entry['quantity'] = entry['quantity'] + line.product_qty
                    price_unit = 0
                    discount = 0
                                    
        for line in invoice_line_data:
            invoice_line_obj.create(cr, uid, line)
        
        self.write(cr, uid, ids, {'invoice_created': 't'})

        return True

stock_picking()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
