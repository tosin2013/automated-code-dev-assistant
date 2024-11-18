import os
import json
import requests
import questionary
import inquirer
import httpx

def ensure_api_key():
    """
    Checks if the environment variable 'GROQ_API_KEY' is set.

    If the 'GROQ_API_KEY' environment variable is not set, it prints an error message
    and exits the program with a status code of 1.

    Raises:
        SystemExit: If 'GROQ_API_KEY' is not set in the environment variables.
    """
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY is not set. Please export your API key.")
        exit(1)

def select_option(prompt_text, options):
    """
    Display a selection prompt to the user and return the selected option.

    Args:
        prompt_text (str): The text to display as the prompt.
        options (list): A list of options for the user to choose from.

    Returns:
        str: The option selected by the user.
    """
    answer = questionary.select(
        prompt_text,
        choices=options
    ).ask()
    return answer

def prompt_for_files():
    """
    Prompts the user to select files from the current directory and its subdirectories,
    and saves the selected files to 'files.txt'. If 'files.txt' already exists, the user
    is asked whether to add more files to the existing list.
    Returns:
        list: A list of file paths selected by the user.
    """
    files = []
    for root, _, filenames in os.walk('.'):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    
    existing_files = []
    if os.path.isfile("files.txt"):
        with open("files.txt", "r") as f:
            existing_files = f.read().splitlines()
        if existing_files:
            add_more_files = questionary.confirm(
                message="files.txt already contains files. Would you like to add more files?",
                default=True
            ).ask()
            if not add_more_files:
                return existing_files

    questions = [
        inquirer.Checkbox(
            'selected_files',
            message='Select files to pass to the model',
            choices=files
        )
    ]
    answers = inquirer.prompt(questions)
    selected_files = answers['selected_files']
    
    all_files = existing_files + selected_files
    print("Files to be processed:", ', '.join(all_files))
    with open("files.txt", "w") as f:
        f.write('\n'.join(all_files))
    return all_files

def prompt_for_sensitive_files():
    """
    Prompts the user to specify any sensitive files that should not be modified during the process.

    Returns:
        list: A list of sensitive file paths specified by the user.
    """
    sensitive_files = []
    if os.path.isfile("sensitive_files.txt"):
        with open("sensitive_files.txt", "r") as f:
            sensitive_files = f.read().splitlines()
        if sensitive_files:
            add_more_sensitive_files = questionary.confirm(
                message="sensitive_files.txt already contains files. Would you like to add more files?",
                default=True
            ).ask()
            if not add_more_sensitive_files:
                return sensitive_files

    files = []
    for root, _, filenames in os.walk('.'):
        for filename in filenames:
            files.append(os.path.join(root, filename))

    questions = [
        inquirer.Checkbox(
            'sensitive_files',
            message='Select sensitive files that should not be modified',
            choices=files
        )
    ]
    answers = inquirer.prompt(questions)
    selected_sensitive_files = answers['sensitive_files']
    
    all_sensitive_files = sensitive_files + selected_sensitive_files
    print("Sensitive files:", ', '.join(all_sensitive_files))
    with open("sensitive_files.txt", "w") as f:
        f.write('\n'.join(f"--read {file}" for file in all_sensitive_files))
    return all_sensitive_files

def send_message(user_message, api_key):
    """
    Sends a message to the OpenAI API and retrieves the assistant's reply.

    Args:
        user_message (str): The message to send to the assistant.
        api_key (str): The API key for authenticating the request.

    Returns:
        str: The assistant's reply.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.

    The function sends a POST request to the OpenAI API with the user's message and API key.
    It then processes the response to extract the assistant's reply, prints it, and writes it to a file named 'prompt.txt'.
    """
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": user_message}]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )

    response.raise_for_status()

    response_json = response.json()
    assistant_reply = response_json['choices'][0]['message']['content']
    print("Assistant:", assistant_reply)
    with open("prompt.txt", "w") as f:
        f.write(assistant_reply)
    return assistant_reply

def check_user_agent() -> str:
    """
    Makes a GET request to httpbin.org/user-agent and returns the user agent string.

    Returns:
        str: The user agent string from the response.
    """
    response = httpx.get('https://httpbin.org/user-agent')
    return response.json()['user-agent']

