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
from datetime import datetime, timedelta
from osv import osv, fields
import netsvc
from tools.translate import _

class mrp_bom(osv.osv):
	_inherit = 'mrp.bom'
	_name = 'mrp.bom'
	_description = 'Bill of Material'

	_columns = {
		'subcontract': fields.boolean('Subcontract', help="If your product is subcontracting then please checked it, It will provide you to create a invoice"),
		'product_ids': fields.many2many('product.product', 'subcontract_product_rel', 'bom_id', 'product_id', 'Service Product for subcontracting ', domain=[('type', '=', 'service')]),
	}

	_defaults = {
		'subcontract': False,
	}

mrp_bom()


class mrp_production(osv.osv):
	_inherit = 'mrp.production'
	_name = 'mrp.production'
	_description = 'Manufacturing Order'

	def onchange_partner_id(self, cr, uid, ids, part, address_id):
		""" On change of partner sets the values of partner address,
		partner invoice address and pricelist.
		@param part: Changed id of partner.
		@param address_id: Address id from current record.
		@return: Dictionary of values.
		"""
		part_obj = self.pool.get('res.partner')
		pricelist_obj = self.pool.get('product.pricelist')
		if not part:
			return {'value': {
				'address_id': False,
				'pricelist_id': pricelist_obj.search(cr, uid, [('type', '=', 'purchase')])[0]
				}
			}
		addr = part_obj.address_get(cr, uid, [part], ['invoice'])
		partner = part_obj.browse(cr, uid, part)
		pricelist = partner.property_product_pricelist_purchase and partner.property_product_pricelist_purchase.id or False
		return {'value': {
				'address_id': addr['invoice'],
				'pricelist_id': pricelist
				}
			}


	_columns = {
		'subcontract': fields.boolean('Subcontract'),
		'partner_id' : fields.many2one('res.partner', 'Supplier'),
		'address_id' : fields.many2one('res.partner.address', 'Invoice Address', domain="[('partner_id','=',partner_id)]"),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', help='The pricelist comes from the selected partner, by default.'),
		'invoice_id': fields.many2one('account.invoice', 'Invoice'),
		'invoice': fields.boolean('invoice'),

	}

	_defaults = {
		'subcontract': False,
		'invoice': False,
#        'pricelist_id': lambda self, cr, uid,context : self.pool.get('product.pricelist').search(cr, uid, [('type','=','purchase')])[0]
	}

	def create_invoice_subcontract(self, cr, uid, ids, context=None):
		""" Creates invoice(s) for subcontracting.
		@param group: It is set to true when group invoice is to be generated.
		@return: Invoice Ids.
		"""
		inv_line_obj = self.pool.get('account.invoice.line')
		inv_obj = self.pool.get('account.invoice')
		production_obj = self.browse(cr, uid, ids[0])
		service_products = production_obj.bom_id.product_ids
		journal_id = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'purchase')])[0]
		if not (production_obj.partner_id.id and production_obj.address_id.id):
			raise osv.except_osv(_('No partner !'), _('You have to select a Partner Invoice Address on Invoice tab !'))
		else:
			if not production_obj.partner_id.property_account_payable:
				raise osv.except_osv(_('Error !'), _('No account defined for Supplier "%s".') % production_obj.partner_id.name)
			account_id = production_obj.partner_id.property_account_payable.id
			inv = {
			'name': production_obj.name,
			'origin':production_obj.name,
			'journal_id':journal_id,
			'type': 'in_invoice',
			'account_id': account_id,
			'partner_id': production_obj.partner_id.id,
			'address_invoice_id': production_obj.address_id.id,
			'currency_id': production_obj.company_id.currency_id.id,
			'fiscal_position': production_obj.partner_id.property_account_position.id
			}
			inv_id = inv_obj.create(cr, uid, inv)
			self.write(cr, uid, production_obj.id, {'invoice_id': inv_id, 'invoice' : True})
		if service_products:
			for product in service_products:
				if product.property_account_expense:
					account_id = operation.product_id.property_account_expense.id
				elif product.categ_id.property_account_expense_categ:
					account_id = product.categ_id.property_account_expense_categ.id
				else:
					raise osv.except_osv(_('Error !'), _('No account defined for product "%s".') % product.name)

				invoice_line_id = inv_line_obj.create(cr, uid, {
					'invoice_id': inv_id,
					'name': product.name,
					'origin': production_obj.name,
					'account_id': account_id,
					'quantity': production_obj.product_qty,
					'uos_id': product.uom_po_id.id,
					'price_unit': product.standard_price,
					'price_subtotal': production_obj.product_qty * product.standard_price,
					'product_id': product.id
					})
		return True

	def write(self, cr, uid, ids, vals, context=None, update=False):
		if not isinstance(ids, list):
			ids = [ids]
		if ids:
			order_obj = self.browse(cr, uid, ids)[0]
			if order_obj.bom_id.subcontract == True:
				vals['subcontract'] = True
		return super(mrp_production, self).write(cr, uid, ids, vals, context=context)
	
