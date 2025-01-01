from vertexai.preview.generative_models import GenerativeModel
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import aiplatform
from constants import CREDENTIAL_PATH, LOCATION, PROJECT_ID
import os


aiplatform.init(project=PROJECT_ID, location=LOCATION)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIAL_PATH


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


def run_search(question):
    credentials = service_account.Credentials.from_service_account_file(CREDENTIAL_PATH)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    sql = f"""
        SELECT
            query.query,
            base.spotify_id,
            base.name,
            base.artists,
            base.danceability,
            base.popularity,
            base.energy,
            base.content
        FROM VECTOR_SEARCH(
            TABLE `{PROJECT_ID}.spotifydata.embedding2`,
            'text_embedding',
            (
                SELECT text_embedding, content as query
                FROM ML.GENERATE_TEXT_EMBEDDING(
                    MODEL `{PROJECT_ID}.spotifydata.embedding_model_5`,
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

    data = []
    for row in query_job:
        # print(row)
        data.append(
            {
                "spotify_id": row.spotify_id,
                "name": row.name,
                "artists": row.artists,
                "danceability": row.danceability,
                "popularity": row.popularity,
                "energy": row.energy,
                "content": row.content,
            }
        )

    return data


def build_prompt(data, question):
    prompt = """
        Instructions: Answer the question using the following Context. You only have to list the spotify id and the name of the song, also please explain why you recommend them.

        Context: {0}

        Question: {1}
    """.format(data, question)
    return prompt


def answer_question(question):
    data = run_search(question)

    print("Retrieved Data:")
    print(data)

    prompt = build_prompt(data, question)

    answer_gemini = answer_question_gemini(prompt)
    return answer_gemini
