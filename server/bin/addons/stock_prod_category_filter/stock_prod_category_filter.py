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

class stock_production_lot(osv.osv):
	_name = "stock.production.lot"
	_inherit = "stock.production.lot"
	
	_columns = {
			'prod_categ': fields.many2one('product.category', 'Product Category')
			}
	
	def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
		reccount = 0
		for entry in args:
			if 'prod_categ' in entry:
				categ_id = self.get_category_ids(cr, user, entry[2])
				product_id = self.pool.get('product.product').search(cr, user, [('categ_id','in',categ_id)])
				print product_id
				args.pop(reccount)
				args.append(('product_id','in', product_id))
				return super(stock_production_lot, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)
				print entry[2]
			reccount = reccount + 1
		
		return super(stock_production_lot, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)
	
	def get_category_ids(self, cr, uid, categ_id):
		
		categ_ids = []
		categ_rec = self.pool.get('product.category').search(cr, uid, [('parent_id','=',categ_id)])
		categ_ids.append(categ_id)
		
		while categ_rec != []:
			categ_ids.append(categ_rec[0])
			categ_sub_rec = self.pool.get('product.category').search(cr, uid, [('parent_id','=',categ_rec[0])])
			for entry in categ_sub_rec:
				categ_rec.append(entry)
			categ_rec.pop(0)
			
		return categ_ids

stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: