from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class CarRental(models.Model):
    _name = "car.rental"
    _description = 'Rental Records'
    _inherit = ['mail.thread']
    _sql_constraints = [
        ('check_date', 'CHECK(start_date<finish_date)',
         ' The start date must be before the end date of the rent!'),
    ]
    _rec_name = 'ref'

    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    client_id = fields.Many2one('res.partner', string='The Client', required=True,  ondelete='cascade')
    agency_id = fields.Many2one('company.agency', string='The agency', domain="[('state', '=', 'active')]",
                                required=True,  ondelete='cascade')
    responsible = fields.Many2one('res.users', related='agency_id.responsible_id', string='Responsible Person',
                                  readonly=True)
    agency_image = fields.Image(string="The Agency Logo", related='agency_id.logo', compute_sudo="True")
    client_image = fields.Image(string="The Client Image", related='client_id.image_1920', compute_sudo="True")
    car_id = fields.Many2one(
        'company.car', string='Car',
        domain="[('agency_id', '=', agency_id), ('state', 'in', ['reserved', 'available']), ('situation', '!=', '0')]",
        required=True,  ondelete='cascade')
    car_situation = fields.Selection('company.car', related='car_id.situation', string='Car Situation', readonly=True)
    finish_date = fields.Date(
        'Contract End Date',
        help='Date when the coverage of the contract ends', required=True)
    brand_image = fields.Image(string="The Brand Logo", related='car_id.brand_image', compute_sudo="True")
    registration_number = fields.Char(string='Registration Number',
                                      compute_sudo="True", related='car_id.registration_number')
    start_date = fields.Date(
        'Contract Start Date',
        help='Date when the coverage of the contract begins', required=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('accepted', 'Accepted'),
         ('rented', 'Rented'),
         ('returned', 'Returned'),
         ('cancelled', 'Cancelled'),
         ], default='draft', string='Status',  tracking=True)
    notes = fields.Html('Terms and Conditions', copy=False)
    rent_price = fields.Monetary(string='Rent Price For One Day', compute='_compute_rent_price', readonly=True)
    nb_day = fields.Integer(string='The number Of Rental Days ', compute='_number_of_the_days', readonly=True)
    company_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    total = fields.Monetary(string='Rent Price', compute='_total_price', readonly=True)
    active = fields.Boolean(default=True)
    date = fields.Date(string="Date of License", related='car_id.date', compute_sudo="True")
    total_return = fields.Monetary(string='Total Price', compute='_compute_total_price', readonly=True)
    situation = fields.Selection([('normal', 'Normal'), ('damaged', 'Damaged')], string='Car Situation', readonly=True,
                                 default='normal')
    damage_ids = fields.Many2many('car.damage', 'car_rental_damage', string='Damage', readonly=True)
    costs = fields.Monetary(string='The Damage Costs', readonly=True)
    services_ids = fields.Many2many('car.services', 'car_services_rental', string='Services Needed', readonly=True)
    paid = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Paid', default='no', readonly=True)

    def name_get(self):
        res = []
        for rec in self :
            res.append((rec.id, f'{rec.client_id.name}-{rec.car_id.name_get()[0][1]}'))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('car.rental')
        return super(CarRental, self).create(vals_list)

    def action_draft(self):
        self.write({'state': 'draft'})
        for rec in self:
            for ren in rec.car_id.rental_ids:
                if rec.id != ren.id:
                    break
                self.car_id.state = 'available'

    def action_rented(self):
        self.car_id.state = 'rented'
        self.write({'state': 'rented'})

    def action_rented_and_print(self):
        self.car_id.state = 'rented'
        self.write({'state': 'rented'})
        return self.env.ref("car_agency.report_rent").report_action(self)

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        for rec in self:
            for ren in rec.car_id.rental_ids:
                if rec.id != ren.id and ren.state in ['accepted']:
                    self.car_id.state = 'reserved'
                    break
                self.car_id.state = 'available'

    def action_return(self):
        self.car_id.state = 'available'
        self.write({'state': 'draft'})

    def action_accept(self):
        self.car_id.state = 'reserved'
        self.write({'state': 'accepted'})

    @api.depends('total', 'costs')
    def _compute_total_price(self):
        for rec in self:
            rec.total_return = rec.total + rec.costs

    @api.depends('car_id')
    def _compute_rent_price(self):
        for rec in self:
            if rec.car_id:
                if rec.car_id.situation == '1':
                    rec.rent_price = 30
                elif rec.car_id.situation == '2':
                    rec.rent_price = 50
                elif rec.car_id.situation == '3':
                    rec.rent_price = 70
                elif rec.car_id.situation == '4':
                    rec.rent_price = 100
                elif rec.car_id.situation == '5':
                    rec.rent_price = 150
                else:
                    rec.rent_price = '0'
            else:
                rec.rent_price = '0'

    @api.depends('start_date', 'finish_date')
    def _number_of_the_days(self):
        for record in self:
            if record.start_date and record.finish_date:
                start_date = fields.Date.from_string(record.start_date)
                finish_date = fields.Date.from_string(record.finish_date)
                delta = finish_date - start_date
                record.nb_day = delta.days
            else:
                record.nb_day = 0

    @api.depends('nb_day', 'rent_price')
    def _total_price(self):
        for rec in self:
            rec.total = rec.nb_day*rec.rent_price

    @api.constrains('start_date', 'finish_date')
    def _valid_date(self):
        for rec in self:
            if rec.start_date > rec.finish_date:
                raise ValidationError(_("The start date must be before the end date."))

            for rent in self.env['car.rental'].search([
                ('car_id', '=', rec.car_id.id),
                ('id', '!=', rec.id)
            ]):
                if rec.start_date < rent.start_date and rec.finish_date > rent.start_date :
                    raise ValidationError(_("You cannot reserve this car in this period as it is already reserved."))
                if rec.start_date >= rent.start_date and rec.start_date < rent.finish_date:
                    raise ValidationError(_("You cannot reserve this car in this period as it is already reserved."))

    @api.constrains('car_id')
    def _valid_costs(self):
        if self.car_id.situation == '0':
            raise ValidationError(_("You can not rent this car ,the situation is very low."))


