<%inherit file="/openerp/controllers/templates/base_dispatch.mako"/>
<%!
    KINDS = {
        'M2O': 1,
        'M2M': 2
    }
%>        

<%def name="header()">
    <%
        if params.selectable == KINDS['M2O']:
            create_url = "/openm2o/edit"
        elif params.selectable == KINDS['M2M']:
            create_url = "/openm2m/new"
    %>
    <title>Search ${form.screen.string}</title>

    <script type="text/javascript">
        var form_controller = '/openerp/search';
    </script>
    % if params.selectable == KINDS['M2O']:
    <script type="text/javascript">
        function close_dialog() {
            jQuery.m2o('close');
        }
        function do_select(selected_id){
            if (!selected_id) {
                var ids = new ListView('_terp_list').getSelectedRecords();

                if (ids.length<1)
                    return;

                selected_id = ids[0];
            }
            jQuery.m2o('close', selected_id);
        }
    </script>
    % elif params.selectable == KINDS['M2M']:
        % if params.get('return_to'):
            <script type="text/javascript">
                function close_dialog() {
                    window.close()
                }
                function do_select() {
                    var list_this = new ListView('_terp_list');
                    with(window.opener) {
                       var boxes = list_this.getSelectedRecords();
                       if(boxes) {
                            var groups = eval(jQuery('#groups_id').val());
                            var new_groups = new Array();
                            forEach(boxes, function(b){
                                if(jQuery.inArray(parseInt(b), groups) < 0) {
                                    new_groups.push(parseInt(b));
                                }
                            });
                            var color_filters = groups.concat(new_groups);
                            getCalendar(null, null, color_filters);
                       }

                       else {
                            error_display(_("No record selected..."));
                            return;
                       }
                    }
                    close_dialog();
                }
            </script>
        % else:
		    <script type="text/javascript">
                function close_dialog() {
                    jQuery.m2m('close');
                }
		        function do_select(id) {
                    jQuery.m2m('close',
                        id ? [parseInt(id, 10)]
                           : ListView('_terp_list').$getSelectedItems().map(function () {
                                return parseInt(this.value, 10); }).get()
                    );
		        }
		    </script>
        % endif
    % endif
    <script type="text/javascript">
        function do_create(){
            openLink(openobject.http.getURL('/openerp${create_url}', {
                _terp_model: '${params.model}',
                _terp_source: '${params.source}',
                _terp_m2m: '${params.source}',
                _terp_domain: openobject.dom.get('_terp_domain').value,
                _terp_context: openobject.dom.get('_terp_context').value}));
        }
    </script>
</%def>

<%def name="content()">
<div class="view">
    <form id="search_form" name="search_form" action="" method="post">
        <input type="hidden" id="_terp_source" name="_terp_source" value="${params.source}"/>
        <input type="hidden" id="_terp_selectable" name="_terp_selectable" value="${params.selectable}"/>
        <input type="hidden" id="_terp_search_domain" name="_terp_search_domain" value="${params.search_domain}"/>
        <input type="hidden" id="_terp_filter_domain" name="_terp_filter_domain" value="${params.filter_domain}"/>
        <input type="hidden" id="_terp_search_data" name="_terp_search_data" value="${params.search_data}"/>
		<input type="hidden" id="_terp_search_text" name="_terp_search_text" value="${params.search_text}"/>
        <table width="100%" border="0" cellpadding="2">
            <tr>
                <td>
                    <table width="100%" class="titlebar" style="border: none;">
                        <tr>
                            <td width="100%">
                                <h1>${_("Search %(name)s", name=form.screen.string)}</h1>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td>${form.search.display()}</td>
            </tr>
            <tr>
                <td class="toolbar" style="padding: 4px 5px 0px;">
                    <table cellpadding="0" cellspacing="0">
                        <tr>
                            <td width="100%">
                                % if params.selectable != 1:
                                    <a class="button-a select-link" href="javascript: void(0)" onclick="do_select()">${_("Select")}</a>
                                % endif
                            	<a class="button-a" href="javascript: void(0)" onclick="search_filter()" >${_("Search")}</a>
                           	    <a class="button-a" href="javascript: void(0)" onclick="do_create()">${_("New")}</a>
                            	<a class="button-a" href="javascript: void(0)" onclick="close_dialog();">${_("Close")}</a>
	                            
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td style="padding: 5px">
                    <div style="position:relative">
                       
                        ${form.screen.display()}
                        % if not params.ids and 'default_name' in params.context:
                            <div id="no-record-warning" class="no-record-warning">
                                <p>${_("No record found : '%(searched_string)s'.", searched_string=params.context['default_name'])}</p>
                                <p>
                                    <a class="button-a" href="javascript: void(0)" onclick="do_create()">${_("Create")}</a>
                                </p>
                            </div>
                        % endif 
                    </div>
                </td>
            </tr>
        </table>
        
        <script type="text/javascript">
            jQuery('table.search_table input:text').eq(0).focus();
            /*
            % if params.selectable == KINDS['M2M']:
            */
                var $select_link = jQuery('a.select-link').hide();
                jQuery('#search_form').click(function(event) {
                    if (!jQuery(event.target).is(".grid-record-selector")) { return; }
                    $select_link.toggle(
                        !!jQuery('#search_form .grid-record-selector:checked').length)
                });
            /*
            % endif
            */
        </script>
    </form>
</div>
</%def>
