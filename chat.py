import json
import time
import os
from openai import OpenAI, OpenAIError
import concurrent.futures

MODEL = "gpt-4"
MAX_TOKENS = 1024
TEMPERATURE = 0.7

class Chat:
    def __init__(self, retries, timeout, max_empty_chunks, retry_delay):
        self.max_retries = retries
        self.timeout = timeout
        self.max_empty_chunks = max_empty_chunks
        self.retry_delay = retry_delay
        self.system_prompt = ""

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt

    def create_prompt(self, user_prompt):
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def call_api(self, client, messages):
        """
        Call the OpenAI API to generate a response.
        """
        # This function will be run in a separate thread to enforce the timeout.
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stream=True
        )
        return response

    def generate_response(self, messages, spinner=None):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        retries = 0
        empty_chunk_count = 0
        while retries < self.max_retries:
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.call_api, client, messages)
                    response = future.result(timeout=self.timeout)  # 60 seconds timeout

                text = ""
                for chunk in response:
                    match (r := chunk.choices[0].finish_reason):
                        case "max_tokens" | "stop":
                            break
                        case None:
                            pass
                        case _:
                            if spinner:
                                spinner.stop()
                                spinner.clear()
                            print("Unexpected completion reason:", r)
                    chunk_text = chunk.choices[0].delta.content
                    if chunk_text.strip() == "":
                        empty_chunk_count += 1
                    text += chunk_text

                if empty_chunk_count > self.max_empty_chunks:
                    retries += 1
                    empty_chunk_count = 0
                    if retries < self.max_retries:
                        if spinner:
                            spinner.stop()
                            spinner.clear()
                        print(" [Received too many empty chunks. Retrying...]")
                        time.sleep(self.retry_delay)
                        if spinner:
                            spinner.start()
                        continue
                    else:
                        raise Exception(" [Received too many empty chunks. Max retries exceeded.]")

                yield text

                break

            except (OpenAIError, concurrent.futures.TimeoutError) as e:
                retries += 1
                if retries < self.max_retries:
                    if spinner:
                        spinner.stop()
                        spinner.clear()
                    print(f"Error occurred. Retrying in {self.retry_delay} seconds... ({e})")
                    time.sleep(self.retry_delay)
                    if spinner:
                        spinner.start()
                else:
                    raise e  # Re-raise if max retries exceeded.

    def accumulate_responses(self, messages, spinner=None):
        text = ""
        try:
            for chunk in self.generate_response(messages, spinner):
                text += chunk
        except Exception as e:
            if spinner:
                spinner.stop()
                spinner.clear()
            print(e)
            return ""
        return text


    def call_gpt4(self, messages, spinner=None):
        messages = self.create_prompt(messages)
        return self.accumulate_responses(messages, spinner)




