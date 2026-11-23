# Odoo custom addons

## 1. Проєкт і версії

`library_rental` — навчальний модуль обліку книг, примірників, читачів і видач для **Odoo 19 Community** та **Python 3.13**. Для бази даних використовується PostgreSQL; конкретну версію PostgreSQL у модулі не фіксовано — звірте сумісність із вимогами вашої збірки Odoo 19.

## 2. Запуск і оновлення

Приклад команд у PowerShell на Windows:

```powershell
git clone --depth 1 --branch 19.0 https://github.com/odoo/odoo.git D:\odoo\server
py -3.13 -m venv D:\odoo\venv
D:\odoo\venv\Scripts\Activate.ps1
python -m pip install -r D:\odoo\server\requirements.txt
```

Створіть `D:\odoo\odoo.conf` після налаштування PostgreSQL-користувача `odoo`. Приклад не містить пароля:

```ini
[options]
db_host = localhost
db_port = 5432
db_user = odoo
db_password = False
addons_path = D:\odoo\server\odoo\addons,D:\odoo\server\addons,D:\odoo\custom_addons
data_dir = D:\odoo\data
http_port = 8069
```

Перший запуск для створення/ініціалізації бази та встановлення модуля:

```powershell
python D:\odoo\server\odoo-bin -c D:\odoo\odoo.conf -d library_rental_dev -i library_rental --stop-after-init
```

Звичайний запуск сервера:

```powershell
python D:\odoo\server\odoo-bin -c D:\odoo\odoo.conf -d library_rental_dev
```

Оновлення коду встановленого модуля:

```powershell
python D:\odoo\server\odoo-bin -c D:\odoo\odoo.conf -d library_rental_dev -u library_rental --stop-after-init
```

## 3. Модель даних

- **Book 1→N Copy** — книга має один або кілька фізичних примірників; кожен примірник належить одній книзі.
- **Copy 1→N Loan** — примірник може мати багато видач у часі, щоб зберігати історію.
- **Member 1→N Loan** — читач може мати багато видач; кожна видача має одного читача.
- **Loan** посилається на конкретний `library.copy`, а не безпосередньо на книгу: книга для видачі визначається через примірник.
- `library.member` — окрема модель, а не делегування від `res.partner`; вона зберігає бібліотечні дані незалежно від контактів Odoo.

Політика `ondelete="restrict"` потрібна для збереження посилань і історії: пов'язану книгу, примірник або читача не можна видалити, доки на них є залежні записи. У поточному коді `restrict` задано для `library.copy.book_id`, `library.member.user_id`, `library.loan.copy_id` і `library.loan.member_id`. Для тимчасового `library.return.wizard.loan_id` використано `cascade`. Related-поле `library.loan.book_id` не зберігається (`store=False`), тому окрема політика `ondelete` для нього не потрібна.

## 4. Бізнес-логіка

- `due_date` обчислюється як `loan_date + 14 днів` і зберігається (`store=True`).
- `fine_amount` зберігається (`store=True`): для поверненої після терміну видачі це кількість днів між `due_date` і `return_date`, помножена на **5 грн за день**; інакше сума дорівнює нулю.
- `is_overdue` обчислюється за активним станом і терміном раніше за сьогодні; поле не зберігається.
- `@api.onchange("copy_id")` попереджає у формі про наявну активну видачу, але сам по собі не блокує збереження.
- `@api.constrains("copy_id", "state")` блокує другу активну видачу примірника; пошук явно виключає поточний `self.id`.
- `@api.constrains("loan_date", "due_date")` вимагає, щоб термін був пізніше дати видачі.
- `@api.constrains("loan_date", "return_date")` не дозволяє повернення раніше дати видачі.

## 5. Безпека

Групи `Бібліотекар` (`group_library_librarian`) і `Читач` (`group_library_reader`) — окремі групи внутрішніх користувачів; обидві явно включають `base.group_user`. Адміністратор Odoo доданий до групи Бібліотекаря.

Права ACL у порядку read/write/create/unlink:

| Модель | Бібліотекар | Читач |
|---|---:|---:|
| `library.book` | 1/1/1/1 | 1/0/0/0 |
| `library.copy` | 1/1/1/1 | 1/0/0/0 |
| `library.member` | 1/1/1/1 | 0/0/0/0 |
| `library.loan` | 1/1/1/1 | 1/0/0/0 |

У `ir.model.access.csv` є також окремий доступ до `library.return.wizard` для Бібліотекаря. Record rule для `library.loan` має непорожнє `groups` — лише `group_library_reader` — і домен `member_id.user_id = user.id`; у правилі позначені read/write/create/unlink, але фактичні права обмежуються також ACL.

Кореневе меню «Бібліотека» доступне обом групам. Books, Copies, Members і Loans бачить лише Бібліотекар; Читач бачить лише «Мої видачі».

## 6. Wizard і звіт

`library.return.wizard` — `TransientModel` з `loan_id`, `condition_on_return` і необов'язковими `notes`. `action_confirm()` використовує `ensure_one()`, перевіряє активність видачі, ставить стан `returned` і сьогоднішню дату повернення, а також переносить вибраний стан на примірник. Поле `notes` наразі не обробляється методом.

QWeb-звіт **«Історія видач читача»** прив'язаний до `library.member` (не до `library.loan`). Шаблон `report_member_loan_history` використовує `web.html_container`, а `report_member_loan_history_document` — `web.external_layout` і таблицю видач. Друк доступний з картки читача; для створення PDF на сервері потрібен сумісний `wkhtmltopdf`.

