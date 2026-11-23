from odoo import api, fields, models
from odoo.exceptions import UserError


class LibraryReturnWizard(models.TransientModel):
    _name = "library.return.wizard"
    _description = "Майстер повернення книги"

    loan_id = fields.Many2one(
        "library.loan",
        required=True,
        string="Видача",
    )
    condition_on_return = fields.Selection(
        selection=lambda self: self.env["library.copy"]._fields[
            "condition"
        ]._description_selection(self.env),
        required=True,
    )
    notes = fields.Text()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("active_model") == "library.loan":
            values["loan_id"] = self.env.context.get("active_id")
        return values

    def action_confirm(self):
        self.ensure_one()
        if self.loan_id.state != "active":
            raise UserError("Повернути можна лише активну видачу.")
        self.loan_id.write({
            "state": "returned",
            "return_date": fields.Date.context_today(self),
        })
        self.loan_id.copy_id.condition = self.condition_on_return
        return {"type": "ir.actions.act_window_close"}
