from termcolor import colored
from server.llm_adapter import HttpLLMClient
import click

from server.config import load_app_config
from server.tts_utils import create_tts
from xtts_scripts import create_speaker_samples, speak

DEFAULT_TTS_TEXT = "The current algorithm only upscales the luma, the chroma is preserved as-is. This is a common trick known"


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default="config_xtts.yaml",
    show_default=True,
    help="Config file",
)
def serve(config: str):
    """Start the server for TTS service"""

    import sys
    import platform
    import torch
    import torch.serialization

    from TTS.tts.configs.xtts_config import XttsConfig
    from server.server import create_server, start_server
    from server.socket_msg_handler import SocketMsgHandler
    from server.app_logic import AppLogic

    STATIC_DIR = "./server/static"

    # ---- PyTorch / XTTS compatibility patch ----
    if hasattr(torch.serialization, "add_safe_globals"):
        torch.serialization.add_safe_globals([XttsConfig])

    _original_torch_load = torch.load

    def patched_torch_load(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return _original_torch_load(*args, **kwargs)

    torch.load = patched_torch_load
    # --------------------------------------------

    cfg = load_app_config(config)
    print(colored("Config:", "blue"), cfg)
    print(colored("OS:", "blue"), f"{platform.system()} ({platform.machine()})")
    print(colored("Python:", "blue"), sys.version)
    print(colored("Torch:", "blue"), f"{torch.__version__}")
    print(colored("Loaded LLM API:", "green"), cfg.llm.api)
    print(colored("Loaded LLM model:", "green"), cfg.llm.model)
    print(colored("Loaded API key present:", "green"), bool(cfg.llm.api_key))

    llm = HttpLLMClient(
        api_url=cfg.llm.api,
        api_key=cfg.llm.api_key,
        system_message=cfg.llm.system_message,
    )

    # Safer for Windows/local testing
    cfg.tts.use_gpu = False
    cfg.tts.deepspeed_enabled = False

    tts = create_tts(cfg)
    app_logic = AppLogic(cfg, llm, tts)

    create_ws_handler = lambda ws, is_unity: SocketMsgHandler(ws, app_logic, is_unity)
    app = create_server(STATIC_DIR, create_ws_handler, app_logic)

    print(colored("Webui:", "green"), f"http://{cfg.server.host}:{cfg.server.port}/ui")
    start_server(app, host=cfg.server.host, port=cfg.server.port)

    print("=== DONE ===")


@click.group()
def main():
    """Available commands below"""


if __name__ == "__main__":
    main.add_command(serve)
    main.add_command(create_speaker_samples)
    main.add_command(speak)
    main()