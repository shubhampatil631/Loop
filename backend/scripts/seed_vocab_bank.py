import os
import sys
import re
from pathlib import Path

# Add backend directory to sys.path so it can run standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def normalize_vocab_id(lemma: str, level: str) -> str:
    """Deterministic, clean document ID for Chroma and in-memory storage."""
    clean_lemma = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ]", "_", lemma.lower().strip())
    clean_lemma = re.sub(r"_+", "_", clean_lemma).strip("_")
    return f"vocab_{level.lower()}_{clean_lemma}"

# Comprehensive Leveled CEFR Spanish Vocab Bank Dataset (100+ items across A1-B2)
VOCAB_DATA = [
    # -------------------------------------------------------------
    # A1 - Cafe & Dining
    # -------------------------------------------------------------
    {"lemma": "el café", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "Quiero un café con leche caliente, por favor.", "translation": "I want a coffee with hot milk, please."},
    {"lemma": "el té", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "¿Tiene té verde o solo té negro?", "translation": "Do you have green tea or only black tea?"},
    {"lemma": "el agua", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "¿Me puedes traer un vaso de agua mineral fría?", "translation": "Can you bring me a glass of cold mineral water?"},
    {"lemma": "la cuenta", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "La cuenta, por favor, cuando tenga un momento.", "translation": "The check, please, when you have a moment."},
    {"lemma": "el azúcar", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "Prefiero tomar mi café con poco azúcar.", "translation": "I prefer to take my coffee with little sugar."},
    {"lemma": "el zumo", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "Un zumo de naranja natural para el desayuno, por favor.", "translation": "A fresh orange juice for breakfast, please."},
    {"lemma": "el desayuno", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "El desayuno está incluido en el precio de la habitación.", "translation": "Breakfast is included in the room price."},
    {"lemma": "la tostada", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "Tomaré una tostada con tomate y aceite de oliva.", "translation": "I will have toast with tomato and olive oil."},
    {"lemma": "el menú", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "¿Tienen el menú del día en español e inglés?", "translation": "Do you have the daily menu in Spanish and English?"},
    {"lemma": "la mesa", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "Quisiéramos una mesa para dos personas cerca de la ventana.", "translation": "We would like a table for two near the window."},
    {"lemma": "el camarero", "cefr_level": "A1", "pos": "noun", "theme": "cafe", "sentence": "El camarero fue muy amable con nosotros durante la cena.", "translation": "The waiter was very kind to us during dinner."},
    {"lemma": "pedir", "cefr_level": "A1", "pos": "verb", "theme": "cafe", "sentence": "¿Qué vas a pedir de comer hoy?", "translation": "What are you going to order to eat today?"},
    {"lemma": "pagar", "cefr_level": "A1", "pos": "verb", "theme": "cafe", "sentence": "¿Puedo pagar con tarjeta de crédito o solo en efectivo?", "translation": "Can I pay with a credit card or only in cash?"},
    {"lemma": "tomar", "cefr_level": "A1", "pos": "verb", "theme": "cafe", "sentence": "¿Qué desean tomar los señores para empezar?", "translation": "What would you like to drink to start?"},

    # -------------------------------------------------------------
    # A1 - Travel & Transport
    # -------------------------------------------------------------
    {"lemma": "el boleto", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "Necesito un boleto de tren para ir a Barcelona hoy.", "translation": "I need a train ticket to go to Barcelona today."},
    {"lemma": "el billete", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "Compré un billete de ida y vuelta a Sevilla.", "translation": "I bought a round-trip ticket to Seville."},
    {"lemma": "la estación", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "¿Dónde está la estación central de metro más cercana?", "translation": "Where is the nearest central subway station?"},
    {"lemma": "el hotel", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "Tengo una reserva en este hotel para dos noches.", "translation": "I have a reservation at this hotel for two nights."},
    {"lemma": "el taxi", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "¿Podría llamar a un taxi para ir al aeropuerto ahora?", "translation": "Could you call a taxi to go to the airport now?"},
    {"lemma": "el aeropuerto", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "Llegamos al aeropuerto con dos horas de anticipación.", "translation": "We arrived at the airport two hours early."},
    {"lemma": "la maleta", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "Mi maleta pesa quince kilos y llevo ropa cómoda.", "translation": "My suitcase weighs fifteen kilos and I carry comfortable clothes."},
    {"lemma": "el tren", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "El tren de alta velocidad sale a las nueve en punto.", "translation": "The high-speed train leaves at nine o'clock sharp."},
    {"lemma": "el autobús", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "Tomamos el autobús turístico para ver los monumentos.", "translation": "We took the tourist bus to see the monuments."},
    {"lemma": "la calle", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "Esta calle principal llega directamente a la plaza mayor.", "translation": "This main street leads directly to the main square."},
    {"lemma": "el mapa", "cefr_level": "A1", "pos": "noun", "theme": "travel", "sentence": "¿Tiene un mapa turístico de la ciudad?", "translation": "Do you have a tourist map of the city?"},
    {"lemma": "llegar", "cefr_level": "A1", "pos": "verb", "theme": "travel", "sentence": "¿A qué hora llega el próximo tren de Madrid?", "translation": "What time does the next train from Madrid arrive?"},
    {"lemma": "viajar", "cefr_level": "A1", "pos": "verb", "theme": "travel", "sentence": "Me gusta mucho viajar a países hispanohablantes.", "translation": "I really like traveling to Spanish-speaking countries."},

    # -------------------------------------------------------------
    # A1 - Family & Daily Routine
    # -------------------------------------------------------------
    {"lemma": "la casa", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Mi casa está cerca de un bonito parque arbolado.", "translation": "My house is close to a nice tree-lined park."},
    {"lemma": "la madre", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Mi madre cocina una deliciosa paella los domingos.", "translation": "My mother cooks delicious paella on Sundays."},
    {"lemma": "el padre", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Mi padre lee el periódico todas las mañanas con café.", "translation": "My father reads the newspaper every morning with coffee."},
    {"lemma": "el hermano", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Tengo un hermano menor que estudia en la universidad.", "translation": "I have a younger brother who studies at the university."},
    {"lemma": "la hermana", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Mi hermana vive en Valencia y trabaja como médica.", "translation": "My sister lives in Valencia and works as a doctor."},
    {"lemma": "el amigo", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Voy a cenar con un amigo en el centro histórico.", "translation": "I am going to have dinner with a friend downtown."},
    {"lemma": "el perro", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Paseo a mi perro temprano por la mañana en el parque.", "translation": "I walk my dog early in the morning in the park."},
    {"lemma": "el gato", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "El gato duerme plácidamente en el sofá de la sala.", "translation": "The cat sleeps peacefully on the living room sofa."},
    {"lemma": "el hijo", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Mi hijo juega al fútbol en el parque los sábados.", "translation": "My son plays soccer in the park on Saturdays."},
    {"lemma": "la hija", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Su hija pequeña aprende a tocar la guitarra clásica.", "translation": "Her young daughter is learning to play the classical guitar."},
    {"lemma": "vivir", "cefr_level": "A1", "pos": "verb", "theme": "family", "sentence": "Vivo en un apartamento acogedor en el centro de Madrid.", "translation": "I live in a cozy apartment in the center of Madrid."},
    {"lemma": "comer", "cefr_level": "A1", "pos": "verb", "theme": "family", "sentence": "Nos gusta comer juntos en familia todos los días.", "translation": "We like to eat together as a family every day."},
    {"lemma": "dormir", "cefr_level": "A1", "pos": "verb", "theme": "family", "sentence": "Suelo dormir ocho horas para tener energía.", "translation": "I usually sleep eight hours to have energy."},
    {"lemma": "la ciudad", "cefr_level": "A1", "pos": "noun", "theme": "family", "sentence": "Esta ciudad tiene muchos monumentos históricos y museos.", "translation": "This city has many historical monuments and museums."},

    # -------------------------------------------------------------
    # A1 - Shopping & Everyday Needs
    # -------------------------------------------------------------
    {"lemma": "la panadería", "cefr_level": "A1", "pos": "noun", "theme": "shopping", "sentence": "Voy a comprar pan fresco en la panadería del barrio.", "translation": "I am going to buy fresh bread at the neighborhood bakery."},
    {"lemma": "el supermercado", "cefr_level": "A1", "pos": "noun", "theme": "shopping", "sentence": "Hacemos las compras semanales en el gran supermercado.", "translation": "We do weekly grocery shopping at the large supermarket."},
    {"lemma": "el pan", "cefr_level": "A1", "pos": "noun", "theme": "shopping", "sentence": "¿Cuánto cuesta esta barra de pan artesanal?", "translation": "How much does this loaf of artisan bread cost?"},
    {"lemma": "la fruta", "cefr_level": "A1", "pos": "noun", "theme": "shopping", "sentence": "La fruta de temporada es fresca y muy saludable.", "translation": "Seasonal fruit is fresh and very healthy."},
    {"lemma": "el dinero", "cefr_level": "A1", "pos": "noun", "theme": "shopping", "sentence": "Tengo suficiente dinero para comprar los ingredientes.", "translation": "I have enough money to buy the ingredients."},
    {"lemma": "el euro", "cefr_level": "A1", "pos": "noun", "theme": "shopping", "sentence": "El precio total es de quince euros.", "translation": "The total price is fifteen euros."},

    # -------------------------------------------------------------
    # A2 - Work & Professional Routine
    # -------------------------------------------------------------
    {"lemma": "el trabajo", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Empiezo mi nuevo trabajo en una oficina internacional el lunes.", "translation": "I start my new job at an international office on Monday."},
    {"lemma": "la reunión", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Tenemos una reunión de equipo a las diez de la mañana.", "translation": "We have a team meeting at ten in the morning."},
    {"lemma": "el correo", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Acabo de enviar un correo importante al cliente principal.", "translation": "I just sent an important email to the main client."},
    {"lemma": "el proyecto", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Estamos trabajando en un proyecto de tecnología muy interesante.", "translation": "We are working on a very interesting tech project."},
    {"lemma": "el horario", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Mi horario de oficina es flexible los viernes por la tarde.", "translation": "My office schedule is flexible on Friday afternoons."},
    {"lemma": "el informe", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Preparé el informe de resultados trimestrales para la gerencia.", "translation": "I prepared the quarterly results report for management."},
    {"lemma": "la llamada", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Tengo una llamada importante con el cliente a las tres.", "translation": "I have an important call with the client at three."},
    {"lemma": "la cita", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Programé una cita médica para el próximo jueves.", "translation": "I scheduled a medical appointment for next Thursday."},
    {"lemma": "la empresa", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Nuestra empresa promueve la innovación continua y el trabajo en equipo.", "translation": "Our company promotes continuous innovation and teamwork."},
    {"lemma": "el compañero", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Mi compañero me ayudó a terminar la tarea a tiempo.", "translation": "My colleague helped me finish the task on time."},
    {"lemma": "el jefe", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "El jefe aprobó la propuesta de capacitación profesional.", "translation": "The boss approved the professional training proposal."},
    {"lemma": "el problema", "cefr_level": "A2", "pos": "noun", "theme": "work", "sentence": "Hemos resuelto el problema con el servidor rápidamente.", "translation": "We resolved the problem with the server quickly."},
    {"lemma": "organizar", "cefr_level": "A2", "pos": "verb", "theme": "work", "sentence": "Debo organizar las tareas pendientes de la semana.", "translation": "I must organize the pending tasks for the week."},
    {"lemma": "desarrollar", "cefr_level": "A2", "pos": "verb", "theme": "work", "sentence": "Nuestro equipo busca desarrollar soluciones prácticas y escalables.", "translation": "Our team seeks to develop practical and scalable solutions."},
    {"lemma": "revisar", "cefr_level": "A2", "pos": "verb", "theme": "work", "sentence": "Voy a revisar los documentos antes de la presentación final.", "translation": "I will review the documents before the final presentation."},
    {"lemma": "enviar", "cefr_level": "A2", "pos": "verb", "theme": "work", "sentence": "¿Puedes enviar los archivos adjuntos antes del mediodía?", "translation": "Can you send the attached files before noon?"},
    {"lemma": "terminar", "cefr_level": "A2", "pos": "verb", "theme": "work", "sentence": "Espero terminar la presentación antes de las cinco.", "translation": "I hope to finish the presentation before five."},

    # -------------------------------------------------------------
    # A2 - Shopping, Leisure & Social Life
    # -------------------------------------------------------------
    {"lemma": "la tienda", "cefr_level": "A2", "pos": "noun", "theme": "shopping", "sentence": "Esa tienda de ropa tiene descuentos excelentes este mes.", "translation": "That clothing store has excellent discounts this month."},
    {"lemma": "el precio", "cefr_level": "A2", "pos": "noun", "theme": "shopping", "sentence": "¿Cuál es el precio final con los impuestos incluidos?", "translation": "What is the final price with taxes included?"},
    {"lemma": "el regalo", "cefr_level": "A2", "pos": "noun", "theme": "social", "sentence": "Buscamos un regalo especial para el aniversario de bodas.", "translation": "We are looking for a special gift for the wedding anniversary."},
    {"lemma": "la fiesta", "cefr_level": "A2", "pos": "noun", "theme": "social", "sentence": "Organizamos una fiesta sorpresa para celebrar su cumpleaños.", "translation": "We organized a surprise party to celebrate their birthday."},
    {"lemma": "la película", "cefr_level": "A2", "pos": "noun", "theme": "social", "sentence": "Vimos una película española muy entretenida en el cine.", "translation": "We watched a very entertaining Spanish movie at the cinema."},
    {"lemma": "el fin de semana", "cefr_level": "A2", "pos": "phrase", "theme": "social", "sentence": "El fin de semana planeamos salir al campo a caminar.", "translation": "On the weekend we plan to go out to the countryside for a walk."},
    {"lemma": "el restaurante", "cefr_level": "A2", "pos": "noun", "theme": "social", "sentence": "Ese restaurante sirve mariscos frescos y tapas típicas.", "translation": "That restaurant serves fresh seafood and typical tapas."},
    {"lemma": "comprar", "cefr_level": "A2", "pos": "verb", "theme": "shopping", "sentence": "Quiero comprar algunos recuerdos típicos para mis amigos.", "translation": "I want to buy some typical souvenirs for my friends."},
    {"lemma": "visitar", "cefr_level": "A2", "pos": "verb", "theme": "travel", "sentence": "El fin de semana planeamos visitar el museo de arte moderno.", "translation": "This weekend we plan to visit the modern art museum."},
    {"lemma": "invitar", "cefr_level": "A2", "pos": "verb", "theme": "social", "sentence": "Quiero invitar a mis compañeros de trabajo a cenar.", "translation": "I want to invite my coworkers to dinner."},
    {"lemma": "celebrar", "cefr_level": "A2", "pos": "verb", "theme": "social", "sentence": "Vamos a celebrar nuestro aniversario en un restaurante del centro.", "translation": "We are going to celebrate our anniversary at a downtown restaurant."},
    {"lemma": "conocer", "cefr_level": "A2", "pos": "verb", "theme": "social", "sentence": "Es un placer conocer la cultura y las tradiciones locales.", "translation": "It is a pleasure to get to know local culture and traditions."},

    # -------------------------------------------------------------
    # A2 - Health & Well-being
    # -------------------------------------------------------------
    {"lemma": "el médico", "cefr_level": "A2", "pos": "noun", "theme": "health", "sentence": "El médico me recomendó beber abundante agua y descansar.", "translation": "The doctor recommended that I drink plenty of water and rest."},
    {"lemma": "la farmacia", "cefr_level": "A2", "pos": "noun", "theme": "health", "sentence": "¿Hay alguna farmacia de turno abierta por aquí cerca?", "translation": "Is there an on-duty pharmacy open nearby?"},
    {"lemma": "la medicina", "cefr_level": "A2", "pos": "noun", "theme": "health", "sentence": "Tomo la medicina prescrita dos veces al día.", "translation": "I take the prescribed medicine twice a day."},
    {"lemma": "cansado", "cefr_level": "A2", "pos": "adj", "theme": "health", "sentence": "Me siento un poco cansado después de un largo viaje en tren.", "translation": "I feel a bit tired after a long train ride."},
    {"lemma": "descansar", "cefr_level": "A2", "pos": "verb", "theme": "health", "sentence": "Necesito descansar un momento antes de continuar la caminata.", "translation": "I need to rest a moment before continuing the walk."},

    # -------------------------------------------------------------
    # B1 - Professional Collaboration & Discussion
    # -------------------------------------------------------------
    {"lemma": "la sugerencia", "cefr_level": "B1", "pos": "noun", "theme": "work", "sentence": "Agradezco tu valiosa sugerencia para optimizar el proceso.", "translation": "I appreciate your valuable suggestion to optimize the process."},
    {"lemma": "el presupuesto", "cefr_level": "B1", "pos": "noun", "theme": "work", "sentence": "Tenemos que ajustar el presupuesto trimestral con cautela.", "translation": "We have to adjust the quarterly budget cautiously."},
    {"lemma": "la propuesta", "cefr_level": "B1", "pos": "noun", "theme": "work", "sentence": "Presentamos una propuesta innovadora a los directores del proyecto.", "translation": "We presented an innovative proposal to the project directors."},
    {"lemma": "el acuerdo", "cefr_level": "B1", "pos": "noun", "theme": "work", "sentence": "Ambas partes llegaron a un acuerdo beneficioso tras la reunión.", "translation": "Both parties reached a beneficial agreement after the meeting."},
    {"lemma": "la ventaja", "cefr_level": "B1", "pos": "noun", "theme": "work", "sentence": "Una gran ventaja de este sistema es su alta flexibilidad técnica.", "translation": "A major advantage of this system is its high technical flexibility."},
    {"lemma": "la desventaja", "cefr_level": "B1", "pos": "noun", "theme": "work", "sentence": "Debemos evaluar la desventaja económica de un retraso.", "translation": "We must evaluate the economic disadvantage of a delay."},
    {"lemma": "la experiencia", "cefr_level": "B1", "pos": "noun", "theme": "work", "sentence": "Tiene una amplia experiencia en gestión de equipos multiculturales.", "translation": "He has extensive experience in managing multicultural teams."},
    {"lemma": "acordar", "cefr_level": "B1", "pos": "verb", "theme": "work", "sentence": "Acordamos posponer la presentación hasta el próximo mes.", "translation": "We agreed to postpone the presentation until next month."},
    {"lemma": "mantener", "cefr_level": "B1", "pos": "verb", "theme": "work", "sentence": "Es fundamental mantener una comunicación fluida entre departamentos.", "translation": "It is essential to maintain fluent communication between departments."},
    {"lemma": "solicitar", "cefr_level": "B1", "pos": "verb", "theme": "work", "sentence": "Quisiera solicitar información detallada sobre los nuevos requisitos.", "translation": "I would like to request detailed information regarding the new requirements."},
    {"lemma": "negociar", "cefr_level": "B1", "pos": "verb", "theme": "work", "sentence": "Logramos negociar condiciones favorables para el contrato anual.", "translation": "We managed to negotiate favorable terms for the annual contract."},
    {"lemma": "resolver", "cefr_level": "B1", "pos": "verb", "theme": "work", "sentence": "Pudimos resolver las diferencias con un diálogo constructivo.", "translation": "We were able to resolve differences through constructive dialogue."},

    # -------------------------------------------------------------
    # B1 - Travel, Culture & Nuanced Exchange
    # -------------------------------------------------------------
    {"lemma": "recomendar", "cefr_level": "B1", "pos": "verb", "theme": "travel", "sentence": "¿Qué restaurante tradicional me recomendarías para cenar esta noche?", "translation": "What traditional restaurant would you recommend to me for dinner tonight?"},
    {"lemma": "el recorrido", "cefr_level": "B1", "pos": "noun", "theme": "travel", "sentence": "Hicimos un recorrido guiado por el casco antiguo de la ciudad.", "translation": "We took a guided tour through the old town of the city."},
    {"lemma": "el alojamiento", "cefr_level": "B1", "pos": "noun", "theme": "travel", "sentence": "Buscamos un alojamiento céntrico, cómodo y bien comunicado.", "translation": "We are looking for central, comfortable, and well-connected accommodation."},
    {"lemma": "la costumbre", "cefr_level": "B1", "pos": "noun", "theme": "family", "sentence": "Es una costumbre familiar reunirnos para celebrar los cumpleaños.", "translation": "It is a family custom to gather to celebrate birthdays."},
    {"lemma": "la tradición", "cefr_level": "B1", "pos": "noun", "theme": "travel", "sentence": "Esta fiesta folclórica es una tradición que data de siglos.", "translation": "This folk festival is a tradition dating back centuries."},
    {"lemma": "el paisaje", "cefr_level": "B1", "pos": "noun", "theme": "travel", "sentence": "El paisaje montañoso desde el mirador es verdaderamente impresionante.", "translation": "The mountainous landscape from the viewpoint is truly impressive."},
    {"lemma": "la conversación", "cefr_level": "B1", "pos": "noun", "theme": "social", "sentence": "Tuvimos una conversación muy enriquecedora sobre nuestras metas.", "translation": "We had a very enriching conversation about our goals."},
    {"lemma": "la opinión", "cefr_level": "B1", "pos": "noun", "theme": "social", "sentence": "En mi opinión, es crucial fomentar el aprendizaje activo.", "translation": "In my opinion, it is crucial to foster active learning."},
    {"lemma": "la oportunidad", "cefr_level": "B1", "pos": "noun", "theme": "social", "sentence": "Aprovechamos cada oportunidad para practicar el idioma.", "translation": "We take advantage of every opportunity to practice the language."},
    {"lemma": "descubrir", "cefr_level": "B1", "pos": "verb", "theme": "travel", "sentence": "Durante el viaje logramos descubrir rincones históricos poco conocidos.", "translation": "During the trip we discovered little-known historic spots."},
    {"lemma": "explicar", "cefr_level": "B1", "pos": "verb", "theme": "work", "sentence": "¿Podrías explicar el funcionamiento de este nuevo módulo?", "translation": "Could you explain how this new module works?"},

    # -------------------------------------------------------------
    # B2 - Advanced Fluency, Strategic & Complex Expression
    # -------------------------------------------------------------
    {"lemma": "el planteamiento", "cefr_level": "B2", "pos": "noun", "theme": "work", "sentence": "Su planteamiento estratégico permitió superar los desafíos comerciales.", "translation": "Their strategic approach allowed overcoming commercial challenges."},
    {"lemma": "desempeñar", "cefr_level": "B2", "pos": "verb", "theme": "work", "sentence": "Desempeña un rol imprescindible en la toma de decisiones corporativas.", "translation": "Plays an indispensable role in corporate decision making."},
    {"lemma": "la repercusión", "cefr_level": "B2", "pos": "noun", "theme": "work", "sentence": "La medida legislativa tuvo una notable repercusión en el sector.", "translation": "The legislative measure had a notable impact on the sector."},
    {"lemma": "garantizar", "cefr_level": "B2", "pos": "verb", "theme": "travel", "sentence": "La agencia se compromete a garantizar la máxima seguridad durante la expedición.", "translation": "The agency commits to guaranteeing maximum safety during the expedition."},
    {"lemma": "la perspectiva", "cefr_level": "B2", "pos": "noun", "theme": "work", "sentence": "Desde mi perspectiva profesional, este enfoque maximiza el impacto formativo.", "translation": "From my professional perspective, this approach maximizes educational impact."},
    {"lemma": "el enfoque", "cefr_level": "B2", "pos": "noun", "theme": "work", "sentence": "Adoptamos un enfoque interdisciplinario para abordar la problemática compleja.", "translation": "We adopted an interdisciplinary approach to address the complex problem."},
    {"lemma": "optimizar", "cefr_level": "B2", "pos": "verb", "theme": "work", "sentence": "Buscamos optimizar los algoritmos de recuperación léxica en tiempo real.", "translation": "We aim to optimize lexical retrieval algorithms in real time."},
    {"lemma": "fomentar", "cefr_level": "B2", "pos": "verb", "theme": "social", "sentence": "Es prioritario fomentar la retención nemotécnica a través de intervalos adaptativos.", "translation": "It is a priority to foster mnemonic retention through adaptive intervals."},
    {"lemma": "el matiz", "cefr_level": "B2", "pos": "noun", "theme": "social", "sentence": "Captar cada matiz semántico en una conversación fluida enriquece la competencia bilingüe.", "translation": "Capturing each semantic nuance in fluent conversation enriches bilingual proficiency."},
    {"lemma": "superar", "cefr_level": "B2", "pos": "verb", "theme": "work", "sentence": "Logramos superar las barreras idiomáticas mediante la práctica conversacional contextualizada.", "translation": "We managed to overcome language barriers through contextualized conversational practice."}
]

def seed_vocab(reset: bool = False):
    from app.rag.vocab_store import vocab_store
    print(f"[Seed] Seeding {len(VOCAB_DATA)} leveled vocabulary items into vocab_bank (reset={reset})...")
    
    if reset and vocab_store.is_chroma_ready and vocab_store.collection:
        try:
            # Recreate or clear collection
            vocab_store.chroma_client.delete_collection("vocab_bank")
            vocab_store.collection = vocab_store.chroma_client.create_collection(
                name="vocab_bank",
                metadata={"description": "Static leveled reference CEFR vocabulary bank"}
            )
            vocab_store.in_memory_docs = []
            print("[Seed] Successfully reset ChromaDB collection 'vocab_bank'.")
        except Exception as e:
            print(f"[Seed] Note during collection reset: {e}")

    docs = [item["sentence"] for item in VOCAB_DATA]
    metas = [
        {
            "lemma": item["lemma"],
            "cefr_level": item["cefr_level"],
            "pos": item["pos"],
            "theme": item["theme"],
            "translation": item.get("translation", "")
        }
        for item in VOCAB_DATA
    ]
    ids = [normalize_vocab_id(item["lemma"], item["cefr_level"]) for item in VOCAB_DATA]

    vocab_store.add_documents(documents=docs, metadatas=metas, ids=ids)
    print(f"[Seed] Successfully seeded {len(VOCAB_DATA)} CEFR vocabulary examples into vocab_bank.")

if __name__ == "__main__":
    seed_vocab(reset=True)
