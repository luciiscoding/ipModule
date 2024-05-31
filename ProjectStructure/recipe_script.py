
import sys
import json
import redis
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

# Set up Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Set up YouTube Data API credentials
# YOUTUBE_API_KEY = 'AIzaSyBabQ47nM7so8JHe1xmqwMlOIQasrdPD3E'
YOUTUBE_API_KEY = 'AIzaSyDENTGhys3s7euqT2bm3htcfkDO18BcYto'
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Set up OpenAI API
llm = OpenAI(api_key='sk-proj-jZmzwh4ILvTVReD8ZiWOT3BlbkFJdvftKvqnwzfaRmzgMyp0', temperature=0,
             max_tokens=1000)  # type: ignore

def get_transcript(video_id):
    cache_key_transcript = f"transcript:{video_id}"

    # Check if transcript is cached already
    cached_transcript = redis_client.get(cache_key_transcript)
    if cached_transcript:
        print(f"!!!!  Transcript for video '{video_id}' found in cache.")
        return json.loads(cached_transcript)

    # If not cached, retrieve transcript from YouTube Transcript API
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None

        # Check for manually created English transcript
        for t in transcript_list:
            if t.language_code == 'en' and not t.is_generated:
                transcript = t.fetch()
                break

        # If no manually created English transcript, check for auto-generated English transcript
        if transcript is None:
            for t in transcript_list:
                if t.language_code == 'en' and t.is_generated:
                    transcript = t.fetch()
                    break

        # Cache the transcript for future use (3 days)
        redis_client.setex(cache_key_transcript, 259200, json.dumps(transcript))

        return transcript

    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as e:
        # print(f"Error retrieving transcript for video '{video_id}': {e}")
        # Save empty transcript to cache to avoid repeated API calls
        redis_client.setex(cache_key_transcript, 259200, json.dumps([]))
        return None


# Function to search for recipe titles on YouTube and retrieve captions
def search_and_retrieve_captions(recipe_title, main_ingredients):
    cache_key_captions = f"search:{recipe_title}:{':'.join(main_ingredients)}"

    # Check if search results are cached already
    cached_caption_search_res = redis_client.get(cache_key_captions)
    if cached_caption_search_res:
        print(f"!!!!!   Search results for recipe '{recipe_title}' with main ingredients '{main_ingredients}' found in cache.")
        return json.loads(cached_caption_search_res)

    try:
        # Search for videos based on recipe title
        search_response = youtube.search().list(
            q=recipe_title,
            part='id,snippet',
            type='video',
            maxResults=50  # Limit to first 50 videos
        ).execute()

        # Loop through search results
        for search_result in search_response.get('items', []):
            video_id = search_result['id']['videoId']
            video_title = search_result['snippet']['title']

            # Check if the main ingredients are both in the video_title
            # if the main ingredients are not in the video title, skip to the next video
            if all(ingredient.lower() in video_title.lower() for ingredient in main_ingredients):
                # print(f"Found a video with the main ingredients in the title: {video_title} (ID: {video_id})")

                # Retrieve captions for the current video
                captions = get_transcript(video_id)

                # Check if captions are available
                if captions:
                    # Check if all main ingredients appear at least twice
                    all_ingredients_present = all(
                        sum(1 for caption in captions if ingredient in caption['text'].lower()) >= 2
                        for ingredient in main_ingredients
                    )

                    if all_ingredients_present:
                        # Check if captions contain meaningful content related to recipe steps
                        step_count = sum(1 for caption in captions if 'step' in caption['text'].lower())

                        if step_count >= 1:
                            # Found a valid recipe video
                            #print(f"Found a valid recipe video: {video_title} (ID: {video_id})")
                            captions_text = " ".join(caption['text'] for caption in captions)
                            # captions_text = captions_text.replace('\n', ' ')

                            # Cache the captions for future use (3 days)
                            redis_client.setex(cache_key_captions, 259200, json.dumps(captions_text))

                            return captions_text
            else:
                # print(f"Skipping video '{video_title}' (ID: {video_id}) as it does not contain the main ingredients.")
                redis_client.setex(cache_key_captions, 259200, json.dumps(None))
                continue

        # print("No valid recipe video found.")
        redis_client.setex(cache_key_captions, 259200, json.dumps(None))
        return None

    except Exception as e:
        # print(f"An error occurred during the search: {e}")
        return None


# Parsing the captions
def parse_recipe(recipe_text: str, recipe_title: str, main_ingredients: list) -> dict:
    # Generate a unique cache key for the recipe
    ingredients_str = ":".join(main_ingredients)
    cache_key = f"parse_recipe:{recipe_title}:{ingredients_str}"

    # Check if parsed recipe is cached already
    cached_recipe = redis_client.get(cache_key)
    if cached_recipe:
        #print("!!!!   Recipe found in cache.")
        return json.loads(cached_recipe)

    # Initial prompt to extract the instructions and ingredients
    extract_prompt = PromptTemplate(
        input_variables=["recipe"],
        template="""{recipe}

        Extract the ingredients and instructions from the above, output as json with keys lowercase keys instructions and ingredients. For ingredients extract quantity if available, if not estimate the quantity. """,
    )

    # # Secondary prompt to group extracted ingredients into categories
    # grouping_prompt = PromptTemplate(
    #     input_variables=["ingredients"],
    #     template="""
    #     {ingredients}
    #
    #     Group above ingredients into similar categories, output as json with lowercase keys categories:""",
    # )

    # Create the RunnableSequences
    extract_chain = RunnableSequence(extract_prompt, llm)
    # grouping_chain = RunnableSequence(grouping_prompt, llm)

    # Run the extract chain
    text_result = extract_chain.invoke({"recipe": recipe_text})
    json_result = json.loads(text_result)

    # # Run the grouping chain
    # ingredient_group_text = grouping_chain.invoke({"ingredients": json.dumps(json_result["ingredients"])})
    # ingredient_group_json = json.loads(ingredient_group_text)

    # json_result["grouped_ingredients"] = ingredient_group_json

    # Cache the recipe for future use (3 days)
    redis_client.setex(cache_key, 259200, json.dumps(json_result))
    return json_result


if __name__ == "__main__":
    recipe_format = sys.argv[1]
    #recipe_format = "youtube"
    input = sys.argv[2]
    #input = "apple pie recipe"
    if recipe_format == "youtube":
        main_ingredients = sys.argv[3:]

    if recipe_format == "youtube":
        recipe_text = search_and_retrieve_captions(input, main_ingredients)
        if recipe_text:
            # if recipe_text == "None":
            #     print("Error at generating recipe...")
            #     sys.exit()

            #print("Captions for the found video:", recipe_text)
            parsed_recipe = parse_recipe(recipe_text, input, main_ingredients)
            #print("Generated recipe:")
            print(json.dumps(parsed_recipe, indent=2))
        else:
            print("Error at generating recipe...")
    elif recipe_format == "text":
        parsed_recipe = parse_recipe(input, input, [])
        if parsed_recipe:
            #print("Generated recipe:")
            print(json.dumps(parsed_recipe, indent=2))
        else:
            print("Error at generating recipe...")

# # Example usage
# recipe_format = "youtube"
# recipe_title = "beef quesadillas recipe"
# main_ingredients = ["beef"]
#
# if recipe_format == "youtube":
#     recipe_text = search_and_retrieve_captions(recipe_title, main_ingredients)
#     if recipe_text:
#         print("Captions for the found video:", recipe_text)
#         parsed_recipe = parse_recipe(recipe_text)
#         print("Generated recipe:")
#         print(json.dumps(parsed_recipe, indent=2))
