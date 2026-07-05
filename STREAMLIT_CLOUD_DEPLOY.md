# Publicação no Streamlit Cloud

## Pré-requisitos

- Repositório Git com este projeto
- Conta no Streamlit Cloud
- Projeto Supabase já configurado

## Arquivo principal

- Main file path: `app.py`

## Secrets no Streamlit Cloud

No painel da app no Streamlit Cloud, abrir:

- `App settings`
- `Secrets`

Copiar os valores do exemplo em `.streamlit/secrets.toml.example` e preencher:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-chave-anon"
SUPABASE_SERVICE_ROLE_KEY = "sua-service-role-key"
GOOGLE_CSE_API_KEY = ""
GOOGLE_CSE_CX = ""
SERPER_API_KEY = ""
SERPAPI_API_KEY = ""
GROQ_API_KEY = ""
TAVILY_API_KEY = ""
```

## Deploy

1. Subir o projeto para GitHub
2. No Streamlit Cloud, clicar em `New app`
3. Selecionar o repositório
4. Definir `Main file path` como `app.py`
5. Guardar os `Secrets`
6. Fazer o deploy

## Banco de dados

Se o banco atual ainda não tiver os campos de contacto, aplicar também:

- `database/add_contatos_candidatos.sql`
- `database/fix_rls_funil.sql`

## Observações

- O projeto já está preparado para ler segredos tanto de `.env` local como de `st.secrets`
- Não publicar `.env` nem `.streamlit/secrets.toml` no repositório
