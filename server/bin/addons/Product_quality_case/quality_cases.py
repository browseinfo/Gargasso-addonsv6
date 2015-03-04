from osv import osv, fields
from tools.translate import _

import pooler
import time
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

from tools import config

class quality_cases(osv.osv):
	_name = "quality.cases"
	_description = "This module creates the testing parameter groups."
	_columns = {
			'case_code' : fields.char("Test Case Code", size=32, required=True, help="Product Test Case Code."),
			'name' : fields.char("Test Case Name", size=32, required=True, help="Product Test Case Name."),
			'product_type' : fields.many2one('type.parameters','Product Type', required=True),
			'conductor_name' : fields.many2one('conductor.parameters','Conductor', required=True),
			'parameter_ids' : fields.one2many('quality.caselines','case_id','Parameters')
			}
	def pullparameters(self, cr, uid, ids, context=None):
		print uid
		print ids
		print ids[0]
		print context
		type_id = context.get('product_type', False)
		conductor_id = context.get('conductor_name', False)
		
		if conductor_id and type_id:
			try:
				cr.execute('SELECT id, param_id, requirement, max_value, min_value, standard, unit, method, condition FROM conductor_parameters_caselines where conductor_id=%s', (conductor_id,))
				param_ids = map(lambda x: x[0], cr.fetchall())
				for param in self.pool.get('conductor.parameters.caselines').browse(cr, uid, param_ids):
					if param.max_value==False:
						max_value=''
					else:
						max_value=param.max_value
						
					if param.min_value==False:
						min_value=''
					else:
						min_value=param.min_value
						
					if param.min_max_check==False:
						min_max_check=''
					else:
						min_max_check=param.min_max_check
						
					if param.unit==False:
						unit=''
					else:
						unit=param.unit
						
					if param.standard==False:
						standard=''
					else:
						standard=param.standard
						
					if param.method==False:
						method=''
					else:
						method=param.method
						
					if param.condition==False:
						condition=''
					else:
						condition=param.condition
						
					if param.requirement==False:
						requirement=''
					else:
						requirement=param.requirement
						
					cr.execute('insert into quality_caselines (create_uid, create_date, write_date, requirement, max_value, min_value, min_max_check, unit, case_id, param_id, standard, method, condition) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), requirement, max_value, min_value, min_max_check, unit, ids[0], param.param_id.id, standard, method, condition))
					
				cr.execute('SELECT id, param_id, requirement, max_value, min_value, standard, unit, method, condition FROM type_parameters_caselines where type_id=%s', (type_id,))
				param_ids = map(lambda x: x[0], cr.fetchall())
				for param in self.pool.get('type.parameters.caselines').browse(cr, uid, param_ids):
					if param.max_value==False:
						max_value=''
					else:
						max_value=param.max_value
						
					if param.min_value==False:
						min_value=''
					else:
						min_value=param.min_value
						
					if param.min_max_check==False:
						min_max_check=''
					else:
						min_max_check=param.min_max_check
						
					if param.unit==False:
						unit=''
					else:
						unit=param.unit
						
					if param.standard==False:
						standard=''
					else:
						standard=param.standard
						
					if param.method==False:
						method=''
					else:
						method=param.method
						
					if param.condition==False:
						condition=''
					else:
						condition=param.condition
						
					if param.requirement==False:
						requirement=''
					else:
						requirement=param.requirement
						
					cr.execute('insert into quality_caselines (create_uid, create_date, write_date, requirement, max_value, min_value, min_max_check, unit, case_id, param_id, standard, method, condition) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), requirement, max_value, min_value, min_max_check, unit, ids[0], param.param_id.id, standard, method, condition))
			except IOError:
				raise osv.except_osv(_('valid action !'), _('Please select Product Type and Conductor.'))				
		return True
	
	def onchange_product_type(self, cr, uid, ids, product_type, context=None):
		print product_type
		if product_type:
			prod = self.pool.get('type.parameters').browse(cr, uid, product_type, context=context)
        	v = {'product_type': prod.id}
        	return {'value': v}
        


quality_cases()

class quality_caselines(osv.osv):
	_name = "quality.caselines"
	_description = "This module creates the testing parameter case lines."
	_columns = {
			'case_id' : fields.many2one('quality.cases','Test Cases', required=True, ondelete="cascade"),
			'max_value' : fields.char("Max Value", size=32, readonly="0", attrs="{'readonly':[('param_id.id.min_max_check','=',True)]}"),
			'min_value' : fields.char("Min Value", size=32,readonly="0", attrs="{'readonly':[('param_id.id.min_max_check','=',True)]}"),
			'param_id' : fields.many2one('quality.parameters', 'Parameter', required=True, ondelete="cascade"),
			'requirement' : fields.char("Requirements", size=1000, required=True),
			'standard' : fields.char("Standard Value", size=500, attrs="{'readonly':[('param_id.id.min_max_check','=',False)]}"),
			'unit' : fields.char("Unit", size=32),
			'method' : fields.char("Method",size=32),
			'condition' : fields.char("Test Condition", size=500),
			'min_max_check' : fields.char("Min Max Check", size=10),
			}
	
	def onchange_param_id(self, cr, uid, ids, param_id):
		if not param_id:
			return {}
           
		if param_id:
			result={}
			param_obj=self.pool.get('quality.parameters')
			param=param_obj.browse(cr,uid,[param_id])[0]
			if (param.min_max_check):
				result =  {'min_max_check':'True'}
				print param.min_max_check
				print result
		return {'value': result}

quality_caselines()

class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
    _columns = {
            'test_code': fields.many2one('quality.cases','Test Case'),
            }
product_product()

class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"
    _columns = {
            'test_ids': fields.one2many('delivery.order.testing','picking_id','Quality Testing'),
            }
stock_picking()

class delivery_order_testing(osv.osv):
	_name = "delivery.order.testing"
	_description = "Product list in delivery order with test case name."
	_columns = {
			'product_id': fields.many2one('product.product',  string='Product'),
			'picking_id' : fields.many2one('stock.picking','Stock Picking', required=True, ondelete="cascade"),
			'testinglines_ids' : fields.one2many('delivery.order.testing.lines','testing_id','Parameters')
			}
	
	
	def onchange_product_id(self, cr, uid, ids, product_id, context=None):
		
		if not product_id:
			return {'value': {
                'param_id': False
            }}
		
		qa_obj = self.pool.get('delivery.order.testing')
		wf_service = netsvc.LocalService("workflow")
		product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
		cr.execute('select test_code from product_product where id=%s', (product_id,))
		case_ids = map(lambda x: x[0], cr.fetchall())
		for case in self.pool.get('quality.cases').browse(cr, uid, case_ids):
			qa_id = case.id
		result = []
		qalines_obj = self.pool.get('delivery.order.testing.lines')
		if qa_id:
			cr.execute('select param_id from quality_caselines where case_id=%s', (qa_id,))
			param_ids = map(lambda x: x[0], cr.fetchall())
			for param in self.pool.get('quality.caselines').browse(cr, uid, param_ids):
				qalines_obj._set_params(cr, uid, param.id)
				result = {
						'param_id': param.id
						}
		return {'value': result}
    
	def _case_find(self, cr, uid, product_id):
		cr.execute('select test_code from product_product where id=%s', (product_id,))
		ids = map(lambda x: x[0], cr.fetchall())
		result = False
		for case in self.pool.get('quality.cases').browse(cr, uid, ids):
			result = case.id
		return result
delivery_order_testing()

class delivery_order_testing_lines(osv.osv):
	_name = "delivery.order.testing.lines"
	_description = "Testing parameters for products in delivery order."
	_columns = {
			'testing_id': fields.many2one('delivery.order.testing','Testing', required=True, ondelete="cascade"),
	 		'param_id' : fields.many2one('quality.parameters', 'Parameter', required=True, ondelete="cascade"),
			'max_value' : fields.char("Max Value", size=32, attrs="{'readonly':[('param_id.id.min_max_check','=',True)]}"),
			'min_value' : fields.char("Min Value", size=32, attrs="{'readonly':[('param_id.id.min_max_check','=',True)]}"),
			'requirement' : fields.char("Requirements", size=1000, required=True),
			'standard' : fields.char("Standard Value", size=500, attrs="{'readonly':[('param_id.id.min_max_check','=',False)]}"),
			'unit' : fields.char("Unit", size=32),
			'method' : fields.char("Method",size=32),
			'condition' : fields.char("Test Condition", size=500),
	 		'param_value': fields.char('Parameter Value', size=32),			
			}

	def _set_params(self, cr, uid, param_id):
		result = []
		result = {
				'param_id': param_id
				}
		return result
	
delivery_order_testing_lines()


