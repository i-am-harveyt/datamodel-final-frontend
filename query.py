from vertexai.preview.generative_models import GenerativeModel
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import aiplatform
import os
import requests


PROJECT_ID = ""
LOCATION = ""
aiplatform.init(project=PROJECT_ID, location=LOCATION)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""  # credential path


def answer_question_gemini(prompt):  # Gemini回答
    model = GenerativeModel("gemini-pro")
    response = model.generate_content(
        prompt,
        generation_config={
            "max_output_tokens": 8192,
            "temperature": 0.5,
            "top_p": 0.5,
            "top_k": 10,
        },
        stream=False,
    )
    try:
        return response.text
    except Exception:
        print("An Error Ocuured Cleaning the Data")
        return "An Error Ocuured Cleaning the Data"


def validate_spotify_id(name, artist, spotify_id, spotify_token):
    """使用 Spotify API 驗證 Spotify ID 是否正確"""
    url = f"https://api.spotify.com/v1/tracks/{spotify_id}"
    headers = {"Authorization": f"Bearer {spotify_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        track_name_matches = data["name"].lower() == name.lower()
        artist_matches = any(
            artist.lower() in a["name"].lower() for a in data["artists"]
        )
        return track_name_matches and artist_matches
    return False


def run_search(question):
    credentials = service_account.Credentials.from_service_account_file(
        "musicrag-446006-a54782fccfa1.json"
    )
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    sql = """
        SELECT
            base.spotify_id,
            base.name,
            base.artists,
            base.danceability,
            base.popularity,
            base.country_name,
            base.content
        FROM VECTOR_SEARCH(
            TABLE `musicrag-446006.spotifydata.musicrag_with_embedding_updated`,
            'text_embedding',
            (
                SELECT text_embedding, content as query
                FROM ML.GENERATE_TEXT_EMBEDDING(
                    MODEL `musicrag-446006.spotifydata.embedding_model_5`,
                    (SELECT @question AS content)
                )
            ),
            top_k => 3
        )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("question", "STRING", question),
        ]
    )

    query_job = client.query(sql, job_config=job_config)

    # 打印查詢返回的數據
    data = []
    for row in query_job:
        print(row)
        data.append(
            {
                "spotify_id": row.spotify_id,
                "name": row.name,
                "artists": row.artists,
                "danceability": row.danceability,
                "popularity": row.popularity,
                "country_name": row.country_name,
                "content": row.content,
            }
        )

    return data


def build_prompt(data, question):
    user_preference = "I enjoy songs by Ariana Grande and similar pop artists."

    # 格式化上下文數據
    context_lines = []
    for item in data:
        context_lines.append(
            f"- {item['name']} by {item['artists']} (Spotify ID: {item['spotify_id']})"
        )
    context = "\n".join(context_lines)

    # 打印上下文
    print("Generated Context:")
    print(context)

    prompt = f"""
        Instructions: Based on the following Context and User Preference, recommend songs and provide:
        1. A list of recommended songs with their artists and Spotify IDs (ensure Spotify IDs come directly from the Context).
        2. An explanation of why these songs were chosen (e.g., similarity to Ariana Grande's style, mood, or other factors).
        3. Any fun facts or trivia about the recommended songs or artists.

        User Preference: {user_preference}

        Context:
        {context}

        Question: {question}
    """
    return prompt


def answer_question(question):
    # 運行查詢
    data = run_search(question)

    # 打印查詢返回的數據（調試用）
    print("Retrieved Data:")
    for item in data:
        print(item)

    # 構建 Prompt
    prompt = build_prompt(data, question)
    print("Generated Prompt:")
    print(prompt)

    # 使用 Gemini 生成回答
    answer_gemini = answer_question_gemini(prompt)
    return answer_gemini
