from osv import osv, fields
from tools.translate import _

import pooler
import time
import math

from tools import config


class type_parameters(osv.osv):
    _name = "type.parameters"
    _description = "Product Type Parameters"
    _columns = {
               'name' : fields.char("Product Type", size=32, required=True, help="Product Type e.g. E, EE, ET, etc."),
               'typecase_ids' : fields.one2many('type.parameters.caselines','type_id','Parameters'),           
               } 
    
type_parameters()

class type_parameters_caselines(osv.osv):
    _name = "type.parameters.caselines"
    _description = "This module creates the product type parameter case lines."
    _columns = {
            'type_id' : fields.many2one('type.parameters','Test Cases', required=True, ondelete="cascade"),
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
    
type_parameters_caselines()
