# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
from lxml import etree
import StringIO
import cStringIO
import base64
from datetime import datetime
import os
import re
import time
from interface import report_rml
import preprocess
import logging
import pooler
import tools
import zipfile
import common
from osv.fields import float as float_class, function as function_class
from osv.orm import browse_record

DT_FORMAT = '%Y-%m-%d'
DHM_FORMAT = '%Y-%m-%d %H:%M:%S'
HM_FORMAT = '%H:%M:%S'

rml_parents = {
    'tr':1,
    'li':1,
    'story': 0,
    'section': 0
}

rml_tag="para"

sxw_parents = {
    'table-row': 1,
    'list-item': 1,
    'body': 0,
    'section': 0,
}

html_parents = {
    'tr' : 1,
    'body' : 0,
    'div' : 0
    }
sxw_tag = "p"

rml2sxw = {
    'para': 'p',
}

class _format(object):
    def set_value(self, cr, uid, name, object, field, lang_obj):
        self.object = object
        self._field = field
        self.name = name
        self.lang_obj = lang_obj

class _float_format(float, _format):
    def __init__(self,value):
        super(_float_format, self).__init__()
        self.val = value

    def __str__(self):
        digits = 2
        if hasattr(self,'_field') and getattr(self._field, 'digits', None):
            digits = self._field.digits[1]
        if hasattr(self, 'lang_obj'):
            return self.lang_obj.format('%.' + str(digits) + 'f', self.name, True)
        return self.val

class _int_format(int, _format):
    def __init__(self,value):
        super(_int_format, self).__init__()
        self.val = value and str(value) or str(0)

    def __str__(self):
        if hasattr(self,'lang_obj'):
            return self.lang_obj.format('%.d', self.name, True)
        return self.val

class _date_format(str, _format):
    def __init__(self,value):
        super(_date_format, self).__init__()
        self.val = value and str(value) or ''

    def __str__(self):
        if self.val:
            if getattr(self,'name', None):
                date = datetime.strptime(self.name, DT_FORMAT)
                return date.strftime(str(self.lang_obj.date_format))
        return self.val

class _dttime_format(str, _format):
    def __init__(self,value):
        super(_dttime_format, self).__init__()
        self.val = value and str(value) or ''

    def __str__(self):
        if self.val and getattr(self,'name', None):
            return datetime.strptime(self.name, DHM_FORMAT)\
                   .strftime("%s %s"%(str(self.lang_obj.date_format),
                                      str(self.lang_obj.time_format)))
        return self.val


_fields_process = {
    'float': _float_format,
    'date': _date_format,
    'integer': _int_format,
    'datetime' : _dttime_format
}

#
# Context: {'node': node.dom}
#
class browse_record_list(list):
    def __init__(self, lst, context):
        super(browse_record_list, self).__init__(lst)
        self.context = context

    def __getattr__(self, name):
        res = browse_record_list([getattr(x,name) for x in self], self.context)
        return res

    def __str__(self):
        return "browse_record_list("+str(len(self))+")"

