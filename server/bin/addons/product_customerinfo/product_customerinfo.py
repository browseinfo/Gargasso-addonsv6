from osv import osv, fields
from tools.translate import _

import pooler
import time
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

from tools import config

class product_customerinfo(osv.osv):
	_name = "product.customerinfo"
	_description = "Customer Information"
	def _get_prod_id(self, cr, uid, ids, *args):
		return product.name

	def _get_uom_id(self, cr, uid, *args):
		cr.execute('select id from product_uom order by id limit 1')
		res = cr.fetchone()
		return res and res[0] or False

	_columns = {
		'name' : fields.many2one('res.partner', 'Customer', required=True,domain = [('customer','=',True)], ondelete='cascade', help="Customer of this product"),
		'product_id' : fields.many2one('product.template', 'Product', required=True, ondelete='cascade', select=True),
		'product_uom': fields.many2one('product.uom', string="Customer UoM", help="Choose here the Unit of Measure in which the prices and quantities are expressed below."),				
		'product_code': fields.char('Customer Product Code', size=128, help="This supplier's product code will be used when printing a packing slip. Keep empty to use the internal one."),
		'product_name': fields.char('Customer Product Name', size=128, help="This customer's product name will be used when printing a packing slip. Keep empty to use the internal one."),
		'company_id':fields.many2one('res.company','Company',select=1),
	}
	
	_defaults = {
		'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'product.supplierinfo', context=c),
		'product_uom': _get_uom_id,
	}
	
	def _check_uom(self, cr, uid, ids, context=None):
		for customer_info in self.browse(cr, uid, ids, context=context):
			if customer_info.product_uom and customer_info.product_uom.category_id.id <> customer_info.product_id.uom_id.category_id.id:
				return False
		return True

	_constraints = [
		(_check_uom, 'Error: The default UOM and the Customer Product UOM must be in the same category.', ['product_uom']),
	]

	_order = 'name'	

product_customerinfo()

class product_template(osv.osv):
    _name = "product.template"
    _inherit = "product.template"
    _columns = {
            'customer_ids': fields.one2many('product.customerinfo','product_id','Customers'),
            }
product_template()