def generate_conventions_md(task_description, intent):
    """
    Generates a CONVENTIONS.md file based on the task description and intent using the Groq LLM.

    Args:
        task_description (str): The task description provided by the user.
        intent (str): The intent or goal of the change.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY is not set. Please export your API key.")
        return

    # Define a structured prompt for the LLM
    prompt = f"""
    You are an assistant helping to create a coding conventions document.
    Based on the task description: "{task_description}", generate a CONVENTIONS.md file
    in the following format:

    ```
    # Coding Conventions

    - **Task Context:** [Brief description of the task or feature]
    - **HTTP Library:** [Preferred library for HTTP requests]
    - **Type Annotations:** [Whether to use type hints or not]
    - **Code Formatting:** [Formatting style, e.g., PEP 8, Google Style]
    - **Error Handling:** [How errors should be handled, e.g., custom exceptions]
    - **Sensitive Files:** [List of sensitive files that should not be modified]

    Add any additional relevant best practices or guidelines specific to the task.
    Ensure the output is concise and formatted properly for a markdown file.
    ```
    """
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        response_json = response.json()
        llm_reply = response_json['choices'][0]['message']['content']
        with open('CONVENTIONS.md', 'w') as file:
            file.write(llm_reply.strip())
        print("CONVENTIONS.md has been generated.")
    else:
        print(f"Error: Received status code {response.status_code} from the API.")

def generate_aider_command():
    """
    Generates the aider command based on the outputs of the script.
    """
    command = [
        "aider",
        "$(cat files.txt)",
        "--architect",
        "--model", "groq/llama3-8b-8192",
        "--editor-model", "groq/llama3-8b-8192",
        "--message-file", "prompt.txt",
        "--read", "CONVENTIONS.md",
        "$(cat sensitive_files.txt)"
    ]
    return " ".join(command)

def main():
    """
    Main function to execute the script.

    This function performs the following steps:
    1. Ensures the API key is available.
    2. Prompts the user to select an action, focus, and subject from predefined lists.
    3. Reads context information from a file named 'context.txt'.
    4. Prompts the user to specify file paths.
    5. Constructs an initial prompt using the selected options and context information.
    6. Writes the initial prompt to a file named 'initial_prompt.md'.
    7. Sends the initial prompt to an assistant and handles the assistant's replies in a loop.
        - If the assistant's reply ends with a question mark, prompts the user for a response.
        - Appends the user's response to the initial prompt and sends it to the assistant again.
        - Exits the loop if the user types 'exit' or if the assistant has no further questions.

    Raises:
         SystemExit: If the context file 'context.txt' does not exist.
    """
    ensure_api_key()
    actions = [
        "Implement", "Debug", "Optimize", "Refactor", "Review",
        "Integrate", "Document", "Test", "Deploy"
    ]
    focuses = [
        "Login System", "Sorting Algorithm", "Database Connection",
        "User Interface", "API Endpoint", "Vue.js Component",
        "Vue.js State Management", "Ansible Playbook", "Ansible Role", "Vite"
    ]
    subjects = [
        "JavaScript", "Python", "Java", "C++", "React", "Angular",
        "Django", "Flask", "TensorFlow", "Vue.js", "Ansible", "Vite"
    ]

    action = select_option("Select an action", actions)
    focus = select_option("Select a focus", focuses)
    subject = select_option("Select a subject", subjects)

    context_file = "context.txt"

    if os.path.isfile(context_file):
        with open(context_file, "r") as f:
            context = f.read()
    else:
        print(f"The context file '{context_file}' does not exist.")
        print("Please create the file with the necessary context information.")
        print("You can use the following command to create the file:")
        print(f"  nano {context_file}")
        print("After creating the file, run this script again.")
        exit(1)

    file_paths = prompt_for_files()
    sensitive_files = prompt_for_sensitive_files()

    initial_prompt = (
        f"Action: {action}\n"
        f"Focus: {focus}\n"
        f"Subject: {subject}\n"
        f"Context:\n{context}\n"
        f"Sensitive Files: {', '.join(sensitive_files)}"
    )

    with open("initial_prompt.md", "w") as f:
        f.write(initial_prompt)

    intent = input("What is the intent or goal of this change? ")

    if os.path.isfile("CONVENTIONS.md"):
        update_conventions = questionary.confirm(
            message="CONVENTIONS.md already exists. Would you like to update it?",
            default=True
        ).ask()
        if update_conventions:
            generate_conventions_md(f"Action: {action}, Focus: {focus}, Subject: {subject}", intent)
    else:
        generate_conventions_md(f"Action: {action}, Focus: {focus}, Subject: {subject}", intent)

    assistant_reply = send_message(initial_prompt, os.getenv("GROQ_API_KEY"))

    while True:
        if assistant_reply.strip().endswith("?"):
            user_input = input("Your response (or type 'exit' to end): ")
            if user_input.lower() == "exit":
                print("Exiting chat.")
                break

            initial_prompt += f"\nUser: {user_input}"

            with open("initial_prompt.md", "w") as f:
                f.write(initial_prompt)

            assistant_reply = send_message(initial_prompt, os.getenv("GROQ_API_KEY"))
        else:
            print("No further questions from the assistant. Exiting chat.")
            break



if __name__ == "__main__":
    main()
    print("\nPlease manually review the generated files before proceeding.")
    print("Note: This script is still in development. Contributions are welcome!")
    # Generate and print the aider command
    aider_command = generate_aider_command()
    print(f"Run the following command to start aider:\n{aider_command}")
