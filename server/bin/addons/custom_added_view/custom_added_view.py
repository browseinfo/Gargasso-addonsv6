from osv import fields, osv

class product_product(osv.osv):
    
    _name="product.product"
    
    _inherit = "product.product"
    
    _columns = {
                'x_thickness' : fields.char('Thickness', size=120),
                'x_width' : fields.char('Width',size=120),
                'x_colour' : fields.char('Colour',size=120),
                'x_diameter' : fields.float('Diameter'),
                'x_spools' : fields.integer('Spools'),
                }
    
product_product()

class stock_picking(osv.osv):
    
    
    _name = "stock.picking"
   
    _inherit = "stock.picking"
    
    _columns = {
                'x_weight_net': fields.float('Net Weight :'),
                'x_weight_gross': fields.float('Gross Weight :'),
                'x_weight_packed': fields.float('Packed Weight :'),
                'x_dimension' : fields.char('Dimensions :', size=300),
                }
stock_picking()

class stock_move(osv.osv):
    
    _name = "stock.move"
    
    _inherit = "stock.move"
    
    _columns = {
                'x_spool_number' : fields.char('Spool Number',size=64),
#                'x_mo_prod_seq' : fields.integer('temp'),
                }
stock_move()

class mrp_production(osv.osv):
    
    _name = "mrp.production"
    
    _inherit = "mrp.production"
    
    _columns = {
                'x_subspoolnumber' : fields.char('Sub Spool Number :',size=64),
                'x_length' : fields.char('Length on Spool :',size=64),
                'x_colour' : fields.char('Cables/Wires Colour :',size=64),
                'x_job_order_type' : fields.char('Domestic/Export/AS :',size=64),
                }
mrp_production()

class mrp_bom(osv.osv):
    
    _name = "mrp.bom"
    
    _inherit = "mrp.bom"
    
    _columns = {
                'x_remarks' : fields.text('Remarks :'),
                'x_mo_prod_seq': fields.integer('SL NO'),
                'x_work_center_id' : fields.integer('WORK CENTER'),
                }
