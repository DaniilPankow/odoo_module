{
    "name": "Library Rental",
    "version": "19.0.1.0.0",
    "category": "Services",
    "summary": "Manage library rentals.",
    "author": "Odoo Custom Addons",
    "depends": ["base"],
    "data": [
        "security/library_security.xml",
        "security/ir.model.access.csv",
        "views/book_views.xml",
        "views/copy_views.xml",
        "views/member_views.xml",
        "views/loan_views.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/library_demo.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
