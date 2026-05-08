from app.db.supabase_client import supabase

def validar_credenciales(nombre, password):
    try:
        response = supabase.table("Usuario") \
            .select("id, nombre") \
            .eq("nombre", nombre) \
            .eq("password", password) \
            .single() \
            .execute()
        
        return response.data
    except Exception as e:
        print(f"Error de autenticación: {e}")
        return None