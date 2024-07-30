from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleCarWizard(models.TransientModel):
    _name = 'car.sale.wizard'
    _description = 'Sell Car Wizard'

    ref = fields.Char(string="Brand Reference", default=lambda self: _('New'))
    client_id = fields.Many2one('res.partner', string='The Client')
    agency_id = fields.Many2one('company.agency', string='The agency', readonly=True)
    car_id = fields.Many2one('company.car', string='Car', readonly=True)
    start_date = fields.Date(
        'Contract Start Date', default=fields.Date.context_today,
        help='Date when the coverage of the contract begins')
    notes = fields.Html('Terms and Conditions', copy=False)
    sale_price = fields.Float(string='Sale Price', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', 'company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    payment_method = fields.Selection([('cryptocurrencies', 'Cryptocurrencies'), ('cash', 'Cash'),
                                       ('bank_transfers', 'Bank Transfers'), ('cheque', 'Cheque')],
                                      string='Payment Method', default='cryptocurrencies')
    pay_mode = fields.Selection([('monthly_installments', 'Monthly Installments'), ('full_payment', 'Full Payment')],
                                string='Pay Mode', default='monthly_installments')
    nbr_years = fields.Selection(
        [('1', '1 year'), ('2', '2 years'), ('3', '3 years'), ('4', '4 years'), ('5', '5 years')],
        string='Number Of Years For Installments', default='1')
    advance_installment = fields.Monetary(
        string='Advanced Installment',
        compute='_advanced_installment',
        readonly=True)
    percentage_advanced = fields.Selection(
        [('0.5', '50%'), ('0.4', '40%'), ('0.3', '30%'), ('0.2', '20%')],
        string='Percentage Of The Advanced Installment', default='0.2')
    percentage_of_increase = fields.Float(string='Percentage Of Increase (%)', compute='_increase', readonly=True)
    monthly_installment = fields.Monetary(string='Monthly Installment', compute='_monthly_installment', readonly=True)
    responsible = fields.Many2one('res.users', related='agency_id.responsible_id', string='Responsible Person',
                                  readonly=True)
    brand_image = fields.Image(string="The Brand Logo", related='car_id.brand_image', compute_sudo="True")

    @api.model
    def default_get(self, fields):
        res = super(SaleCarWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            car = self.env['company.car'].browse(active_id)
            res.update({
                'car_id': car.id,
                'agency_id': car.agency_id.id,
            })
        return res

    def action_save(self):
        active_id = self.env.context.get('active_id')
        car = self.env['company.car'].browse(active_id)
        if not car.situation or car.situation == '0':
            raise ValidationError(_("You cannot rent this car the situation is very low!"))
        sale_contract = self.env['car.sale'].create({
            'client_id': self.client_id.id,
            'agency_id': self.car_id.agency_id.id,
            'car_id': car.id,
            'sale_price': self.sale_price,
            'start_date': self.start_date,
            'state': 'draft',
            'payment_method': self.payment_method,
            'pay_mode': self.pay_mode,
            'nbr_years': self.nbr_years,
            'percentage_advanced': self.percentage_advanced,


        })

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'car.sale',
            'res_id': sale_contract.id,
            'target': 'current',
        }

    @api.depends('sale_price', 'percentage_advanced')
    def _advanced_installment(self):
        self.advance_installment = float(self.percentage_advanced) * self.sale_price

    @api.depends('nbr_years', 'percentage_advanced')
    def _increase(self):
        for record in self:
            if record.percentage_advanced:
                try:
                    record.percentage_of_increase = float(record.nbr_years) // float(record.percentage_advanced)
                except ZeroDivisionError:
                    record.percentage_of_increase = 0
            else:
                record.percentage_of_increase = 0

    @api.depends('sale_price', 'percentage_of_increase', 'percentage_advanced')
    def _monthly_installment(self):
        for record in self:
            if record.nbr_years:
                try:
                    record.monthly_installment = (record.sale_price * (
                                1 + (record.percentage_of_increase / 100)) - record.advance_installment) / (
                                                             (float(record.nbr_years)) * 12)
                except ZeroDivisionError:
                    record.monthly_installment = 0
            else:
                record.monthly_installment = 0

    def action_signe(self):
        active_id = self.env.context.get('active_id')
        car = self.env['company.car'].browse(active_id)
        if not car.situation or car.situation == '0':
            raise ValidationError (_("You cannot rent this car the situation is very low!"))
        self.car_id.state = 'sold'
        self.car_id.active = False
        if self.pay_mode == 'monthly_installments':
            self.write({'state': 'in_progress'})
        else:
            self.write({'state': 'done'})

        sale_contract = self.env['car.sale'].create({
            'client_id': self.client_id.id,
            'agency_id': self.car_id.agency_id.id,
            'car_id': car.id,
            'sale_price': self.sale_price,
            'start_date': self.start_date,
            'state': 'draft',
            'payment_method': self.payment_method,
            'pay_mode': self.pay_mode,
            'nbr_years': self.nbr_years,
            'percentage_advanced': self.percentage_advanced,

        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'car.sale',
            'res_id': sale_contract.id,
            'target': 'current',
        }


