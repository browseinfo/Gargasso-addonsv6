# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - module extension
#    Copyright (C) 2010- O4SB (<http://openforsmallbusiness.co.nz>).
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

from osv import osv, fields
from tools.translate import _

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    
    def draft_force_assign(self, cr, uid, ids, *args):
        """ Confirms Productio Lot assignment in draft state.
        @return: True
        """
        message=""
        msg=1
        for pick in self.browse(cr, uid, ids):
            if pick.move_lines:
                print pick.move_lines
                for line in pick.move_lines:
                    if not line.prodlot_id:
                        msg=0
                        if message=="":
                            message = "You cannot process picking without lot assignment for: " + line.product_id.default_code
                        else:
                            message = message + ", " + line.product_id.default_code
                if msg != 1:
                    raise osv.except_osv(_('Error !'),_(message))
        return super(stock_picking, self).draft_force_assign(cr, uid, ids, *args)

stock_picking()
