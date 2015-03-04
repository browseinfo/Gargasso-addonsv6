# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
from osv import fields,osv
from tools.translate import _
import time
import cStringIO
import xlwt
from datetime import datetime

class mrp_report(osv.osv_memory):
    """
    Wizard to create custom report
    """
    _name = "mrp.report"
    _description = "Create Report"
    _columns = {
               'state': fields.selection( ( ('choose','choose'),   # choose date
                     ('get','get'),         # get the file
                   ) ),
               'data': fields.binary('File', readonly=True),
               'name': fields.char('Filename', 16, readonly=True),
               'mo_type': fields.selection([('MO','MO'), ('CO','CO'), ('JR','JR'), ('all','All')], 'MO Type', size=32, required=True),
               'mo_state': fields.selection([('in_production','In Production'), ('confirmed','Confirmed'), ('ready','Ready'), ('draft','Draft'),('done','Done'), ('picking_except','Picking Exception'), ('cancel','Cancel'), ('all_no_cancel','All except Cancel & Done')], 'MO State', size=32, required=True),
    }
    _defaults = {
                 'state': lambda *a: 'choose',
                }
   
    def create_report(self,cr,uid,ids,context={}):
       if not context:
           return False
       this = self.browse(cr, uid, ids)[0]
       mo_type = this.mo_type
       mo_state = this.mo_state
       
       
       
       if mo_type:
           if mo_type <> "all":
               mo_type = mo_type + "%"
           prod_obj = self.pool.get('mrp.production')
           if mo_state == "all_no_cancel":
               if mo_type <> "all":
                   prod_ids = prod_obj.search(cr, uid, [('name','like',mo_type), ('state','<>','done'), ('state','<>','cancel')])
               else:
                   prod_ids = prod_obj.search(cr, uid, [('state','<>','cancel'), ('state','<>','done')])
           else:
               if mo_type <> "all":
                   prod_ids = prod_obj.search(cr, uid, [('name','like',mo_type), ('state','=',mo_state)])
               else:
                   prod_ids = prod_obj.search(cr, uid, [('state','=',mo_state)])
           prod_data = prod_obj.browse(cr, uid, prod_ids, context)
           f = cStringIO.StringIO()
           book = xlwt.Workbook(encoding="utf-8")
           
           sheet1 = book.add_sheet("Sheet 1")
           
           font = xlwt.Font() # Create the Font 
           font.name = 'Arial' 
           font.bold = True 
           font.underline = False
           font.italic = False
           style = xlwt.XFStyle() # Create the Style 
           style.font = font # Apply the Font to the Style 
           
           sheet1.write(0, 0, "Name", style)
           sheet1.write(0, 1, "Create Date", style)
           sheet1.write(0, 2, "Origin", style)
           sheet1.write(0, 3, "Customer", style)
           sheet1.write(0, 4, "Due Date", style)
           sheet1.write(0, 5, "Product Code", style)
           sheet1.write(0, 6, "Product", style)
           sheet1.write(0, 7, "Ordered Quantity", style)
           sheet1.write(0, 8, "Produced", style)
           sheet1.write(0, 9, "Balance", style)
           sheet1.write(0, 10, "Status", style)
           
           i=1
           for data in prod_data:
               print data.id
               sheet1.write(i, 0, data.name)
               if data.create_date:
                   sheet1.write(i, 1, datetime.strptime(data.create_date.split(' ')[0],'%Y-%m-%d').strftime('%d-%m-%Y'))
               if data.origin:
                   sheet1.write(i, 2, data.origin)
               if data.sale_ref:
                   sheet1.write(i, 3, data.sale_ref)
               if data.sale_requested_date:
                   sheet1.write(i, 4, datetime.strptime(data.sale_requested_date,'%Y-%m-%d').strftime('%d-%m-%Y'))
               sheet1.write(i, 5, data.product_id.default_code)
               sheet1.write(i, 6, data.product_id.name)
               sheet1.write(i, 7, str(data.product_qty))
               sheet1.write(i, 8, str(reduce(lambda x, move_created_ids2: x+ move_created_ids2.product_qty , data.move_created_ids2 , 0 )))
               sheet1.write(i, 9, str(data.product_qty - reduce(lambda x, move_created_ids2: x+ move_created_ids2.product_qty , data.move_created_ids2 , 0 )))
               sheet1.write(i, 10, data.state)
               i = i+1
       
       book.save(f)
       out=base64.encodestring(f.getvalue())
       return self.write(cr, uid, ids, {'state':'get', 'data':out, 'name':'MO Export.xls'}, context=context)
   
mrp_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
