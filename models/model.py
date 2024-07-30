from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CarModel(models.Model):
    _name = "car.model"
    _description = 'model Records'
    _inherit = ['mail.thread']
    _rec_name = 'brand_id'

    name = fields.Char(string='Model Name ', required=True, tracking=True)
    nbr = fields.Char(string='ID ')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('concept', 'Concept'),
        ('prototype', 'Prototype'),
        ('production', 'In Production'),
        ('discontinued', 'Discontinued')
    ], string='Status', default='concept')
    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    active = fields.Boolean(default=True,  ondelete='cascade')
    brand_id = fields.Many2one('car.brand', string="The Brand", required=True)
    brand_image = fields.Image(string="The Brand", related='brand_id.brand_image', compute_sudo="True")
    transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission')
    date = fields.Selection(selection='_get_year_selection', string="Model Year")
    seats = fields.Integer(string='Seats Number')
    doors = fields.Integer(string='Doors Number')
    power = fields.Integer('Power')
    horsepower = fields.Integer()
    horsepower_tax = fields.Float('Horsepower Taxation')
    electric_assistance = fields.Boolean(default=False)

    def _get_year_selection(self):
        year_list = [(str(year), str(year)) for year in range(1890, 2025)]
        return year_list

    def name_get(self):
        res = []
        for rec in self :
            res.append((rec.id, f'{rec.brand_id.name}-{rec.name}'))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('car.model')
        return super(CarModel, self).create(vals_list)

