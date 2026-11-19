from settings.common import LogServiceName, common_settings
from settings.web import web_settings
from settings.mongo import mongo_settings
from settings.fish_audio import fish_audio_settings
from settings.elevenlabs import elevenlabs_settings
from settings.deepseek import deepseek_settings
from settings.worker import worker_settings


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
    web_api_key = web_settings.web_api_key

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



settings = Settings()
