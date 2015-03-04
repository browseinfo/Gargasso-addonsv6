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

class stock_move(osv.osv):
    _inherit = 'stock.move'

    def action_consume(self, cr, uid, ids, product_qty, location_id=False, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            if (not move.prodlot_id.id) and (move.product_id.track_production and location_id):
                raise osv.except_osv(_('Warning!'), _('Please provide Production Lots before consuming ! [product:%s]') % move.product_id.name)
#                raise osv.except_osv(_('Warning!'), _('Please provide Production Lots before consuming !'))
        result = super(stock_move, self).action_consume(cr, uid, ids, product_qty, location_id=location_id, context=context)
        return result
    
stock_move()
