###############################################################################
#
#  Copyright (C) 2007-TODAY OpenERP SA. All Rights Reserved.
#
#  $Id$
#
#  Developed by OpenERP (http://openerp.com) and Axelor (http://axelor.com).
#
#  The OpenERP web client is distributed under the "OpenERP Public License".
#  It's based on Mozilla Public License Version (MPL) 1.1 with following 
#  restrictions:
#
#  -   All names, links and logos of OpenERP must be kept as in original
#      distribution without any changes in all software screens, especially
#      in start-up page and the software header, even if the application
#      source code has been changed or updated or code has been added.
#
#  You can see the MPL licence at: http://www.mozilla.org/MPL/MPL-1.1.html
#
###############################################################################

"""
This module implementes heirarchical tree view for a tiny model having
    view_type = 'tree'
"""
import time
import simplejson
import cherrypy

import actions

from openobject.i18n.format import format_datetime
from openobject.tools import url, expose

from openerp.controllers import SecuredController
from openerp.utils import rpc, cache, icons, common, TinyDict, expr_eval
from openerp.widgets import tree_view

FORMATTERS = {
    'integer': lambda value, _i: '%s' % int(value),
    'float': lambda value, _i: '%.02f' % (value),
    'date': lambda value, _i: format_datetime(value, 'date'),
    'datetime': lambda value, _i: format_datetime(value, 'datetime'),
    'one2one': lambda value, _i: value[1],
    'many2one': lambda value, _i: value[1],
    'selection': lambda value, info: dict(info['selection']).get(value, ''),
}

