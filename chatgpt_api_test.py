import openai
import os

def chatgpt_input(text):
    env_var = "openaikey"
    # Set your OpenAI API key
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(f"Environment variable '{env_var}' is not set or is empty.")
    openai.api_key = api_key

    # Define system prompt and messages
    messages = [
        {
            "role": "system",
            "content": (
                "The following is information on my female dating profile. "
                "If you wanted to match with me, provide a witty opening that starts a conversation "
                "based on what you know about me. You should use less than 150 characters and only use words when replying."
            )
        }
    ]

    if not text:
        raise ValueError("Input text is empty.")
    messages.append({"role": "user", "content": text})

    # Get ChatGPT response
    try:
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = chat.choices[0].message.content
        print(f"ChatGPT: {reply}")
        return reply
    except Exception as e:
        print(f"Error: {e}")
        return None
