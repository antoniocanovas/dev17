def movimientos_stock_prompt(question, raw_response):
    return f"""
        Dada la siguiente información (la respuesta final debe ser en HTML con estilos y formateo):

        Pregunta del usuario:
        "{question}"

        Datos obtenidos desde la base de datos:
        "{raw_response}"

        Por favor, genera una **respuesta en HTML** clara y amigable para el usuario final con el siguiente formato y reglas:

        <h2>Movimientos de stock pendientes</h2>
        <p>Los albaranes y movimientos pendientes son los siguientes, agrupados por estado:</p>

        <ul style="list-style-type:none; padding-left:0;">
          <!-- Ejemplo de estructura que deseamos conseguir -->
          <!--
            <li>
              <h3>Estado: En Preparación</h3>
              <ul>
                <li>
                  <h4>Albarán WH/OUT/00001</h4>
                  <ul>
                    <li>Producto: p1, Cantidad: 0.0</li>
                    <li>Producto: p2, Cantidad: 0.0</li>
                  </ul>
                </li>
                <li>
                  <h4>Albarán WH/OUT/00002</h4>
                  <ul>
                    <li>Producto: p1, Cantidad: 0.0</li>
                    <li>Producto: p2, Cantidad: 0.0</li>
                  </ul>
                </li>
              </ul>
            </li>
            <li>
              <h3>Estado: Listo para Envío</h3>
              ...
            </li>
          -->
        </ul>

        Reglas:
        - Si el estado es 'confirmed', muestra el estado como "En Preparación".
        - Si el estado es 'assigned', muestra el estado como "Listo para Envío".
        - Agrupa los albaranes por estado en bloques HTML <li> o similar.
        - Dentro de cada estado, muestra los albaranes con sus productos y cantidades.
        - Cada albarán debe estar dentro de una lista anidada como en el ejemplo proporcionado.
        - Excluye cualquier referencia a IDs, fechas u otros datos técnicos irrelevantes.
        - Usa un formato HTML consistente y fácil de leer, similar al ejemplo anterior.
        -si no tengo algo de ingormacion como el producto o la cantidad no lo escribo lo dejo en blanco nolo relleno

        Genera ÚNICAMENTE el cuerpo HTML que cumpla estas reglas, sin texto adicional ni comentarios.
        """


def classify_question_with_ai(question):
    return f"""
    pregunta del usuariao: {question}
    Clasifica la intención del usuario según su pregunta.
    
    Categorías posibles:
    - 'movimientos': El usuario pregunta por movimientos o productos específicos de un albarán.
    - 'albaranes': El usuario pregunta por una lista de albaranes, sin interés en los movimientos específicos.
    - 'general': La pregunta es demasiado genérica o no está relacionada con albaranes o movimientos.


    Retorna:
    -Una de las categorías (movimientos, albaranes, general).
    """
