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

{
    'name': "Stock don't auto create lots",
    'version': '1.0',
    'category': 'Sales',
    'author': 'O4SB - Graeme Gellatly',
    'website': 'http://www.openforsmallbusiness.co.nz',
    'depends': ["base", 'stock'],
    "description": """
    This module provides :
        a very simple extension to Raise Exception rather than auto create lots.  
        This isn't meant to be a permanent module, just help for people suffering with the standard functionality.
        
        Ported from custom module
    """,
    "init_xml": [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}