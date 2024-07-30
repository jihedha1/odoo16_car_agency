from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SituationCarWizard(models.TransientModel):
    _name = 'car.situation.wizard'
    _description = 'Car Situation Wizard'

    situation = fields.Selection([
        ('0', 'very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
        ('4', 'Very High'),
        ('5', 'Excellent'), ], string="situation", required=True)

    def action_situation(self):
        active_id = self.env.context.get('active_id')
        maintenance = self.env['car.maintenance'].browse(active_id)
        car = maintenance.car_id
        if self.situation == '1' and car.situation not in ['0', '1']:
            raise ValidationError('The New situation must be upgraded')
        elif self.situation == '2' and car.situation not in ['0', '1', '2']:
            raise ValidationError('The New situation must be upgraded')
        elif self.situation == '3' and car.situation not in ['0', '1', '2', '3']:
            raise ValidationError('The New situation must be upgraded')
        elif self.situation == '4' and car.situation not in ['0', '1', '2', '3', '4']:
            raise ValidationError('The New situation must be upgraded')
        elif self.situation == '0':
            raise ValidationError('The New situation must be upgraded')
        car.situation = self.situation
        maintenance.car_id.state = 'available'
        maintenance.write({'state': 'done'})


