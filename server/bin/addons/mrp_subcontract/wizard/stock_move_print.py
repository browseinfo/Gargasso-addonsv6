# -*- coding: utf-8 -*-
##############################################################################
#
#    Manufacturing Subcontracting Process
#    Copyright (C) 2004-2010 Browse Info Pvt Ltd (<http://www.browseinfo.in>).
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

from osv import fields, osv

class stock_move_print(osv.osv_memory):

   _name ='stock.move.print'
   _description = 'stock moves Report'
   _columns = {
        'date': fields.date('Date', required=True),
    }

   _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }

   def print_report(self, cr, uid, ids, context=None):
        """
         To get the date and print the report
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: return report
        """
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}

        res = self.read(cr, uid, ids, context=context)
        res = res and res[0] or {}
        datas.update({'form': res})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'stock.do.move',
            'datas': datas,
       }

stock_move_print()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
