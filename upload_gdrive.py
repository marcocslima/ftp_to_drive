# upload_gdrive.py

import os
import mimetypes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
import traceback # Para o traceback.print_exc()

try:
    from aux_ import resource_path
except ImportError:
    print("AVISO: Não foi possível importar 'resource_path' de 'aux_.py'. Usando fallback.")
    def resource_path(relative_path):
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive']

TOKEN_FILE = resource_path('credentials/token.json')
CREDENTIALS_FILE = resource_path('credentials/credentials.json')

def get_drive_service():
    creds = None
    credentials_dir = os.path.dirname(TOKEN_FILE)
    if not os.path.exists(credentials_dir):
        try: os.makedirs(credentials_dir); print(f"Diretório '{credentials_dir}' criado.")
        except OSError as e: print(f"Erro ao criar '{credentials_dir}': {e}"); return None, None

    if os.path.exists(TOKEN_FILE):
        try: creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except ValueError as e: print(f"Erro ao carregar token (malformado?): {e}"); creds = None
        except Exception as e: print(f"Erro desconhecido ao carregar token: {e}"); creds = None
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try: print("Token expirado. Atualizando..."); creds.refresh(Request()); print("Token atualizado.")
            except Exception as e: print(f"Erro ao atualizar token: {e}"); creds = None
        
        if not creds:
            print("Iniciando novo fluxo de autenticação...")
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERRO CRÍTICO: '{CREDENTIALS_FILE}' não encontrado."); return None, None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0); print("Autenticação bem-sucedida.")
            except FileNotFoundError: print(f"ERRO CRÍTICO: '{CREDENTIALS_FILE}' não encontrado durante auth."); return None, None
            except Exception as e: print(f"Falha na autenticação: {e}"); return None, None
        try:
            with open(TOKEN_FILE, 'w') as token_f: token_f.write(creds.to_json())
            print(f"Token salvo em '{TOKEN_FILE}'.")
        except IOError as e: print(f"Erro ao salvar token: {e}")

    if not creds or not creds.valid:
        print("ERRO CRÍTICO: Não foi possível obter credenciais OAuth válidas."); return None, None

    try:
        drive_service_obj = build('drive', 'v3', credentials=creds)
        print("Serviço do Google Drive construído com sucesso.")
        return drive_service_obj, creds
    except HttpError as e: print(f'Erro HTTP ao construir serviço Drive: {e.resp.status} - {e.content.decode()}'); return None, None
    except Exception as e: print(f'Erro inesperado ao construir serviço Drive: {e}'); return None, None

def upload_file_to_folder(service, local_file_path, folder_id, drive_filename=None):
    if not service: print("ERRO: Serviço Drive não fornecido para upload."); return None
    if not os.path.exists(local_file_path): print(f"Arquivo local não encontrado: {local_file_path}"); return None
    if drive_filename is None: drive_filename = os.path.basename(local_file_path)
    mimetype, _ = mimetypes.guess_type(local_file_path)
    if mimetype is None: mimetype = 'application/octet-stream'
    file_metadata = {'name': drive_filename, 'parents': [folder_id]}
    media = MediaFileUpload(local_file_path, mimetype=mimetype, resumable=True)
    try:
        print(f"Upload: '{local_file_path}' como '{drive_filename}' para Drive ID '{folder_id}'...")
        file_obj = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        print(f"Arquivo '{file_obj.get('name')}' enviado com sucesso para o Drive!")
        return file_obj.get('id')
    except HttpError as e: print(f'Erro HTTP upload "{drive_filename}": {e.resp.status} - {e.content.decode()}')
    except Exception as e: print(f'Erro inesperado upload "{drive_filename}": {e}')
    return None

if __name__ == '__main__':
    print("--- Testando módulo upload_gdrive.py ---")
    
    tg_folder_id_test = os.getenv('TARGET_FOLDER_ID_TESTE_DRIVE', os.getenv('TARGET_FOLDER_ID'))
    if not tg_folder_id_test: print("\nAVISO: Var TARGET_FOLDER_ID_TESTE_DRIVE não definida para teste de upload.")
    else:
        print("\n--- Teste de Upload Drive ---")
        example_file = resource_path('test_drive_upload.txt')
        try:
            with open(example_file, 'w') as f: f.write('Teste upload Drive!')
            test_drive_svc, test_drive_creds_val = get_drive_service()
            if test_drive_svc: upload_file_to_folder(test_drive_svc, example_file, tg_folder_id_test)
            else: print("Falha ao obter serviço Drive para teste upload.")
        finally:
            if os.path.exists(example_file): os.remove(example_file)
            
    print("\n--- Fim dos testes upload_gdrive.py ---")