from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ReturnCarWizard(models.TransientModel):
    _name = 'return.car'
    _description = 'Return The Car'

    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    client_id = fields.Many2one('res.partner', string='The Client', readonly=True)
    agency_id = fields.Many2one('company.agency', string='The Agency', readonly=True)
    responsible = fields.Many2one('res.users', related='agency_id.responsible_id', string='Responsible Person', readonly = True)
    car_id = fields.Many2one('company.car', string='Car', readonly=True)
    car_situation = fields.Selection([('normal', 'Normal'), ('damaged', 'Damaged')], string='Car Situation', required=True, default='normal')
    damage_ids = fields.Many2many('car.damage', 'car_return_damage', string='Damage')
    services_ids = fields.Many2many('car.services', 'car_services_return', string='Services Needed',
                                    domain="[('damage_id', '=', damage_ids)]")
    registration_number = fields.Char(string='Registration Number', compute_sudo=True, related='car_id.registration_number', readonly=True)
    notes = fields.Html('Terms and Conditions', copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    price_rent = fields.Monetary(string='Rent Price', readonly=True)
    costs = fields.Monetary(string='Damage Costs', compute='_damage_cost', readonly=True)
    total = fields.Monetary(string='Total Price', compute='_compute_total_price', readonly=True)
    active = fields.Boolean(default=True)

    @api.model
    def default_get(self, fields):
        res = super(ReturnCarWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            rental = self.env['car.rental'].browse(active_id)
            if rental.exists():  # Ensure the rental record exists
                res.update({
                    'car_id': rental.car_id.id,
                    'agency_id': rental.agency_id.id,
                    'client_id': rental.client_id.id,
                    'price_rent': rental.total
                })
        return res

    @api.depends('price_rent', 'costs')
    def _compute_total_price(self):
        for rec in self:
            rec.total = rec.price_rent + rec.costs

    def action_save(self):
        for wizard in self:
            rental_id = self.env.context.get('active_id')
            rental = self.env['car.rental'].browse(rental_id)
            if not rental.exists():
                raise ValidationError(_("No active car rental record found."))

            _logger.info(f'Saving return car wizard for rental ID: {rental_id}')

            rental.write({
                'situation': wizard.car_situation,
                'damage_ids': wizard.damage_ids,
                'services_ids': wizard.services_ids,
                'costs': wizard.costs,
                'total': wizard.total,
            })

            rental.state = 'returned'

            _logger.info(f'Updating car state for car ID: {wizard.car_id.id}')
            if wizard.car_situation == 'damaged':
                wizard.car_id.write({'state': 'damaged',
                                     'damage_ids': self.damage_ids,
                                     'services_ids': wizard.services_ids,
                                     'costs': self.costs,
                                     'damage_res': self.client_id.name})
            else:
                if self.car_id.reservation_count != 0:
                    wizard.car_id.write({'state': 'reserved'})
                else:
                    wizard.car_id.write({'state': 'available'})

            return {
                'type': 'ir.actions.act_window',
                'name': 'Car Rental',
                'res_model': 'car.rental',
                'view_mode': 'form',
                'res_id': rental.id,
                'target': 'current',
            }

    @api.constrains('costs')
    def _valid_damage_costs(self):
        if self.car_situation == 'damaged':
            if self.costs == 0:
                raise ValidationError(_("The costs must be different to zero."))

    @api.depends('services_ids')
    def _damage_cost(self):
        self.costs = 0
        for rec in self:
            for service in rec.services_ids:
                rec.costs = service.price + rec.costs

    def action_create_inv(self):
        for wizard in self:
            rental_id = self.env.context.get('active_id')
            rental = self.env['car.rental'].browse(rental_id)
            rental.paid = 'yes'
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': wizard.client_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': f'Rental for {wizard.car_id.registration_number}',
                    'quantity': 1,
                    'price_unit': wizard.price_rent,
                })],
                'company_id': wizard.company_id.id,
            }

            if wizard.car_situation == 'damaged':
                invoice_vals['invoice_line_ids'].append((0, 0, {
                    'name': 'Damage Costs',
                    'quantity': 1,
                    'price_unit': wizard.costs,
                }))

            invoice = self.env['account.move'].create(invoice_vals)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice.id,
                'target': 'current',
            }

    def action_save_and_create_inv(self):
        self.action_save()
        return self.action_create_inv()