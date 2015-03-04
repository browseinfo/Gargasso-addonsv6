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

from osv import fields, osv
import time
from datetime import datetime
from lxml import etree
from tools.translate import _

class subcontract_wizard(osv.osv_memory):

    _name = 'subcontract.wizard'

#    _description = 'Use this wizard to select production order for subcontracting report'

    _columns={
    
        'production_ids':fields.many2many('mrp.production', 'mrp_production_report_rel', 'report_id', 'production_id', 'Production Order', domain=[('state', '!=', 'draft')]),
        'comments': fields.text('Comments'),
     }
    
    
    def default_get(self, cr, uid, fields, context=None):
        """
        This function gets default values
        """
        record_ids = context and context.get('active_ids', False) or False
        res = super(subcontract_wizard, self).default_get(cr, uid, fields, context=context)
        create_date = ''
        error_message = ''
        error_collect = []
        date_check = True
        flag = True

        if record_ids:
            mo_ids = []
            mo_records = self.pool.get('mrp.production').browse(cr, uid, record_ids, context=context)
            for mo in mo_records:
                date_check = True
                if mo.state not in ('draft') and not mo.send_report and mo.name[:2]=='CO':
                    for mo1 in mo_records:
                        if mo1.create_date.split(' ')[0] <> mo.create_date.split(' ')[0]:
                            date_check = False
                            flag = False
                            if '1' not in error_collect:
                                error_collect.append('1')
                    if date_check:
                        mo_ids.append(mo.id)
                        create_date = mo.create_date.split(' ')[0]
                else:
                    if mo.send_report:
                        flag = False
                        if '2' not in error_collect:
                            error_collect.append('2')
                    if mo.name[:2]<>'CO':
                        flag = False
                        if '3' not in error_collect:
                            error_collect.append('3')
                    if mo.state in ('draft'):
                        flag = False
                        if '4' not in error_collect:
                            error_collect.append('4')

            if not flag:
                for i in error_collect:
                    if i == '1':
                        error_message += ' Select MO with same create date.'
                    if i == '2':
                        error_message += ' One of the selected MO already ordered, use report wizard for reprint.'
                    if i == '3':
                        error_message += ' One of the selected MO is not valid Subcontracting MO, select valid Subcontracting MO.'
                    if i == '4':
                        error_message += ' One of the selected MO is in draft state, select valid MO.'
                    
                raise osv.except_osv(('Error !'),(error_message))               
            
            if create_date <> '':
                pick_obj = self.pool.get('stock.picking')
                mrp_obj = self.pool.get('mrp.production')
                pick_ids = pick_obj.search(cr,uid, [('type','=', 'out')])
                mrp_ids = mrp_obj.search(cr,uid, [('picking_id', 'in', pick_ids )])
                for mrp in mrp_obj.browse(cr,uid, mrp_ids,):
                    date = mrp.create_date.split()[0]
                    if date == create_date and mrp.id not in mo_ids and mrp.state not in ('draft', 'cancel') and not mrp.send_report:
                        raise osv.except_osv(('Error !'),('Select all MO with same create date.'))
                    
            if 'production_ids' in fields:
                res.update({'production_ids': mo_ids})
        return res

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
            'report_name': 'mrp.print.report',
            'datas': datas,
       }

    def print_send_report(self, cr, uid, ids, context=None):
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
        res.append('send_report')
        res = res and res[0] or {}
        datas.update({'form': res})
        datas['form'].update({ 'send_report': True})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'mrp.print.report',
            'datas': datas,
       }

subcontract_wizard()

class mrp_production(osv.osv):
	_inherit = 'mrp.production'
	_name = 'mrp.production'
	
	_columns = {
		'send_report': fields.boolean('MO Ordered', readonly=True),

	}
	_defaults = {
		'send_report': False,
	}
mrp_production()