class rml_parse(object):
    def __init__(self, cr, uid, name, parents=rml_parents, tag=rml_tag, context=None):
        if not context:
            context={}
        self.cr = cr
        self.uid = uid
        self.pool = pooler.get_pool(cr.dbname)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        self.localcontext = {
            'user': user,
            'setCompany': self.setCompany,
            'repeatIn': self.repeatIn,
            'get_pagebreak': self.get_pagebreak,
            'get_qt_total': self.get_qt_total,
            'get_qt_list' : self.get_qt_list,
            'get_prod_uom': self.get_prod_uom,
            'get_customer_info': self.get_customer_info,
            'get_total_quantity': self.get_total_quantity,
            'get_box_count' : self.get_box_count,
            'get_custom_list': self.get_custom_list,
            'get_main_prod': self.get_main_prod,
            'get_prod_total': self.get_prod_total,
            'get_conductor_check': self.get_conductor_check,
            'get_bom_products': self.get_bom_products,
            'get_bom_products_multi_routing': self.get_bom_products_multi_routing,
            'get_bom_routing_type': self.get_bom_routing_type,
            'get_qty_details': self.get_qty_details,
            'get_testing_result': self.get_testing_result,
            'get_qt_total_picking': self._get_qt_total_picking,
            'get_qt_list_picking': self._get_qt_list_picking,
            'get_prod_total_picking': self._get_prod_total_picking,
            'get_customer_info_picking': self._get_customer_info_picking,
            'get_total_quantity_picking': self._get_total_quantity_picking,
            'get_box_count_picking': self._get_box_count_picking,
            'get_main_prod_picking': self._get_main_prod_picking,
            'get_custom_list_picking': self._get_custom_list_picking,
            'get_uom_name_picking': self._get_uom_name_picking,
            'get_mo_reference_date': self._get_mo_reference_date,
            'get_uppercase': self._get_uppercase,
            'get_buyer_address': self._get_buyer_address,
            'get_partner_address':self._get_partner_address,
            'get_invoice_number': self._get_invoice_number,
            'get_invoice_total': self._get_invoice_total,
            'get_invoice_value': self._get_invoice_value,
            'get_duty_details': self._get_duty_details,
            'get_change_date_format': self._get_change_date_format,
            'get_invoice_lines': self._get_invoice_lines,
            'get_invoice_customer_code': self._get_invoice_customer_code,
            'amount_words': self._amount_words,
            'setLang': self.setLang,
            'setTag': self.setTag,
            'removeParentNode': self.removeParentNode,
            'format': self.format,
            'formatLang': self.formatLang,
            'lang' : user.company_id.partner_id.lang,
            'translate' : self._translate,
            'setHtmlImage' : self.set_html_image,
            'strip_name' : self._strip_name,
            'time' : time,
            # more context members are setup in setCompany() below:
            #  - company_id
            #  - logo
        }
        self.setCompany(user.company_id)
        self.localcontext.update(context)
        self.name = name
        self._node = None
        self.parents = parents
        self.tag = tag
        self._lang_cache = {}
        self.lang_dict = {}
        self.default_lang = {}
        self.lang_dict_called = False
        self._transl_regex = re.compile('(\[\[.+?\]\])')

    def setTag(self, oldtag, newtag, attrs=None):
        return newtag, attrs

    def _ellipsis(self, char, size=100, truncation_str='...'):
        if len(char) <= size:
            return char
        return char[:size-len(truncation_str)] + truncation_str

    def setCompany(self, company_id):
        if company_id:
            self.localcontext['company'] = company_id
            self.localcontext['logo'] = company_id.logo
            self.rml_header = company_id.rml_header
            self.rml_header2 = company_id.rml_header2
            self.rml_header3 = company_id.rml_header3
            self.logo = company_id.logo

    def _strip_name(self, name, maxlen=50):
        return self._ellipsis(name, maxlen)

    def format(self, text, oldtag=None):
        return text.strip()

    def removeParentNode(self, tag=None):
        raise GeneratorExit('Skip')

    def set_html_image(self,id,model=None,field=None,context=None):
        if not id :
            return ''
        if not model:
            model = 'ir.attachment'
        try :
            id = int(id)
            res = self.pool.get(model).read(self.cr,self.uid,id)
            if field :
                return res[field]
            elif model =='ir.attachment' :
                return res['datas']
            else :
                return ''
        except Exception:
            return ''
        
    def _get_uppercase(self, value):
        return value.upper()
    
    def _get_buyer_address(self, invoice):
        address = '0'
        if invoice.buyers_address:
            address = str(invoice.buyers_address).split('!')
        return address
    
    def _get_invoice_number(self, invoice):
        if invoice.date_invoice:
            inv_date = str(invoice.date_invoice).split('/')
            return_txt = str(invoice.name) + ' dt. ' + str(inv_date[0]) + '.' + str(inv_date[1]) + '.' + str(inv_date[2])
        else:
            return_txt = str(invoice.name)  
        return return_txt
    
    def _get_invoice_customer_code(self, product_id, customer_id):
        customer_code = ''
        custinfo_obj = self.pool.get('product.customerinfo')
        cust_ids = custinfo_obj.search(self.cr, self.uid,[('product_id','=',product_id),('name','=',customer_id)])
        if cust_ids:
            cust_data = custinfo_obj.browse(self.cr, self.uid, cust_ids[0])
            customer_code = ' (' + str(cust_data.product_code) + ')'
        return customer_code
    
    def _get_invoice_total(self, invoice, item):
        quantity = 0
        amount = 0
        rate = 0
        for line in invoice.invoice_line:
            quantity = quantity + line.quantity
            amount = amount + line.price_subtotal
        if item == 'quantity':
            return str(quantity).split('.')[0]
        if item == 'amount':
            return str(round(amount,2))
        if item == 'rate':
            return str(round(amount/quantity,5))
        
        return True
    
    def _get_invoice_value(self, invoice):
        amount = self._get_invoice_total(invoice, 'amount')
        return str(round(float(amount) * float(invoice.currency_rate)))
    
    def _get_duty_details(self, invoice, value, type):
        val = 0
        if value=='rate':
            if type=="vat":
                if invoice.vat_flag:
                    return str(round(invoice.vat,0)).split('.')[0]
                else:
                    return "0"
            if type=="edu":
                if invoice.vat_flag and invoice.edu_flag:
                    return str(round(invoice.edu_cess,0)).split('.')[0]
                else:
                    return "0"
            if type=="sedu":
                if invoice.vat_flag and invoice.sedu_flag:
                    return str(round(invoice.sedu_cess,0)).split('.')[0]
                else:
                    return "0"
        if value=='amount':
            val = float(self._get_invoice_value(invoice))
            if type=="vat":
                if invoice.vat_flag:
                    return str(round(val*(invoice.vat/100))).split('.')[0]
                else:
                    return "0"
            if type=="edu":
                if invoice.vat_flag and invoice.edu_flag:
                    return str(round((val*(invoice.vat/100))*(invoice.edu_cess/100))).split('.')[0]
                else:
                    return "0"
            if type=="sedu":
                if invoice.vat_flag and invoice.sedu_flag:
                    return str(round((val*(invoice.vat/100))*(invoice.sedu_cess/100))).split('.')[0]
                else:
                    return "0"
        return val
    
    def _get_change_date_format(self,date):
        if date:
            d = str(date).split('/')
            return str(d[0]) + '.' + str(d[1]) + '.' + str(d[2])
        return True
    
    def _get_invoice_lines(self, invoice):
        lst = []
        length = len(invoice.invoice_line)
        cnt = 0
        if invoice.invoice_line:
            for line in invoice.invoice_line:
                cnt += 1
                dic = {}
                if cnt == 1:
                    dic = {
                           'default_code': line.product_id.default_code,
                           'product': line.product_id.name,
                           'product_id': line.product_id.id,
                           'quantity': line.quantity,
                           'price_unit': line.price_unit,
                           'price_subtotal': line.price_subtotal,
                           'box_no': invoice.lot_numbers
                       }
                    lst.append(dic)
                else:
                    dic = {
                           'default_code': line.product_id.default_code,
                           'product': line.product_id.name,
                           'product_id': line.product_id.id,
                           'quantity': line.quantity,
                           'price_unit': line.price_unit,
                           'price_subtotal': line.price_subtotal,
                           'box_no': ''
                       }
                    lst.append(dic)
		
        print '_______________lst_______________',lst