##Code for subcontracting Process(action_confrirm Override here)

	def _make_production_line_procurement(self, cr, uid, production_line, shipment_move_id, context=None):
		wf_service = netsvc.LocalService("workflow")
		procurement_order = self.pool.get('procurement.order')
		production = production_line.production_id
		location_id = production.location_src_id.id
		date_planned = production.date_planned
		procurement_name = (production.origin or '').split(':')[0] + ':' + production.name
		procurement_id = procurement_order.create(cr, uid, {
				    'name': procurement_name,
				    'origin': procurement_name,
				    'date_planned': date_planned,
				    'product_id': production_line.product_id.id,
				    'product_qty': production_line.product_qty,
				    'product_uom': production_line.product_uom.id,
				    'product_uos_qty': production_line.product_uos and production_line.product_qty or False,
				    'product_uos': production_line.product_uos and production_line.product_uos.id or False,
				    'location_id': location_id,
				    'procure_method': production_line.product_id.procure_method,
				    'move_id': shipment_move_id,
				    'company_id': production.company_id.id,
				})
		wf_service.trg_validate(uid, procurement_order._name, procurement_id, 'button_confirm', cr)
		return procurement_id
	
	
	def _make_production_internal_shipment_line(self, cr, uid, production_line, shipment_id, parent_move_id, destination_location_id=False, context=None):
		stock_move = self.pool.get('stock.move')
		move_obj = self.pool.get('stock.move')
		stock_picking = self.pool.get('stock.picking')
		stock_location = self.pool.get('stock.location')
		product_uom_obj = self.pool.get('product.uom')
		product_obj = self.pool.get('product.product')
		production = production_line.production_id
		date_planned = production.date_planned
        # Internal shipment is created for Stockable and Consumer Products
		if production_line.product_id.type not in ('product', 'consu'):
			return False
		move_name = _('PROD: %s') % production.name
		source_location_id = production.location_src_id.id
		if not destination_location_id:
			destination_location_id = source_location_id
		usage = stock_location.browse(cr, uid, [destination_location_id], context=context)[0].usage
		if destination_location_id and usage == 'supplier':
			location_subcontract = production.bom_id.routing_id.location_id.id
			product_obj = product_obj.browse(cr, uid, production_line.product_id.id, context=context)
			default_uom = product_obj.uom_id and product_obj.uom_id.id
			outgoing_qty = 0.0
			incoming_qty = 0.0
			outgoing_ids = move_obj.search(cr, uid, [('product_id', 'in', [production_line.product_id.id]), ('location_dest_id', 'in', [location_subcontract]), ['state', 'not in', ('draft', 'cancel')]]) ##Qty Going TO Supplier
			incoming_ids = move_obj.search(cr, uid, [('product_id', 'in', [production_line.product_id.id]), ('location_id', 'in', [location_subcontract]), ['state', 'not in', ('draft', 'cancel')]]) ## Qty coming from the Supplier
			if outgoing_ids:
				for move in move_obj.browse(cr, uid, outgoing_ids):
					move_product_qty_uom = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)
					outgoing_qty = outgoing_qty + move_product_qty_uom
			if incoming_ids:
				for move in move_obj.browse(cr, uid, incoming_ids):
					move_product_qty_uom = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)
					incoming_qty = incoming_qty + move_product_qty_uom
				line_qty_withuom = product_uom_obj._compute_qty(cr, uid, production_line.product_uom.id, production_line.product_qty, default_uom) 
				incoming_qty = incoming_qty - line_qty_withuom ##Deducted the current stock move 's aqty
			location_stock = outgoing_qty - incoming_qty ##Find the Virtual stock of the Supplier Location
			
