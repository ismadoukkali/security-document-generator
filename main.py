import streamlit as st
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import markdown
import pdfkit
from datetime import datetime
import requests
from pprint import pprint
import os
import shutil
import streamlit_ext as ste
import requests
from urllib3.util.retry import Retry
from pprint import pprint
import zipfile

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

def zip_all_files_in_directory(directory_path, output_zip_file):
    with zipfile.ZipFile(output_zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, directory_path))

def get_country_emoji(language):

            language_to_emoji = {
                'Spanish': '🇪🇸', # Spain
                'Portuguese': '🇵🇹', # Portugal
                'English': '🇬🇧', # United Kingdom
                'German': '🇩🇪', # Germany
                'French': '🇫🇷', # France
                'Italian': '🇮🇹', # Italy
                'Polish': '🇵🇱', # Poland
                'Turkish': '🇹🇷', # Turkey
            }

            return language_to_emoji.get(language, '')

def create_button(filename):

        file = filename.split("generated_documents/")[1]
        language = filename.split('-')[1].split('.')[0]
        country_emoji = get_country_emoji(language)

        with open(filename, "rb") as fp:
            with st.sidebar:
                ste.download_button(
                    f"Descargar en {country_emoji}",
                    fp,
                    f"{file}",
                )

def create_download_all(zip_name, product):
    with open(zip_name, "rb") as fp:
            with st.sidebar:
                ste.download_button(
                    f"Descargar todos 🌍",
                    fp,
                    f"{product}-all.zip",
                )

wipe_out_directory('generated_documents')

def generate_response_stream(prev_prompt):
    response = client.chat.completions.create(
    model="gpt-4o",
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
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": str(prev_prompt)}],
    max_tokens=1000
)
    selection = response.choices[0].message.content
    return selection

@st.cache_data
def get_product(product_url):
    session = requests.Session()

    retries = Retry(total=5,  
                    backoff_factor=1,  
                    status_forcelist=[429, 500, 502, 503, 504],  # Status codes to retry
                    allowed_methods=frozenset(['POST']))  # Allowed HTTP methods to retry

    adapter = requests.adapters.HTTPAdapter(max_retries=retries)

    session.mount('http://', adapter)
    session.mount('https://', adapter)

    payload = {
        'source': 'amazon',
        'user_agent_type': 'desktop',
        'render': 'html',
        'parse': True,
        'url': product_url
    }
    
    print(payload)

    response = session.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=('puertas_Rycjt', 'Javiisma2002='),
        json=payload,
    )

    pprint(response.json())
    return response.json()


def parse_json(json_data):
    try:
        result = json_data["results"][0]
        content = result["content"]
        
        # Extract the required fields
        asin = content.get("asin", "")
        # Try to get brand first, if not available use manufacturer
        brand = content.get("brand") or content.get("manufacturer", "")
        product_name = content.get("product_name", "")
        bulletpoints = content.get("bullet_points", "")

        parsed_json = {
            "Asin": asin,
            "Marca": brand,
            "Nombre de Producto": product_name,
            "Información relevante": bulletpoints
        }
        return parsed_json
    except KeyError as e:
        raise KeyError(f"Missing required field in JSON structure: {e}")
    except Exception as e:
        raise Exception(f"Error parsing JSON data: {e}")

prompt = ''' 

Basado en la siguiente información, genera una ficha de seguridad sobre el uso de este producto.

La ficha debe seguir la normativa GPSR (General Product Safety Regulation) impuesta por Amazon al igual que otro tipo de regulaciones.

La ficha, debe seguir la siguiente estructura:

- Descripción general del producto: Incluirá una breve descripción del programador de riego, destacando su propósito principal (por ejemplo, automatizar el riego de jardines).
- Materiales de fabricación: Se detallarán los materiales específicos utilizados, como tipos de plástico o metal, considerando su impacto en la seguridad y durabilidad.
- Instrucciones de uso: Explicación clara de cómo instalar y programar el dispositivo, incluyendo cualquier precaución para evitar daños al producto o al usuario.
- Mantenimiento y cuidados: Consejos para la limpieza, almacenamiento y manejo adecuado del programador de riego para asegurar su larga vida útil.
- Medidas de seguridad: Advertencias sobre los riesgos potenciales (como el riesgo de daños por agua o eléctricos) y cómo mitigarlos.
- Disposición al final de su vida útil: Información sobre cómo deshacerse o reciclar el producto de manera responsable.

Respondeme simplemente con la ficha de seguridad en formato 'Markdown'. No incluyas ``` al principio y final del markdown, solo dame el texto markdown.

Aquí la información del producto. Ten en cuenta que el texto a sido extraído directamente de la página web, por lo que podrá estar mal escrito:
'''

