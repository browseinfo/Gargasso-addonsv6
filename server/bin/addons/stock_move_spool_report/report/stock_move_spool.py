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
import time
import datetime
from os.path import join
import addons
import itertools
import operator
import math
from report import report_sxw

class stock_move_spool(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self.stock_move_dict = {}
        self.spool = []
        super(stock_move_spool, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
             'time': time,
             'get_spool_stock_move': self._get_spool_stock_move,
        })

    def _get_spool_stock_move(self, do_ids):
        res = []
        if do_ids:
            for do in do_ids:
                for stock in do.move_lines:
                    date1 = []
                    date1 = stock.date.split(' ')
                    date2 = []
                    date2 = stock.create_date.split(' ')
                    date_formate = date2[0].split('-')
                    final_date2 = date_formate[2] + '-' + date_formate[1] + '-' + date_formate[0]
                    customer_product_code = ''
                    crm_po_no = ''
                    if stock.partner_id:
                        print "\n\nstock.partner_id!!!!!!",stock.partner_id,stock.partner_id.id
                        customer_prod_id = self.pool.get('product.customerinfo').search(self.cr,self.uid,[('product_id', '=', stock.product_id.id)])
                        print "\n\ncustomer_prod_id",customer_prod_id
                        
                        if customer_prod_id:
                            customer_product_code = self.pool.get('product.customerinfo').browse(self.cr,self.uid,customer_prod_id[0]).product_code
                            print "\n\ncustomer_prod_code",customer_product_code
#                     if stock.sale_line_id:
#                         sale_line_id = stock.sale_line_id
#                         if isinstance(sale_line_id, list):
#                             sale_line_id = int(sale_line_id[0])
#                         sale_line_id = int(sale_line_id)
#                         so_id = self.pool.get('sale.order.line').browse(self.cr,self.uid,sale_line_id).order_id
#                         crm_po_no = self.pool.get('sale.order').browse(self.cr,self.uid,so_id.id).crm_po_no
#                         if crm_po_no:
#                             crm_po_no = str(crm_po_no).split(' ')[0]
                    
                    if stock.crm_po_no:
                        crm_po_no = str(stock.crm_po_no).split(' ')[0]
                        
                    res.append({
                        'spool_number':stock.x_spool_number,
                        'product':stock.product_id.name,
                        'product_code':stock.product_id.code,
                        'qty':stock.product_qty,
                        'uom':stock.product_uom.name,
                        'variants':stock.product_id.variants,
                        'color':stock.product_id.x_colour,
                        'partner':stock.picking_id.partner_id.name,
                        'partner_ref':stock.partner_id.ref,
                        'production_lot':stock.prodlot_id.name,
                        'serial':stock.tracking_id.serial,
                        'company':stock.company_id.name,
                        'company_logo':stock.company_id.logo,
                        'date':date1[0],
                        'create_date':final_date2,
                        'customer_product_code':customer_product_code,
                        'crm_po_no':crm_po_no,
                        'partner_city':stock.partner_id.city,
                        
                    })
                groups = itertools.groupby(res, key=operator.itemgetter('spool_number'))
                result = [{'spool_number':k,'values':[x for x in v]} for k, v in groups]
                final_list=[]
                counter = 0
                for semi_result in result:
                    qty = 0
#                     if (counter+1) % 7==0:
#                         counter = 1
#                     else:
                    counter+=1
                    qty_list = []
                    index = 0
                    for result1 in semi_result['values']:
                        qty += result1['qty']
                        index += 1
                        qty_list.append(result1['qty'])
                    final_list.append({
                        'product': semi_result['values'][0]['product'],
                        'partner_ref':semi_result['values'][0]['partner_ref'],
                        'spool_number':semi_result['values'][0]['spool_number'],
                        'production_lot':semi_result['values'][0]['production_lot'],
                        'partner':semi_result['values'][0]['partner'],
                        'variants':semi_result['values'][0]['variants'],
                        'product_code':semi_result['values'][0]['product_code'],
                        'serial':semi_result['values'][0]['serial'],
                        'uom':semi_result['values'][0]['uom'],
                        'qty': qty,
                        'company':semi_result['values'][0]['company'],
                        'date':semi_result['values'][0]['date'],
                        'create_date':semi_result['values'][0]['create_date'],
                        'color':semi_result['values'][0]['color'],
                        'customer_product_code':semi_result['values'][0]['customer_product_code'],
                        'index':index,
                        'qty_list':qty_list,
                        'company_logo':semi_result['values'][0]['company_logo'],
                        'crm_po_no':semi_result['values'][0]['crm_po_no'],
                        'partner_city':semi_result['values'][0]['partner_city'],
                        'counter':counter
                    })
                print "\n\nfinal result",final_list
        return final_list 
        
    
file_path = join(addons.get_module_resource('stock_move_spool_report'),'report/stock_move_spool.rml')
report_sxw.report_sxw(
    'report.stock.move.spool.report',
    'stock.picking',
    file_path,
    parser=stock_move_spool,
    header=False
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
