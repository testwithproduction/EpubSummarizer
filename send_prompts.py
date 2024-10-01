import os
from pathlib import Path

import click
from openai import OpenAI
from dotenv import load_dotenv


class Model:
    openai_models = ["gpt-4o-mini", "gpt-4o"]

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.client = None
        if name in self.openai_models:
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("API key not found. Please set it in the .env file.")
        else:
            if not self.url:
                raise ValueError("Please provide a valid URL for the model.")
            # could be any value except an empty string
            api_key = name
        self.client = OpenAI(base_url=self.url, api_key=api_key)


class PromptProcessor:
    def __init__(self, book_path, model):
        self.book_path = Path(book_path)
        self.order_file = self.book_path / "files_order.txt"
        self.base_prompt_file = "base_prompt.txt"
        self.responses_dir = self.book_path / "responses"
        self.responses_dir.mkdir(exist_ok=True)
        self.model = model
        self.base_prompt = self.read_base_prompt()

    def read_order_file(self):
        with open(self.order_file, "r", encoding="utf-8") as file:
            order = file.readlines()
        return [x.strip() for x in order]

    def read_base_prompt(self):
        with open(self.base_prompt_file, "r", encoding="utf-8") as file:
            base_prompt = file.read()
        return base_prompt

    def read_file_content(self, file_name):
        file_path = self.book_path / file_name
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    def send_prompt(self, prompt):
        response = self.model.client.chat.completions.create(
            model=self.model.name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def process_files(self):
        ordered_files = self.read_order_file()
        total_files = len(ordered_files)
        print(f"Processing {total_files} files...")

        for i, file_name in enumerate(ordered_files, 1):
            print(f"Reading file {i}/{total_files}: {file_name}")
            content = self.read_file_content(file_name)
            full_prompt = f"{self.base_prompt}\n\n{content}"
            print(f"Sending prompt for file {i}/{total_files}")
            response = self.send_prompt(full_prompt)
            response_file = self.responses_dir / f"{Path(file_name).stem}_response.md"
            with open(response_file, "w", encoding="utf-8") as file:
                file.write(response)
            total_response_file = self.responses_dir / "total_response.md"
            with open(total_response_file, "a", encoding="utf-8") as file:
                file.write(f"{response}\n\n")
            print(f"Response for file {i}/{total_files} saved to {response_file}")

        print("All files processed successfully.")


@click.command()
@click.argument("book_folder")
@click.option("--model_name", default="gpt-4o-mini")
@click.option("--model_url")
def main(book_folder, model_name, model_url):
    model = Model(model_name, model_url)
    prompt_processor = PromptProcessor(book_folder, model)
    prompt_processor.process_files()
    print(f"Responses saved in {prompt_processor.responses_dir}")


if __name__ == "__main__":
    main()
