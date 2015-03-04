# -*- coding: utf-8 -*-
##############################################################################
#
#    Manufacturing Subcontracting Process
#    Copyright (C) 2004-2010 Browse Info Pvt Ltd (<http://www.browseinfo.com>).
#    $autor:
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
from os.path import join
import addons
import time
from datetime import datetime
from report import report_sxw

class stock_do_move(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(stock_do_move, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
             'time': time,
             'do_move_line':self._do_move_line,
             'print_date': self._print_date,
        })
        
    def _print_date(self,form):
        date_form = form.get('date')
        date = datetime.strptime(date_form,"%Y-%m-%d").strftime("%d%m%Y")
        return date        
        
    def _do_move_line(self,form):
        
        date_form = form.get('date')
        pick_obj = self.pool.get('stock.picking')
        mrp_obj = self.pool.get('mrp.production')
        lines = []
        res = []

        pick_ids = pick_obj.search(self.cr,self.uid, [('type','=', 'out')])
        mrp_ids = mrp_obj.search(self.cr,self.uid, [('picking_id', 'in', pick_ids )])
        for mrp in mrp_obj.browse(self.cr,self.uid, mrp_ids,):
            date = mrp.create_date.split()[0]
            if date == str(date_form):
                lines.append(mrp.id)
                
        for mo in mrp_obj.browse(self.cr,self.uid, lines):
            if mo.picking_id:
                if mo.picking_id.move_lines:
                    for pick in mo.picking_id.move_lines:
                        res.append({
                                'mrp_no': mo.name,
                                'mrp_product':mo.product_id.name,
                                'mrp_uom': mo.product_uom.name,
                                'mrp_qty': mo.product_qty,
                                'do_no': mo.picking_id.name,
                                'product_name': pick.product_id.name ,
                                'product_uom': pick.product_uom.name,
                                'product_qty': pick.product_qty,
                                })
                else:
                    res.append({
                                'mrp_no': mo.name,
                                'mrp_product':mo.product_id.name,
                                'mrp_uom': mo.product_uom.name,
                                'mrp_qty': mo.product_qty,
                                'do_no': mo.picking_id.name,
                                'product_name': 'Raw Material Stock Available at Subcontractor',
                                'product_uom': '',
                                })
        return res
file_path = join(addons.get_module_resource('mrp_subcontract'),'report/stock_move.rml')
report_sxw.report_sxw(
    'report.stock.do.move',
    'stock.move',
    file_path,
    parser=stock_do_move,
    header='external'
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

