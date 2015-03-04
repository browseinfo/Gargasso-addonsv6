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
from crm import crm
from osv import osv, fields
from tools.translate import _


class stock_move_spool_wizard(osv.osv_memory):
    _name = 'stock.move.spool.wizard'
    _description = 'Stock Move Spool Wizard'
    _columns = {
        'stock_move_ids': fields.many2many('stock.move', rel='stock_move_rel', id1='stock_move_id', id2='stock_move_wizard_id', string='Stock Move'),
    }

    def print_report(self,cr, uid, ids, context=None):
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
        data = self.read(cr, uid, ids, [], context=context)[0]
        print "\n\ndata", data
        datas = {
             'ids': [data.get('id')],
             'model': 'stock.move',
             'form': data
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'stock.move.spool.report',
            'datas': datas,
        }
    
    #def default_get(self, cr, uid, fields, context=None):
    #    if context is None:
    #        context = {}
    #    record_ids = context.get('active_ids', False)
    #    res = super(stock_move_spool_wizard, self).default_get(cr, uid, fields, context=context)

    #    if record_ids:
    #        opp_ids = []
    #        opps = self.pool.get('stock.move').browse(cr, uid, record_ids, context=context)
    #        for opp in opps:
    #            if opp.state not in ('done', 'cancel'):
    #                opp_ids.append(opp.id)
    #        if 'stock_move_ids' in fields:
    #            res.update({'stock_move_ids': opp_ids})

    #    return res
stock_move_spool_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
