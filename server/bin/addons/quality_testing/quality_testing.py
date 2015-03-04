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


class quality_param_type(osv.osv):
	_name = "quality.param.type"
	_description = "This section creates the quality parameters type."
	_order = "id desc"
	_columns = {
			'name': fields.char("Parameter Type", size=256, required=True, help="Quality Parameter Type. E.g. COND, CORE, etc.")
			}
quality_param_type()

class quality_standards(osv.osv):
	_name = "quality.standards"
	_description = "This section creates the quality standards."
	_order = "id desc"
	_columns = {
			'name': fields.char("Standards", size=256, required=True, help="Quality Standards")
			}
quality_standards()

class quality_product_type(osv.osv):
	_name = "quality.product.type"
	_description = "This section creates the product type."
	_order = "id desc"
	_columns = {
			'name': fields.char("Product Type", size=256, required=True, help="Quality Standards")
			}
quality_product_type()

class quality_parameters(osv.osv):
	_name = "quality.parameters"
	_description = "This section defines the parameters."
	_order = "param_sequence"
	_columns = {
			'name': fields.char("Parameter", size=256, required=True, help="Parameter Name."),
			'param_sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of parameters."),
			'param_type': fields.many2one('quality.param.type', 'Parameter Type', required = True),
			'method': fields.char('Method', size = 256, help = "Method"),
			'standards': fields.many2one('quality.standards', 'Standards'),
			'unit': fields.char("Unit", size=256, help="Unit of parameter."),
			'prod_type_depend': fields.boolean("Product Type", help="Product type dependency"),
			'cr_depend': fields.boolean("CR", help="CR dependency"),
			'rti_depend': fields.boolean("RTI", help="RTI dependency"),
			'manual_depend': fields.boolean("Manual", help="Manual dependency")
			}
quality_parameters()

class quality_testing(osv.osv):
	_name = "quality.testing"
	_description = "This module created testing paramters group."
	_order = "id desc"
	_columns = {
			'case_code' : fields.char("Test Case Code", size=256, required=True, help="Product Test Case Code."),
			'name' : fields.char("Test Case Name", size=256, required=True, help="Product Test Case Name."),
			'product_type': fields.many2one('quality.product.type','Product Type', help = "Product Type."),
			'product_id': fields.many2one('product.product', "Conductor", domain = [('product_tmpl_id.categ_id.parent_id.name','=','Conductors')], help = "Conductor name."),
#			'hookup_check' : fields.boolean("Hook-up", help="Hook Up Wire"),
			'multi_check' : fields.boolean("Multicore", help = "Multicore Wire"),
			'coaxial_check' : fields.boolean("Coaxial", help = "Coaxial Wire"),
			'hvdc_check' : fields.boolean("HVDC", help = "HVDC Wire"),
			'twist_check' : fields.boolean("Twisted Pair", help = "Twisted Pair", readonly=True),
			'quality_testing_line_ids': fields.one2many('quality.testing.line', 'testing_id', 'Parameters'),
			}
	
	def pull_testing_parameters(self, cr, uid, ids, context=None):
		if not context:
			context = {}
		product_id = context.get('product_id', False)
		print ids
		try:
			if product_id:
				product_obj = self.pool.get('product.product')
				testing_obj = self.pool.get('quality.testing')
				testing_line_obj = self.pool.get('quality.testing.line')
				do_line_obj = self.pool.get('delivery.order.testing.lines')
				print product_obj
