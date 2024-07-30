from odoo import fields, models, api


class FleetServiceType(models.Model):

    _name = 'car.damage'
    _description = 'Car Damage'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    services_ids = fields.One2many('car.services', 'damage_id', string='Services')
    cost = fields.Monetary(string='Cost', compute='_compute_cost', store=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    active = fields.Boolean(default=True)

    @api.depends('services_ids.price')
    def _compute_cost(self):
        for rec in self:
            rec.cost = sum(service.price for service in rec.services_ids)

