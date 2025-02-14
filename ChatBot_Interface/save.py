import streamlit as st
from streamlit.external.langchain import StreamlitCallbackHandler

from chat_with_documents import configure_retrieval_chain
from utils import LOGGER, MEMORY, DocumentLoader, save_chat_messages

#Configuración de la página
LOGGER.info("Show title")
st.set_page_config(page_title="Soporte: Arduino en parques", page_icon="📟")
st.title("📟Soporte: Arduino en parques")

# Colores predeterminados
DEFAULT_BACKGROUND_COLOR = "#2e302e"
DEFAULT_TEXT_COLOR = "#FFFFFF"
DEFAULT_SIDEBAR_BG_COLOR = "#057195"
DEFAULT_SIDEBAR_TEXT_COLOR = "#000000"

# Aplicar estilos predeterminados al cargar la página
custom_style = f"""
    <style>
        .stApp {{
            background-color: {DEFAULT_BACKGROUND_COLOR};
            color: {DEFAULT_TEXT_COLOR};
        }}
        .stSidebar {{
            background-color: {DEFAULT_SIDEBAR_BG_COLOR};
            color: {DEFAULT_SIDEBAR_TEXT_COLOR};
        }}
    </style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# Verificación de contraseña para acceder al panel de personalización
password_correct = False
if "password_entered" not in st.session_state:
    st.session_state.password_entered = False

if not st.session_state.password_entered:
    password_input = st.sidebar.text_input("Ingrese la contraseña para personalizar", type="password")
    stored_password = st.secrets.get("customization_password", None)

    if stored_password is None:
        st.sidebar.error("Error: La contraseña no está configurada en secrets.toml")
    elif password_input == stored_password:
        st.session_state.password_entered = True
        st.sidebar.success("Acceso concedido")
    elif password_input:
        st.sidebar.error("Contraseña incorrecta")

# Si el usuario ingresó la contraseña, permitir personalización
if st.session_state.password_entered:
    with st.sidebar.expander("🎨 Personaliza la interfaz"):
        background_color = st.color_picker("Color de fondo", DEFAULT_BACKGROUND_COLOR)
        text_color = st.color_picker("Color del texto", DEFAULT_TEXT_COLOR)
        sidebar_bg_color = st.color_picker("Color de fondo del Sidebar", DEFAULT_SIDEBAR_BG_COLOR)
        sidebar_text_color = st.color_picker("Color del texto del Sidebar", DEFAULT_SIDEBAR_TEXT_COLOR)

    # Aplicar los colores seleccionados por el usuario
    custom_style = f"""
        <style>
            .stApp {{
                background-color: {background_color};
                color: {text_color};
            }}
            .stSidebar {{
                background-color: {sidebar_bg_color};
                color: {sidebar_text_color};
            }}
        </style>
    """
    st.markdown(custom_style, unsafe_allow_html=True)


# Carga de archivos
LOGGER.info("Upload files")
uploaded_files = st.sidebar.file_uploader(
    label="Upload files",
    type=list(DocumentLoader.supported_extensions.keys()),
    accept_multiple_files=True,
)
if not uploaded_files:
    st.info("Please upload documents to continue.")
    st.stop()

# Configuración adicional
use_compression = st.checkbox("compression", value=False)
use_flare = st.checkbox("flare", value=False)
use_moderation = st.checkbox("moderation", value=False)

LOGGER.info("Configure chain")
CONV_CHAIN = configure_retrieval_chain(
    uploaded_files,
    use_compression=use_compression,
    use_flare=use_flare,
    use_moderation=use_moderation,
)

# Botón para limpiar el historial
LOGGER.info("Clear button")
if st.sidebar.button("Clear message history"):
    MEMORY.chat_memory.clear()

# Botón para guardar el historial del chat
if st.sidebar.button("Guardar historial de chat"):
    try:
        filename = save_chat_messages(MEMORY.chat_memory.messages)
        st.sidebar.success(f"Chat guardado en {filename}")
    except Exception as e:
        st.sidebar.error(f"Error al guardar el chat: {e}")

# Interfaz de chat
avatars = {"human": "user", "ai": "assistant"}
if len(MEMORY.chat_memory.messages) == 0:
    st.chat_message("assistant").markdown("Ask me anything!")

for msg in MEMORY.chat_memory.messages:
    st.chat_message(avatars[msg.type]).write(msg.content)

# Entrada del usuario
LOGGER.info("Chat interface")
container = st.container()
if user_query := st.chat_input(placeholder="Give me 3 keywords for what you have right now"):
    st.chat_message("user").write(user_query)
    stream_handler = StreamlitCallbackHandler(container)
    with st.chat_message("assistant"):
        params = (
            {"user_input": user_query}
            if use_flare
            else {"question": user_query, "chat_history": MEMORY.chat_memory.messages}
        )
        response = CONV_CHAIN.invoke(
            {"question": user_query, "chat_history": MEMORY.chat_memory.messages},
            callbacks=[stream_handler],
        )
        # Muestra la respuesta del chatbot
        if response:
            container.markdown(response["answer"])
