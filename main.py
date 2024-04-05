import streamlit as st
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from dotenv import load_dotenv
import markdown
import pdfkit
from datetime import datetime
import requests
from pprint import pprint
import os
import shutil
import streamlit_ext as ste

load_dotenv()
client = OpenAI()
st.set_page_config(page_title='IA Documentos de Seguridad', page_icon = '🤖', layout = 'wide', initial_sidebar_state = 'auto')


def wipe_out_directory(directory_path):
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

    else:
        print(f"The directory {directory_path} does not exist.")

def get_country_emoji(language):

            language_to_emoji = {
                'Spanish': '🇪🇸', # Spain
                'Portuguese': '🇵🇹', # Portugal
                'English': '🇬🇧', # United Kingdom
                'German': '🇩🇪', # Germany
                'French': '🇫🇷', # France
                'Italian': '🇮🇹', # Italy
                'Polish': '🇵🇱', # Poland
                'Russian': '🇷🇺', # Russia
            }

            return language_to_emoji.get(language, '')

def create_button(filename):

        language = filename.split('-')[1].split('.')[0]
        country_emoji = get_country_emoji(language)

        with open(filename, "rb") as fp:
            with st.sidebar:
                ste.download_button(
                    f"Descargar en {country_emoji}",
                    fp,
                    f"Descargar_en_{country_emoji}.pdf",
                )


wipe_out_directory('generated_documents')

def generate_response_stream(prev_prompt):
    response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "Eres un asistente util experto en crear documentos de seguridad para productos online."},
        {"role": "user", "content": str(prev_prompt)}],
    stream=True,
    max_tokens=1000)
    full_text = ""
    for chunk in response:
 
        if chunk.choices[0].delta.content is not None:
            stream = chunk.choices[0].delta.content
            yield stream
    
    return full_text

def generate_response_gpt3(prev_prompt):
    response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": str(prev_prompt)}],
    max_tokens=1000
)
    selection = response.choices[0].message.content
    return selection

@st.cache_data
def get_product(product_url):
   payload = {
      'source': 'amazon',
      'user_agent_type': 'desktop',
      'render': 'html',
      'parse': True,
      'url': product_url}
   
   response = requests.request(
        'POST',
        'https://realtime.oxylabs.io/v1/queries',
        auth=(os.getenv('USER_NAME_OXYLABS'), os.getenv('PASSWORD_OXYLABS')), 
        json=payload,
   )

   pprint(response.json())
   return response.json()

def parse_json(json_data):
    result = json_data["results"][0]
    asin = result["content"]["asin"]
    brand = result["content"]["brand"]
    product_name = result["content"]["product_name"]
    bulletpoints = result["content"]["bullet_points"]

    parsed_json = {"Asin": asin,
                   "Marca": brand,
                   "Nombre de Producto": product_name,
                   "Información relevante": bulletpoints}
    return parsed_json

prompt = ''' 

Basado en la siguiente información, genera una ficha de seguridad sobre el uso de este producto.

Son artículos como aspersores de riego, programadores de riego, o pistolas de riego. Fabricados en plástico y/o metal.

La ficha debe seguir la normativa GPSR (General Product Safety Regulation) impuesta por Amazon al igual que otro tipo de regulaciones.

La ficha, debe seguir la siguiente estructura:

- Descripción general del producto: Incluirá una breve descripción del programador de riego, destacando su propósito principal (por ejemplo, automatizar el riego de jardines).
- Materiales de fabricación: Se detallarán los materiales específicos utilizados, como tipos de plástico o metal, considerando su impacto en la seguridad y durabilidad.
- Instrucciones de uso: Explicación clara de cómo instalar y programar el dispositivo, incluyendo cualquier precaución para evitar daños al producto o al usuario.
- Mantenimiento y cuidados: Consejos para la limpieza, almacenamiento y manejo adecuado del programador de riego para asegurar su larga vida útil.
- Medidas de seguridad: Advertencias sobre los riesgos potenciales (como el riesgo de daños por agua o eléctricos) y cómo mitigarlos.
- Disposición al final de su vida útil: Información sobre cómo deshacerse o reciclar el producto de manera responsable.

Aquí información del producto. Ten en cuenta que el texto a sido extraído directamente de la página web, por lo que estará mal escrito:
'''

