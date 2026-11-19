from settings.common import LogServiceName, common_settings
from settings.web import web_settings
from settings.mongo import mongo_settings
from settings.fish_audio import fish_audio_settings
from settings.elevenlabs import elevenlabs_settings
from settings.deepseek import deepseek_settings
from settings.worker import worker_settings
from settings.auth import auth_settings


class Settings:

    def get_service_debug(self, service: LogServiceName) -> bool:
        service_debug_map = {
            "web": web_settings.web_debug,
            "worker": worker_settings.worker_debug,
        }
        service_debug = service_debug_map[service]
        if service_debug is None:
            return common_settings.debug
        return service_debug

    debug = common_settings.debug

    web_debug = web_settings.web_debug
    web_name = web_settings.web_name
    web_version = web_settings.web_version

    mongodb_host = mongo_settings.mongodb_host
    mongodb_port = mongo_settings.mongodb_port
    mongodb_username = mongo_settings.mongodb_username
    mongodb_password = mongo_settings.mongodb_password
    mongodb_database = mongo_settings.mongodb_database

    fish_audio_base_url = fish_audio_settings.fish_audio_base_url
    fish_audio_api_key = fish_audio_settings.fish_audio_api_key
    fish_audio_timeout = fish_audio_settings.fish_audio_timeout

    elevenlabs_base_url = elevenlabs_settings.elevenlabs_base_url
    elevenlabs_api_keys = elevenlabs_settings.elevenlabs_api_keys
    elevenlabs_music_model_id = elevenlabs_settings.elevenlabs_music_model_id
    elevenlabs_sound_model_id = elevenlabs_settings.elevenlabs_sound_model_id
    elevenlabs_timeout = elevenlabs_settings.elevenlabs_timeout

    deepseek_base_url = deepseek_settings.deepseek_base_url
    deepseek_api_key = deepseek_settings.deepseek_api_key
    deepseek_model = deepseek_settings.deepseek_model
    deepseek_temperature = deepseek_settings.deepseek_temperature
    deepseek_max_tokens = deepseek_settings.deepseek_max_tokens
    deepseek_timeout = deepseek_settings.deepseek_timeout
    deepseek_max_retries = deepseek_settings.deepseek_max_retries

    worker_debug = worker_settings.worker_debug
    worker_poll_interval = worker_settings.worker_poll_interval
    music_data_dir = worker_settings.music_data_dir

    google_client_id = auth_settings.google_client_id
    session_secret = auth_settings.session_secret
    session_ttl_seconds = auth_settings.session_ttl_seconds
    allowed_origins = auth_settings.allowed_origins


settings = Settings()
