from osv import osv, fields
from tools.translate import _

import pooler
import time
import math

from tools import config

class awg_parameters(osv.osv):
    _name = "awg.parameters"
    _description = "Product AWG Parameters"
    _columns = {
               'awg_code' : fields.char("AWG Code", size=32, required=True, help="AWG Code."),
               'name' : fields.char("AWG Number", size=32, required=True, help="AWG Number."),
               } 
    
awg_parameters()
