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
from openerp.controllers import SecuredController
from openerp.utils import rpc, TinyDict, TinyForm

from openobject.tools import expose

class FieldPref(SecuredController):

    _cp_path = "/openerp/fieldpref"

    @expose(template="/openerp/controllers/templates/fieldpref.mako")
    def index(self, **kw): #_terp_model, _terp_field, _terp_deps

        click_ok = None
        params, data = TinyDict.split(kw)
        deps = params.deps
        return dict(model=params.model, click_ok=click_ok, field=params.field, deps=deps)

    @expose('json')
    def get(self, **kw):
        params, data = TinyDict.split(kw)

        field = params.field.split('/')

        prefix = '.'.join(field[:-1])
        field = field[-1]

        pctx = TinyForm(**kw).to_python(safe=True)
        ctx = pctx.chain_get(prefix) or pctx

        fields = rpc.RPCProxy(params.model).fields_get(False, rpc.session.context)

        if field not in fields:
            return {}
        text = fields[field].get('string')
        deps = []

        for name, attrs in fields.iteritems():
            if attrs.get('change_default'):
                value = ctx.get(name)
                if value:
                    deps.append((name, name, value, value))

        return dict(text=text, deps=str(deps))

    @expose(template="/openerp/controllers/templates/fieldpref.mako")
    def save(self, **kw):
        params, data = TinyDict.split(kw)

        deps = False
        if params.deps:
            for n, v in params.deps.items():
                deps = "%s=%s" %(n,v)
                break

        model = params.model
        field = params.field['name']
        value = params.field['value']
        click_ok = 1

        field = field.split('/')[-1]

        proxy = rpc.RPCProxy('ir.values')
            
        res = proxy.set('default', deps, field, [(model,False)], value, True, False, False, params.you or False, True)

        return dict(model=params.model, click_ok=click_ok, field=params.field, deps=params.deps2, should_close=True)

# vim: ts=4 sts=4 sw=4 si et