#        page = len(lst) / 20
#        main_lst = []
#
#        for i in range(0, len(lst), 20):
#            main_lst.append(lst[i:i+20])
#        print '__________main_lst____________',main_lst
#        stop
        return lst
        
    
    def _amount_words(self,num,txt):
        select={'0' : '','1' : 'One','2' : 'Two','3' : 'Three','4' : 'Four','5' : 'Five','6' : 'Six',
                '7' : 'Seven','8' : 'Eight','9' : 'Nine','10' : 'Ten','11' : 'Eleven','12' : 'Twelve',
                '13' : 'Thirteen','14' : 'Fourteen','15' : 'Fifteen','16' : 'Sixteen','17' : 'Seventeen',
                '18' : 'Eighteen','19' : 'Nineteen','20' : 'Twenty','30' : 'Thirty','40' : 'Forty',
                '50' : 'Fifty','60' : 'Sixty','70' : 'Seventy','80' : 'Eighty','90' : 'Ninety'}
        select_digit={'1' :'', '2':'', '3':'Hundred', '4': 'Thousand','5': 'Thousand', '6': 'Lakh',
                      '7': 'Lakh', '8': 'Crore','9': 'Crore', '10' :'Sael', '11':'Sael'}
        word= ""
        length=len(str(num).replace(',','').split('.')[0])
        number=str(num).replace(',','').split('.')[0]
        word=""
        while number:
            if len(number)%2==0 and len(number)>3:
                i=number[0]
                word = word + " " + select.get(i) +" "+ select_digit.get(str(len(number)))
                number=number[1:]
            elif len(number)%2 !=0 and len(number)>3:
                i=number[:2]
                if i=="00":
                    number=number[2:]
                elif i[0]=="0" :
                    word = word + " " + select.get(i[1]) +" "+ select_digit.get(str(len(number)))
                    number=number[2:]
                elif i[0]=="1":
                    word = word + " " + select.get(i) + " " + select_digit.get(str(len(number)))
                    number=number[2:]
                else:
                    if i[1]=="0":
                        word = word + " " + select.get(i) + " " + select_digit.get(str(len(number)))
                        number=number[2:]
                    else:
                        word = word + " " + select.get(str(int(i[0] ) * 10)) + " " + select.get(i[1]) + " " + select_digit.get(str(len(number)))
                        number=number[2:]
            elif  len(number)<=3:
                while number:
                    if len(number)==3:
                        if number[0] !="0":
                            i=number[0]
                            if number[1:] =="00":
                                word = word + " " + select.get(i) +" "+ select_digit.get(str(len(number)))
                                number=number[1:]
                            else:
                                word = word + " " + select.get(i) +" "+ select_digit.get(str(len(number))) + " " + "and"
                                number=number[1:]
    
                        else:
                            number=number[1:]
                    else:
                        i=number
                        if i=="00":
                            number=""
                        elif i[0]=="0" and len(number)>1:
                            word = word + " " + select.get(i[1]) +" "+ select_digit.get(str(len(number)))
                            number=""
                        elif i[0]=="0" and len(number)==1:
                            word = " Zero"
                            number=""
    
                        elif i[0]=="1":
                            word = word + " " + select.get(i) + " " + select_digit.get(str(len(number)))
                            number=""
                        else:
                            if len(number)==1:
                                word = word + " " + select.get(i) + " " + select_digit.get(str(len(number)))
                                number="" 
                            elif i[1]=="0":
                                word = word + " " + select.get(i) + " " + select_digit.get(str(len(number)))
                                number=""
                            else:
                                word = word + " " + select.get(str(int(i[0] ) * 10)) + " " + select.get(i[1]) + " " + select_digit.get(str(len(number)))
                                number=""
    
        
        up=word[1].upper()
        word =up + word[2:]
        word = word +  " " + txt
        return word.upper()
    
    def _get_partner_address(self, address_id, value):
        return_txt = ''
        if value=='street':
            if address_id.street and address_id.street2:
                return str(address_id.street).upper() + ', ' + str(address_id.street2).upper()
            if address_id.street and not address_id.street2:
                return str(address_id.street).upper()
            if not address_id.street and address_id.street2:
                return str(address_id.street2).upper()
        
        if value=='country':
            return_txt = ''
            if address_id.city:
                return_txt = str(address_id.city).upper()
            if address_id.state_id and return_txt=='':
                return_txt = str(address_id.state_id.name).upper()
            elif address_id.state_id and return_txt!='':
                return_txt = return_txt + ', ' + str(address_id.state_id.name).upper()
            if address_id.country_id and return_txt=='':
                return_txt = str(address_id.country_id.name).upper()
            elif address_id.country_id and return_txt!='':
                return_txt = return_txt + ', ' + str(address_id.country_id.name).upper()
            
            return return_txt
        
        if value=='contact':
            return_txt = ''
            if address_id.phone:
                return_txt = 'Tel: ' + str(address_id.phone)
            if address_id.fax and return_txt=='':
                return_txt = 'Fax: ' + str(address_id.fax)
            elif address_id.fax and return_txt!='':
                return_txt = return_txt + ' Fax: ' + str(address_id.fax)
                
            if return_txt=='':
                return return_txt
            else:
                return '(' + return_txt + ')'
        
        
        return return_txt
    
    def _get_qt_total_picking(self, lst, prodlotid):
        totalqty=0
        for id in lst:
#            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and prodlotid==id.x_spool_number):
            if(id.state<>'cancel' and prodlotid==id.x_spool_number):
                totalqty+=id.product_qty
        return totalqty

    def _get_qt_list_picking(self,lst,spoolnumber):
        finallist=''
        for id in lst:
#            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and spoolnumber==id.x_spool_number):
            if(id.state<>'cancel' and spoolnumber==id.x_spool_number):
                if(finallist==''):
                    if id.product_qty > 0:
                        finallist=str("%.1f" % round(id.product_qty,2))
                else:
                    if id.product_qty > 0:
                        finallist=finallist + ' + ' + str("%.1f" % round(id.product_qty,2))
        return finallist
    
    def _get_prod_total_picking(self,lst,prodid):
        totalqty=0
        for id in lst:
#            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and prodid==id.product_id.id):
            if(id.state<>'cancel' and prodid==id.product_id.id):
                totalqty+=id.product_qty
        return totalqty

    def _get_customer_info_picking(self,lst,prodid,custid,part):
        for id in lst:
            if(id.name.id==custid.id and id.product_id.id==prodid.id):
                if(part=='code'):
                    prodinfo=id.product_code
                if(part=='name'):
                    prodinfo=id.product_name
        return prodinfo

    def _get_total_quantity_picking(self,lst):
        totalqty=0
        for line in lst:
            if(line['state']<>'cancel'):
#            if(line['state']=='done'):
                totalqty=totalqty+line['product_qty']
        return totalqty
    
    def _get_box_count_picking(self,lst):
        ret_lst = []
        cust_lst = []
        final_list = []
        return_list = []
        index = 0
        intSum = 0
        boxcount=0
        flag = 0

        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
        
        
        for line in sortedRes:
            if(line['state']<>'cancel'):
                cust_lst.append(line)
        
        if(cust_lst<>[]):
            curId = cust_lst[0]['tracking_id']


        for line in cust_lst:
            if final_list==[]:
                final_list.append(line)
            else:
                for line2 in final_list:
                    if(line['tracking_id']==line2['tracking_id']):
                        flag=0
                        break
                    else:
                        flag=1
                if(flag==1):
                    final_list.append(line)
                    flag=0
        
        for line in final_list:
            boxcount=boxcount+1
                
        return boxcount

    def _get_main_prod_picking(self, lst):
        ret_lst = []
        cust_lst = []
        final_list = []
        return_list = []
        index = 0
        intSum = 0
        flag = 0

        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
        
        
        for line in sortedRes:
            if(line['state']<>'cancel'):
#            if(line['state']=='done'):
                cust_lst.append(line)
        
        if(cust_lst<>[]):
            curId = cust_lst[0]['product_id']


        for line in cust_lst:
            if final_list==[]:
                final_list.append(line)
            else:
                for line2 in final_list:
                    if(line['product_id']==line2['product_id']):
                        flag=0
                        break
                    else:
                        flag=1
                if(flag==1):
                    final_list.append(line)
                    flag=0
        final_list.sort(key=lambda tup: tup.product_id.id)
        return final_list

    def _get_uom_name_picking(self,lst):
        name=''
        for item in lst:
            if item.product_id.categ_id.name=="Tapes" or item.product_id.categ_id.parent_id.name=="Tapes" or item.product_id.categ_id.name=="Conductors" or item.product_id.categ_id.parent_id.name=="Conductors":
                name="Kg"
            else:
                name="M" 
        return name
    
    def _get_mo_reference_date(self, mo, date_type):
        print mo,date_type
        if mo.sale_requested_date and date_type=="due_date":
            date = datetime.strptime(mo.sale_requested_date,'%Y-%m-%d').strftime('%d/%m/%Y')
        
        return date

    
    def _get_custom_list_picking(self,lst):
        ret_lst = []
        cust_lst = []
        final_list = []
        return_list = []
        index = 0
        intSum = 0
        flag = 0
        
        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]

        for line in sortedRes:
            if(line['state']<>'cancel'):
                cust_lst.append(line)
        
        if(cust_lst<>[]):
            curId = cust_lst[0]['x_spool_number']

        for line in cust_lst:
            if final_list==[]:
                final_list.append(line)
            else:
                for line2 in final_list:
                    if(line['x_spool_number']==line2['x_spool_number']):
                        flag=0
                        break
                    else:
                        flag=1
                if(flag==1):
                    final_list.append(line)
                    flag=0
        final_list.sort(key=lambda tup: tup.product_id.id)
        return final_list

    def setLang(self, lang):
        self.localcontext['lang'] = lang
        self.lang_dict_called = False
        for obj in self.objects:
            obj._context['lang'] = lang

    def _get_lang_dict(self):
        pool_lang = self.pool.get('res.lang')
        lang = self.localcontext.get('lang', 'en_US') or 'en_US'
        lang_ids = pool_lang.search(self.cr,self.uid,[('code','=',lang)])[0]
        lang_obj = pool_lang.browse(self.cr,self.uid,lang_ids)
        self.lang_dict.update({'lang_obj':lang_obj,'date_format':lang_obj.date_format,'time_format':lang_obj.time_format})
        self.default_lang[lang] = self.lang_dict.copy()
        return True

    def digits_fmt(self, obj=None, f=None, dp=None):
        digits = self.get_digits(obj, f, dp)
        return "%%.%df" % (digits, )

    def get_digits(self, obj=None, f=None, dp=None):
        d = DEFAULT_DIGITS = 2
        if dp:
            decimal_precision_obj = self.pool.get('decimal.precision')
            ids = decimal_precision_obj.search(self.cr, self.uid, [('name', '=', dp)])
            if ids:
                d = decimal_precision_obj.browse(self.cr, self.uid, ids)[0].digits
        elif obj and f:
            res_digits = getattr(obj._columns[f], 'digits', lambda x: ((16, DEFAULT_DIGITS)))
            if isinstance(res_digits, tuple):
                d = res_digits[1]
            else:
                d = res_digits(self.cr)[1]
        elif (hasattr(obj, '_field') and\
                isinstance(obj._field, (float_class, function_class)) and\
                obj._field.digits):
                d = obj._field.digits[1] or DEFAULT_DIGITS
        return d

    def formatLang(self, value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False):
        """
            Assuming 'Account' decimal.precision=3:
                formatLang(value) -> digits=2 (default)
                formatLang(value, digits=4) -> digits=4
                formatLang(value, dp='Account') -> digits=3
                formatLang(value, digits=5, dp='Account') -> digits=5
        """
        if digits is None:
            if dp:
                digits = self.get_digits(dp=dp)
            else:
                digits = self.get_digits(value)

        if isinstance(value, (str, unicode)) and not value:
            return ''

        if not self.lang_dict_called:
            self._get_lang_dict()
            self.lang_dict_called = True

        if date or date_time:
            if not str(value):
                return ''

            date_format = self.lang_dict['date_format']
            parse_format = DT_FORMAT
            if date_time:
                value=value.split('.')[0]
                date_format = date_format + " " + self.lang_dict['time_format']
                parse_format = DHM_FORMAT
            if not isinstance(value, time.struct_time):
                return time.strftime(date_format, time.strptime(value, parse_format))

            else:
                date = datetime(*value.timetuple()[:6])
            return date.strftime(date_format)

        return self.lang_dict['lang_obj'].format('%.' + str(digits) + 'f', value, grouping=grouping, monetary=monetary)

    def repeatIn(self, lst, name,nodes_parent=False):
        ret_lst = []
        for id in lst:
            ret_lst.append({name:id})
        return ret_lst

    def get_pagebreak(self, list, prod_id):
        print len(list)
        print prod_id
        count=0
        val = 'True'
        for lst in list:
            if lst.product_id.id<>prod_id:
                count+=1
            else:
                count+=1
                if count<len(list):
                    val='True'
                    break
                else:
                    val='False'
                    break
        return val

    def get_qt_total(self,lst,prodlotid):
        totalqty=0
        for id in lst:
            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and prodlotid==id.x_spool_number):
                totalqty+=id.product_qty
        return totalqty

    def get_qt_list(self,lst,spoolnumber):
        finallist=''
        for id in lst:
            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and spoolnumber==id.x_spool_number):
                if(finallist==''):
                    finallist=str(round(id.product_qty,0))
                else:
                    finallist=finallist + ' + ' + str(round(id.product_qty,0))
        return finallist
    
    def get_prod_uom(self,prodid):
        uom = prodid.product_uom.name
        return uom
    
    def get_prod_total(self,lst,prodid):
        totalqty=0
        for id in lst:
            if((id.state=='confirmed' or id.state=='done' or id.state=='assigned') and prodid==id.product_id.id):
                totalqty+=id.product_qty
        return totalqty

    def get_customer_info(self,lst,prodid,custid,part):
        for id in lst:
            if(id.name.id==custid.id and id.product_id.id==prodid.id):
                if(part=='code'):
                    prodinfo=id.product_code
                if(part=='name'):
                    prodinfo=id.product_name
        return prodinfo

    def get_total_quantity(self,lst):
        totalqty=0
        for line in lst:
