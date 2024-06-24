{
    "name": "RRHH Personalizada",
    "summary": "añade una serie de campos requeridos para los empleados",
    "version": "17.0.1.0.1",
    "category": "Customizations",
    "website": "https://www.puntsistemes.es",
    "author": "Punt Sistemes",
    "maintainers": [
        "PuntSistemes S.L.U"
    ],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr",

    ],
    "data": [
        'views/hr_employee_views.xml',
        'views/emergency_plan_views.xml',
        'security/ir.model.access.csv',

    ],

}
