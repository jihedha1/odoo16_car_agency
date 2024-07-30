from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CompanyCar(models.Model):
    _name = "company.car"
    _description = 'Car Records'
    _inherit = ['mail.thread']

    registration_number = fields.Char(string='Registration Number', required=True)
    notes = fields.Char(string='Terms and Conditions', config_parameter='car_agency.notes', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('rented', 'Rented'),
        ('maintenance', 'Maintenance'),
        ('sold', 'Sold'),
        ('damaged', 'Damaged')
    ], string='Status', default='draft')
    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    active = fields.Boolean(default=True)
    agency_logo = fields.Image(string='The Agency Logo', related='agency_id.logo', compute_sudo="True")
    agency_id = fields.Many2one('company.agency', string='The Owner Agency', required=True, ondelete='cascade')
    model_id = fields.Many2one('car.model', string="The Model", required=True,
                               domain="[('state', 'in', ['production','discontinued'])]")
    brand_image = fields.Image(string="The Brand", related='model_id.brand_image', compute_sudo="True")
    date = fields.Date(string="Date of License")
    mileage = fields.Integer(string='Mileage')
    situation = fields.Selection([
        ('0', 'very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
        ('4', 'Very High'),
        ('5', 'Excellent'),], string="situation")
    nb_photo = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')], string="Number of Car Photos", default='0', required=True)
    ph1 = fields.Image(string="The Front Side")
    ph2 = fields.Image(string="The Back Side")
    ph3 = fields.Image(string="The Left Side")
    ph4 = fields.Image(string="The Right Side")
    rental_ids = fields.One2many('car.rental', 'car_id', string='Rental')
    responsible = fields.Many2one('res.users', related='agency_id.responsible_id', string='Responsible Person',
                                  readonly=True)
    damage_ids = fields.Many2many('car.damage', 'car_car_damage', string='Damage', readonly=True)
    costs = fields.Monetary(string='Damaged Costs', readonly=True, tracking=True)
    company_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    damage_res = fields.Char(string='Responsible of The Damage', readonly=True, tracking=True)
    rent_count = fields.Integer(string='Rent Count', compute='_rent_count')
    reservation_count = fields.Integer(string='reservation Count', compute='_reservation_count')
    services_ids = fields.Many2many('car.services', 'car_services_car', string='Services Needed', readonly=True)
    services_count = fields.Integer(string='Services Count', compute='_services_count')
    name = fields.Char(string='Name')

    def name_get(self):
        res = []
        for rec in self :
            res.append((rec.id, f'{rec.model_id.brand_id.name}-{rec.model_id.name}-TN{rec.registration_number}'))
            rec.name = f'{rec.model_id.brand_id.name}-{rec.model_id.name}-TN{rec.registration_number}'
            print(rec.name)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('company.car')
        return super(CompanyCar, self).create(vals_list)

    @api.onchange('active')
    def _onchange_active(self):
        if not self.active:
            self.state = 'draft'

    def action_available(self):
        self.write({'state': 'available'})

    def action_draft(self):
        self.write({'state': 'draft', 'active': True})

    @api.depends('rental_ids')
    def _rent_count(self):
        for rec in self:
            rec.rent_count = self.env['car.rental'].search_count([('car_id', '=', rec.id), ('state', '=', 'returned')])

    def action_view_rents(self):
        return {
            'name': _('Rents'),
            'view_mode': 'tree,form',
            'res_model': 'car.rental',
            'type': 'ir.actions.act_window',
            'context': {'default_car_id': self.id},
            'target': 'current',
            'domain': [('car_id', '=', self.id), ('state', '=', 'returned')],

        }

    @api.depends('rental_ids')
    def _reservation_count(self):
        for rec in self:
            rec.reservation_count = self.env['car.rental'].search_count([('car_id', '=', rec.id), ('state', '=', 'accepted')])

    def action_view_reservation(self):
        return {
            'name': _('reservations'),
            'view_mode': 'tree,form',
            'res_model': 'car.rental',
            'type': 'ir.actions.act_window',
            'context': {'default_car_id': self.id},
            'target': 'current',
            'domain': [('car_id', '=', self.id), ('state', '=', 'accepted')],

        }

    @api.depends('services_ids')
    def _services_count(self):
        for rec in self:
            rec.services_count = self.env['car.maintenance'].search_count(
                [('car_id', '=', rec.id), ('state', '=', 'done')])

    def action_view_services(self):
        return {
            'name': _('Services'),
            'view_mode': 'tree,form',
            'res_model': 'car.maintenance',
            'type': 'ir.actions.act_window',
            'context': {'default_car_id': self.id},
            'target': 'current',
            'domain': [('car_id', '=', self.id), ('state', '=', 'done')],

        }

