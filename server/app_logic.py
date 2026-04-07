from TTS.api import TTS
from typing import Optional, Any
import types
import asyncio

from termcolor import colored

from server.config import AppConfig
from server.tts_utils import exec_tts, wav2bytes, wav2bytes_streamed
from server.signal import Signal
from server.utils import Timer, generate_id


class AppLogic:
    """
    1. Execute all actions. Ask LLM, do the TTS etc.
    2. Event dispatcher between websockets. A pub/sub.
    """

    def __init__(
        self,
        cfg: AppConfig,
        llm: Any,
        tts: TTS,
    ):
        self.cfg = cfg
        self.llm = llm
        self._tts = tts

        self.on_query = Signal()
        self.on_text_response = Signal()
        self.on_tts_response = Signal()
        self.on_tts_timings = Signal()
        self.on_tts_first_chunk = Signal()
        self.on_play_vfx = Signal()

    async def ask_query(self, query: str, msg_id: Optional[str] = ""):
        if not msg_id:
            msg_id = generate_id()

        print(colored("Query:", "blue"), f"'{query}' (msg_id={msg_id})")
        await self.on_query.send(query, msg_id)

        time_to_first_tts = Timer(start=True)

        with Timer() as llm_timer:
            resp_text = await self._exec_llm(query)

        await self.on_text_response.send(resp_text, msg_id, llm_timer.delta)

        # internally can use different thread
        await self._exec_tts(resp_text, msg_id, time_to_first_tts)

        return resp_text

    async def play_vfx(self, vfx: str):
        print(colored("VFX (particle system):", "blue"), f"'{vfx}'")
        await self.on_play_vfx.send(vfx)

    def reset_context(self):
        # No local Gemma/Ollama prompt history anymore.
        # Add your own history management later if needed.
        pass

    async def _exec_llm(self, query: str) -> str:
        """
        Calls a generic async LLM client with:
            generate(model, prompt, options=None) -> {"response": "..."}
        """

        cfg = self.cfg.llm

        if isinstance(cfg.mocked_response, str):
            print(
                colored("Mocked LLM response based on config:", "blue"),
                f"'{cfg.mocked_response}'",
            )
            return query if cfg.mocked_response == "" else cfg.mocked_response

        resp = await self.llm.generate(
            model=cfg.model,
            prompt=query,
            options={
                "temperature": cfg.temperature,
                "top_k": cfg.top_k,
                "top_p": cfg.top_p,
            },
        )

        text = resp.get("response", "")
        if not isinstance(text, str):
            return ""
        return text

    async def _exec_tts(self, text: str, msg_id: str, time_to_first_tts: Timer):
        # skip if no event listeners
        if not self.on_tts_response:
            await self.on_tts_timings.send(msg_id, 0)
            await self.on_tts_first_chunk.send(msg_id, 0)
            return

        # split into sentences to lower time to first chunk
        sentences = self._tts.synthesizer.split_into_sentences(text)

        async def tts_internal():
            with Timer() as tts_timer:
                for sentence in sentences:
                    await self._tts_sentence(sentence)
                    await self._time_first_audio_chunk(msg_id, time_to_first_tts)

            # tts done, send timings
            await self.on_tts_timings.send(msg_id, tts_timer.delta)

        loop = asyncio.get_running_loop()
        loop.create_task(tts_internal())

    async def _tts_sentence(self, sentence: str):
        output = exec_tts(self.cfg, self._tts, sentence)  # either object or generator

        if not isinstance(output, types.GeneratorType):
            # when not streaming
            audio_bytes = wav2bytes(self._tts, output)
            await self.on_tts_response.send(audio_bytes)
        else:
            # when streaming
            for _, chunk in enumerate(output):
                audio_bytes = wav2bytes_streamed(self._tts, chunk)
                await self.on_tts_response.send(audio_bytes)

    async def _time_first_audio_chunk(self, msg_id: str, time_to_first_tts: Timer):
        if not time_to_first_tts.is_running():
            return

        delta = time_to_first_tts.stop()
        await self.on_tts_first_chunk.send(msg_id, delta)
        print(
            colored("First TTS chunk:", "blue"),
            f"{time_to_first_tts.delta:.2f}s",
        )