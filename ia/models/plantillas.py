def classify_question_with_ai(question, categories_description):
    return f"""
     Dada la siguiente pregunta del usuario:
     "{question}"

     Tenemos las siguientes categorías (este listado puede ampliarse en el futuro):

     {categories_description}

     Instrucciones:
     1. Analiza cuidadosamente la intención del usuario reflejada en su pregunta.
     2. Determina cuál de las categorías se ajusta mejor al propósito de la pregunta.
     3. Si la pregunta no se adapta perfectamente a una categoría, elige la más cercana.
     4. Si la pregunta es demasiado genérica o no se relaciona con ninguna categoría, elige 'general'.

     Retorna:
     - Únicamente el nombre de la categoría elegida, sin explicación adicional.
     """
