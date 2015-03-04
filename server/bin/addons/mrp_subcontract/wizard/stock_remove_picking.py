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

from osv import osv, fields

class stock_rm_picking(osv.osv_memory):
    """
    delete all picking which have no move line
    """
    _name = "stock.rm.picking"
    _description = "delete all picking which have no move line"

    def delete_picking(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        picks = []
        pick_obj = self.pool.get('stock.picking')
        pick_ids = pick_obj.search(cr, uid, [('type', '=', 'out' )])
        for pick in pick_obj.browse(cr, uid, pick_ids, context=context):
            if not pick.move_lines:
                picks.append(pick.id)
        if picks:
            pick_obj.write(cr, uid, picks, {'active': False}, context=context)
#            cr.execute('delete from stock_picking where id IN %s', (tuple(picks),))
        return {'type': 'ir.actions.act_window_close'}

stock_rm_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
