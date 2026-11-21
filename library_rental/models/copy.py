from odoo import fields, models


class LibraryCopy(models.Model):
    _name = "library.copy"
    _description = "Library Copy"

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