#            if(line['state']<>'cancel' and line['state']<>'draft'):
            if(line['state']=='done'):
                totalqty=totalqty+line['product_qty']
        return totalqty
    
    def get_testing_result(self,testline):
        result=''
        if testline.result<>'N/A':
            result=testline.result
        return result

    def get_box_count(self,lst):
        ret_lst = []
        cust_lst = []
        final_list = []
        return_list = []
        index = 0
        intSum = 0
        boxcount=0
        flag = 0

        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
        
        
        for line in sortedRes:
            if(line['state']<>'cancel' and line['state']<>'draft'):
                cust_lst.append(line)
        
        if(cust_lst<>[]):
            curId = cust_lst[0]['tracking_id']


        for line in cust_lst:
            if final_list==[]:
                final_list.append(line)
            else:
                for line2 in final_list:
                    if(line['tracking_id']==line2['tracking_id']):
                        flag=0
                        break
                    else:
                        flag=1
                if(flag==1):
                    final_list.append(line)
                    flag=0
        
        for line in final_list:
            boxcount=boxcount+1
                
        return boxcount

    def get_main_prod(self,lst):
        ret_lst = []
        cust_lst = []
        final_list = []
        return_list = []
        index = 0
        intSum = 0
        flag = 0

        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
        
        
        for line in sortedRes:
