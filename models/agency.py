from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CompanyAgency(models.Model):
    _name = "company.agency"
    _description = 'agency Records'
    _inherit = ['mail.thread']

    name = fields.Char(string='Agency Name', required=True)
    registration_number = fields.Char(string='Registration Number', required=True)
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed_temporarily', 'Closed Temporarily'),
        ('closed_permanently', 'Closed Permanently'),
    ], default='draft', string='Status', required=True)
    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    active = fields.Boolean(default=True)
    car_ids = fields.One2many('company.car', 'agency_id', string='Cars')
    logo = fields.Image(string="The Agency Logo")
    responsible_id = fields.Many2one('res.users', string='Responsible Person')
    date = fields.Date(string="Date of License")
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    address = fields.Char(string='Address ', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('company.agency')
        return super(CompanyAgency, self).create(vals_list)