## 7. Автоматизація (cron)

Cron щодня шукає прострочені активні видачі методом ORM `search()` і записує результати, помилки та загальну кількість у системний лог через `_logger`. Обрано логування, а не `message_post()`: модуль не залежить від `mail`, а технічній перевірці не потрібні chatter і сповіщення. Обробка кожного запису обгорнута окремо в `try/except`; у `loan.py` не використовується сирий SQL.

## 8. Що згенерував AI без правок

Нижче — файли, створені в ході практичних 1–6; перелік повних промптів доступний в історії Copilot. Окремі подальші зміни, підтверджені у поточному коді, зазначено в пункті 9.

1. **Практична 1 — каркас:** `library_rental/__init__.py`, `__manifest__.py`, `models/__init__.py`, `views/.gitkeep`, `security/.gitkeep`. Початковий промпт:

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

2. **Практична 2 — моделі:** `models/book.py`, `copy.py`, `member.py`, `loan.py`; зв'язки книги, примірника, читача й видачі, обчислювані суми/дати та перевірки.
3. **Практична 3 — інтерфейс і безпека:** `views/book_views.xml`, `copy_views.xml`, `member_views.xml`, `loan_views.xml`, `menu.xml`; `security/library_security.xml`, `ir.model.access.csv`.
4. **Практична 4 — демодані:** `demo/library_demo.xml` із книгами, примірниками, читачами та видачами.
5. **Практична 5 — повернення і звіт:** `models/return_wizard.py`, `views/return_wizard_views.xml`, `report/report_member_loan_history.xml`.
6. **Практична 6 — автоматизація та завершальні покращення:** `data/ir_cron_data.xml`, kanban у `views/loan_views.xml`, читабельний `display_name` примірника в `models/copy.py`.

## 9. Що виправлено вручну

Поточний код підтверджує наявність таких змін (Git-історію на цьому кроці не перевіряв, тому авторство змін за комітами не встановлював):

- **ACL wizard:** у `security/ir.model.access.csv` є рядок `access_library_return_wizard_librarian` з правами для `library.return.wizard` групі Бібліотекаря.
- **Читабельна назва примірника:** `models/copy.py` містить `_rec_name = "inventory_number"` і `_compute_display_name` з залежностями `inventory_number` та `book_id.name`; назва має формат «інвентарний номер: книга».
- **Порядок завантаження:** маніфест завантажує security XML перед ACL, views перед звітом і cron; `return_wizard_views.xml` стоїть перед `loan_views.xml`, що містить посилання на дію wizard.
- **`ondelete` у wizard:** для `library.return.wizard.loan_id` явно вказано `cascade`, оскільки wizard є `TransientModel` із тимчасовими записами без бізнес-даних; для зв'язків Copy → Book, Loan → Copy та Loan → Member використано `restrict`.
- **Related Many2one:** `library.loan.book_id` є related-полем без `store`, тому `ondelete` до нього не застосовується.
- **Читабельна назва видачі:** `library.loan` у заголовку форми показувалась як `library.loan,1`, бо немає поля `name`; додано `_compute_display_name` з `@api.depends("copy_id.book_id.name", "member_id.name")`, формат — `<книга> — <читач>`.

## 10. Наскрізна самоперевірка

Результати нижче стосуються статичної перевірки файлів; запуск Odoo і перевірка поведінки в браузері не виконувалися.

| Ділянка | Результат |
|---|---|
| Моделі | Файли моделей наявні; `ondelete` задано на зберігаємих Many2one, а `book_id` є незбережуваним related-полем. Runtime: Перевірено вручну: ______ |
| Views | XML-файли розібрані без синтаксичних помилок; `<tree>` не знайдено. Завантаження в Odoo: Перевірено вручну: ______ |
| Безпека | ACL, групи, права Читача та непорожнє `groups` у loan rule присутні. Перевірка ролями в Odoo: Перевірено вручну: ______ |
| Wizard | `TransientModel`, `ensure_one()` та зміна стану примірника присутні. UI/ACL runtime: Перевірено вручну: ______ |
| Звіт | Шаблони та дія прив'язані до `library.member`. Генерація PDF/wkhtmltopdf: Перевірено вручну: ______ |
| Cron | Щоденна дія викликає ORM-метод із логуванням і окремим `try/except`. Виконання в Odoo: Перевірено вручну: ______ |

## 11. Сценарій демонстрації (5–7 хвилин)

1. **Нова видача й термін (1 хв):** увійти як Бібліотекар, створити видачу для вільного примірника та показати автоматичний `due_date` через 14 днів.
2. **Штраф (1 хв):** відкрити повернену прострочену демо-видачу та показати `fine_amount`.
3. **Попередження й блокування дубля (1 хв):** спробувати вибрати вже виданий примірник в іншій формі, показати onchange-попередження, а потім зберегти дубль і показати помилку constraint.
4. **Wizard повернення (1 хв):** на активній видачі натиснути «Оформити повернення», змінити стан примірника й підтвердити.
5. **PDF-звіт (1 хв):** у читача вибрати «Друк → Історія видач читача» та показати сформований PDF.
6. **Cron вручну (1 хв):** відкрити Settings → Technical → Scheduled Actions, запустити «Library: перевірка прострочених видач» через Run Manually і перевірити системний лог.
7. **Роль Читача (1 хв):** увійти читачем, перевірити наявність лише «Мої видачі» та спробувати відкрити чужу видачу, щоб побачити обмеження доступу.
