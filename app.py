import os, logging, requests
from threading import Thread
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import replicate

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = App(token=os.environ["SLACK_BOT_TOKEN"])
MODEL = os.environ["REPLICATE_MODEL_VERSION"]
TRIGGER = os.environ.get("TRIGGER_WORD", "diya")


def generate_image(scene: str) -> str:
    prompt = (
        f"A candid photorealistic photograph of {TRIGGER}, a young Indian woman, "
        f"as a child. {scene}. Sharp focus on face, natural daylight, "
        f"film grain, shot on 35mm."
    )
    output = replicate.run(
        MODEL,
        input={
            "prompt": prompt,
            "num_outputs": 1,
            "aspect_ratio": "1:1",
            "output_format": "png",
            "output_quality": 90,
            "guidance_scale": 3.5,
            "num_inference_steps": 35,
            "lora_scale": 1.0,
        },
    )
    return output[0] if isinstance(output, list) else output


def worker(client, channel, thread_ts, user, scene):
    try:
        client.chat_postMessage(
            channel=channel, thread_ts=thread_ts,
            text=":hourglass_flowing_sand: Digging into the memory box... ~45s.",
        )
        url = generate_image(scene)
        img = requests.get(url, timeout=60).content
        client.files_upload_v2(
            channel=channel, thread_ts=thread_ts,
            file=img, filename="memory.png",
            initial_comment=f":sparkles: <@{user}> - *{scene}*",
        )
    except Exception as e:
        logging.exception("gen failed")
        client.chat_postMessage(
            channel=channel, thread_ts=thread_ts,
            text=f":x: Generation failed: `{e}`",
        )


@app.event("app_mention")
def on_mention(event, client):
    scene = event["text"].split(">", 1)[-1].strip()
    thread_ts = event.get("thread_ts", event["ts"])
    if not scene:
        client.chat_postMessage(
            channel=event["channel"], thread_ts=thread_ts,
            text="Give me a scene, e.g. `@MemoryBot my 5-year-old self on a beach`",
        )
        return
    Thread(target=worker, args=(client, event["channel"], thread_ts, event["user"], scene)).start()


@app.command("/memory")
def on_slash(ack, command, client):
    ack()
    scene = command["text"].strip()
    if not scene:
        client.chat_postEphemeral(
            channel=command["channel_id"], user=command["user_id"],
            text="Usage: `/memory <scene>` - e.g. `/memory my 10-year-old self in a classroom`",
        )
        return
    starter = client.chat_postMessage(
        channel=command["channel_id"],
        text=f"<@{command['user_id']}> asked for: _{scene}_",
    )
    Thread(target=worker, args=(client, command["channel_id"], starter["ts"], command["user_id"], scene)).start()


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()