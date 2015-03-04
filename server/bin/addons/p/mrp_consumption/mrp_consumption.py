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

class mrp_consumption_report(osv.osv_memory):
    """
    Wizard to create custom report
    """
    _name = "mrp.consumption.report"
    _description = "Create Consumption Report"
    _columns = {
               'state': fields.selection( ( ('choose','choose'),   # choose date
                     ('get','get'),         # get the file
                   ) ),
               'data': fields.binary('File', readonly=True),
               'name': fields.char('Filename', 16, readonly=True),
               'mo_type': fields.selection([('Export','Export'), ('Domestic','Domestic'), ('Aerospace','Aerospace'), ('All','All')], 'MO Type', size=32, required=True),
               'partner_id': fields.many2one('res.partner', "Customer", domain = [('customer','=',True)]),
               'from_date': fields.date("From Date"),
               'to_date': fields.date("To Date"),
    }
    _defaults = {
                 'state': lambda *a: 'choose',
                }

    def get_sale_ref(self, cr, uid, ids, field_name=False):
        move_obj = self.pool.get('stock.move')

        def get_parent_move(move_id):
            move = move_obj.browse(cr, uid, move_id)
            if move.move_dest_id:
                return get_parent_move(move.move_dest_id.id)
            return move_id

        res = ''
        production = self.pool.get('mrp.production').browse(cr, uid, ids)
        if production.move_prod_id:
            parent_move_line = get_parent_move(production.move_prod_id.id)
            if parent_move_line:
                move = move_obj.browse(cr, uid, parent_move_line)
                if move.sale_line_id or move.sale_line_id is not None:
                    if field_name == 'name':
                        res = move.sale_line_id and move.sale_line_id.order_id.name or False
                    if field_name == 'partner_id':
                        res = move.sale_line_id and move.sale_line_id.order_id.partner_id.name or False
                    if field_name == 'requested_date':
                        res = move.sale_line_id and move.sale_line_id.order_id.requested_date or False
                    if field_name == 'origin':
                        res = move.sale_line_id and move.sale_line_id.order_id.origin or False
                    if field_name == 'create_date':
                        res = move.sale_line_id and move.sale_line_id.order_id.create_date or False
        return res


    def create_report(self,cr,uid,ids,context={}):
        print "=====cretae report======================="
        if not context:
            return False
        this = self.browse(cr, uid, ids)[0]
        print "=====cretae report=====this==================",this
        mo_type = False
        partner_name = False
        from_date = False
        to_date = False

        if this.mo_type:
            mo_type = this.mo_type
        if this.partner_id:
            partner_name = this.partner_id.name
        if this.from_date:
            from_date = this.from_date
        if this.to_date:
            to_date = this.to_date

        state_arr = ['draft','cancel']
        search_string = [('state','not in',state_arr),('name','like','MO')]

        if mo_type:
            if mo_type != "All":
                params = ('x_job_order_type','=',mo_type)
                search_string.append(params)

        if from_date:
            from_date = datetime.strptime(from_date,'%Y-%m-%d')
            params = ('create_date','>=',str(from_date))
            search_string.append(params)

        if to_date:
            to_date = datetime.strptime(to_date,'%Y-%m-%d')
            params = ('create_date','<=',str(to_date))
            search_string.append(params)


        prod_obj = self.pool.get('mrp.production')
        do_pool = self.pool.get('stock.picking')
#        if mo_type:
#            if mo_type=="All":
#                mo_ids = prod_obj.search(cr, uid, search_string)
#            else:
#                mo_ids = prod_obj.search(cr, uid, [('x_job_order_type','=',mo_type),('state','not in',state_arr),('name','like','MO')])

        mo_ids = prod_obj.search(cr, uid, search_string)
        print '_________mo_ids_____',mo_ids
        lst_mo = []
        for mo_id in mo_ids:
            mo_browse = prod_obj.browse(cr, uid, mo_id)
            do_search = do_pool.search(cr, uid, [('state','=','done'),('type','=','out'),('origin','=',mo_browse.origin)])
            print '______do_search_____',do_search
            if do_search:
                for do in do_search:
                    do_browse = do_pool.browse(cr, uid, do)
                    for move_line in do_browse.move_lines:
                        if move_line.product_id == mo_browse.product_id and move_line.partner_id.id == this.partner_id.id:
                            print '________if____1___'
                            if mo_browse.bom_id:
                                print '________if____2___'
                                for bom_line in mo_browse.bom_id.bom_lines:
                                    dic_mo = {
                                              'name': mo_browse.name,
                                              'create_date': datetime.strptime(mo_browse.date_start.split(' ')[0],'%Y-%m-%d').strftime('%d-%m-%Y'),
                                              'origin': mo_browse.origin or '',
                                              'customer': this.partner_id.name or '',
                                              'mo_type': this.mo_type,
                                              'product_code': mo_browse.product_id.default_code or '',
                                              'product_name': mo_browse.product_id.name,

                                              'consumed_product': bom_line.product_id.name,
                                              'consumed_product_category': bom_line.product_id.categ_id.name,
                                              'consumed_product_qty': bom_line.product_qty * move_line.product_qty,
                                              }
                                    lst_mo.append(dic_mo)
        print '________lst_mo_____________',lst_mo
#        final_data = [dict_ for (key, dict_) in decorated]
#        best = sorted([Player(v,k) for (k,v) in d.items()], reverse=True)



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
        sheet1.write(0, 4, "MO Type", style)
        sheet1.write(0, 5, "Product Code", style)
        sheet1.write(0, 6, "Product", style)
        sheet1.write(0, 7, "Raw Material", style)
        sheet1.write(0, 8, "Raw Material Category", style)
        sheet1.write(0, 9, "Raw Material Qty", style)

        i=1
        for data in lst_mo:
            sheet1.write(i, 0, data['name'])
            sheet1.write(i, 1, data['create_date'])
            sheet1.write(i, 2, data['origin'])
            sheet1.write(i, 3, data['customer'])
            sheet1.write(i, 4, data['mo_type'])
            sheet1.write(i, 5, data['product_code'])
            sheet1.write(i, 6, data['product_name'])
            sheet1.write(i, 7, data['consumed_product'])
            sheet1.write(i, 8, data['consumed_product_category'])
            sheet1.write(i, 9, data['consumed_product_qty'])
            i = i+1

        book.save(f)
        out=base64.encodestring(f.getvalue())
        return self.write(cr, uid, ids, {'state':'get', 'data':out, 'name':'Consumption Report.xls'}, context=context)

mrp_consumption_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