#				primary_test_code = product_obj.primary_test_code
#            	addon_code1 = product_obj.addon_code1
#             	addon_code2 = product_obj.addon_code2
				product = product_obj.browse(cr, uid, product_id, context=context)
				case_ids = []
				data = {}
				if product.primary_test_code or product.addon_code1 or product.addon_code2:
					if product.primary_test_code:
						case_ids.append(product.primary_test_code.id)
						if product.addon_code1:
							case_ids.append(product.addon_code1.id)
					if product.addon_code2:
						case_ids.append(product.addon_code2.id)
					testing_line_ids = testing_line_obj.search(cr, uid, [('testing_id','in',case_ids)])
					testing_lines = testing_line_obj.browse(cr, uid, testing_line_ids)
					for line in testing_lines:
						data ={
							'testing_id': ids,
							'param_id': line.name.id,
							'param_sequence': line.param_sequence,
							'standards': line.standards.id,
							'unit': line.unit,
							'method': line.method,
							}
						if line.min_value:
							data.update({'requirement': line.min_value})
						if line.max_value:
							if data.has_key('requirement'):
								print line.min_value
								if line.min_value=="0":
									data.update({'requirement': line.max_value})
								else:
									data.update({'requirement': data['requirement'] + ' - ' + line.max_value})
							else:
								data.update({'requirement': line.max_value})
								
						do_line_obj.create(cr, uid, data)
										
		
		except IOError:
				raise osv.except_osv(_('valid action !'), _('Some error occured please contact administrator.'))
		
		return True
	
	def pullparameters(self, cr, uid, ids, context=None):
		try:
			quality_testing = self.pool.get('quality.testing').browse(cr, uid, ids)
			type_id = quality_testing[0].product_type.id
			product_id = quality_testing[0].product_id.id
			multi_check = quality_testing[0].multi_check
			coaxial_check = quality_testing[0].coaxial_check
			hvdc_check = quality_testing[0].hvdc_check
			twist_check = quality_testing[0].twist_check
			
			query=''
			
			if type_id and not product_id:
				query="select id from quality_param_type where name like '%CORE'"
			if type_id and product_id:
				query="select id from quality_param_type where name like '%CORE' or name like '%COND'"
			if multi_check:
				if query=='':
					query="select id from quality_param_type where name like '%MULT'"
				else:
					query= query + " or name like '%MULT'"
				if twist_check:
					query= query + " or name like '%TWIST'"
			if coaxial_check:
				if query=='':
					query="select id from quality_param_type where name like '%COAX'"
				else:
					query= query + " or name like '%COAX'"
			if hvdc_check:
				if query=='':
					query="select id from quality_param_type where name like '%HVDC'"
				else:
					query= query + " or name like '%HVDC'" 
			
			if query=='':
				return True
			cr.execute(query)
			param_type_ids = map(lambda x: x[0], cr.fetchall())
			
			param_ids = self.pool.get('quality.parameters').search(cr, uid, [('param_type',"in",param_type_ids)], context=context)
			testinglines_obj = self.pool.get('quality.testing.line')
			testinglines_ids = testinglines_obj.search(cr, uid, [('testing_id', 'in', ids)])
			testinglines = testinglines_obj.browse(cr, uid, testinglines_ids)
			
			for param in self.pool.get('quality.parameters').browse(cr, uid, param_ids):
				flag = True
				for line in testinglines:
					if line.name.id == param.id:
						flag=False
				if flag:				
					if param.param_sequence==False:
						param_sequence=''
					else:
						param_sequence=param.param_sequence
						
					if param.standards==False:
						standards=None
					else:
						if param.standards.id:
							standards=param.standards.id
						else:
							standards=None
					
					if param.unit==False:
						unit=''
					else:
						unit=param.unit
					
					if param.method==False:
						method=''
					else:
						method=param.method
					
					cr.execute('insert into quality_testing_line (create_uid, create_date, write_date, testing_id, name, param_sequence, standards, unit, method) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ids[0], param.id, param_sequence, standards, unit, method))
				
		except IOError:
				raise osv.except_osv(_('valid action !'), _('Some error occured please contact administrator.'))

		return True
	
quality_testing()

class quality_testing_line(osv.osv):
	_name = "quality.testing.line"
	_description = "This section records parameters against quality testing."
	_order = "param_sequence"
	_columns = {
			'testing_id': fields.many2one('quality.testing','Test Cases', required=True, ondelete="cascade"),
			'name': fields.many2one('quality.parameters', "Parameters",required=True , help = "Parameter Name."),
			'param_sequence': fields.integer('Sequence', size=64),
			'standards': fields.many2one('quality.standards', "Standards", help = "Standards."),
			'min_value': fields.char('Requirements/Min Value', size=256, help = "Requirement/Minimum Value."),
			'max_value': fields.char('Max Value', size = 256, help = "Maximum Value"),
			'unit': fields.char('Unit', size = 256, help = "Unit"),
			'method': fields.char('Method', size = 256, help = "Method")
			}
	
	def create(self, cr, uid, data, context=None):
		if data:
			print data["name"]
			param_obj = self.pool.get('quality.parameters')
			params = param_obj.browse(cr, uid, data["name"])
			data.update({'param_sequence':params.param_sequence})
		return super(quality_testing_line, self).create(cr, uid, data, context)
	

quality_testing_line()

class product_product(osv.osv):
	_name = "product.product"
	_inherit = "product.product"
	_columns = {
            'primary_test_code': fields.many2one('quality.testing','Primary Test Code'),
            'addon_code1': fields.many2one('quality.testing','Addon Test Code 1'),
            'addon_code2': fields.many2one('quality.testing','Addon Test Code 2'),
            }
product_product()

class delivery_order_testing(osv.osv):
	_name = "delivery.order.testing"
	_description = "Product list in delivery order with test case name."
	
	_columns = {
			'product_id': fields.many2one('product.product', required=True, string='Product'),
			'testinglines_ids' : fields.one2many('delivery.order.testing.lines','testing_id','Parameters'),
			'purchase_order_info': fields.char("Purchase Order/Date", size=300, help="Purchase Order Details"),
			'invoice_info': fields.char("Sales Order No.", size=300, help="Sales Order Number"),
			'work_order_info': fields.char("Work Order Details", size=300, help="Work Order Number"),
			'net_weight': fields.char("Net Weight", size=256, help = "Net Weight"),
			'spool_info': fields.char("Spool No/Size", size=256, help="Spool Number/Size"),
			'partner_id': fields.many2one('res.partner', 'Customer'),
			'quantity': fields.char("Qty. (m)/Pcs/Min/Max/Av", size=256, help="Qty. (m)/Pcs/Min/Max/Av"),
			'create_date': fields.datetime('Create Date', readonly=True),
			}
	_order = "id desc"
	
	def write(self, cr, uid, ids, vals, context=None):
		if vals.has_key('testinglines_ids'):
			if not vals['testinglines_ids'][0][2].has_key('result'):
				vals['testinglines_ids'][0][2]['result']=''
			vals['testinglines_ids'][0][2]['result'] = self.check_result(cr, uid, ids, vals, context)
		del context['__last_update']
		return super(delivery_order_testing, self).write(cr, uid, ids, vals, context=context)
	
	def is_number(self, s):
		try:
			if not s:
				return False
			float(s) # for int, long and float
		except ValueError:
			try:
				complex(s) # for complex
			except ValueError:
				return False
		return True
	
	def check_result(self, cr, uid, ids, vals, context=None):
		result = ''
		if vals['testinglines_ids'][0][2]['param_value'] and not vals['testinglines_ids'][0][2]['result']:
			result = "N/A"
		else:
			if vals['testinglines_ids'][0][2]['result']:
				result = vals['testinglines_ids'][0][2]['result']
			else:
				return False
		
		testcaseline_id = vals['testinglines_ids'][0][1]
		
		do_testing_obj = self.pool.get('delivery.order.testing')
		do_testinglines_obj = self.pool.get('delivery.order.testing.lines')
		
		product_obj = self.pool.get('product.product')
		
		quality_obj = self.pool.get('quality.testing')
		qualityline_obj = self.pool.get('quality.testing.line')
		
		do_testing_data = do_testing_obj.browse(cr, uid, ids[0])
		testline_data = do_testinglines_obj.browse(cr, uid, testcaseline_id)
		
		product_data = product_obj.browse(cr, uid, do_testing_data.product_id.id)
		
		quality_ids = quality_obj.search(cr, uid, [('id','in',[product_data.primary_test_code.id,product_data.addon_code1.id,product_data.addon_code2.id])])
		qualityline_ids = qualityline_obj.search(cr, uid, [('testing_id','in',quality_ids)])
		
		quality_data = qualityline_obj.browse(cr, uid, qualityline_ids)
		
		if result=='' or result=='N/A':
			for data in quality_data:
				if data.name.id == testline_data.param_id.id:
					if data.min_value and data.max_value:
						if self.is_number(data.min_value) and self.is_number(data.max_value):
							if len(vals['testinglines_ids'][0][2]['param_value'].split('-'))>1:
								min_value = vals['testinglines_ids'][0][2]['param_value'].split('-')[0].strip()
								max_value = vals['testinglines_ids'][0][2]['param_value'].split('-')[1].strip()
							else:
								min_value = vals['testinglines_ids'][0][2]['param_value']
								max_value = vals['testinglines_ids'][0][2]['param_value']
							if float(min_value) >= float(data.min_value) and float(max_value) <= float(data.max_value):
								result = 'Pass'
							else:
								result = 'Fail'
						else:
							result = 'N/A'
					else:
						if data.min_value or data.max_value:
							if self.is_number(data.min_value) or self.is_number(data.max_value):
								if float(vals['testinglines_ids'][0][2]['param_value']) == float(data.min_value) or float(vals['testinglines_ids'][0][2]['param_value']) == float(data.max_value):
									result = 'Pass'
								else:
									result = 'Fail'
							else:
								result = 'N/A'
		return result
	
	def pull_testing_parameters(self, cr, uid, ids, context=None):
		if not context:
			context = {}
		try:
			if ids:
				delivery_order_obj = self.browse(cr, uid, ids[0])
				product_id = delivery_order_obj.product_id.id
			if product_id:
				product_obj = self.pool.get('product.product')
				testing_line_obj = self.pool.get('quality.testing.line')
				do_line_obj = self.pool.get('delivery.order.testing.lines')
				product = product_obj.browse(cr, uid, product_id, context=context)
				case_ids = []
				data = {}
				if product.primary_test_code or product.addon_code1 or product.addon_code2:
					if product.primary_test_code:
						case_ids.append(product.primary_test_code.id)
						if product.addon_code1:
							case_ids.append(product.addon_code1.id)
					if product.addon_code2:
						case_ids.append(product.addon_code2.id)
					testing_line_ids = testing_line_obj.search(cr, uid, [('testing_id','in',case_ids)])
					testing_lines = testing_line_obj.browse(cr, uid, testing_line_ids)
					do_param_line_ids = do_line_obj.search(cr, uid, [('testing_id','in',ids)])
					do_param_lines = do_line_obj.browse(cr, uid, do_param_line_ids)
					do_line_ids = []
					for param in do_param_lines:
						do_line_ids.append(param.param_id.id)
					for line in testing_lines:
						if line.name.id not in do_line_ids:
							data ={
								'testing_id': ids[0],
								'param_id': line.name.id,
								'param_sequence': line.param_sequence,
								'standards': line.standards.id,
								'unit': line.unit,
								'method': line.method,
								}
							if line.min_value:
								data.update({'requirement': line.min_value})
							if line.max_value:
								if data.has_key('requirement'):
									print line.min_value
									if line.min_value=="0":
										data.update({'requirement': line.max_value})
									else:
										data.update({'requirement': data['requirement'] + ' - ' + line.max_value})
								else:
									data.update({'requirement': line.max_value})
									
							do_line_obj.create(cr, uid, data)
										
		
		except IOError:
				raise osv.except_osv(_('valid action !'), _('Some error occured please contact administrator.'))
		
		return True
	
delivery_order_testing()

class delivery_order_testing_lines(osv.osv):
	_name = "delivery.order.testing.lines"
	_description = "Testing parameters for products in delivery order."
	_order = 'param_sequence'
	
	def _check_permissions(self, cr, uid, ids, field_name, arg, context):
		res = {}
		for i in ids:
			if not i:
				continue
			# Get the Quality User/Quality Manager
			group_obj = self.pool.get('res.groups')
			manager_ids = group_obj.search(cr, uid, ['|',('name','=', 'Quality / User'),('name','=', 'Quality / Manager')])
			
			# Get the user and see what groups he/she is in
			user_obj = self.pool.get('res.users')
			user = user_obj.browse(cr, uid, uid, context=context)
			
			group_ids = []
			for grp in user.groups_id:
				group_ids.append(grp.id)
			
			if (manager_ids[1] in group_ids) and manager_ids[0] not in group_ids:
				res[i] = 'User'
			elif (manager_ids[0] in group_ids):
				res[i] = 'Manager'
		
		return res
	
	_columns = {
			'testing_id': fields.many2one('delivery.order.testing','Testing', required=True, ondelete="cascade"),
	 		'param_id' : fields.many2one('quality.parameters', 'Parameter', required=True, readonly=True),
	 		'param_sequence': fields.integer('Sequence', size=64, readonly=True),
			'standards' : fields.many2one('quality.standards', "Standards", readonly=True),
			'requirement' : fields.char("Requirement", size=256, readonly=True),
			'unit' : fields.char("Unit", size=256, readonly=True),
			'method' : fields.char("Method",size=256, readonly=True),
	 		'param_value': fields.char('Parameter Value', size=256),
	 		'result': fields.char('Result', size=256),
	 		'permissions': fields.function(_check_permissions, type='char', method=True, string="Permissions"),
			}
	
#	def write(self, cr, uid, ids, vals, context=None):
#		if vals.has_key('testinglines_ids'):
#			vals['testinglines_ids'][0][2]['result'] = self.check_result(cr, uid, ids, vals, context)
#		del context['__last_update']
#		return super(delivery_order_testing_lines, self).write(cr, uid, ids, vals, context=context)
#	
#	def check_result(self, cr, uid, ids, vals, context=None):
#		if vals['testinglines_ids'][0][2]['param_value']:
#			result = "N/A"
#		else:
#			return False
#		
#		testcaseline_id = vals['testinglines_ids'][0][1]
#		
#		do_testing_obj = self.pool.get('delivery.order.testing')
#		do_testinglines_obj = self.pool.get('delivery.order.testing.lines')
#		
#		product_obj = self.pool.get('product.product')
#		
#		quality_obj = self.pool.get('quality.testing')
#		qualityline_obj = self.pool.get('quality.testing.line')
#		
#		do_testing_data = do_testing_obj.browse(cr, uid, ids[0])
#		testline_data = do_testinglines_obj.browse(cr, uid, testcaseline_id)
#		
#		product_data = product_obj.browse(cr, uid, do_testing_data.product_id.id)
#		
#		quality_ids = quality_obj.search(cr, uid, [('id','in',[product_data.primary_test_code.id,product_data.addon_code1.id,product_data.addon_code2.id])])[0]
#		qualityline_ids = qualityline_obj.search(cr, uid, [('testing_id','in',[quality_ids])])
#		
#		quality_data = qualityline_obj.browse(cr, uid, qualityline_ids)
#		
#		for data in quality_data:
#			if data.name.id == testline_data.param_id.id:
#				if data.min_value and data.max_value:
#					if self.is_number(data.min_value) and self.is_number(data.max_value):
#						if float(vals['testinglines_ids'][0][2]['param_value']) >= float(data.min_value) and float(vals['testinglines_ids'][0][2]['param_value']) <= float(data.max_value):
#							result = 'Pass'
#						else:
#							result = 'Fail'
#					else:
#						result = 'N/A'
#				else:
#					if data.min_value or data.max_value:
#						if self.is_number(data.min_value) or self.is_number(data.max_value):
#							if float(vals['testinglines_ids'][0][2]['param_value']) == float(data.min_value) or float(vals['testinglines_ids'][0][2]['param_value']) == float(data.max_value):
#								result = 'Pass'
#							else:
#								result = 'Fail'
#						else:
#							result = 'N/A'
#		return result
	
delivery_order_testing_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


