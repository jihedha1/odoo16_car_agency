from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RentCarWizard(models.TransientModel):
    _name = 'car.rental.wizard'
    _description = 'Rent Car Wizard'
    _sql_constraints = [
        ('check_date', 'CHECK(start_date<finish_date)',
         ' The start date must be before the end date of the rent!'),
    ]

    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    client_id = fields.Many2one('res.partner', string='The Client', required=True)
    agency_id = fields.Many2one('company.agency', string='The agency', domain="[('state', '=', 'active')]",
                                required=True)
    responsible = fields.Many2one('res.users', related='agency_id.responsible_id', string='Responsible Person',
                                  readonly=True)
    car_id = fields.Many2one(
        'company.car', string='Car',
        domain="[('agency_id', '=', agency_id), ('state', 'in', ['reserved', 'available']), ('situation', '!=', '0')]",
        required=True)
    car_situation = fields.Selection('company.car', related='car_id.situation', string='Car Situation',
                                     readonly=True)
    finish_date = fields.Date(
        'Contract End Date',
        help='Date when the coverage of the contract ends', required=True)
    registration_number = fields.Char(string='Registration Number',
                                      compute_sudo="True", related='car_id.registration_number')
    start_date = fields.Date(
        'Contract Start Date',
        help='Date when the coverage of the contract begins', required=True)
    notes = fields.Html('Terms and Conditions', copy=False)
    rent_price = fields.Monetary(string='Rent Price For One Day', compute='_compute_rent_price', readonly=True)
    nb_day = fields.Integer(string='The number Of Rental Days ', compute='_number_of_the_days', readonly=True)
    company_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    total = fields.Monetary(string='Total Price', compute='_total_price', readonly=True)
    active = fields.Boolean(default=True)

    @api.model
    def default_get(self, fields):
        res = super(RentCarWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            car = self.env['company.car'].browse(active_id)
            res.update({
                'car_id': car.id,
                'agency_id': car.agency_id.id,
            })
        return res

    def action_create_rent(self):
        active_id = self.env.context.get('active_id')
        car = self.env['company.car'].browse(active_id)
        if not car.situation or car.situation == '0':
            raise ValidationError(_("You cannot rent this car the situation is very low!"))
        if not car:
            raise ValidationError(_("Car record not found."))

        rent_contract = self.env['car.rental'].create({
            'client_id': self.client_id.id,
            'agency_id': self.car_id.agency_id.id,
            'car_id': car.id,
            'start_date': self.start_date,
            'finish_date': self.finish_date,
            'state': 'draft',
        })

        if not rent_contract:
            raise ValidationError(_("Failed to create rental contract."))

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'car.rental',
            'res_id': rent_contract.id,
            'target': 'current',
        }

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
            rec.total = rec.nb_day * rec.rent_price

    @api.constrains('start_date', 'finish_date')
    def _valid_date(self):
        for rec in self:
            if rec.start_date > rec.finish_date:
                raise ValidationError(_("The start date must be before the end date."))

            for rent in self.env['car.rental'].search([
                ('car_id', '=', rec.car_id.id),
                ('id', '!=', rec.id)
            ]):
                if rec.start_date < rent.start_date and rec.finish_date > rent.start_date:
                    raise ValidationError(_("You cannot reserve this car in this period as it is already reserved."))
                if rec.start_date >= rent.start_date and rec.start_date < rent.finish_date:
                    raise ValidationError(_("You cannot reserve this car in this period as it is already reserved."))
