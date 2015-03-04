from osv import osv, fields
from tools.translate import _

import pooler
import time
import math

from tools import config


class quality_parameters(osv.osv):
    _name = "quality.parameters"
    _description = "Product Quality Testing Parameters"
    _columns = {
               'parameter_code' : fields.char("Parameter Code", size=32, required=True, help="Quality Testing Parameter Code."),
               'name' : fields.char("Parameter Name", size=32, required=True, help="Quality Testing Parameter Name."),
               'min_max_check': fields.boolean("Min Max Parameter Applied", help="Determines whether product quality parameter consists Min Max parameter quantity range."),
               'parameter_type': fields.selection([('normal','Normal'),('electric','Electric Test'),('finished','Test on Finished Cable')],"Parameter Type", size=32,required=True, help="Type of Parameter e.g. Normal or Testing parameter."),
               } 
    
quality_parameters()