#			loc = self.pool.get('stock.location')
#			ctx = {'product_id':production_line.product_id.id}
#			ids_loc = production.routing_id.location_id.id
#			location_ids = loc.search(cr, uid, [('location_id', 'child_of', ids_loc)])
#			loc_dict = ['stock_virtual', 'stock_real']
#			prod_val = loc._product_value(cr, uid, location_ids,loc_dict,None,context=ctx)              
#			data_stock = prod_val.values()
#			location_stock = data_stock[0]['stock_real']
			
			consume_line_qty = product_uom_obj._compute_qty(cr, uid, production_line.product_uom.id, production_line.product_qty, default_uom)
			if location_stock < consume_line_qty:
				new_qty = consume_line_qty - location_stock
				new_qty_withuom = product_uom_obj._compute_qty(cr, uid, default_uom , new_qty, production_line.product_uom.id)
				return stock_move.create(cr, uid, {
						'name': move_name,
						'picking_id': shipment_id,
						'product_id': production_line.product_id.id,
						'product_qty': new_qty_withuom,
						'product_uom': production_line.product_uom.id,
						'product_uos_qty': production_line.product_uos and production_line.product_uos_qty or False,
						'product_uos': production_line.product_uos and production_line.product_uos.id or False,
						'date': date_planned,
						'move_dest_id': parent_move_id,
						'location_id': source_location_id,
						'location_dest_id': destination_location_id,
						'state': 'waiting',
						'company_id': production.company_id.id,
				})
			else:
				return {}
		return stock_move.create(cr, uid, {
				    'name': move_name,
				    'picking_id': shipment_id,
				    'product_id': production_line.product_id.id,
				    'product_qty': production_line.product_qty,
				    'product_uom': production_line.product_uom.id,
				    'product_uos_qty': production_line.product_uos and production_line.product_uos_qty or False,
				    'product_uos': production_line.product_uos and production_line.product_uos.id or False,
				    'date': date_planned,
				    'move_dest_id': parent_move_id,
				    'location_id': source_location_id,
				    'location_dest_id': destination_location_id,
				    'state': 'waiting',
				    'company_id': production.company_id.id,
			})
	
	def _make_production_internal_shipment(self, cr, uid, production, context=None):
		ir_sequence = self.pool.get('ir.sequence')
		stock_picking = self.pool.get('stock.picking')
		routing_loc = None
		pick_type = 'internal'
		address_id = False
		loc_usage = 'internal'

        # Take routing address as a Shipment Address.
        # If usage of routing location is a internal, make outgoing shipment otherwise internal shipment
		if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
			routing_loc = production.bom_id.routing_id.location_id
			if routing_loc.usage <> 'internal':
				pick_type = 'out'
				loc_usage = routing_loc.usage
			address_id = routing_loc.address_id and routing_loc.address_id.id or False
                
        # Take next Sequence number of shipment base on type
		if loc_usage == 'supplier':
			pick_name = ir_sequence.get(cr, uid, 'stock.picking.subcontract')
		else:
			pick_name = ir_sequence.get(cr, uid, 'stock.picking.' + pick_type)
            
		picking_id = stock_picking.create(cr, uid, {
			'name': pick_name,
			'origin': (production.origin or '').split(':')[0] + ':' + production.name,
			'type': pick_type,
			'move_type': 'one',
			'state': 'auto',
		    'address_id': address_id,
			'auto_picking': self._get_auto_picking(cr, uid, production),
			'company_id': production.company_id.id,
		})
		production.write({'picking_id': picking_id}, context=context)
		return picking_id

	def _make_production_produce_line(self, cr, uid, production, context=None):
		stock_move = self.pool.get('stock.move')
		source_location_id = production.product_id.product_tmpl_id.property_stock_production.id
		destination_location_id = production.location_dest_id.id
		move_name = _('PROD: %s') + production.name
		data = {
		    'name': move_name,
		    'date': production.date_planned,
		    'product_id': production.product_id.id,
		    'product_qty': production.product_qty,
		    'product_uom': production.product_uom.id,
		    'product_uos_qty': production.product_uos and production.product_uos_qty or False,
		    'product_uos': production.product_uos and production.product_uos.id or False,
		    'location_id': source_location_id,
		    'location_dest_id': destination_location_id,
		    'move_dest_id': production.move_prod_id.id,
		    'state': 'waiting',
		    'company_id': production.company_id.id,
		}
		move_id = stock_move.create(cr, uid, data, context=context)
		production.write({'move_created_ids': [(6, 0, [move_id])]}, context=context)
		return move_id

	def _make_production_consume_line(self, cr, uid, production_line, parent_move_id, source_location_id=False, context=None):
		stock_move = self.pool.get('stock.move')
		production = production_line.production_id
		# Internal shipment is created for Stockable and Consumer Products
		if production_line.product_id.type not in ('product', 'consu'):
		    return False
		move_name = _('PROD: %s') % production.name
		destination_location_id = production.product_id.product_tmpl_id.property_stock_production.id
		if not source_location_id:
		    source_location_id = production.location_src_id.id
		move_id = stock_move.create(cr, uid, {
		    'name': move_name,
		    'date': production.date_planned,
		    'product_id': production_line.product_id.id,
		    'product_qty': production_line.product_qty,
		    'product_uom': production_line.product_uom.id,
		    'product_uos_qty': production_line.product_uos and production_line.product_uos_qty or False,
		    'product_uos': production_line.product_uos and production_line.product_uos.id or False,
		    'location_id': source_location_id,
		    'location_dest_id': destination_location_id,
		    'move_dest_id': parent_move_id,
		    'state': 'waiting',
		    'company_id': production.company_id.id,
		    'x_mo_prod_seq': production_line.x_mo_prod_seq
		})
		production.write({'move_lines': [(4, move_id)]}, context=context)
		return move_id

	def action_confirm(self, cr, uid, ids, context=None):
		""" Confirms production order.
		@return: Newly generated Shipment Id.
		"""
		shipment_id = False
		wf_service = netsvc.LocalService("workflow")
		uncompute_ids = filter(lambda x:x, [not x.product_lines and x.id or False for x in self.browse(cr, uid, ids, context=context)])
		self.action_compute(cr, uid, uncompute_ids)
		for production in self.browse(cr, uid, ids, context=context):
		    shipment_id = self._make_production_internal_shipment(cr, uid, production, context=context)
		    produce_move_id = self._make_production_produce_line(cr, uid, production, context=context)

		    # Take routing location as a Source Location.
		    source_location_id = production.location_src_id.id
		    if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
		        source_location_id = production.bom_id.routing_id.location_id.id

		    for line in production.product_lines:
		        consume_move_id = self._make_production_consume_line(cr, uid, line, produce_move_id, source_location_id=source_location_id, context=context)
		        shipment_move_id = self._make_production_internal_shipment_line(cr, uid, line, shipment_id, consume_move_id, \
		                         destination_location_id=source_location_id, context=context)
		        self._make_production_line_procurement(cr, uid, line, shipment_move_id, context=context)

		    wf_service.trg_validate(uid, 'stock.picking', shipment_id, 'button_confirm', cr)
		    
		    production.write({'state':'confirmed'}, context=context)
		    message = _("Manufacturing order '%s' is scheduled for the %s.") % (
				production.name,
				datetime.strptime(production.date_planned, '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y'),
			)
		    self.log(cr, uid, production.id, message)
		for production in self.browse(cr, uid, ids):
			source = production.product_id.product_tmpl_id.property_stock_production.id
			self.set_order_type(cr, uid, [production.id])
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
				'name': 'PROD:' + production.name,
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
				'x_job_order_type': production.x_job_order_type,
				'production_id': production.id
				}
				self.pool.get('stock.move').create(cr, uid, data)
		return shipment_id
		
	def product_id_change(self, cr, uid, ids, product_id, mo_name, context=None):
		""" Finds UoM of changed product.
		@param product_id: Id of changed product.
		@return: Dictionary of values.
		"""
		if not product_id:
			return {'value': {
				'product_uom': False,
				'bom_id': False,
				'routing_id': False
			}}
		bom_obj = self.pool.get('mrp.bom')
		part_obj = self.pool.get('res.partner')
		product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
		bom_id = bom_obj._bom_find(cr, uid, product.id, product.uom_id and product.uom_id.id, [])
		routing_id = False
		if bom_id:
			bom_point = bom_obj.browse(cr, uid, bom_id, context=context)
			routing_id = bom_point.routing_id.id or False
			result = {
				'product_uom': product.uom_id and product.uom_id.id or False,
				'bom_id': bom_id,
				'routing_id': routing_id
			}
			if bom_point.subcontract:
				if bom_point.product_ids:
					service_products = bom_point.product_ids[0]
					if service_products.seller_ids:
						subcontract_supplier = service_products.seller_ids[0]
						part = subcontract_supplier.name.id
						addr = part_obj.address_get(cr, uid, [part], ['invoice'])
						result.update({'partner_id': part, 'address_id': addr['invoice']})
					
		else :
		
			result = {
				'product_uom': product.uom_id and product.uom_id.id or False,
				'bom_id': bom_id,
				'routing_id': routing_id
			}

		if product.product_tmpl_id.categ_id.parent_id.name == 'Tapes':
			if mo_name == False or mo_name[:2] == 'MO' or mo_name[:2] == 'CO':
				result.update({'name': self.pool.get('ir.sequence').get(cr, uid, 'mrp.production.jumbo.roll') or '/', })
		else:
			if product.product_tmpl_id.categ_id.parent_id.name == 'Conductors' or product.product_tmpl_id.categ_id.name == 'Conductors':
				if mo_name == False or mo_name[:2] == 'JR' or mo_name[:2] == 'MO':
					result.update({'name': self.pool.get('ir.sequence').get(cr, uid, 'mrp.production.conductors') or '/', })
			else:
				if mo_name == False or mo_name[:2] == 'JR' or mo_name[:2] == 'CO':
					result.update({'name': self.pool.get('ir.sequence').get(cr, uid, 'mrp.production') or '/', })
		
		return {'value': result}
		
mrp_production()



