from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_ANON_KEY

class NucleoSupabase:
    def __init__(self):
        self.db: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        self.sessao_atual = None
        self.sessao_auth = None
        self.ultimo_erro_login = None

    def login(self, email, senha):
        self.ultimo_erro_login = None
        try:
            res = self.db.auth.sign_in_with_password({
                "email": (email or "").strip(),
                "password": senha,
            })
            if not getattr(res, "user", None):
                self.ultimo_erro_login = "Resposta de autenticação sem utilizador."
                self.sessao_atual = None
                self.sessao_auth = None
                return False

            self.sessao_atual = res.user
            self.sessao_auth = getattr(res, "session", None)
            return True
        except Exception as e:
            self.sessao_atual = None
            self.sessao_auth = None
            self.ultimo_erro_login = str(e)
            print(f"[Erro de Login]: {e}")
            return False

    def esta_autenticado(self):
        return bool(self.sessao_atual)

    def salvar_candidato_pipeline(self, vaga_id, dados_perfil, lista_nrs):
        if not self.sessao_atual:
            raise PermissionError("Autenticação necessária.")

        res_cand = self.db.table("candidatos").upsert(dados_perfil, on_conflict="url_perfil").execute()
        cand_id = res_cand.data[0]["id"]

        for nr in lista_nrs:
            try:
                self.db.table("competencias").insert({"nome": nr, "tipo": "Norma Regulamentadora"}).execute()
            except: pass 

            comp = self.db.table("competencias").select("id").eq("nome", nr).execute()
            if comp.data:
                try:
                    self.db.table("candidato_competencias").upsert(
                        {"candidato_id": cand_id, "competencia_id": comp.data[0]["id"]}
                    ).execute()
                except: pass

        try:
            self.db.table("pipeline_recrutamento").insert(
                {"vaga_id": vaga_id, "candidato_id": cand_id, "etapa": "Mapeado"}
            ).execute()
        except: pass

        return cand_id

    def consultar_pipeline_exportacao(self, usuario_id):
        vagas = (
            self.db.table("vagas")
            .select("id, titulo, cidade, estado, status, data_criacao")
            .eq("recrutador_id", usuario_id)
            .order("data_criacao", desc=True)
            .execute()
        )
        vagas_data = vagas.data or []
        if not vagas_data:
            return []

        vaga_ids = [item["id"] for item in vagas_data]
        pipeline = (
            self.db.table("pipeline_recrutamento")
            .select("vaga_id, candidato_id, etapa, data_atualizacao")
            .in_("vaga_id", vaga_ids)
            .order("data_atualizacao", desc=True)
            .execute()
        )
        pipeline_data = pipeline.data or []
        if not pipeline_data:
            return []

        candidato_ids = list({item["candidato_id"] for item in pipeline_data if item.get("candidato_id")})
        candidatos = (
            self.db.table("candidatos")
            .select("id, nome, titulo_profissional, empresa_atual, localizacao, email, telefone, whatsapp, url_perfil, fonte_origem")
            .in_("id", candidato_ids)
            .execute()
        )
        candidatos_data = candidatos.data or []

        vaga_por_id = {item["id"]: item for item in vagas_data}
        candidato_por_id = {item["id"]: item for item in candidatos_data}

        linhas = []
        for item in pipeline_data:
            vaga = vaga_por_id.get(item.get("vaga_id"))
            candidato = candidato_por_id.get(item.get("candidato_id"))
            if not vaga or not candidato:
                continue
            linhas.append(
                {
                    "vaga_titulo": vaga.get("titulo"),
                    "vaga_cidade": vaga.get("cidade"),
                    "vaga_estado": vaga.get("estado"),
                    "vaga_status": vaga.get("status"),
                    "etapa": item.get("etapa"),
                    "candidato_nome": candidato.get("nome"),
                    "titulo_profissional": candidato.get("titulo_profissional"),
                    "empresa_atual": candidato.get("empresa_atual"),
                    "localizacao": candidato.get("localizacao"),
                    "email": candidato.get("email"),
                    "telefone": candidato.get("telefone"),
                    "whatsapp": candidato.get("whatsapp"),
                    "fonte_origem": candidato.get("fonte_origem"),
                    "url_perfil": candidato.get("url_perfil"),
                    "data_atualizacao": item.get("data_atualizacao"),
                }
            )
        return linhas