#            if(line['state']<>'cancel' and line['state']<>'draft'):
            if(line['state']=='done'):
                cust_lst.append(line)
        
        if(cust_lst<>[]):
            curId = cust_lst[0]['product_id']


        for line in cust_lst:
            if final_list==[]:
                final_list.append(line)
            else:
                for line2 in final_list:
                    if(line['product_id']==line2['product_id']):
                        flag=0
                        break
                    else:
                        flag=1
                if(flag==1):
                    final_list.append(line)
                    flag=0
        return final_list
    
    
    def get_custom_list(self,lst):
        ret_lst = []
        cust_lst = []
        final_list = []
        return_list = []
        index = 0
        intSum = 0
        flag = 0
        
        decorated = [(stock_move.product_id,i,stock_move) for i,stock_move in enumerate(lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]

        for line in sortedRes:
            if(line['state']<>'cancel' and line['state']<>'draft'):
                cust_lst.append(line)
        
        if(cust_lst<>[]):
            curId = cust_lst[0]['x_spool_number']

        for line in cust_lst:
            if final_list==[]:
                final_list.append(line)
            else:
                for line2 in final_list:
                    if(line['x_spool_number']==line2['x_spool_number']):
                        flag=0
                        break
                    else:
                        flag=1
                if(flag==1):
                    final_list.append(line)
                    flag=0
        return final_list

    def get_conductor_check(self,prod_id):
        result='False'
        
        res = self.get_bom_products(prod_id)
        for prod in res:
            if prod.product_id.categ_id.parent_id.name=="Conductors":
                result='True'
        return result
    
    def get_bom_products(self,prod_id):
        tmp={}
        result={}
        prod = self.pool.get('mrp.production').browse(self.cr, self.uid, prod_id)
        self.cr.execute('select id from mrp_bom where bom_id=%s order by tape_sequence', (prod['bom_id'].id,))
        ids = map(lambda x: x[0], self.cr.fetchall())
    
        prod_lst = self.pool.get('mrp.bom').browse(self.cr, self.uid, ids)
        
        final_list = []
        tapeRes = []
        prodRes = []
        flag = 0

        decorated = [(mrp_bom.product_id,i,mrp_bom) for i,mrp_bom in enumerate(prod_lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
        
        
        for line in sortedRes:
            if (line['name'][:5] == 'Jumbo' or (line['name'][0]=='T' and (line['name'][1]<>'P' and line['name'][1]<>'W')) or line['name'][:2] == 'PC' or (line['name'][0]=='K' and (line['name'][1]<>'D' and line['name'][1]<>'N'))):
                tapeRes.append(line)
            else:
                prodRes.append(line)
        
        groupedRes = []
        intSum = 0
        if(prodRes<>[]):
            curId = prodRes[0]['product_id']
        
        for line in prodRes:
            if final_list==[]:
                final_list.append(line)
            else:
                for line2 in final_list:
                    if(line['product_id']==line2['product_id']):
                        flag=0
                        break
                    else:
                        flag=1
                if(flag==1):
                    final_list.append(line)
                    flag=0
                    
        for line in tapeRes:
            final_list.append(line)

        decorated = [(mrp_bom.tape_sequence,i,mrp_bom) for i,mrp_bom in enumerate(final_list)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
         
        return sortedRes
    
    def get_bom_products_multi_routing(self,prod_id):
        tmp={}
        result={}
        prod = self.pool.get('mrp.production').browse(self.cr, self.uid, prod_id)
        self.cr.execute('select id from mrp_bom where bom_id=%s order by tape_sequence', (prod['bom_id'].id,))
        ids = map(lambda x: x[0], self.cr.fetchall())
    
        prod_lst = self.pool.get('mrp.bom').browse(self.cr, self.uid, ids)
        
        final_list = []
        tapeRes = []
        prodRes = []
        flag = 0

        decorated = [(mrp_bom.product_id,i,mrp_bom) for i,mrp_bom in enumerate(prod_lst)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
        
        
#        for line in sortedRes:
#            if (line['name'][:5] == 'Jumbo' or (line['name'][0]=='T' and (line['name'][1]<>'P' and line['name'][1]<>'W')) or line['name'][:2] == 'PC' or (line['name'][0]=='K' and (line['name'][1]<>'D' and line['name'][1]<>'N'))):
#                tapeRes.append(line)
#            else:
#                prodRes.append(line)
#        
#        groupedRes = []
#        intSum = 0
#        if(prodRes<>[]):
#            curId = prodRes[0]['product_id']
#        
#        for line in prodRes:
#            if final_list==[]:
#                final_list.append(line)
#            else:
#                for line2 in final_list:
#                    if(line['product_id']==line2['product_id']):
#                        flag=0
#                        break
#                    else:
#                        flag=1
#                if(flag==1):
#                    final_list.append(line)
#                    flag=0
#                    
#        for line in tapeRes:
#            final_list.append(line)

        decorated = [(mrp_bom.tape_sequence,i,mrp_bom) for i,mrp_bom in enumerate(sortedRes)]
        decorated.sort()
        sortedRes = [dict_ for (key,i,dict_) in decorated]
         
        return sortedRes
    
    
    def get_bom_routing_type(self,prod_id):
        type=1
        
        prod = self.pool.get('mrp.production').browse(self.cr, self.uid, prod_id)
        self.cr.execute('select "name" from mrp_routing_workcenter where routing_id=%s order by "name"', (prod['routing_id'].id,))
        WCs = map(lambda x: x[0], self.cr.fetchall())
        WCs.sort()
        tmp=[]
        if WCs:
            for wc in WCs:
                if tmp.__contains__(wc):
                    type=2
                else:
                    tmp.append(wc)
        return type
    
    def get_qty_details(self, picking, product_id):
        print picking
        print type
        result = False
        count = 0
        min_qty = 0
        max_qty = 0
        qty = 0
        stock_move_obj = self.pool.get('stock.move')
        move_ids = stock_move_obj.search(self.cr, self.uid, [('picking_id','=',picking),('product_id','=',product_id)])
        move_data = stock_move_obj.browse(self.cr, self.uid, move_ids)
        for data in move_data:
            if count == 0:
                min_qty = data.product_qty
                max_qty = data.product_qty
            count += 1
            
            if data.product_qty < min_qty:
                min_qty = data.product_qty
            if data.product_qty > max_qty:
                max_qty = data.product_qty
            qty += data.product_qty
            
        result = str(qty) + ' / ' + str(count) + ' / ' + str(min_qty) + ' / ' + str(max_qty) + ' / ' + str(qty/count)
            
        return result

    def _translate(self,text):
        lang = self.localcontext['lang']
        if lang and text and not text.isspace():
            transl_obj = self.pool.get('ir.translation')
            piece_list = self._transl_regex.split(text)
            for pn in range(len(piece_list)):
                if not self._transl_regex.match(piece_list[pn]):
                    source_string = piece_list[pn].replace('\n', ' ').strip()
                    if len(source_string):
                        translated_string = transl_obj._get_source(self.cr, self.uid, self.name, ('report', 'rml'), lang, source_string)
                        if translated_string:
                            piece_list[pn] = piece_list[pn].replace(source_string, translated_string)
            text = ''.join(piece_list)
        return text

    def _add_header(self, rml_dom, header='external'):
        if header=='internal':
            rml_head =  self.rml_header2
        elif header=='internal landscape':
            rml_head =  self.rml_header3
        else:
            rml_head =  self.rml_header

        head_dom = etree.XML(rml_head)
        for tag in head_dom:
            found = rml_dom.find('.//'+tag.tag)
            if found is not None and len(found):
                if tag.get('position'):
                    found.append(tag)
                else :
                    found.getparent().replace(found,tag)
        return True

    def set_context(self, objects, data, ids, report_type = None):
        self.localcontext['data'] = data
        self.localcontext['objects'] = objects
        self.localcontext['digits_fmt'] = self.digits_fmt
        self.localcontext['get_digits'] = self.get_digits
        self.datas = data
        self.ids = ids
        self.objects = objects
        if report_type:
            if report_type=='odt' :
                self.localcontext.update({'name_space' :common.odt_namespace})
            else:
                self.localcontext.update({'name_space' :common.sxw_namespace})

        # WARNING: the object[0].exists() call below is slow but necessary because
        # some broken reporting wizards pass incorrect IDs (e.g. ir.ui.menu ids)
        if objects and len(objects) == 1 and \
            objects[0].exists() and 'company_id' in objects[0] and objects[0].company_id:
            # When we print only one record, we can auto-set the correct
            # company in the localcontext. For other cases the report
            # will have to call setCompany() inside the main repeatIn loop.
            self.setCompany(objects[0].company_id)

class report_sxw(report_rml, preprocess.report):
    def __init__(self, name, table, rml=False, parser=rml_parse, header='external', store=False):
        report_rml.__init__(self, name, table, rml, '')
        self.name = name
        self.parser = parser
        self.header = header
        self.store = store
        self.internal_header=False
        if header=='internal' or header=='internal landscape':
            self.internal_header=True

    def getObjects(self, cr, uid, ids, context):
        table_obj = pooler.get_pool(cr.dbname).get(self.table)
        return table_obj.browse(cr, uid, ids, list_class=browse_record_list, context=context, fields_process=_fields_process)

    def create(self, cr, uid, ids, data, context=None):
        if self.internal_header:
            context.update({'internal_header':self.internal_header})
        pool = pooler.get_pool(cr.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        report_xml_ids = ir_obj.search(cr, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_xml_ids:
            report_xml = ir_obj.browse(cr, uid, report_xml_ids[0], context=context)
        else:
            title = ''
            report_file = tools.file_open(self.tmpl, subdir=None)
            try:
                rml = report_file.read()
                report_type= data.get('report_type', 'pdf')
                class a(object):
                    def __init__(self, *args, **argv):
                        for key,arg in argv.items():
                            setattr(self, key, arg)
                report_xml = a(title=title, report_type=report_type, report_rml_content=rml, name=title, attachment=False, header=self.header)
            finally:
                report_file.close()
        if report_xml.header:
            report_xml.header = self.header
        report_type = report_xml.report_type
        if report_type in ['sxw','odt']:
            fnct = self.create_source_odt
        elif report_type in ['pdf','raw','txt','html']:
            fnct = self.create_source_pdf
        elif report_type=='html2html':
            fnct = self.create_source_html2html
        elif report_type=='mako2html':
            fnct = self.create_source_mako2html
        else:
            raise 'Unknown Report Type'
        fnct_ret = fnct(cr, uid, ids, data, report_xml, context)
        if not fnct_ret:
            return (False,False)
        return fnct_ret

    def create_source_odt(self, cr, uid, ids, data, report_xml, context=None):
        return self.create_single_odt(cr, uid, ids, data, report_xml, context or {})

    def create_source_html2html(self, cr, uid, ids, data, report_xml, context=None):
        return self.create_single_html2html(cr, uid, ids, data, report_xml, context or {})

    def create_source_mako2html(self, cr, uid, ids, data, report_xml, context=None):
        return self.create_single_mako2html(cr, uid, ids, data, report_xml, context or {})

    def create_source_pdf(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context={}
        pool = pooler.get_pool(cr.dbname)
        attach = report_xml.attachment
        if attach:
            objs = self.getObjects(cr, uid, ids, context)
            results = []
            for obj in objs:
                aname = eval(attach, {'object':obj, 'time':time})
                result = False
                if report_xml.attachment_use and aname and context.get('attachment_use', True):
                    aids = pool.get('ir.attachment').search(cr, uid, [('datas_fname','=',aname+'.pdf'),('res_model','=',self.table),('res_id','=',obj.id)])
                    if aids:
                        brow_rec = pool.get('ir.attachment').browse(cr, uid, aids[0])
                        if not brow_rec.datas:
                            continue
                        d = base64.decodestring(brow_rec.datas)
                        results.append((d,'pdf'))
                        continue
                result = self.create_single_pdf(cr, uid, [obj.id], data, report_xml, context)
                if not result:
                    return False
                if aname:
                    try:
                        name = aname+'.'+result[1]
                        pool.get('ir.attachment').create(cr, uid, {
                            'name': aname,
                            'datas': base64.encodestring(result[0]),
                            'datas_fname': name,
                            'res_model': self.table,
                            'res_id': obj.id,
                            }, context=context
                        )
                    except Exception:
                        #TODO: should probably raise a proper osv_except instead, shouldn't we? see LP bug #325632
                        logging.getLogger('report').error('Could not create saved report attachment', exc_info=True)
                results.append(result)
            if results:
                if results[0][1]=='pdf':
                    from pyPdf import PdfFileWriter, PdfFileReader
                    output = PdfFileWriter()
                    for r in results:
                        reader = PdfFileReader(cStringIO.StringIO(r[0]))
                        for page in range(reader.getNumPages()):
                            output.addPage(reader.getPage(page))
                    s = cStringIO.StringIO()
                    output.write(s)
                    return s.getvalue(), results[0][1]
        return self.create_single_pdf(cr, uid, ids, data, report_xml, context)

    def create_single_pdf(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context={}
        logo = None
        context = context.copy()
        title = report_xml.name
        rml = report_xml.report_rml_content
        # if no rml file is found
        if not rml:
            return False
        rml_parser = self.parser(cr, uid, self.name2, context=context)
        objs = self.getObjects(cr, uid, ids, context)
        rml_parser.set_context(objs, data, ids, report_xml.report_type)
        processed_rml = etree.XML(rml)
        if report_xml.header:
            rml_parser._add_header(processed_rml, self.header)
        processed_rml = self.preprocess_rml(processed_rml,report_xml.report_type)
        if rml_parser.logo:
            logo = base64.decodestring(rml_parser.logo)
        create_doc = self.generators[report_xml.report_type]
        pdf = create_doc(etree.tostring(processed_rml),rml_parser.localcontext,logo,title.encode('utf8'))
        return (pdf, report_xml.report_type)

    def create_single_odt(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context={}
        context = context.copy()
        report_type = report_xml.report_type
        context['parents'] = sxw_parents

        # if binary content was passed as unicode, we must
        # re-encode it as a 8-bit string using the pass-through
        # 'latin1' encoding, to restore the original byte values.
        # See also osv.fields.sanitize_binary_value()
        binary_report_content = report_xml.report_sxw_content.encode("latin1")

        sxw_io = StringIO.StringIO(binary_report_content)
        sxw_z = zipfile.ZipFile(sxw_io, mode='r')
        rml = sxw_z.read('content.xml')
        meta = sxw_z.read('meta.xml')
        mime_type = sxw_z.read('mimetype')
        if mime_type == 'application/vnd.sun.xml.writer':
            mime_type = 'sxw'
        else :
            mime_type = 'odt'
        sxw_z.close()

        rml_parser = self.parser(cr, uid, self.name2, context=context)
        rml_parser.parents = sxw_parents
        rml_parser.tag = sxw_tag
        objs = self.getObjects(cr, uid, ids, context)
        rml_parser.set_context(objs, data, ids, mime_type)

        rml_dom_meta = node = etree.XML(meta)
        elements = node.findall(rml_parser.localcontext['name_space']["meta"]+"user-defined")
        for pe in elements:
            if pe.get(rml_parser.localcontext['name_space']["meta"]+"name"):
                if pe.get(rml_parser.localcontext['name_space']["meta"]+"name") == "Info 3":
                    pe[0].text=data['id']
                if pe.get(rml_parser.localcontext['name_space']["meta"]+"name") == "Info 4":
                    pe[0].text=data['model']
        meta = etree.tostring(rml_dom_meta, encoding='utf-8',
                              xml_declaration=True)

        rml_dom =  etree.XML(rml)
        elements = []
        key1 = rml_parser.localcontext['name_space']["text"]+"p"
        key2 = rml_parser.localcontext['name_space']["text"]+"drop-down"
        for n in rml_dom.iterdescendants():
            if n.tag == key1:
                elements.append(n)
        if mime_type == 'odt':
            for pe in elements:
                e = pe.findall(key2)
                for de in e:
                    pp=de.getparent()
                    if de.text or de.tail:
                        pe.text = de.text or de.tail
                    for cnd in de:
                        if cnd.text or cnd.tail:
                            if pe.text:
                                pe.text +=  cnd.text or cnd.tail
                            else:
                                pe.text =  cnd.text or cnd.tail
                            pp.remove(de)
        else:
            for pe in elements:
                e = pe.findall(key2)
                for de in e:
                    pp = de.getparent()
                    if de.text or de.tail:
                        pe.text = de.text or de.tail
                    for cnd in de:
                        text = cnd.get("{http://openoffice.org/2000/text}value",False)
                        if text:
                            if pe.text and text.startswith('[['):
                                pe.text +=  text
                            elif text.startswith('[['):
                                pe.text =  text
                            if de.getparent():
                                pp.remove(de)

        rml_dom = self.preprocess_rml(rml_dom, mime_type)
        create_doc = self.generators[mime_type]
        odt = etree.tostring(create_doc(rml_dom, rml_parser.localcontext),
                             encoding='utf-8', xml_declaration=True)
        sxw_z = zipfile.ZipFile(sxw_io, mode='a')
        sxw_z.writestr('content.xml', odt)
        sxw_z.writestr('meta.xml', meta)

        if report_xml.header:
            #Add corporate header/footer
            rml_file = tools.file_open(os.path.join('base', 'report', 'corporate_%s_header.xml' % report_type))
            try:
                rml = rml_file.read()
                rml_parser = self.parser(cr, uid, self.name2, context=context)
                rml_parser.parents = sxw_parents
                rml_parser.tag = sxw_tag
                objs = self.getObjects(cr, uid, ids, context)
                rml_parser.set_context(objs, data, ids, report_xml.report_type)
                rml_dom = self.preprocess_rml(etree.XML(rml),report_type)
                create_doc = self.generators[report_type]
                odt = create_doc(rml_dom,rml_parser.localcontext)
                if report_xml.header:
                    rml_parser._add_header(odt)
                odt = etree.tostring(odt, encoding='utf-8',
                                     xml_declaration=True)
                sxw_z.writestr('styles.xml', odt)
            finally:
                rml_file.close()
        sxw_z.close()
        final_op = sxw_io.getvalue()
        sxw_io.close()
        return (final_op, mime_type)

    def create_single_html2html(self, cr, uid, ids, data, report_xml, context=None):
        if not context:
            context = {}
        context = context.copy()
        report_type = 'html'
        context['parents'] = html_parents

        html = report_xml.report_rml_content
        html_parser = self.parser(cr, uid, self.name2, context=context)
        html_parser.parents = html_parents
        html_parser.tag = sxw_tag
        objs = self.getObjects(cr, uid, ids, context)
        html_parser.set_context(objs, data, ids, report_type)

        html_dom =  etree.HTML(html)
        html_dom = self.preprocess_rml(html_dom,'html2html')

        create_doc = self.generators['html2html']
        html = etree.tostring(create_doc(html_dom, html_parser.localcontext))

        return (html.replace('&amp;','&').replace('&lt;', '<').replace('&gt;', '>').replace('</br>',''), report_type)

    def create_single_mako2html(self, cr, uid, ids, data, report_xml, context=None):
        mako_html = report_xml.report_rml_content
        html_parser = self.parser(cr, uid, self.name2, context)
        objs = self.getObjects(cr, uid, ids, context)
        html_parser.set_context(objs, data, ids, 'html')
        create_doc = self.generators['makohtml2html']
        html = create_doc(mako_html,html_parser.localcontext)
        return (html,'html')

