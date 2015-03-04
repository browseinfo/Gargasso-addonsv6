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
from lxml import etree
import decimal_precision as dp

import netsvc
import pooler
from osv import fields, osv, orm
from tools.translate import _


class to_deliver(osv.osv):
    _name = "to.deliver"
    _columns = {
               'name':fields.char('Company Name', size=150),
               'city':fields.char('City', size=150),
               }
to_deliver()

class under_duty(osv.osv):
     
    _name = "under.duty"
     
    _columns = {
                'name':fields.char('Duty', size=150),
               }    
under_duty()

class account_invoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"

    _columns = {
                'buyers_order_no': fields.char("Buyer's Order No & Date", size=500),
                'buyers_address': fields.char("Buyer's Address", size=1000, help="Buyer Address (If other than consignee). Address details should be splitted by '!' character. E.g. Garg Associates!D-6, Meerut Road!Ghaziabad-201003 (U.P.)!India!Tel.: +91 120-2712128"),
                'carriage': fields.char("carriage", size=120),
                'receipt_place': fields.char("Place of Receipt by Pre-carrier", size=150),
                'vessel': fields.char("Vessel/Flight No.", size=120),
                'loading_port': fields.char("Port of Loading", size=120),
                'discharge_port': fields.char("Port of Discharge", size=120),
                'final_destination': fields.char("Final Destination", size=120),
                'final_destination_country': fields.char("Country of Final Destination", size=120),
                'excise_chapter': fields.char("Excise Chapter", size=200),
                'incoterm1': fields.char("Incoterm 1", size=120),
                'incoterm2': fields.char("incoterm 2", size=120),
                'lot_numbers': fields.char("Packages", size=120, help="Provide packages details as e.g. 13/852 TO 13/858"),
                'weight': fields.char("Weight KG Net", size=120),
                'packed': fields.char("Packed", size=120),
                'delivery_term': fields.char("Terms of Delivery and Payment", size=120),
                'no_of_cartons': fields.integer("Number of Cartons"),
                'community_type': fields.char("Community Type", size=120, required=True),
                'removal_date': fields.date("Goods Removal Date"),
                'are_form_number': fields.char("Form A.R.E. No.", size=200),
                'currency_rate': fields.float("Currency Rate"),
                'vat_flag': fields.boolean('Cenvat'),
                'edu_flag': fields.boolean('Education Cess'),
                'sedu_flag': fields.boolean('S.H. Education Cess'),
                'vat': fields.float("Cenvat Percentage"),
                'edu_cess': fields.float("Education Cess Percentage"),
                'sedu_cess': fields.float("S.H. Education Cess Percentage"),
                'undertaking_bond': fields.char("Undertaking Bond No.", size=150),
                'to_deliver':fields.many2one('to.deliver','To Deliver'),
                'under_duty':fields.many2one('under.duty','Duty'),
                'registration_no':fields.char('Registration No.',size=120),
                'advance_licence_no':fields.char('Advance Licence No.',size=120),
                'dimension' : fields.char('Dimensions', size=240),
    }
    _defaults = {
                 'carriage': "DHL",
                 'receipt_place': "GHAZIABAD",
                 'loading_port': "IGIA, NEW DELHI",
                 'excise_chapter': "PTFE WIRES & CABLES (CH 85441920)",
                 'incoterm1': "FOB",
                 'incoterm2': "DAP",
                 'community_type': "EUROPEAN",
                 'currency_rate': 0.0,
                 'vat_flag': fields.boolean('Cenvat'),
                 'edu_flag': fields.boolean('Education Cess'),
                 'sedu_flag': fields.boolean('S.H. Education Cess'),
                 'vat': True,
                 'edu_cess': True,
                 'sedu_cess': True,
                 'vat': 12,
                 'edu_cess': 2,
                 'sedu_cess': 1,
                 'undertaking_bond': "33/2012 dt. 11.12.2012"
                 }


account_invoice()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
