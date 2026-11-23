from odoo import api, fields, models


class LibraryCopy(models.Model):
    _name = "library.copy"
    _description = "Library Copy"
    _rec_name = "inventory_number"

    book_id = fields.Many2one("library.book", required=True, ondelete="restrict")
    inventory_number = fields.Char(required=True)
    condition = fields.Selection(
        [
            ("new", "Новий"),
            ("good", "Добрий"),
            ("damaged", "Пошкоджений"),
        ],
        default="good",
    )
    loan_ids = fields.One2many("library.loan", "copy_id")

    @api.depends("inventory_number", "book_id.name")
    def _compute_display_name(self):
        for record in self:
            if record.inventory_number and record.book_id.name:
                record.display_name = f"{record.inventory_number}: {record.book_id.name}"
            elif record.inventory_number:
                record.display_name = record.inventory_number
            else:
                record.display_name = "Новий примірник"
