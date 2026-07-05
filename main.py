import os

from src.sourcing import MotorBuscaSourcing
from src.supabase_client import NucleoSupabase


def autenticar_recrutador(db: NucleoSupabase):
    email = os.getenv("RECRUTADOR_EMAIL")
    senha = os.getenv("RECRUTADOR_SENHA")
    if not email or not senha:
        return False, "RECRUTADOR_EMAIL e RECRUTADOR_SENHA não configurados no .env."

    autenticado = db.login(email, senha)
    if not autenticado:
        return False, db.ultimo_erro_login or "Falha de autenticação no Supabase."
    return True, None


def rodar_pipeline_recrutamento():
    print("🚀 Iniciando Motor de Busca de Candidatos Reais...")

    motor = MotorBuscaSourcing()
    db = NucleoSupabase()

    cargo = "Médico do Trabalho"
    local = "São Paulo"
    nrs = ["NR-7"]
    senioridade = "Sênior"
    fontes = ["linkedin", "lattes", "doctoralia", "bancos_curriculos"]

    query = motor.construir_query_segura(
        cargo=cargo,
        local=local,
        nrs=nrs,
        senioridade=senioridade,
        fontes_selecionadas=fontes,
    )
    print(f"🔍 Buscando com query:\n{query}\n")

    if not motor.busca_api_configurada():
        print(
            "⚠️ Nenhum provedor de busca está configurado. Configure no .env pelo menos "
            "SERPER_API_KEY, SERPAPI_API_KEY ou o legado GOOGLE_CSE_API_KEY + GOOGLE_CSE_CX."
        )
        return

    print(f"🌐 Provedores ativos: {', '.join(motor.descrever_provedores_busca())}")

    cargo_id = motor.resolver_id_cargo(cargo)
    resultados = motor.buscar_resultados_higienizados(
        id_cargo=cargo_id,
        local=local,
        senioridade=senioridade,
        fontes_selecionadas=fontes,
        inclusoes_extras=nrs,
        limite_por_fonte=5,
    )

    print(f"📦 Resultados brutos elegíveis: {len(resultados)}")

    candidatos_validos = [item for item in resultados if motor.candidato_tem_contato_ou_registro(item)]
    print(f"✅ Resultados com contacto ou registro profissional: {len(candidatos_validos)}")

    if not candidatos_validos:
        print("ℹ️ Nenhum candidato validado com contacto ou CRM/COREN/CREA foi encontrado.")
        return

    autenticado, erro_auth = autenticar_recrutador(db)
    if not autenticado:
        print(f"⚠️ Modo apenas leitura. {erro_auth}")
        print("ℹ️ Configure também VAGA_ID_PADRAO no .env para inserir candidatos no pipeline.")
        for candidato in candidatos_validos[:10]:
            print(f"- {candidato['nome']} | {candidato['fonte_nome']} | {candidato['url_perfil']}")
        return

    vaga_id = os.getenv("VAGA_ID_PADRAO")
    if not vaga_id:
        print("⚠️ VAGA_ID_PADRAO não configurado no .env. Não é possível gravar no pipeline.")
        for candidato in candidatos_validos[:10]:
            print(f"- {candidato['nome']} | {candidato['fonte_nome']} | {candidato['url_perfil']}")
        return

    inseridos = 0
    for candidato in candidatos_validos:
        dados_perfil = {
            "nome": candidato["nome"],
            "titulo_profissional": candidato["titulo_profissional"],
            "empresa_atual": candidato["empresa_atual"],
            "localizacao": candidato["localizacao"],
            "url_perfil": candidato["url_perfil"],
            "fonte_origem": candidato["fonte_origem"],
        }
        try:
            db.salvar_candidato_pipeline(vaga_id, dados_perfil, nrs)
            inseridos += 1
            print(
                f"✔ Inserido: {candidato['nome']} | "
                f"{candidato.get('registro_profissional') or candidato.get('email') or candidato.get('telefone')}"
            )
        except Exception as erro:
            print(f"✖ Falha ao inserir {candidato['nome']}: {erro}")

    print(f"\n✅ Pipeline executado com sucesso. Total inserido: {inseridos}")
    print("🔎 Verifique o seu painel Supabase.")


if __name__ == "__main__":
    rodar_pipeline_recrutamento()
