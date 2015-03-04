from osv import osv, fields
from tools.translate import _

import pooler
import time
import math

from tools import config

class conductor_parameters(osv.osv):
    _name = "conductor.parameters"
    _description = "Conductor Parameters"
    _columns = {
                'conductor_id': fields.many2one('product.product', 'Conductor', required=True, ondelete='cascade', domain = [('product_tmpl_id.categ_id.parent_id.name','=','Conductors')]),
                'name': fields.char("Conductor Name",size=32, required=True),
                'conductor_ids' : fields.one2many('conductor.parameters.caselines','conductor_id','Parameters'),               
               }
    
    def onchange_product_id(self, cr, uid, ids, prod_id):
        if not prod_id:
            return {}
           
        if prod_id:
            result={}
            prod_obj=self.pool.get('product.product')
            param=prod_obj.browse(cr,uid,[prod_id])[0]
            if (param.name):
                result =  {'name':param.name}
                print param.name
                print result
        return {'value': result} 
    
conductor_parameters()

class conductor_parameters_caselines(osv.osv):
    _name = "conductor.parameters.caselines"
    _description = "This module creates the Conductor parameter case lines."
    _columns = {
            'conductor_id' : fields.many2one('conductor.parameters','Test Cases', required=True, ondelete="cascade"),
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
    
conductor_parameters_caselines()
