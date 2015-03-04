from osv import osv, fields
from tools.translate import _

import pooler
import time
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import re

from tools import config

def _float_check_precision(precision_digits=None, precision_rounding=None):
	assert (precision_digits is not None or precision_rounding is not None) and \
		not (precision_digits and precision_rounding), \
			"exactly one of precision_digits and precision_rounding must be specified"
	if precision_digits is not None:
		return 10 ** -precision_digits
	return precision_rounding

def float_round(value, precision_digits=None, precision_rounding=None):
	rounding_factor = _float_check_precision(precision_digits=precision_digits, precision_rounding=precision_rounding)
	if rounding_factor == 0 or value == 0:
		return 0.0
	normalized_value = value / rounding_factor # normalize
	epsilon_magnitude = math.log(abs(normalized_value), 2)
	epsilon = 2 ** (epsilon_magnitude - 53)
	normalized_value += cmp(normalized_value, 0) * epsilon
	rounded_value = round(normalized_value) # round to integer
	result = rounded_value * rounding_factor # de-normalize
	return result

def float_is_zero(value, precision_digits=None, precision_rounding=None):
	epsilon = _float_check_precision(precision_digits=precision_digits, precision_rounding=precision_rounding)
	return abs(float_round(value, precision_rounding=epsilon)) < epsilon

def float_compare(value1, value2, precision_digits=None, precision_rounding=None):
	rounding_factor = _float_check_precision(precision_digits=precision_digits,precision_rounding=precision_rounding)
	value1 = float_round(value1, precision_rounding=rounding_factor)
	value2 = float_round(value2, precision_rounding=rounding_factor)
	delta = value1 - value2
	if float_is_zero(delta, precision_rounding=rounding_factor):
		return 0
	return -1 if delta < 0.0 else 1

class mrp_production(osv.osv):
	_name = "mrp.production"
	_inherit = "mrp.production"

	def action_produce(self, cr, uid, production_id, production_qty, production_mode, context=None):
		""" To produce final product based on production mode (consume/consume&produce).
		If Production mode is consume, all stock move lines of raw materials will be done/consumed.
		If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
		and stock move lines of final product will be also done/produced.
		@param production_id: the ID of mrp.production object
		@param production_qty: specify qty to produce
		@param production_mode: specify production mode (consume/consume&produce).
		@return: True
		"""
		production = self.browse(cr, uid, production_id, context=context)
		
		if production.name[:2] == 'CO':
			return super(mrp_production, self).action_produce(cr, uid, production_id, production_qty, production_mode, context=context)
		
		error_message = ''

		produced_qty = 0

		for produced_product in production.move_created_ids2:
			if (produced_product.scrapped) or (produced_product.product_id.id <> production.product_id.id):
				continue
			produced_qty += produced_product.product_qty

		if production_mode in ['consume', 'consume_produce']:

			consumed_data = {}

			# Calculate already consumed qtys
			for consumed in production.move_lines2:
				if consumed.scrapped:
					continue
				if not consumed_data.get(consumed.x_mo_prod_seq, False):
					consumed_data[consumed.x_mo_prod_seq] = 0
				consumed_data[consumed.x_mo_prod_seq] += consumed.product_qty

			# Find product qty to be consumed and consume it
			for scheduled in production.product_lines:

				# total qty of consumed product we need after this consumption
				total_consume = ((production_qty + produced_qty) * scheduled.product_qty / production.product_qty)

				# qty available for consume and produce
				qty_avail = scheduled.product_qty - consumed_data.get(scheduled.x_mo_prod_seq, 0.0)

				if qty_avail <= 0.0:
					# there will be nothing to consume for this raw material
					continue

				raw_products = [move for move in production.move_lines if (move.product_id.id == scheduled.product_id.id and move.x_mo_prod_seq == scheduled.x_mo_prod_seq)]
				if raw_products:
					for raw_product in raw_products:
						# qtys we have to consume
						qty = total_consume - consumed_data.get(scheduled.x_mo_prod_seq, 0.0)
						
						prodlot = self.pool.get('stock.production.lot')
						uom_obj = self.pool.get('product.uom')
						product_obj = self.pool.get('product.product')
						if raw_product.prodlot_id:
							prodlotid = prodlot.browse(cr, uid, raw_product.prodlot_id.id, context=context)
						else:
							prodlot_errormsg = 'Please assign production lot to ' + raw_product.product_id.name + '.'
							raise osv.except_osv(_('Error!'), _(prodlot_errormsg))
						
						product_uom = product_obj.browse(cr, uid, raw_product.product_id.id, context=context).uom_id
						product_uom_categ = product_obj.browse(cr, uid, scheduled.product_id.id, context=context).uom_id.category_id.id
						product_ref_uom_id = uom_obj.search(cr, uid, [('category_id', '=', product_uom_categ), ('uom_type', '=', 'reference')], context=context)[0]
						product_ref_uom = uom_obj.browse(cr, uid, product_ref_uom_id, context=context)
						uom = uom_obj.browse(cr, uid, product_uom.id, context=context)
						amount_actual = uom_obj._compute_qty_obj(cr, uid, product_ref_uom, prodlotid.stock_available, uom, context=context)
						
						if raw_product.product_id.categ_id.parent_id:
							if raw_product.product_id.categ_id.parent_id.name == 'Raw Material' or raw_product.product_id.categ_id.parent_id.name == 'Tapes' or raw_product.product_id.categ_id.parent_id.name == 'Conductors':
								if uom.uom_type == 'reference':
									if amount_actual - qty < -1:
										if error_message == '':
											error_message = 'Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
										else:
											error_message = error_message + ' Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
								elif uom.uom_type == 'smaller':
									if amount_actual/uom.factor - qty/uom.factor < -1:
										if error_message == '':
											error_message = 'Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
										else:
											error_message = error_message + ' Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
								elif uom.uom_type == 'bigger':
									if amount_actual*uom.factor - qty*uom.factor < -1:
										if error_message == '':
											error_message = 'Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
										else:
											error_message = error_message + ' Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
							else:
								if qty > amount_actual:
									if error_message == '':
										error_message = 'Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
									else:
										error_message = error_message + ' Production lot "' + raw_product.prodlot_id.name + '" assigned to "' + raw_product.product_id.name + '" does not have enough quantity.'
							
		if error_message != '':
			raise osv.except_osv(_('Error!'), _(error_message))

		return super(mrp_production, self).action_produce(cr, uid, production_id, production_qty, production_mode, context=context)

	
mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