def return_html_language(language, brand):

    created_portuguese = "Criado em:"
    created_english = "Created on:"
    created_german = "Erstellt am:"
    created_french = "Créé le:"
    created_italian = "Creato il:"
    created_polish = "Utworzono:"
    created_turkish = "Oluşturuldu:"

    footer_html_portuguese = """
        <footer>
            <!-- Seu conteúdo do rodapé -->
            <p>Marca registrada: {brand} <br> Fabricante: Ejemplo S.A. <br> Endereço: Ejemplo Dirección, Madrid. Espanha. <br> www.Ejemplo.com - info@Ejemplo.com <br> Número de contato: +34 999999XXX <br> </p>
        </footer>
    </body>
    </html>
    """.format(brand=brand)

    footer_html_english = """
            <footer>
                <!-- Your footer content -->
                <p>Trademark: {brand} <br> Manufacturer: Ejemplo S.A. <br> Address: Ejemplo Dirección, Madrid. Spain. <br> www.Ejemplo.com - info@Ejemplo.com <br> Contact number: +34 999999XXX <br> </p>
            </footer>
        </body>
        </html>
        """.format(brand=brand)

    footer_html_german = """
            <footer>
                <!-- Ihr Footer-Inhalt -->
                <p>Warenzeichen:{brand} <br> Hersteller: Ejemplo S.A. <br> Adresse: Ejemplo Dirección, Madrid. Spanien. <br> www.Ejemplo.com - info@Ejemplo.com <br> Kontakt Nummer: +34 999999XXX <br> </p>
            </footer>
        </body>
        </html> 
    """.format(brand=brand)

    footer_html_french = """
            <footer>
                <!-- Votre contenu de pied de page -->
                <p>Marque déposée: {brand} <br> Fabricant: Ejemplo S.A. <br> Adresse: Ejemplo Dirección, Madrid. Espagne. <br> www.Ejemplo.com - info@Ejemplo.com <br> Numéro de contact: +34 999999XXX <br> </p>
            </footer>
        </body>
        </html>
        """.format(brand=brand)

    footer_html_italian = """
            <footer>
                <!-- Il tuo contenuto del piè di pagina -->
                <p>Marchio registrato: {brand} <br> Produttore: Ejemplo S.A. <br> Indirizzo: Ejemplo Dirección, Madrid. Spagna. <br> www.Ejemplo.com - info@Ejemplo.com <br> Numero di contatto: +34 999999XXX <br> </p>
            </footer>
        </body>
        </html>
        """.format(brand=brand)

    footer_html_polish = """
            <footer>
                <!-- Twoja treść stopki -->
                <p>Znak towarowy: {brand} <br> Producent: Ejemplo S.A. <br> Adres: Ejemplo Dirección, Madrid. Hiszpania. <br> www.Ejemplo.com - info@Ejemplo.com <br> Numer kontaktowy: +34 999999XXX <br> </p>
            </footer>
        </body>
        </html>
    """.format(brand=brand)

    footer_html_turkish = """<footer>
    <!-- Altbilginiz -->
    <p>Ticari Marka: {brand}<br> Üretici: Ejemplo S.A. <br> Adres: Ejemplo Dirección, Madrid. İspanya. <br> www.Ejemplo.com - info@Ejemplo.com <br> İletişim Numarası: +34 999999XXX <br> </p>
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
    
    if language == "Turkish":
        footer_html = footer_html_turkish
        created = created_turkish
        return footer_html, created
    
    footer_html = """
        <footer>
            <!-- Your footer content -->
            <p>Marca registrada: {brand} <br> Fabricante: Ejemplo S.A. <br> Dirección: Ejemplo Dirección, Madrid. España. <br> www.Ejemplo.com - info@Ejemplo.com <br> Número de contacto: +34 999999XXX <br> </p>
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
    <meta charset="UTF-8">
    <style>
        body, html {{
            margin: 20px;  # Set the margin around the content
            padding: 0;
            height: calc(100% - 40px);  # Subtract top and bottom margins from the height
        }}
        .content {{
            min-height: 100%;
            position: relative;
            padding-bottom: 120px;  # Adjust based on footer height
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
            height: 10px;  # Adjust based on your footer content
            font-style: italic;
        }}
        .creation-date {{
            position: absolute;
            top: 0;
            right: 0;
            padding: 10px;
            font-style: italic;
            font-size: large;
        }}
    </style>