def return_html_language(language, brand):

    created_portuguese = "Criado em:"
    created_english = "Created on:"
    created_german = "Erstellt am:"
    created_french = "Créé le:"
    created_italian = "Creato il:"
    created_polish = "Utworzono:"
    created_russian = "Создано:"

    footer_html_portuguese = """
        <footer>
            <!-- Seu conteúdo do rodapé -->
            <p>Marca registrada: {brand} <br> Fabricante: Altadex S.A. <br> Endereço: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. Espanha. <br> www.altadex.com - info@altadex.com <br> Número de contato: +34 918457676 <br> </p>
        </footer>
    </body>
    </html>
    """.format(brand=brand)

    footer_html_english = """
            <footer>
                <!-- Your footer content -->
                <p>Trademark: {brand} <br> Manufacturer: Altadex S.A. <br> Address: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. Spain. <br> www.altadex.com - info@altadex.com <br> Contact number: +34 918457676 <br> </p>
            </footer>
        </body>
        </html>
        """.format(brand=brand)

    footer_html_german = """
            <footer>
                <!-- Ihr Footer-Inhalt -->
                <p>Warenzeichen:{brand} <br> Hersteller: Altadex S.A. <br> Adresse: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. Spanien. <br> www.altadex.com - info@altadex.com <br> Kontakt Nummer: +34 918457676 <br> </p>
            </footer>
        </body>
        </html> 
    """.format(brand=brand)

    footer_html_french = """
            <footer>
                <!-- Votre contenu de pied de page -->
                <p>Marque déposée: {brand} <br> Fabricant: Altadex S.A. <br> Adresse: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. Espagne. <br> www.altadex.com - info@altadex.com <br> Numéro de contact: +34 918457676 <br> </p>
            </footer>
        </body>
        </html>
        """.format(brand=brand)

    footer_html_italian = """
            <footer>
                <!-- Il tuo contenuto del piè di pagina -->
                <p>Marchio registrato: {brand} <br> Produttore: Altadex S.A. <br> Indirizzo: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. Spagna. <br> www.altadex.com - info@altadex.com <br> Numero di contatto: +34 918457676 <br> </p>
            </footer>
        </body>
        </html>
        """.format(brand=brand)

    footer_html_polish = """
            <footer>
                <!-- Twoja treść stopki -->
                <p>Znak towarowy: {brand} <br> Producent: Altadex S.A. <br> Adres: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. Hiszpania. <br> www.altadex.com - info@altadex.com <br> Numer kontaktowy: +34 918457676 <br> </p>
            </footer>
        </body>
        </html>
    """.format(brand=brand)

    footer_html_russian = """
            <footer>
                <!-- Ваше содержимое подвала -->
                <p>Торговая марка: {brand}<br> Производитель: Altadex S.A. <br> Адрес: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. España. <br> www.altadex.com - info@altadex.com <br> Контактный номер: +34 918457676 <br> </p>
            </footer>
        </body>
        </html>
    """.format(brand=brand)
    
    if language == "Portuguese":
        footer_html = footer_html_portuguese
        created = created_portuguese
        return footer_html, created

    if language == "English":
        footer_html = footer_html_english
        created = created_english
        return footer_html, created
    
    if language == "German":
        footer_html = footer_html_german
        created = created_german
        return footer_html, created

    if language == "French":
        footer_html = footer_html_french
        created = created_french
        return footer_html, created
    
    if language == "Italian":
        footer_html = footer_html_italian
        created = created_italian
        return footer_html, created
    
    if language == "Polish":
        footer_html = footer_html_polish
        created = created_polish
        return footer_html, created
    
    if language == "Russian":
        footer_html = footer_html_russian
        created = created_russian
        return footer_html, created
    
    footer_html = """
        <footer>
            <!-- Your footer content -->
            <p>Marca registrada: {brand} <br> Fabricante: Altadex S.A. <br> Dirección: Calle Perfumería 7. 28770. Colmenar Viejo. Madrid. España. <br> www.altadex.com - info@altadex.com <br> Número de contacto: +34 918457676 <br> </p>
        </footer>
    </body>
    </html>
    """.format(brand=brand)
    created = "Fecha de creación:"
    
    return footer_html, created

def markdown_to_pdf(markdown_text, output_filename, language, brand):
    
    current_date = datetime.now().strftime("%d/%m/%Y")

    footer_html, created = return_html_language(language, brand)
    
    header_html = f""" 
<!DOCTYPE html>
<html>
<head>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
        }}
        .content {{
            min-height: 100%;
            position: relative;
            padding-bottom: 120px; /* Adjust based on footer height */
        }}
        img {{
            width: 30%;
            height: auto;
            padding-bottom: 50px;
        }}
        footer {{
            position: absolute;
            bottom: 0;
            width: 100%;
            height: 120px; /* Adjust based on your footer content */
            font-style: italic;
        }}
        .creation-date {{
            position: absolute;
            top: 0;
            right: 0;
            padding: 10px;
            font-style: italic;
            font-size:large;
        }}
    </style>
</head>
<body>
<div class="creation-date">{created} <br> {current_date}</div>
<img src="https://i.postimg.cc/DZwj5rnq/Logo-Altadex-1.png">
"""

    markdown_text_with_image = markdown_text
    

    html_text = markdown.markdown(markdown_text_with_image)

    full_html_text = header_html + html_text + footer_html

    print(full_html_text)    
    
    options = {
        'encoding': "UTF-8"
    }
    
    pdfkit.from_string(full_html_text, "generated_documents/" + output_filename, options=options)

