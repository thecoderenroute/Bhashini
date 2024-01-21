from moviepy.editor import AudioFileClip

from telegram import File, Update
from telegram.ext import (
    filters,
    MessageHandler,
    Application,
    ContextTypes,
)

from googletrans import Translator

import speech_recognition as sr

from chat_gpt import GptWrapper, BhashiniWrapper

TOKEN = ""


class Recog:
    def __init__(self) -> None:
        self.r = sr.Recognizer()

    def convert(self, filename):
        with sr.AudioFile(filename) as source:
            audio1 = self.r.record(source)

        text = self.r.recognize_google(audio1, language="auto")

        return text


class Telebot:
    def __init__(self) -> None:
        self.recog = Recog()
        self.translator = Translator()
        self.gpt = GptWrapper()
        self.bhashini = BhashiniWrapper()

    async def get_response(self, file: File):
        path = await file.download_to_drive()

        clip = AudioFileClip(str(path))

        name = str(path).split(".")[0]

        clip.write_audiofile(name + ".wav")

        text = self.recog.convert(name + ".wav")

        return text, path

    async def voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        f = await update.message.voice.get_file()

        text, path = await self.get_response(f)

        name = str(path).split(".")[0]
        name = name + "_resp"

        tt = self.translator.translate(text, src="hi", dest="en")

        rcvd_local = self.bhashini.convert_response(tt.text, "Hindi")

        resp_text = f"Recieved: \n{rcvd_local}"

        await context.bot.send_message(chat_id=update.effective_chat.id, text=resp_text)

        res = self.gpt.chatbot(tt.text)

        response_from_gpt_in_local = self.bhashini.convert_response(
            res, "Hindi", name + ".wav"
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=response_from_gpt_in_local
        )

        with open(name + ".wav", "rb") as f:
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=f)

    def start(self, TOKEN):
        application = Application.builder().token(TOKEN).build()

        voice_handler = MessageHandler(filters.VOICE, self.voice)

        application.add_handler(voice_handler)
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    tb = Telebot()
    tb.start(TOKEN)
