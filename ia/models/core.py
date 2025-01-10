from odoo import models, fields, api
from langchain_openai import ChatOpenAI
from . import plantillas


class StockPickingNLP(models.Model):
    _name = "stock.picking.nlp"
    _description = "Procesador NLP para entregas"

    question = fields.Char("Pregunta", required=True)
    response = fields.Html("Respuesta", readonly=True)

    def get_categories_definition(self):
        """Obtiene las categorías dinámicamente desde QueryPromptManager."""
        query_prompts = self.env["query.prompt.manager"].search([])
        categories = []
        for prompt in query_prompts:
            categories.append(f"- '{prompt.name}': {prompt.description}")
        return "\n".join(categories)

    def get_llm_instance(self, model="gpt-3.5-turbo", temperature=0.0):
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=self.env["ir.config_parameter"]
            .sudo()
            .get_param("odoo_chatgpt_connector.api_key"),
        )

    def get_db_connection_params(self):
        """Devuelve los parámetros de conexión a la base de datos desde la configuración."""
        return {
            "dbname": self.env.cr.dbname,
            "user": "odoo",
            "password": "odoo",
            "host": "postgres",
            "port": 5432,
        }

    @api.model
    def analyze_question_for_filters(self, question):
        """Utiliza IA para analizar la pregunta y devolver filtros dinámicos."""
        try:
            llm = self.get_llm_instance(temperature=0)
            prompt = f"""
            Basándote en la siguiente pregunta del usuario: "{question}", genera un diccionario JSON con los posibles filtros 
            que podrían aplicarse a una consulta SQL. Los filtros deben estar en formato clave-valor y basados en información 
            relevante como teléfono, nombre, país, etc., según el contexto de la pregunta. Si no se puede inferir un filtro, 
            devuelve un diccionario vacío.
            """
            response = llm.invoke(prompt)
            return eval(response.content.strip())
        except Exception as e:
            return {"error": f"Error analizando la pregunta: {str(e)}"}

    def execute_query_by_classification(self, classification):
        """Ejecuta dinámicamente la query asociada a la clasificación con personalización basada en la IA."""
        query_prompt = self.env["query.prompt.manager"].search(
            [("name", "=", classification)], limit=1
        )
        if not query_prompt:
            return "Clasificación no encontrada en QueryPromptManager."

        try:
            # Analizar la pregunta para obtener filtros
            filters = self.analyze_question_for_filters(self.question)

            if "error" in filters:
                return filters["error"]

            # Rellenar la consulta con los filtros dinámicos
            sql_query = query_prompt.sql_query.format(**filters)
            self.env.cr.execute(sql_query)
            return self.env.cr.fetchall()
        except KeyError as e:
            return f"Error: Falta el filtro {str(e)} en la consulta SQL."
        except Exception as e:
            return f"Error ejecutando la consulta: {str(e)}"

    def get_dynamic_prompt(self, classification, question, raw_response):
        """Obtiene dinámicamente el prompt asociado a una clasificación."""
        query_prompt = self.env["query.prompt.manager"].search(
            [("name", "=", classification)], limit=1
        )
        if not query_prompt:
            return ""
        # Rellenar el prompt dinámico
        return query_prompt.prompt.format(question=question, raw_response=raw_response)

    @api.model
    def classify_question_with_ai(self, question):
        try:
            llm = self.get_llm_instance(temperature=0)
            categories_definition = self.get_categories_definition()
            prompt = plantillas.classify_question_with_ai(
                question=question, categories_description=categories_definition
            )
            response = llm.invoke(prompt)
            classification = response.content.strip().lower()
            return classification

        except Exception as e:
            return f"Error clasificando la pregunta: {str(e)}"

    @api.model
    def process_response_with_ai(self, question, raw_response, classification):
        """Procesa la respuesta con IA usando un prompt dinámico."""
        try:
            llm = self.get_llm_instance(temperature=0)
            # Obtiene el prompt dinámico
            dynamic_prompt = self.get_dynamic_prompt(
                classification, question, raw_response
            )
            if not dynamic_prompt:
                return "Error: No se encontró un prompt válido."

            response = llm.invoke(dynamic_prompt)
            return response.content.strip()

        except Exception as e:
            return f"Error al procesar la respuesta con IA: {str(e)}"

    @api.depends("question")
    def action_process_question(self):
        """Procesa la pregunta y genera la respuesta."""
        for record in self:
            try:
                if record.question:
                    classification = self.classify_question_with_ai(record.question)

                    # Ejecutar la query correspondiente a la clasificación
                    raw_response = self.execute_query_by_classification(classification)
                    if isinstance(raw_response, str):
                        # Si no hay resultados o error, devolver el mensaje
                        record.response = raw_response
                    else:
                        # Procesar la respuesta con IA usando el prompt dinámico
                        record.response = self.process_response_with_ai(
                            record.question, raw_response, classification
                        )

                else:
                    record.response = "Pregunta vacía."
            except Exception as e:
                record.response = f"Error procesando la pregunta: {str(e)}"
