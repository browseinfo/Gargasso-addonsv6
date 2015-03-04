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
import decimal_precision as dp
from osv import fields, osv
import time

class account_invoice_type(osv.osv):
    _name = 'account.invoice.type'
    _description = "Account Invoice Type"
    
    _columns = {
                'name': fields.char("Invoice Type", size=120, help="Provide the name for Invoice Type"),
                'type_tax_use': fields.selection([('sale','Sale'),('purchase','Purchase'),('all','All')], 'Tax Application'),
                'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the invoice type without removing it."),
                'invoice_tax_line_ids': fields.one2many('account.invoice.type.line', 'invoice_type_line_id', 'Taxes')
                }
    _defaults = {
                 'active': True,
                 }

account_invoice_type()


class account_invoice_type_line(osv.osv):
    _name = 'account.invoice.type.line'
    _description = "Account Invoice Type Lines"
    
    _columns = {
                'invoice_type_line_id': fields.many2one('account.invoice.type','Invoice Type', required=True, ondelete="cascade"),
                'tax_sequence': fields.integer('Sequence', help="Sequence in which you want to apply taxes."),
                'name': fields.many2one('account.tax', "Taxes",required=True , help = "Tax."),
                }
    
    _default = {
                'tax_sequence': 0,
                }
    _order = 'tax_sequence'

account_invoice_type_line()

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    
    _columns = {
                'purchase_tax_group': fields.many2one('account.invoice.type','Purchase Tax/Invoice Type'),
                'sale_tax_group': fields.many2one('account.invoice.type', 'Sale Tax/Invoice Type')
                }
    
res_partner()

class account_invoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"
    
    _columns = {
                'purchase_tax_group': fields.many2one('account.invoice.type','Purchase Invoice Type'),
                'sale_tax_group': fields.many2one('account.invoice.type', 'Sale Invoice Type')
                }
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        invoice_addr_id = False
        contact_addr_id = False
        partner_payment_term = False
        acc_id = False
        bank_id = False
        fiscal_position = False
        purchase_tax_group = False
        sale_tax_group = False

        opt = [('uid', str(uid))]
        if partner_id:

            opt.insert(0, ('id', partner_id))
            res = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['contact', 'invoice'])
            contact_addr_id = res['contact']
            invoice_addr_id = res['invoice']
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if company_id:
                if p.property_account_receivable.company_id.id != company_id and p.property_account_payable.company_id.id != company_id:
                    property_obj = self.pool.get('ir.property')
                    rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
                    pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
                    if not rec_pro_id:
                        rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('company_id','=',company_id)])
                    if not pay_pro_id:
                        pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('company_id','=',company_id)])
                    rec_line_data = property_obj.read(cr,uid,rec_pro_id,['name','value_reference','res_id'])
                    pay_line_data = property_obj.read(cr,uid,pay_pro_id,['name','value_reference','res_id'])
                    rec_res_id = rec_line_data and rec_line_data[0].get('value_reference',False) and int(rec_line_data[0]['value_reference'].split(',')[1]) or False
                    pay_res_id = pay_line_data and pay_line_data[0].get('value_reference',False) and int(pay_line_data[0]['value_reference'].split(',')[1]) or False
                    if not rec_res_id and not pay_res_id:
                        raise osv.except_osv(_('Configuration Error !'),
                            _('Can not find account chart for this company, Please Create account.'))
                    account_obj = self.pool.get('account.account')
                    rec_obj_acc = account_obj.browse(cr, uid, [rec_res_id])
                    pay_obj_acc = account_obj.browse(cr, uid, [pay_res_id])
                    p.property_account_receivable = rec_obj_acc[0]
                    p.property_account_payable = pay_obj_acc[0]

            if type in ('out_invoice', 'out_refund'):
                acc_id = p.property_account_receivable.id
            else:
                acc_id = p.property_account_payable.id
            fiscal_position = p.property_account_position and p.property_account_position.id or False
            partner_payment_term = p.property_payment_term and p.property_payment_term.id or False
            if p.bank_ids:
                bank_id = p.bank_ids[0].id
            
            if p.purchase_tax_group:
                purchase_tax_group = p.purchase_tax_group.id
                
            if p.sale_tax_group:
                sale_tax_group = p.sale_tax_group.id 

        result = {'value': {
            'address_contact_id': contact_addr_id,
            'address_invoice_id': invoice_addr_id,
            'account_id': acc_id,
            'payment_term': partner_payment_term,
            'fiscal_position': fiscal_position,
            'purchase_tax_group': purchase_tax_group,
            'sale_tax_group': sale_tax_group
            }
        }

        if type in ('in_invoice', 'in_refund'):
            result['value']['partner_bank_id'] = bank_id

        if payment_term != partner_payment_term:
            if partner_payment_term:
                to_update = self.onchange_payment_term_date_invoice(
                    cr, uid, ids, partner_payment_term, date_invoice)
                result['value'].update(to_update['value'])
            else:
                result['value']['date_due'] = False

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(cr, uid, ids, bank_id)
            result['value'].update(to_update['value'])
        return result
    
    def button_reset_taxes(self, cr, uid, ids, context=None):
        taxes = []
        invoice_data = self.browse(cr, uid, ids[0], context)
        if not invoice_data.sale_tax_group and not invoice_data.purchase_tax_group:
            return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)
        fposition_id = invoice_data.fiscal_position
        fpos_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False
        
        if invoice_data.type in ('out_invoice', 'out_refund'):
            if invoice_data.sale_tax_group:
                invoice_type_data = self.pool.get('account.invoice.type').browse(cr, uid, invoice_data.sale_tax_group.id)
                tax_lines = invoice_type_data.invoice_tax_line_ids
                
                decorated = [(dict_['tax_sequence'], dict_) for dict_ in tax_lines]
                decorated.sort()
                sortedRes = [dict_ for (key, dict_) in decorated]
                
                for line in sortedRes:
                    taxes.append(line.name)
        else:
            print invoice_data.type
            if invoice_data.purchase_tax_group:
                invoice_type_data = self.pool.get('account.invoice.type').browse(cr, uid, invoice_data.purchase_tax_group.id)
                tax_lines = invoice_type_data.invoice_tax_line_ids
                
                decorated = [(dict_['tax_sequence'], dict_) for dict_ in tax_lines]
                decorated.sort()
                sortedRes = [dict_ for (key, dict_) in decorated]
                
                for line in sortedRes:
                    taxes.append(line.name)
        
        if len(taxes) > 0:
            tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)

            
        for line in invoice_data.invoice_line:
            if line.product_id:
                for id in tax_id:
                    inv_line_obj.write(cr, uid, [line.id],{'invoice_line_tax_id': [(3, id)]})
                    inv_line_obj.write(cr, uid, [line.id],{'invoice_line_tax_id': [(4, id)]})
        
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)
    
    
account_invoice()

class account_invoice_line(osv.osv):
    _name = "account.invoice.line"
    _inherit = "account.invoice.line"
    
    _columns = {
                'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Unit Price')),
                }
    
account_invoice_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
