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
#        if mo_type:
#            if mo_type=="All":
#                mo_ids = prod_obj.search(cr, uid, search_string)
#            else:
#                mo_ids = prod_obj.search(cr, uid, [('x_job_order_type','=',mo_type),('state','not in',state_arr),('name','like','MO')])

        mo_ids = prod_obj.search(cr, uid, search_string)
        print "========Mo ids===========", mo_ids

#        print p



        production_data = prod_obj.browse(cr, uid, mo_ids)
        main_prod = []
        child_prod = []
        prod_data = []

        final_data = []
        child_data = []
        parent_data = []
        move_data = []
        non_ref_mos = []

        if partner_name:
            for prod in production_data:
                if partner_name == prod.sale_ref:
                    prod_data.append(prod)
        else:
            prod_data = production_data

#        for prod in prod_data:
#            if prod.origin:
#                if 'MO' not in str(prod.origin):
#                    main_prod.append(prod)
#                else:
#                    child_prod.append(prod)
#            else:
#                main_prod.append(prod)

########## TAKES OUT LINES FROM CHILD AND NON REFERNCED PRODUCTION ORDER
        print "===========prod_data==========",prod_data
        for mo in prod_data:
            if mo.origin and 'MO' in str(mo.origin):
                for move in mo.move_lines2:
                    print "=============move=========", move
                    categ_name = str(move.product_id.categ_id.parent_id.name)
                    product_categ_name = str(move.product_id.categ_id.name)
                    raw_material = move.product_id.name
                    mo_partner_name = self.get_sale_ref(cr, uid, mo.id,'partner_id') or ''
                    if (categ_name == 'Conductors' or categ_name == 'Tapes' or categ_name == 'Raw Material'):
                        if not any(item['consumed_product'] == raw_material for item in move_data):
                            move_data.append({
                                 'name': mo.name,
                                 'create_date': datetime.strptime(mo.date_start.split(' ')[0],'%Y-%m-%d').strftime('%d-%m-%Y'),
                                 'origin': mo.origin or '',
                                 'customer': mo_partner_name,
                                 'mo_type': mo.x_job_order_type,
                                 'product_code': mo.product_id.default_code,
                                 'product_name': mo.product_id.name,
                                 'consumed_product': raw_material,
                                 'consumed_product_category': product_categ_name,
                                 'consumed_product_qty': move.product_qty,
                                 })
                        else:
                            for item in move_data:
                                if item['consumed_product'] == raw_material:
                                    item['consumed_product_qty'] = item['consumed_product_qty'] + move.product_qty
                if len(move_data)>0:
                    for line in move_data:
                        child_data.append(line)
                move_data = []

######### TAKES OUT LINES FROM PARENT PRODUCTION ORDER

        for mo in prod_data:
            if not mo.origin or 'MO' not in str(mo.origin):
                mo_partner_name = self.get_sale_ref(cr, uid, mo.id,'partner_id') or ''
                for move in mo.move_lines2:
                    print "================moves2=============", move
                    categ_name = str(move.product_id.categ_id.parent_id.name)
                    product_categ_name = str(move.product_id.categ_id.name)
                    raw_material = move.product_id.name
                    if categ_name == 'Conductors' or categ_name == 'Tapes' or categ_name == 'Raw Material':
                        if not any(item['consumed_product'] == raw_material for item in move_data):
                            move_data.append({
                                 'name': mo.name,
                                 'create_date': datetime.strptime(mo.date_start.split(' ')[0],'%Y-%m-%d').strftime('%d-%m-%Y'),
                                 'origin': mo.origin or '',
                                 'customer': mo_partner_name,
                                 'mo_type': mo.x_job_order_type,
                                 'product_code': mo.product_id.default_code,
                                 'product_name': mo.product_id.name,
                                 'consumed_product': raw_material,
                                 'consumed_product_category': product_categ_name,
                                 'consumed_product_qty': move.product_qty,
                                 })
                        else:
                            for item in move_data:
                                if item['consumed_product'] == raw_material:
                                    item['consumed_product_qty'] = item['consumed_product_qty'] + move.product_qty

                if len(move_data)==0:
                    parent_data.append({
                                 'name': mo.name,
                                 'create_date': datetime.strptime(mo.date_start.split(' ')[0],'%Y-%m-%d').strftime('%d-%m-%Y'),
                                 'origin': mo.origin or '',
                                 'customer': mo_partner_name,
                                 'mo_type': mo.x_job_order_type,
                                 'product_code': mo.product_id.default_code,
                                 'product_name': mo.product_id.name,
                                 'consumed_product': '',
                                 'consumed_product_category': '',
                                 'consumed_product_qty': '',
                                 })
                else:
                    for line in move_data:
                        parent_data.append(line)
                move_data = []

        add_flag = False
        found = False
        search_dict = []

######## Search Child in parent based on origin and add if not exists, if exists add quantity.

        for child in child_data:
#            search_dict.append((item for item in parent_data if item["name"] in str(child['origin'])).next())
            for mo in (item for item in parent_data if item["name"] in str(child['origin'])):
                if mo['name'] in child['origin']:
                    found = True
                    temp_dict = mo
                    if mo['consumed_product'] == child['consumed_product']:
                        add_flag = True
                        mo['consumed_product_qty'] = mo['consumed_product_qty'] + child['consumed_product_qty']
                        break

            if not add_flag and found:
                parent_data.append({
                                    'name': temp_dict['name'],
                                    'create_date': temp_dict['create_date'],
                                    'origin': temp_dict['origin'],
                                    'customer': temp_dict['customer'],
                                    'mo_type': temp_dict['mo_type'],
                                    'product_code': temp_dict['product_code'],
                                    'product_name': temp_dict['product_name'],
                                    'consumed_product': child['consumed_product'],
                                    'consumed_product_category': child['consumed_product_category'],
                                    'consumed_product_qty': child['consumed_product_qty']
                                    })
            if not add_flag and not found:
                parent_data.append(child)
            found = False
            add_flag=False

        decorated = sorted([(dict_['name'], dict_) for dict_ in parent_data], reverse=True)
#        decorated.sort()
        final_data = [dict_ for (key, dict_) in decorated]
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
        for data in final_data:
            if data['consumed_product'] != '':
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