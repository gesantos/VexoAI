from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

class GestaoAdministrativa:
    def __init__(self):
        if not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("Service Role Key ausente.")
        self.admin_db: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    def validar_admin(self, admin_id):
        res = self.admin_db.table("usuarios_perfis").select("nivel_acesso").eq("id", admin_id).execute()
        if not res.data or res.data[0]["nivel_acesso"] != "Admin":
            raise PermissionError("Acesso restrito a Administradores.")

    def cadastrar_recrutador(self, admin_id, email, senha, nome_completo):
        self.validar_admin(admin_id)
        res = self.admin_db.auth.admin.create_user({
            "email": email,
            "password": senha,
            "email_confirm": True,
            "user_metadata": {"nome_completo": nome_completo}
        })
        return res.user.id

    def excluir_usuario(self, admin_id, target_user_id):
        self.validar_admin(admin_id)
        self.admin_db.auth.admin.delete_user(target_user_id)
        return True
