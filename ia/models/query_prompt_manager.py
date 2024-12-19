from odoo import models, fields, api


class QueryPromptManager(models.Model):
    _name = "query.prompt.manager"
    _description = "Almacena prompts y queries para el modelo de IA"

    name = fields.Char(
        string="Variable",
        required=True,
        help="Nombre de la variable que tiene que responder, ejemplo: albaranes.",
    )
    description = fields.Text(
        string="Descripción",
        help="Descripción que ayuda a entender el contexto para solicitar información a la IA.",
    )
    prompt = fields.Text(
        string="Prompt",
        required=True,
        help="Texto del prompt que será enviado al modelo de IA.",
    )
    sql_query = fields.Text(
        string="SQL Query",
        required=True,
        help="Sentencia SQL relacionada para obtener los datos solicitados.",
    )

    def get_prompt_and_query(self, variable_name):
        """
        Método para obtener el prompt y la query SQL relacionados con una variable específica.
        :param variable_name: Nombre de la variable (name).
        :return: Diccionario con el prompt y la query SQL.
        """
        record = self.search([("name", "=", variable_name)], limit=1)
        if record:
            return {"prompt": record.prompt, "sql_query": record.sql_query}
        return None
