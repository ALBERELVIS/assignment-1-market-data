"""
Módulo de gestión de configuración y API keys
Permite cargar API keys desde archivo de configuración o input del usuario
"""

import os
import json
from typing import Optional, Dict
from pathlib import Path


class ConfigManager:
    """
    Gestor de configuración para API keys
    Soporta carga desde archivo .env, config.json o input del usuario
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_file: Ruta al archivo de configuración (opcional)
                         Si no se especifica, busca .env o config.json en el directorio raíz
        """
        self.config_file = config_file
        self._config: Dict[str, str] = {}
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración desde archivos"""
        # Buscar archivo de configuración
        if self.config_file:
            config_path = Path(self.config_file)
        else:
            # Buscar en el directorio raíz del proyecto
            project_root = Path(__file__).parent.parent
            config_path = None
            
            # Intentar .env primero
            env_path = project_root / ".env"
            if env_path.exists():
                self._load_env_file(env_path)
                return
            
            # Intentar config.json
            json_path = project_root / "config.json"
            if json_path.exists():
                config_path = json_path
        
        if config_path and config_path.exists():
            if config_path.suffix == ".json":
                self._load_json_file(config_path)
            elif config_path.suffix == ".env" or config_path.name == ".env":
                self._load_env_file(config_path)
    
    def _load_env_file(self, env_path: Path):
        """Carga configuración desde archivo .env"""
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        self._config[key] = value
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo cargar {env_path}: {e}")
    
    def _load_json_file(self, json_path: Path):
        """Carga configuración desde archivo JSON"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo cargar {json_path}: {e}")
            self._config = {}
    
    def get_api_key(self, key_name: str, prompt: Optional[str] = None, 
                   required: bool = False) -> Optional[str]:
        """
        Obtiene una API key desde la configuración o solicita al usuario
        
        Args:
            key_name: Nombre de la clave (ej: "ALPHA_VANTAGE_API_KEY")
            prompt: Mensaje personalizado para solicitar la key (opcional)
            required: Si True, solicita la key si no está disponible
        
        Returns:
            API key o None si no está disponible y no es requerida
        """
        # Buscar en variables de entorno primero
        env_key = os.getenv(key_name)
        if env_key:
            return env_key
        
        # Buscar en configuración cargada
        if key_name in self._config:
            return self._config[key_name]
        
        # Si no está disponible y es requerida, solicitar al usuario
        if required:
            if prompt is None:
                prompt = f"Ingresa tu {key_name}: "
            
            try:
                api_key = input(prompt).strip()
                if api_key:
                    # Guardar en memoria para esta sesión
                    self._config[key_name] = api_key
                    return api_key
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  Operación cancelada por el usuario")
                return None
        
        return None
    
    def set_api_key(self, key_name: str, value: str):
        """Establece una API key en la configuración (solo en memoria)"""
        self._config[key_name] = value
    
    def save_config(self, file_path: Optional[str] = None):
        """
        Guarda la configuración en un archivo
        
        Args:
            file_path: Ruta donde guardar (opcional, por defecto config.json en raíz)
        """
        if file_path:
            save_path = Path(file_path)
        else:
            project_root = Path(__file__).parent.parent
            save_path = project_root / "config.json"
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuración guardada en {save_path}")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")


# Instancia global del gestor de configuración
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Obtiene la instancia global del gestor de configuración"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

