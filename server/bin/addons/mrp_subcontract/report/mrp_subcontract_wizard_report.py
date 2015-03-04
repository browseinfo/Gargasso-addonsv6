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

import addons
import time
from os.path import join
from datetime import datetime
from report import report_sxw

class mrp_print_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(mrp_print_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
             'time': time,
             'do_move_line':self._do_move_line,
             'do_comment': self._do_comment,
             'get_move_lines': self._get_move_lines,
             'print_date': self._print_date,
             'print_do_no': self._print_do_no,
        })

    def _print_date(self,form):
        date_form = form.get('date')
        date = datetime.strptime(date_form,"%Y-%m-%d").strftime("%d%m%Y")
        return date
    
    def _print_do_no(self,form):
#        date_form = form.get('date')
        production_ids = form.get('production_ids')
        mrp_obj = self.pool.get('mrp.production')
        mo = mrp_obj.browse(self.cr, self.uid, production_ids[0])
        name = 'SUB/' + datetime.strptime(mo.create_date.split(' ')[0],"%Y-%m-%d").strftime("%d%m%Y")
        return name
    
    def _get_move_lines(self, mo_id):
        pick_obj = self.pool.get('stock.picking')
        mrp_obj = self.pool.get('mrp.production')
        lines = []
        res = []
        mo = mrp_obj.browse(self.cr, self.uid, mo_id)
        if mo.picking_id:
                if mo.picking_id.move_lines:
                    for pick in mo.picking_id.move_lines:
                        res.append({
                                    'do_no': mo.picking_id.name,
                                    'product_name': pick.product_id.name ,
                                    'product_uom': pick.product_uom.name,
                                    'product_qty': pick.product_qty,
                                    })
                else:
                    res.append({
                                'do_no': mo.picking_id.name,
                                'product_name': 'Raw Material Stock Available at Subcontractor',
                                'product_uom': '',
                                })
        return res
    
    def _do_move_line(self,form):
        
#        date_form = form.get('date')
        production_ids = form.get('production_ids')
        send_report = form.get('send_report')
        pick_obj = self.pool.get('stock.picking')
        mrp_obj = self.pool.get('mrp.production')
        lines = []
        res = []
        flag = 0

#        pick_ids = pick_obj.search(self.cr,self.uid, [('type','=', 'out')])
#        mrp_ids = mrp_obj.search(self.cr,self.uid, [('picking_id', 'in', pick_ids )])
#        for mrp in mrp_obj.browse(self.cr,self.uid, mrp_ids,):
#            date = mrp.create_date.split()[0]
#            if date == str(date_form):
#                lines.append(mrp.id)
        
        for mo in mrp_obj.browse(self.cr,self.uid, production_ids):
            if send_report:
                mrp_obj.write(self.cr,self.uid, [mo.id], {'send_report':True},)
            
            res.append({
                        'mrp_id': mo.id,
                        'mrp_no': mo.name,
                        'mrp_product':mo.product_id.name,
                        'mrp_uom': mo.product_uom.name,
                        'mrp_qty': mo.product_qty,
                        'do_no': mo.picking_id.name,
                        })
        return res        

#    def _do_move_line(self,form):
#        
#        mrp_ids = form.get('production_ids')
#        send_report = form.get('send_report')
#        mrp_obj = self.pool.get('mrp.production')
#        res = []
#
#        for mo in mrp_obj.browse(self.cr,self.uid, mrp_ids):
#            
#            if send_report:
#                mrp_obj.write(self.cr,self.uid, [mo.id], {'send_report':True},)
#            
#            if mo.picking_id:
#                if mo.picking_id.move_lines:
#                    for pick in mo.picking_id.move_lines:
#                        res.append({
#                                'mrp_no': mo.name,
#                                'mrp_product':mo.product_id.name,
#                                'mrp_uom': mo.product_uom.name,
#                                'mrp_qty': mo.product_qty,
#                                'do_no': mo.picking_id.name,
#                                'product_name': pick.product_id.name ,
#                                'product_uom': pick.product_uom.name,
#                                'product_qty': pick.product_qty,
#                                })
#                else:
#                    res.append({
#                                'mrp_no': mo.name,
#                                'mrp_product':mo.product_id.name,
#                                'mrp_uom': mo.product_uom.name,
#                                'mrp_qty': mo.product_qty,
#                                'do_no': mo.picking_id.name,
#                                'product_name': 'Raw Material Stock Available at Subcontractor',
#                                'product_uom': '',
#                                })
#        return res

    def _do_comment(self,form):
        comment = form.get('comments')
        res = []
        if comment:
            res.append({
                'comment': comment,
              })
        return res
        
file_path = join(addons.get_module_resource('mrp_subcontract'),'report/mrp_stock_move.rml')
report_sxw.report_sxw(
    'report.mrp.print.report',
    'stock.move',
    file_path,
    parser=mrp_print_report,
    header='external'
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

