import os
import json
import requests
import questionary
import inquirer
import httpx
from bs4 import BeautifulSoup
from aider.coders import Coder
from aider.models import Model
from rich.console import Console
from rich.prompt import Prompt
from chromadb import Client
from chromadb.config import Settings
import hashlib
import torch
from transformers import RobertaTokenizer, RobertaModel

console = Console()

# Initialize ChromaDB client
db = Client(Settings())
files_collection = db.create_collection("files")
urls_collection = db.create_collection("urls")

# Load CodeBERT model and tokenizer
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
model = RobertaModel.from_pretrained("microsoft/codebert-base")

def ask_aider_about_issue(issue_description, files):
    """
    Interact with Aider to inquire about a specific issue.

    Args:
        issue_description (str): Description of the task or issue.
        files (list): List of file paths to include in the chat session.

    Returns:
        str: Aider's response regarding the issue.
    """
    # Initialize the model (e.g., 'groq/llama3-70b-8192')
    model = Model("groq/llama3-70b-8192")

    # Create a Coder instance with the specified model and files
    coder = Coder.create(main_model=model, fnames=files)

    # Send the issue description to Aider and get the response
    response = coder.run(issue_description)

    return response

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

def generate_detailed_prompt(action, focus, subject, context, role="senior software developer"):
    """
    Generates a detailed prompt based on the action, focus, subject, and context.

    Args:
        action (str): The action to be performed (e.g., 'Implement', 'Debug').
        focus (str): The focus area (e.g., 'Login System', 'Database Connection').
        subject (str): The subject or technology (e.g., 'Python', 'JavaScript').
        context (str): Additional context or information.

    Returns:
        str: A detailed prompt tailored to the specified parameters.
    """
    templates = {
        "Implement": (
            "As a {role}, Develop a {focus} using {subject} that achieves the following objectives:\n"
            "{context}\n"
            "Ensure the implementation adheres to best practices and is well-documented."
        ),
        "Debug": (
            "As a {role}, Identify and resolve issues in the {focus} developed with {subject}. The current issues are:\n"
            "{context}\n"
            "Provide a detailed analysis of the problems and the steps taken to fix them."
        ),
        "Optimize": (
            "As a {role}, Enhance the performance of the {focus} written in {subject}. Current performance metrics and areas for improvement are:\n"
            "{context}\n"
            "Implement optimizations and document the performance gains achieved."
        ),
        "Refactor": (
            "As a {role}, Restructure the {focus} codebase implemented in {subject} to improve code quality. The current code issues are:\n"
            "{context}\n"
            "Ensure the refactored code is more maintainable and adheres to coding standards."
        ),
        "Review": (
            "As a {role}, Conduct a comprehensive review of the {focus} developed in {subject}. The aspects to be reviewed include:\n"
            "{context}\n"
            "Provide feedback and suggestions for improvement."
        ),
        "Integrate": (
            "As a {role}, Combine the {focus} with existing systems using {subject}. Integration points and requirements are:\n"
            "{context}\n"
            "Ensure seamless integration and document the process."
        ),
        "Document": (
            "As a {role}, Create detailed documentation for the {focus} implemented in {subject}. Areas to be covered include:\n"
            "{context}\n"
            "Ensure the documentation is clear, comprehensive, and user-friendly."
        ),
        "Test": (
            "As a {role}, Develop and execute test cases for the {focus} written in {subject}. Testing requirements and scenarios are:\n"
            "{context}\n"
            "Ensure all functionalities are thoroughly tested and document the results."
        ),
        "Deploy": (
            "As a {role}, Deploy the {focus} developed in {subject} to the target environment. Deployment details and considerations are:\n"
            "{context}\n"
            "Ensure a smooth deployment process and verify the system's stability post-deployment."
        ),
    }

    template = templates.get(action)
    if not template:
        raise ValueError(f"Unsupported action: {action}")

    return template.format(focus=focus, subject=subject, context=context, role=role)

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

