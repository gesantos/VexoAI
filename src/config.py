import os
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


def obter_seguro(chave, padrao=None):
    valor = os.getenv(chave)
    if valor:
        return valor
    if st is not None:
        try:
            if chave in st.secrets:
                return st.secrets[chave]
        except Exception:
            pass
    return padrao


SUPABASE_URL = obter_seguro("SUPABASE_URL")
SUPABASE_ANON_KEY = obter_seguro("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = obter_seguro("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_CSE_API_KEY = obter_seguro("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_CX = obter_seguro("GOOGLE_CSE_CX")
SERPER_API_KEY = obter_seguro("SERPER_API_KEY")
SERPAPI_API_KEY = obter_seguro("SERPAPI_API_KEY")
GROQ_API_KEY = obter_seguro("GROQ_API_KEY")
TAVILY_API_KEY = obter_seguro("TAVILY_API_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Credenciais do Supabase ausentes. Configure via `.env` local ou `st.secrets` no Streamlit Cloud.")
