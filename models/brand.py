from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CarBrand(models.Model):
    _name = "car.brand"
    _description = 'Brand Records'
    _inherit = ['mail.thread']

    name = fields.Char(string='Brand Name ', required=True, tracking=True)
    brand_image = fields.Image(string="The Brand")
    nbr = fields.Char(string='ID ')
    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='draft')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('car.brand')
        return super(CarBrand, self).create(vals_list)