def scrape_url_content(url):
    """
    Scrapes the content of the given URL and returns the text.

    Args:
        url (str): The URL to scrape.

    Returns:
        str: The scraped text content.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()

def generate_id(path: str) -> str:
    """
    Generate a unique ID based on the file path.
    
    Args:
        path (str): The path of the file.
        
    Returns:
        str: A string that serves as a unique identifier.
    """
    return hashlib.sha256(path.encode()).hexdigest()

def sanitize_content(content: str) -> str:
    """
    Sanitize the content to remove any sensitive information.

    Args:
        content (str): The content to sanitize.

    Returns:
        str: The sanitized content.
    """
    # Implement sanitization logic here (e.g., removing API keys, passwords)
    # For demonstration, we'll just return the content as is
    return content

def is_sensitive_content(content: str) -> bool:
    """
    Check if the content contains sensitive information.

    Args:
        content (str): The content to check.

    Returns:
        bool: True if the content is sensitive, False otherwise.
    """
    # Implement logic to identify sensitive content
    # For demonstration, we'll just return False
    return False

def read_code_file(file_path):
    """Read the content of a code file."""
    if not os.path.isfile(file_path):
        print(f"Error: The file {file_path} does not exist.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"An error occurred while reading the file: {str(e)}")
        return None

def vectorize_code(content):
    """Vectorize code content using CodeBERT."""
    inputs = tokenizer(content, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    vectors = outputs.last_hidden_state.mean(dim=1)
    return vectors.numpy().flatten()

def dump_to_chroma(file_path, db_client):
    """Read code file, vectorize it and dump into ChromaDB."""
    code_content = read_code_file(file_path)
    if code_content is None:
        return

    # Vectorize the code content
    code_vector = vectorize_code(code_content)

    # Prepare data for ChromaDB
    document_data = {
        "ids": [os.path.basename(file_path)],  # Unique id for the document
        "types": ["code"],
        "content": [code_content],
        "vectors": [code_vector.tolist()],  # Convert to list for serialization
    }

    # Upsert data into ChromaDB
    db_client.collection("your_collection_name").upsert(document_data)

def store_files_and_urls_in_db(files, urls):
    """
    Store the files and URLs in the ChromaDB database with unique IDs.

    Args:
        files (list): List of file paths.
        urls (list): List of URLs.
    """
    # Process files
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()
            
            if is_sensitive_content(file_content):
                console.print(f"[bold red]Sensitive content detected in file: {file_path}. Please review before uploading.[/bold red]")
                continue

            sanitized_content = sanitize_content(file_content)
            file_id = generate_id(file_path)
            
            # Create vector embedding
            vector = vectorize_code(sanitized_content).tolist()

            # Perform the upsert for a single file
            files_collection.upsert(
                ids=[file_id],
                documents=[sanitized_content],
                metadatas=[{"path": file_path, "type": "file"}],
                embeddings=[vector]
            )
            
        except Exception as e:
            console.print(f"[bold red]Error processing file {file_path}: {str(e)}[/bold red]")

    # Process URLs
    for url in urls:
        try:
            response = requests.get(url)
            url_content = response.text
            
            if is_sensitive_content(url_content):
                console.print(f"[bold red]Sensitive content detected in URL: {url}. Please review before uploading.[/bold red]")
                continue

            sanitized_content = sanitize_content(url_content)
            url_id = generate_id(url)
            
            # Create vector embedding
            vector = vectorize_code(sanitized_content).tolist()

            # Perform the upsert for a single URL
            urls_collection.upsert(
                ids=[url_id],
                documents=[sanitized_content],
                metadatas=[{"url": url, "type": "url"}],
                embeddings=[vector]
            )
            
        except Exception as e:
            console.print(f"[bold red]Error processing URL {url}: {str(e)}[/bold red]")

def load_files_and_urls_from_db():
    """
    Load the files and URLs from the ChromaDB database.

    Returns:
        tuple: A tuple containing a list of file contents and a list of URL contents.
    """
    # Use get() method to retrieve all documents
    files = files_collection.get()
    urls = urls_collection.get()

    # Extract contents from the results
    file_contents = files.get('documents', []) if files else []
    url_contents = urls.get('documents', []) if urls else []

    return file_contents, url_contents

def resolve_conflicts(personas, api_key, file_paths, context_file, max_rounds=10):
    """
    Resolves conflicts between personas by sending their perspectives to the LLM and reaching a consensus.

    Args:
        personas (list): A list of persona dictionaries, each containing 'role', 'background', and 'perspective'.
        api_key (str): The API key for authenticating the request.
        file_paths (list): List of file paths to include in the chat session.
        context_file (str): Path to the context file.
        max_rounds (int): The maximum number of rounds to attempt conflict resolution.

    Returns:
        str: The resolved consensus or final decision after conflict resolution.
    """
    # Read the context file
    with open(context_file, 'r') as f:
        context_contents = f.read()

    # Store files and URLs in the database
    urls = [line.strip() for line in context_contents.splitlines() if line.startswith("http")]
    store_files_and_urls_in_db(file_paths, urls)

    for round in range(max_rounds):
        console.print(f"[bold blue]Conflict Resolution Round {round + 1}[/bold blue]")
        perspectives = "\n".join([f"[bold]{persona['role']}[/bold] ({persona['background']}): {persona['perspective']}" for persona in personas])

        # Reload the files and URLs from the database on each new run
        file_contents, url_contents = load_files_and_urls_from_db()

        # Combine all file contents into one string
        all_files_contents = "\n".join(file_contents)
        all_urls_contents = "\n".join(url_contents)

        # Construct the focus_files string with the file contents and context
        focus_files_str = (
            "Focusing on the following files:\n"
            f"{all_files_contents}\n"
            f"Context from {context_file}:\n"
            f"{context_contents}\n\n"
            f"Additional URL contents:\n"
            f"{all_urls_contents}\n\n"
            "Please provide a supportive response that captures the essence of this process.\n\n"
        )

        # Now integrate that into the content string, using an f-string to interpolate the variable
        prompt = (
            f"The following personas have conflicting perspectives:\n"
            f"{perspectives}\n\n"
            f"David, as the leader, guides the team through a step-by-step process to resolve the issue "
            f"in the given context file. The goal is to foster collaboration among the team members, "
            f"ensuring clarity and structure, and allowing for a consensus on a technical solution that "
            f"addresses all perspectives. The process is:\n\n"
            f"1) Gather All Perspectives: David summarizes each persona's viewpoint.\n"
            f"2) Identify the Core Issue: Examine the context file to determine the root cause.\n"
            f"3) Brainstorm Solutions: Team members offer potential solutions.\n"
            f"4) Discuss and Refine: Collaborate and refine the ideas.\n"
            f"5) Reach Consensus: Arrive at a balanced, feasible technical solution.\n"
            f"6) Record the Action Plan: Document the steps everyone agrees to.\n\n"
            f"7) Display Sudo Code and steps to resolve the issue.\n\n"
            f"{focus_files_str}"
            f"Please provide a structured, supportive response guiding the team through these steps."
        )

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

        response.raise_for_status()

        response_json = response.json()
        aider_response = response_json['choices'][0]['message']['content']
        console.print(f"[bold green]Assistant's Response:[/bold green] {aider_response}")

        for persona in personas:
            console.print(f"[bold]{persona['role']}[/bold] ({persona['background']}): {persona['perspective']}")

        while True:
            user_input = Prompt.ask("[bold yellow]Your response (or type 'exit' to end)[/bold yellow]")
            if user_input.lower() == "exit":
                console.print("[bold red]Exiting chat.[/bold red]")
                return aider_response

            prompt += f"\nUser: {user_input}"

            payload = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )

            response.raise_for_status()

            response_json = response.json()
            aider_response = response_json['choices'][0]['message']['content']
            console.print(f"[bold green]Assistant's Response:[/bold green] {aider_response}")

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
        "User Interface", "API Endpoint", "Vue.js Component", "Dockerfile",
        "Vue.js State Management", "Ansible Playbook", "Ansible Role", "Vite"
    ]
    subjects = [
        "JavaScript", "Python", "Java", "C++", "React", "Angular",  "Dockerfile",
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

    # Extract URL from context and scrape content
    url = None
    for line in context.splitlines():
        if (line.startswith("http")):
            url = line.strip()
            break

    if url:
        url_content = scrape_url_content(url)
        context += f"\n\nScraped Content from URL:\n{url_content}"

    file_paths = prompt_for_files()
    sensitive_files = prompt_for_sensitive_files()
    detailed_prompt = generate_detailed_prompt(action, focus, subject, context)

    personas = [
    {
        "role": "Senior Developer",
        "name": "Emily",
        "background": {
            "experience": "Over 10 years of experience in backend development, specializing in performance optimization and security.",
            "education": "Holds a degree in Computer Science with ongoing professional development in cybersecurity.",
            "work_history": "Has a proven track record of delivering high-performance, secure systems, having worked in both startups and large tech companies."
        },
        "perspective": "Refactor the legacy codebase while maintaining its stability and performance. Prioritize security enhancements and minimize the risk of introducing new bugs."
    },
    {
        "role": "Junior Developer",
        "name": "Jake",
        "background": {
            "experience": "Fresh out of university with a few internships under his belt, eager to prove himself in a professional environment.",
            "education": "Recently completed a degree in Computer Science with a focus on frontend development and user experience.",
            "work_history": "Contributed to minor projects and now ready to contribute to a live product in a high-tech startup."
        },
        "perspective": "Focus on improving the user interface and enhancing the platform's visual appeal. Ensure the code is easy to understand and maintain."
    },
    {
        "role": "DevOps Engineer",
        "name": "Alex",
        "background": {
            "experience": "Extensive experience in setting up and managing CI/CD pipelines and cloud infrastructure, with a focus on automation and efficiency.",
            "education": "Degree in Computer Science with certifications in cloud platforms and DevOps tools.",
            "work_history": "Has worked in various environments, from small startups to large enterprises, ensuring smooth deployments and system stability."
        },
        "perspective": "Prioritize automation and deployment efficiency. Ensure a smooth deployment process and verify the system's stability post-deployment."
    },
    {
        "role": "Product Manager",
        "name": "David",
        "background": {
            "experience": "Background in product management with a focus on user experience and product strategy.",
            "education": "Degree in Business or Marketing with additional training in UX/UI design.",
            "work_history": "Managed products from ideation to launch, with experience in tech startups and digital agencies."
        },
        "perspective": "Refactor the user interface to improve the overall user experience and enhance the platform's visual appeal. Focus on providing a clear and intuitive navigation experience, and consider implementing new features to attract new customers."
    }
    ]

    api_key = os.getenv("GROQ_API_KEY")
    resolved_conflicts = resolve_conflicts(personas, api_key, file_paths, context_file)
    detailed_prompt = generate_detailed_prompt(action, focus, subject, context)

    # Generic pseudoscript outlining best software development steps
    pseudoscript = (
        "1. **Planning**: Define the project scope, objectives, and requirements.\n"
        "2. **Design**: Create architectural and detailed design documents.\n"
        "3. **Development**: Implement the design using {subject}.\n"
        "4. **Testing**: Develop and execute test cases to ensure functionality.\n"
        "5. **Deployment**: Deploy the system to the target environment.\n"
        "6. **Maintenance**: Monitor and maintain the system post-deployment."
        "Please follow the Best Software Development Steps outlined above."
    )

    # Include the detailed prompt in the initial_prompt
    initial_prompt = (
        f"Action: {action}\n"
        f"Focus: {focus}\n"
        f"Subject: {subject}\n"
        f"Sensitive Files: {', '.join(sensitive_files)}\n"
        f"Detailed Prompt:\n{detailed_prompt}\n"
        f"Personas:\n{personas}\n"
        f"Resolved Conflicts:\n{resolved_conflicts}\n"
        f"Please follow the Best Software Development Steps outlined above and incorporate the perspectives of the personas provided.:\n{pseudoscript}\n"
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

    # Read issue_description from context.txt
    issue_description = context

    # Call ask_aider_about_issue with issue_description
    aider_response = ask_aider_about_issue(issue_description, file_paths)
    print(f"Aider's Response: {aider_response}")

if __name__ == "__main__":
    main()
    print("\nPlease manually review the generated files before proceeding.")
    print("Note: This script is still in development. Contributions are welcome!")
    # Generate and print the aider command
    aider_command = generate_aider_command()
    print(f"Run the following command to start aider:\n{aider_command}")
