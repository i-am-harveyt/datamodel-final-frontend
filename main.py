from query import answer_question
import gradio as gr
import re


def fetch(input: str) -> str:
    """
    This function ask question with `input`.

    Args:
        input (str) the question to ask
    """
    return answer_question(input)


def url_sub(data: str) -> str:
    """
    This function substitude spotify ids with urls to spotify with regex.

    Args:
        data (str): string contains "Spotify ID: <id>"

    Returns:
        str: processed data.
    """
    data = re.sub(
    r"\(Spotify ID: ([a-zA-Z0-9]+)\)", 
    r"https://open.spotify.com/track/\1", 
    data)
    return data


def fn(query):
    data = fetch(query)
    return url_sub(data)


if __name__ == "__main__":
    demo = gr.Interface(
        fn=fn,
        inputs=["text"],
        outputs=["markdown"],
    )

    demo.launch()
