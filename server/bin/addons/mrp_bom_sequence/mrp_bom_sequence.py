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

class mrp_bom(osv.osv):
	_name = "mrp.bom"
	_inherit = "mrp.bom"
	
	_columns = {
			'tape_sequence': fields.integer("Sl No"),
			}
	
	def create(self, cr, uid, data, context=None):
		if data:
			if data["bom_id"]:
				count = 0
				print data["bom_id"]
				bom_ids = self.search(cr, uid, [('bom_id','=',data["bom_id"])])
				print bom_ids
				bom_data = self.browse(cr, uid, bom_ids, context)
				if bom_data:
					for entry in bom_data:
						count = count + 1
				count = count + 1
				data.update({'x_mo_prod_seq':count})
		return super(mrp_bom, self).create(cr, uid, data, context)
mrp_bom()



class mrp_bom_sequence(osv.osv):
	_name = "mrp.bom.sequence"
	_description = "MRP BOM Sequence"
	
	def _load_bom_sequence(self, cr):
		cr.execute("SELECT count(*) from mrp_bom where tape_sequence is not NULL;")
		tape_count = cr.fetchone()
		if tape_count[0]==0:
			cr.execute('UPDATE mrp_bom set tape_sequence=x_mo_prod_seq;')
			cr.execute('UPDATE mrp_bom set x_mo_prod_seq=NULL;')
		cr.execute("SELECT id FROM mrp_bom where bom_id is NULL order by id;")
		bom_ids = cr.fetchall()
		for bom_id in bom_ids:
			count = 0
			cr.execute("Select id,x_mo_prod_seq from mrp_bom where bom_id=%s order by id" % (bom_id[0]))
			bom_line_ids = cr.fetchall()
			for bom_line in bom_line_ids:
				count = count + 1
				if bom_line[1]==0 or bom_line[1]==None:
					cr.execute("UPDATE mrp_bom set x_mo_prod_seq=%s where id=%s" % (count,bom_line[0]))
		return True
	
	def init(self, cr):
		self._load_bom_sequence(cr)
	
mrp_bom_sequence()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: