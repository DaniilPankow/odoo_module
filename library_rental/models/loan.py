from odoo import fields, models


class LibraryLoan(models.Model):
    _name = "library.loan"
    _description = "Library Loan"

    copy_id = fields.Many2one("library.copy", required=True, ondelete="restrict")
    member_id = fields.Many2one("library.member", required=True, ondelete="restrict")
    loan_date = fields.Date(default=fields.Date.context_today)
    due_date = fields.Date()
    return_date = fields.Date()
    state = fields.Selection(
        [
            ("active", "Active"),
            ("returned", "Returned"),
        ],
        default="active",
    )
    book_id = fields.Many2one(
        related="copy_id.book_id",
        store=False,
        readonly=True,
    )
    author = fields.Char(related="copy_id.book_id.author", readonly=True)
