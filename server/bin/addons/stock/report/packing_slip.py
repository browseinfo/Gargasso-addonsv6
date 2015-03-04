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

import time
from report import report_sxw
from osv import osv
import pooler

from os.path import join
import addons

class packing_slip(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(packing_slip, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_qtytotal':self._get_qtytotal,
#            'get_qt_total_picking': self._get_qt_total_picking,
#            'get_qt_list_picking': self._get_qt_list_picking,
#            'get_prod_total_picking': self._get_prod_total_picking,
#            'get_customer_info_picking': self._get_customer_info_picking,
#            'get_total_quantity_picking': self._get_total_quantity_picking,
#            'get_box_count_picking': self._get_box_count_picking,
#            'get_main_prod_picking': self._get_main_prod_picking,
#            'get_custom_list_picking': self._get_custom_list_picking,
            
        })
        
    def _get_qtytotal(self,move_lines):
        total = 0.0
        uom = move_lines[0].product_uom.name
        for move in move_lines:
            total+=move.product_qty
        return {'quantity':total,'uom':uom}
    
#    def _get_qt_total_picking(self, lst, prodlotid):
#        totalqty=0
#        for id in lst:
#            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and prodlotid==id.x_spool_number):
#                totalqty+=id.product_qty
#        return totalqty
#
#    def _get_qt_list_picking(self,lst,spoolnumber):
#        finallist=''
#        for id in lst:
#            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and spoolnumber==id.x_spool_number):
#                if(finallist==''):
#                    finallist=str(round(id.product_qty,0))
#                else:
#                    finallist=finallist + ' + ' + str(round(id.product_qty,0))
#        return finallist
#    
#    def _get_prod_total_picking(self,lst,prodid):
#        totalqty=0
#        for id in lst:
#            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and prodid==id.product_id.id):
#                totalqty+=id.product_qty
#        return totalqty
#
#    def _get_customer_info_picking(self,lst,prodid,custid,part):
#        for id in lst:
#            if(id.name.id==custid.id and id.product_id.id==prodid.id):
#                if(part=='code'):
#                    prodinfo=id.product_code
#                if(part=='name'):
#                    prodinfo=id.product_name
#        return prodinfo
#
#    def _get_total_quantity_picking(self,lst):
#        totalqty=0
#        for line in lst:
##            if(line['state']<>'cancel' and line['state']<>'draft'):
#            if(line['state']=='done'):
#                totalqty=totalqty+line['product_qty']
#        return totalqty
#    
#    def _get_box_count_picking(self,lst):
#        ret_lst = []
#        cust_lst = []
#        final_list = []
#        return_list = []
#        index = 0
#        intSum = 0
#        boxcount=0
#        flag = 0
#
#        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
#        decorated.sort()
#        sortedRes = [dict_ for (key,i,dict_) in decorated]
#        
#        
#        for line in sortedRes:
#            if(line['state']<>'cancel' and line['state']<>'draft'):
#                cust_lst.append(line)
#        
#        if(cust_lst<>[]):
#            curId = cust_lst[0]['tracking_id']
#
#
#        for line in cust_lst:
#            if final_list==[]:
#                final_list.append(line)
#            else:
#                for line2 in final_list:
#                    if(line['tracking_id']==line2['tracking_id']):
#                        flag=0
#                        break
#                    else:
#                        flag=1
#                if(flag==1):
#                    final_list.append(line)
#                    flag=0
#        
#        for line in final_list:
#            boxcount=boxcount+1
#                
#        return boxcount
#
#    def _get_main_prod_picking(self, lst):
#        ret_lst = []
#        cust_lst = []
#        final_list = []
#        return_list = []
#        index = 0
#        intSum = 0
#        flag = 0
#
#        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
#        decorated.sort()
#        sortedRes = [dict_ for (key,i,dict_) in decorated]
#        
#        
#        for line in sortedRes:
##            if(line['state']<>'cancel' and line['state']<>'draft'):
#            if(line['state']=='done'):
#                cust_lst.append(line)
#        
#        if(cust_lst<>[]):
#            curId = cust_lst[0]['product_id']
#
#
#        for line in cust_lst:
#            if final_list==[]:
#                final_list.append(line)
#            else:
#                for line2 in final_list:
#                    if(line['product_id']==line2['product_id']):
#                        flag=0
#                        break
#                    else:
#                        flag=1
#                if(flag==1):
#                    final_list.append(line)
#                    flag=0
#        return final_list
#    
#    
#    def _get_custom_list_picking(self,lst):
#        ret_lst = []
#        cust_lst = []
#        final_list = []
#        return_list = []
#        index = 0
#        intSum = 0
#        flag = 0
#        
#        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
#        decorated.sort()
#        sortedRes = [dict_ for (key,i,dict_) in decorated]
#
#        for line in sortedRes:
#            if(line['state']<>'cancel' and line['state']<>'draft'):
#                cust_lst.append(line)
#        
#        if(cust_lst<>[]):
#            curId = cust_lst[0]['x_spool_number']
#
#        for line in cust_lst:
#            if final_list==[]:
#                final_list.append(line)
#            else:
#                for line2 in final_list:
#                    if(line['x_spool_number']==line2['x_spool_number']):
#                        flag=0
#                        break
#                    else:
#                        flag=1
#                if(flag==1):
#                    final_list.append(line)
#                    flag=0
#        return final_list
    

report_sxw.report_sxw('report.stock.packing.slip','stock.picking','addons/stock/report/packing_slip.rml',parser=packing_slip)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
