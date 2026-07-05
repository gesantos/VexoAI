# VexoRH MVP Recrutamento

Aplicação em Streamlit para operação de recrutamento com:

- construtor inteligente de busca
- radar de talentos com enriquecimento
- pipeline de vagas
- automação de abordagem
- exportação do pipeline para Excel

## Executar localmente

1. Criar e preencher o ficheiro `.env`
2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. Executar:

```bash
streamlit run app.py
```

## Publicação no Streamlit Cloud

- arquivo principal: `app.py`
- secrets: usar o modelo em `.streamlit/secrets.toml.example`
- guia completo: `STREAMLIT_CLOUD_DEPLOY.md`

## Banco de dados

Se o banco já existia antes das últimas alterações, aplicar também:

- `database/fix_rls_funil.sql`
- `database/add_contatos_candidatos.sql`

## Principais ficheiros

- `app.py`
- `src/config.py`
- `src/sourcing.py`
- `src/supabase_client.py`
- `requirements.txt`
