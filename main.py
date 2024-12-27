import json
import gradio as gr


def header():
    return """
    <tr>
        <th>Name</th>
        <th>Artist</th>
        <th>Spotify Rank</th>
        <th>Tiktok Rank</th>
    </tr>
    """


def fetch(input: str) -> list[dict[str, str | int]]:
    f"""{input}"""
    with open("./static/output.json") as f:
        lines = f.readlines()
    return json.loads("\n".join(lines))


def body(data: list[dict[str, str | int]]) -> str:
    return "".join(
        [
            f"""
            <tr>
                <td>
                    <a
                    href="https://open.spotify.com/track/{d["spotify_id"]}"
                    target="_blank"
                    >
                    {d["name"]}
                    </a>

                </td>
                <td>
                       {d["artists"]}
                </td>
                <td>
                       {d["daily_rank"]}
                </td>
                <td>
                       {d["is_explicit"]}
                </td>
            </tr>
        """
            for d in data
        ]
    )


def fn(sentence):
    data = fetch(sentence)
    return f"<table>{header()}{body(data)}</table>"


if __name__ == "__main__":
    demo = gr.Interface(
        fn=fn,
        inputs=["text"],
        outputs=["html"],
    )

    demo.launch()