class Tree(SecuredController):
    _cp_path = "/openerp/tree"

    @expose(template="/openerp/controllers/templates/tree.mako")
    def create(self, params):
        view_id = (params.view_ids or False) and params.view_ids[0]
        domain = params.domain
        context = params.context
        ctx = dict(context,
                   **rpc.session.context)

        res_id = params.ids or 0
        model = params.model

        if view_id:
            view_base =  rpc.session.execute(
                    'object', 'execute', 'ir.ui.view', 'read', [view_id],
                    ['model', 'type'], context)[0]
            model = view_base['model']
            view = cache.fields_view_get(model, view_id, view_base['type'], context)
        else:
            view = cache.fields_view_get(model, False, 'tree', context)
        fields = cache.fields_get(view['model'], False, context)
            
        tree = tree_view.ViewTree(view, model, res_id, domain=domain, context=context, action="/tree/action", fields=fields)
        if tree.toolbar:
            proxy = rpc.RPCProxy(model)

            for tool in tree.toolbar:
                if tool.get('icon'):
                    tool['icon'] = icons.get_icon(tool['icon'])
                else:
                    tool['icon'] = False
                id = tool['id']
                ids = proxy.read([id], [tree.field_parent], ctx)[0][tree.field_parent]
                tool['ids'] = ids
            
        can_shortcut = self.can_shortcut_create()
        shortcut_ids = []

        for sc in cherrypy.session.get('terp_shortcuts') or []:
            if isinstance(sc['res_id'], tuple):
                shortcut_ids.append(sc['res_id'][0])
            else:
                shortcut_ids.append(sc['res_id'])
        
        return {'tree': tree, 'model': model, 'can_shortcut': can_shortcut, 'shortcut_ids': shortcut_ids}

    def can_shortcut_create(self):
        return (rpc.session.is_logged() and
                rpc.session.active_id and
                cherrypy.request.path_info == '/openerp/tree/open' and
                cherrypy.request.params.get('model') == 'ir.ui.menu')

    @expose()
    def default(self, id, model, view_id, domain, context):
        params = TinyDict()

        try:
            view_id = int(view_id)
        except TypeError:
            # if view_id is None
            view_id = False

        params.ids = id
        params.view_ids = [view_id]
        params.model = model
        params.domain = domain
        params.context = context or {}

        return self.create(params)

    def sort_callback(self, item1, item2, field, sort_order="asc", type=None):
        a = item1[field]
        b = item2[field]

        if type == 'many2one' and isinstance(a, (tuple, list)):
            a = a[1]
            b = b[1]

        if(sort_order == "dsc"):
            return -cmp(a, b)

        return cmp(a, b)

    @expose('json')
    def data(self, ids, model, fields, field_parent=None, icon_name=None,
             domain=[], context={}, sort_by=None, sort_order="asc", fields_info=None, colors={}):
        
        if ids == 'None' or ids == '':
            ids = []

        if isinstance(ids, basestring):
            ids = map(int, ids.split(','))
        elif isinstance(ids, list):
            ids = map(int, ids)

        if isinstance(fields, basestring):
            fields = eval(fields)

        if isinstance(domain, basestring):
            domain = eval(domain)

        if isinstance(context, basestring):
            context = eval(context)
        
        if isinstance(colors, basestring):
            colors = eval(colors)
            
        if isinstance(fields_info, basestring):
            fields_info = simplejson.loads(fields_info)

        if field_parent and field_parent not in fields:
            fields.append(field_parent)

        proxy = rpc.RPCProxy(model)

        ctx = dict(context,
                   **rpc.session.context)

        if icon_name:
            fields.append(icon_name)

        if model == 'ir.ui.menu' and 'action' not in fields:
            fields.append('action')

        result = proxy.read(ids, fields, ctx)

        if sort_by:
            fields_info_type = simplejson.loads(fields_info[sort_by])
            result.sort(lambda a,b: self.sort_callback(a, b, sort_by, sort_order, type=fields_info_type['type']))

        for item in result:
            if colors:
                for color, expr in colors.items():
                    try:
                        if expr_eval(expr,item or False):
                            item['color'] = color
                            break
                    except:
                            pass

        # format the data
        for field in fields:
            field_info = simplejson.loads(fields_info[field])
            if field_info.get('widget',''):
                field_info['type'] = field_info['widget']
            formatter = FORMATTERS.get(field_info['type'])
            for x in result:
                if x[field] and formatter:
                    x[field] = formatter(x[field], field_info)

        records = []
        for item in result:
            # empty string instead of False or None
            for k, v in item.items():
                if v is None or v is False:
                    item[k] = ''

            id = item.pop('id')
            record = {
                'id': id,
                'action': url('/openerp/tree/open', model=model, id=id, context=ctx),
                'target': None,
                'icon': None,
                'children': [],
                'items': item
            }

            if icon_name and item.get(icon_name):
                icon = item.pop(icon_name)
                record['icon'] = icons.get_icon(icon)

            if field_parent and field_parent in item:
                record['children'] = item.pop(field_parent) or None

                # For nested menu items, remove void action url
                # to suppress 'No action defined' error.
                if (model == 'ir.ui.menu' and record['children'] and
                     not item['action']):
                    record['action'] = None

            records.append(record)

        return {'records': records}

    def do_action(self, name, adds={}, datas={}):
        params, data = TinyDict.split(datas)

        model = params.model
        context = params._terp_context or {}
        ids = data.get('ids') or []

        ctx = rpc.session.context.copy()
        ctx.update(context)

        if ids:
            ids = map(int, ids.split(','))

        id = (ids or False) and ids[0]

        if ids:
            return actions.execute_by_keyword(
                    name, adds=adds, model=model, id=id, ids=ids, context=ctx,
                    report_type='pdf')
        else:
            raise common.message(_("No record selected"))

    @expose()
    def report(self, **kw):
        return self.do_action('client_print_multi', datas=kw)

    @expose()
    def action(self, **kw):
        params, data = TinyDict.split(kw)

        action = params.data

        if not action:
            return self.do_action('tree_but_action', datas=kw)

        import actions

        ids = params.selection or []
        id = (ids or False) and ids[0]

        return actions.execute(action, model=params.model, id=id, ids=ids, report_type='pdf')

    @expose()
    def switch(self, **kw):
        params, data = TinyDict.split(kw)

        ids = params.selection or []
        if ids:
            import actions
            return actions.execute_window(False, res_id=ids, model=params.model, domain=params.domain)
        else:
            raise common.message(_('No resource selected'))

    @expose()
    def open(self, **kw):
        return self.do_action('tree_but_open', datas={
                '_terp_model': kw.get('model'),
                '_terp_context': kw.get('context', {}),
                '_terp_domain': kw.get('domain', []),
                'ids': kw.get('id')})
