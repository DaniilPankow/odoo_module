# Odoo custom addons

## Що згенерував AI-асистент

Файли модуля `library_rental`, створені AI-асистентом:

- `library_rental/__init__.py`
- `library_rental/__manifest__.py`
- `library_rental/models/__init__.py`
- `library_rental/views/.gitkeep`
- `library_rental/security/.gitkeep`

### Промпти

> Контекст: Odoo 19 Community, вихідний код у D:\odoo\server, мої модулі в D:\odoo\custom_addons.  
> Створи мінімальний каркас модуля custom_addons/library_rental:
>
> - __init__.py: from . import models
> - __manifest__.py: name "Library Rental", version "19.0.1.0.0", category "Services",
>   summary (одне речення), author, depends ["base"], data [], installable True,
>   application True, license "LGPL-3"
> - models/__init__.py: порожній
> - views/ і security/: порожні папки з файлами .gitkeep
>
> Вимоги:
> - у depends лише "base", жодних залежностей "про всяк випадок" (без contacts, mail тощо);
> - у data не посилайся на файли, яких не існує;
> - ніяких моделей, полів, меню й прикладів коду, лише каркас;
> - не змінюй нічого поза custom_addons/library_rental;
> - git-команди не виконуй.
> Після створення покажи список файлів і коротко поясни кожне поле __manifest__.py.

## Що я виправив вручну

## Структура зв'язків

- **Book 1→N Copy** — одна книга може мати кілька фізичних примірників; кожен примірник належить одній книзі.
- **Copy 1→N Loan** — один примірник може мати кілька записів видач у часі, щоб зберігати історію користування.
- **Member 1→N Loan** — один читач може мати кілька видач; кожна видача пов'язана з одним читачем.

Вибір моделі для `Member`: TODO

`ondelete`: TODO
