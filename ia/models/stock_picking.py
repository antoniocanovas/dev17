from odoo import models, fields, api
from langchain_openai import ChatOpenAI
import psycopg2
from pkg_resources import require

from . import plantillas


class StockPickingNLP(models.Model):
    _name = "stock.picking.nlp"
    _description = "Procesador NLP para entregas"

    question = fields.Char("Pregunta", required=True)
    response = fields.Html("Respuesta", readonly=True)
    OPENAI_API_KEY = fields.Text("Clave de API de OpenAI", required=True)

    def get_llm_instance(self, model="gpt-3.5-turbo", temperature=0.0):
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=self.OPENAI_API_KEY,
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
    def classify_question_with_ai(self, question):
        """Clasifica si la pregunta está relacionada con albaranes o movimientos de stock."""
        try:

            llm = self.get_llm_instance(temperature=0)
            # Prompt para clasificación
            prompt = plantillas.classify_question_with_ai(question=question)
            response = llm.invoke(prompt)
            classification = response.content.strip().lower()
            return classification

        except Exception as e:
            return f"Error clasificando la pregunta: {str(e)}"

    @api.model
    def query_stock_picking(self):
        """Consulta la tabla stock_picking y devuelve los resultados."""
        try:
            db_params = self.get_db_connection_params()
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            query = """
                SELECT 
                    sp.id AS picking_id,
                    sp.name AS picking_name,
                    sp.scheduled_date AS picking_date,
                    sp.state AS picking_state
                FROM 
                    stock_picking sp
                WHERE 
                    sp.state NOT IN ('draft', 'done', 'cancel')
                ORDER BY 
                    sp.state ASC, sp.name ASC;

            """
            cursor.execute(query)
            rows = cursor.fetchall()
            connection.close()

            if not rows:
                return "No se encontraron albaranes pendientes."

            response = "Albaranes pendientes:\n"
            for row in rows:
                response += f"ID: {row[0]}, Nombre: {row[1]}, Estado: {row[2]}, Fecha Programada: {row[3]}\n"
            return response

        except Exception as e:
            return f"Error al realizar la consulta de albaranes: {str(e)}"

    @api.model
    def query_stock_moves(self):
        """Consulta los movimientos de stock y devuelve los resultados."""
        try:

            db_params = self.get_db_connection_params()
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            query = """
                SELECT 
                    sm.id AS move_id,
                    pt.name AS product_name,
                    sm.product_uom_qty AS quantity,
                    sp.name AS picking_name,
                    sp.scheduled_date AS picking_date,
                    sp.state AS picking_state
                FROM 
                    stock_move sm
                JOIN 
                    stock_picking sp ON sm.picking_id = sp.id
                JOIN 
                    product_product pp ON sm.product_id = pp.id
                JOIN 
                    product_template pt ON pp.product_tmpl_id = pt.id
                WHERE 
                    sp.state NOT IN ('draft','done', 'cancel')
                ORDER BY 
                    sp.state ASC,sp.name ASC, sm.id ASC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            connection.close()

            if not rows:
                return "No se encontraron movimientos de stock pendientes."

            response = "Movimientos de stock:\n"
            for row in rows:
                response += (
                    f"Movimiento ID: {row[0]}, Producto: {row[1]}, Cantidad: {row[2]}, "
                    f"Albarán: {row[3]}, Fecha: {row[4]},Estado: {row[5]}\n"
                )
            return response

        except Exception as e:
            return f"Error al realizar la consulta de movimientos: {str(e)}"

    @api.model
    def process_response_with_ai(self, question, raw_response, classification):
        """Procesa la respuesta con IA para generar un mensaje amigable."""
        try:
            llm = self.get_llm_instance(temperature=0)
            # Prompt para procesar la respuesta
            prompt = plantillas.movimientos_stock_prompt(
                question=question, raw_response=raw_response
            )

            response = llm.invoke(prompt)
            return response.content.strip()

        except Exception as e:
            return f"Error al procesar la respuesta con IA: {str(e)}"

    @api.depends("question")
    def action_process_question(self):
        """Procesa la pregunta y genera la respuesta."""
        for record in self:
            try:
                llm = self.get_llm_instance(temperature=0)
                if record.question:
                    classification = self.classify_question_with_ai(record.question)

                    if classification == "albaranes":
                        raw_response = self.query_stock_picking()
                    elif classification == "movimientos":
                        raw_response = self.query_stock_moves()
                    else:
                        raw_response = "No se pudo clasificar la pregunta. Por favor, intenta nuevamente."

                    # Procesar la respuesta con IA
                    record.response = self.process_response_with_ai(
                        record.question, raw_response, classification
                    )
                else:
                    record.response = "Pregunta vacía."
            except Exception as e:
                record.response = f"Error procesando la pregunta: {str(e)}"
