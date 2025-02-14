import logging
import pathlib
from typing import Any
import json
from datetime import datetime
import os

from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders.epub import UnstructuredEPubLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
from langchain_core.documents import Document
from streamlit.logger import get_logger

logging.basicConfig(encoding="utf-8", level=logging.INFO)
LOGGER = get_logger(__name__)


def init_memory():
    """Initialize the memory for contextual conversation."""
    return ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key="answer"
    )


LOGGER.info("init memory")
MEMORY = init_memory()


def save_chat_messages(messages):
    """
    Guarda los mensajes de la conversación en un archivo JSON con timestamp.
    
    Args:
        messages (list): Lista de mensajes de la conversación
    """
    # Crear directorio de logs si no existe
    log_dir = "chat_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Generar nombre de archivo con fecha y hora actual
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(log_dir, f"chat_log_{timestamp}.json")
    
    # Preparar datos para guardar
    chat_log = []
    for msg in messages:
        chat_log.append({
            "type": msg.type,
            "content": msg.content,
            "timestamp": datetime.now().isoformat()
        })
    
    # Guardar en archivo JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(chat_log, f, ensure_ascii=False, indent=4)
    
    return filename


class EpubReader(UnstructuredEPubLoader):
    def __init__(self, file_path: str | list[str], **unstructured_kwargs: Any):
        super().__init__(file_path, **unstructured_kwargs, mode="elements", strategy="fast")


class DocumentLoaderException(Exception):
    pass


class DocumentLoader(object):
    """Loads in a document with a supported extension."""

    supported_extensions = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".epub": EpubReader,
        ".docx": UnstructuredWordDocumentLoader,
        ".doc": UnstructuredWordDocumentLoader,
    }


def load_document(temp_filepath: str) -> list[Document]:
    """Load a file and return it as a list of documents."""
    ext = pathlib.Path(temp_filepath).suffix
    loader = DocumentLoader.supported_extensions.get(ext)
    if not loader:
        raise DocumentLoaderException(
            f"Invalid extension type {ext}, cannot load this type of file"
        )

    loaded = loader(temp_filepath)
    docs = loaded.load()
    logging.info(docs)
    return docs