from typing import Optional
from yaml import load, Loader
import os
from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    ConfigDict,
    PositiveInt,
    NonNegativeInt,
    PositiveFloat,
    StrictBool,
)
from termcolor import colored

load_dotenv()


class LlmCfg(BaseModel):
    mocked_response: Optional[str] = None
    model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    temperature: PositiveFloat = 0.7
    top_k: PositiveInt = 40
    top_p: PositiveFloat = 0.9
    context_length: NonNegativeInt = 10
    system_message: Optional[str] = None
    api_key: Optional[str] = os.getenv("LLM_API_KEY")
    api: str = os.getenv(
        "LLM_API_URL",
        "http://cci-siscluster1.charlotte.edu:8080/api/v1/chats/completions",
    )


class TtsCfg(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"
    use_gpu: StrictBool = True
    chunk_size: NonNegativeInt = 0
    speaker: Optional[str] = None
    language: Optional[str] = None
    sample_of_cloned_voice_wav: Optional[str] = None
    deepspeed_enabled: StrictBool = True
    streaming_enabled: StrictBool = False
    streaming_chunk_size: PositiveInt = 20
    streaming_overlap_wav_len: PositiveInt = 1024


class ServerCfg(BaseModel):
    host: str = "localhost"
    port: PositiveInt = 8080


class AppConfig(BaseModel):
    llm: LlmCfg = LlmCfg()
    tts: TtsCfg = TtsCfg()
    server: ServerCfg = ServerCfg()


def load_app_config(filepath=None) -> AppConfig:
    if filepath:
        print(colored("Loading config file", "blue"), f"'{filepath}'")
        with open(filepath, "r", encoding="utf-8") as f:
            yaml_content = load(f.read(), Loader=Loader) or {}
        cfg = AppConfig(**yaml_content)
    else:
        cfg = AppConfig()

    print(colored("Loaded LLM API:", "green"), cfg.llm.api)
    print(colored("Loaded LLM model:", "green"), cfg.llm.model)
    print(colored("Loaded API key present:", "green"), bool(cfg.llm.api_key))

    return cfg