def persist_pdf(text, product, language, brand):
    markdown_to_pdf(text, f"{product}-{language}.pdf", language, brand)
    print("PDF generated successfully in", language + ".")


def generate_other_languages(text, product, language, brand):
    text = generate_response_gpt3('Translate the following text to ' + language + '.' + 'Only output the translated text in Markdown. Make sure it has the same format as the input you will be given. Only output the mardown, dont use ´´´ for delimeters or anything. ' + 'Here the text: ' + text)
    persist_pdf(text, product, language, brand)
    return f"{product}-{language}.pdf"

def generate_all(product):
    print('Retrieving product from Oxylabs...')
    json_data = get_product(product)
    parsed_json_data = parse_json(json_data)
    pprint(parsed_json_data)
    
    print('\nRetrieved product! Passing to GPT.')
    product = parsed_json_data["Asin"]
    brand = parsed_json_data["Marca"]
    product_description = f""" 
    Nombre de Producto: {parsed_json_data["Nombre de Producto"]} \n
    Marca: {parsed_json_data["Marca"]}
    Informacion de producto: {parsed_json_data["Información relevante"]} \n
 """
    
    executor = ThreadPoolExecutor(10)
    full_text = generate_response_stream(prompt + product_description)

    persist_pdf(full_text, product, 'Spanish', brand)

    futures = []
    languages = ['Portuguese', 'English', 'German', 'French', 'Italian', 'Polish', 'Russian']
    for lang in languages:
        future = executor.submit(generate_other_languages, full_text, product, lang, brand)
        futures.append(future)

    print('\nLoading documents in other languages...')


def main():
    title = st.header("Generador de Fichas de Seguridad Amazon")
    subtitle = st.write("""👋 Bienvenido al Generador de Fichas de Seguridad de Amazon de Altadex S.A. 
                        \n Este producto emplea Inteligencia Artificial para generar documentos de seguridad a escala. Inserte el <URL de Amazon> de un producto y recibirá como resultado un documento de seguridad. Tiene la opción de traducirlo en Español, Inglés, Francés, Portugés, Polaco y Ruso bajo el formato correspondiente.""")
    input_amazon_url = st.text_input("Url de Amazon (Obligatorio)")
    input_additional_information = st.text_area("Información Adicional (Opcional)")
    generate_button = st.button("Generar documentos")
    sidebar_title = st.sidebar.subheader("Documentos traducidos")
    sidebar_no_doc = st.sidebar.caption("No hay documentos disponible en este momento. Inserte un URL de amazon y genere la documentación pertinente.")

    if generate_button and not input_amazon_url:
        st.warning("Tiene que introducir un link de amazon un 'Url de Amazon' para proseguir.", icon="⚠️")

    if generate_button and input_amazon_url:
        if input_additional_information != None:
            prompt_addition = None
        else:
            prompt_addition = input_additional_information

        st.text("")
        st.text("")
        text_container = st.container()
        with text_container.status('Generando documento base...'):
            st.text('Extrayendo producto de Amazon...')
            try:
                json_data = get_product(input_amazon_url)
                parsed_json_data = parse_json(json_data)
                pprint(parsed_json_data)
            except Exception as e:
                text_container.warning('Ha habido un error al extraer el producto. Pruebe de nuevo porfavor.', icon='🚨')
            
            st.text('\nProducto extraído! Pasando a generación con IA.')
            product = parsed_json_data["Asin"]
            brand = parsed_json_data["Marca"]
            product_description = f""" 
            Nombre de Producto: {parsed_json_data["Nombre de Producto"]} \n
            Marca: {parsed_json_data["Marca"]}
            Informacion de producto: {parsed_json_data["Información relevante"]} \n
        """
            st.text('\nGenerando texto...')
            executor = ThreadPoolExecutor(10)
            text_container.text("")
            full_text = text_container.write_stream(generate_response_stream(prompt + product_description + prompt_addition))
            
            persist_pdf(full_text, product, 'Spanish', brand)
            sidebar_doc = st.sidebar.caption("Encontrará en la siguiente sección todos los documentos de un producto traducidos en acorde. Espere unos segundos a que todos esten listos.")
            st.text('')
            create_button("generated_documents/" + f"{product}-Spanish.pdf")
            st.text('\nDocumento generado en Español...')
            st.text('\nGenerado en otros idiomas...')
        
            with st.sidebar:
                futures = []
                languages = ['Portuguese', 'English', 'German', 'French', 'Italian', 'Polish', 'Russian']
                for lang in languages:
                    future = executor.submit(generate_other_languages, full_text, product, lang, brand)
                    futures.append(future)

                sidebar_no_doc.empty()
                for future in futures:
                    language_filename = future.result()
                    create_button("generated_documents/" + language_filename)

if __name__ == "__main__":
    main()