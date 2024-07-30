from odoo import api, fields, models, _


class CarServices(models.Model):

    _name = "car.services"
    _description = 'Car Services'

    name = fields.Char(string='Name', required=True, tracking=True)
    mode = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')],
                            string='Service Mode', default='automatic', required=True)
    price = fields.Monetary(string='Price', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    repairman_id = fields.Many2one('res.partner', string='Repairman', required=True)
    damage_id = fields.Many2one('car.damage', string='The Damage')
    phone = fields.Char(string="The Worker Phone", related='repairman_id.mobile', compute_sudo="True")
    email = fields.Char(string="The Worker Email", related='repairman_id.email', compute_sudo="True")
    active = fields.Boolean(default=True)
    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('car.services')
        return super(CarServices, self).create(vals_list)