</head>
<body>
<div class="creation-date">{created} <br> {current_date}</div>
<img src="https://i.postimg.cc/VNGph5f4/logo-3.png">
"""

### tu logo link - https://i.postimg.cc/GptYK3Zk/tulogo.png
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


def main():
    title = st.header("AmzProof - Generador de Fichas de Seguridad")
    subtitle = st.write("""👋 Bienvenido a AmzProof, el Generador de Fichas de Seguridad de Amazon de Apolo. 
                        \n Este producto emplea Inteligencia Artificial para generar documentos de seguridad a escala. Inserte el ``<URL de Amazon>`` de un producto y recibirá como resultado un documento de seguridad. Este se traducirá al Español, Inglés, Francés, Portugés, Polaco y Ruso (al igual que otros 25 idiomas).""")
    input_amazon_url = st.text_input("Url de Amazon (Obligatorio)")
    input_additional_information = st.text_area("Información Adicional (Opcional)")
    generate_button = st.button("Generar fichas de seguridad")
    sidebar_title = st.sidebar.subheader("Documentos traducidos")
    sidebar_no_doc = st.sidebar.caption("No hay documentos disponible en este momento. Inserte un URL de amazon y genere la documentación pertinente.")

    st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
    """, unsafe_allow_html=True)
                

    if generate_button and not input_amazon_url:
        st.warning("Tiene que introducir un link de amazon un 'Url de Amazon' para proseguir.", icon="⚠️")

    elif generate_button and input_amazon_url:
        if input_additional_information is None:
            prompt_addition = ""
        else:
            prompt_addition = "Incluye esta información con preferencia: " + input_additional_information

        st.text("")
        text_container = st.container()
        with text_container.status('Generando documento base...'):
            st.text('Extrayendo producto de Amazon...')
            try:
                json_data = get_product(input_amazon_url)
                parsed_json_data = parse_json(json_data)
                pprint(parsed_json_data)
            except Exception as e:
                text_container.warning('Amazon ha bloqueado la respuesta del servidor al extraer el producto. Pruebe de nuevo con el mismo link porfavor.', icon='🚨')
            
            st.text('\nProducto extraído! Pasando a generación con IA.')
            print(parsed_json_data)
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
            full_text = text_container.write_stream(generate_response_stream(prompt + prompt_addition + product_description))
            
            persist_pdf(full_text, product, 'Spanish', brand)
            sidebar_doc = st.sidebar.caption("Encontrará en la siguiente sección todos los documentos de un producto traducidos en acorde. Espere unos segundos a que todos esten listos.")
            st.text('')
            create_button("generated_documents/" + f"{product}-Spanish.pdf")
            st.text('\nDocumento generado en Español...')
            st.text('\nGenerado en otros idiomas...')
        
            with st.sidebar:
                futures = []
                languages = ['Portuguese', 'English', 'German', 'French', 'Italian', 'Polish', 'Turkish']
                for lang in languages:
                    future = executor.submit(generate_other_languages, full_text, product, lang, brand)
                    futures.append(future)

                sidebar_no_doc.empty()
                for future in futures:
                    language_filename = future.result()
                    print(language_filename)
                    create_button("generated_documents/" + language_filename)

            zip_all_files_in_directory("generated_documents", "all.zip")
            create_download_all("all.zip", product)


if __name__ == "__main__":
    main()
